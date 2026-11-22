"""Tests for shared/scripts/compile_contract.py.

Unit tests cover parsing, validation and translation. Integration tests run the real enforcers
(dependency-cruiser, import-linter) on the fixtures in tests/fixtures/, first clean and then with
planted violations; they are skipped only when the tool isn't installed.
"""
from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "shared" / "scripts"))

import compile_contract as cc  # noqa: E402

FIXTURES = REPO_ROOT / "tests" / "fixtures"
IS_WINDOWS = sys.platform == "win32"


def base_contract(**overrides: object) -> dict:
    data: dict = {
        "version": 1,
        "name": "demo",
        "style": "hexagonal",
        "layers": [
            {"name": "domain", "paths": ["src/*/domain/**"], "may_import": [], "external": "none"},
            {"name": "app", "paths": ["src/*/app/**"], "may_import": ["domain"]},
            {"name": "adapters", "paths": ["src/*/adapters/**"], "may_import": ["domain", "app"]},
            {"name": "main", "paths": ["src/main.ts"], "may_import": ["*"]},
        ],
        "targets": {"typescript": {}},
    }
    data.update(overrides)
    return data


def errors_of(data: object) -> list[str]:
    with pytest.raises(cc.ContractError) as exc:
        cc.parse_contract(data)
    return exc.value.errors


# --------------------------------------------------------------------------- glob translation


@pytest.mark.parametrize(
    ("glob", "matches", "rejects"),
    [
        ("src/*/domain/**", ["src/orders/domain/a.ts", "src/x/domain/deep/b.ts"], ["src/domain/a.ts", "src/a/b/domain/c.ts"]),
        ("src/main.ts", ["src/main.ts"], ["src/mainXts", "src/main.ts.bak", "lib/src/main.ts"]),
        ("**/test/**", ["test/a.ts", "pkg/test/a.ts", "a/b/test/c/d.ts"], ["tests/a.ts", "pkg/test"]),
        ("src/**/index.ts", ["src/index.ts", "src/a/index.ts", "src/a/b/index.ts"], ["src/a/xindex.ts"]),
        ("src/*.config.ts", ["src/app.config.ts"], ["src/a/app.config.ts", "src/appXconfig.ts"]),
        ("**", ["a.ts", "a/b.ts"], []),
    ],
)
def test_glob_to_regex(glob: str, matches: list[str], rejects: list[str]) -> None:
    rx = re.compile(cc.glob_to_regex(glob))
    for path in matches:
        assert rx.match(path), f"{glob} should match {path}"
    for path in rejects:
        assert not rx.match(path), f"{glob} should not match {path}"


NESTED_QUANTIFIER = re.compile(r"\((?:\?:)?[^()]*[*+][^()]*\)[*+?{]")


@pytest.mark.parametrize("glob", ["src/*/domain/**", "**/test/**", "src/**/index.ts", "a/**/b/**/c.ts"])
def test_glob_regex_never_nests_quantifiers(glob: str) -> None:
    # dependency-cruiser rejects regexes with nested quantifiers as unsafe and refuses to run.
    assert not NESTED_QUANTIFIER.search(cc.glob_to_regex(glob))


@pytest.mark.parametrize(
    ("glob", "module"),
    [
        ("src/shop/*/domain/**", "shop.*.domain"),
        ("src/shop/main.py", "shop.main"),
        ("src/shop/orders/__init__.py", "shop.orders"),
        ("src/shop/**/adapters/**", "shop.**.adapters"),
    ],
)
def test_python_module(glob: str, module: str) -> None:
    assert cc.python_module(glob, "src", "shop") == module


def test_python_module_with_repo_root_source() -> None:
    assert cc.python_module("shop/*/domain/**", ".", "shop") == "shop.*.domain"


@pytest.mark.parametrize(
    ("glob", "message"),
    [
        ("lib/shop/x/**", "must start with source_root"),
        ("src/other/x/**", "must be inside root_package"),
        ("src/shop/x/file.ts", "must end with '/**' or name a .py file"),
        ("src/shop/x-y/**", "is not a Python module name"),
        ("src/shop/a*b/**", "is not a Python module name"),
    ],
)
def test_python_module_rejects(glob: str, message: str) -> None:
    with pytest.raises(ValueError, match=re.escape(message)):
        cc.python_module(glob, "src", "shop")


# --------------------------------------------------------------------------- validation


def test_valid_contract_parses() -> None:
    contract = cc.parse_contract(base_contract())
    assert [l.name for l in contract.layers] == ["domain", "app", "adapters", "main"]
    assert contract.no_cycles is True


def test_forbidden_pairs_follow_may_import() -> None:
    contract = cc.parse_contract(base_contract())
    pairs = {(s.name, d.name) for s, d in contract.forbidden_pairs()}
    assert pairs == {
        ("domain", "app"), ("domain", "adapters"), ("domain", "main"),
        ("app", "adapters"), ("app", "main"),
        ("adapters", "main"),
    }


@pytest.mark.parametrize(
    ("mutate", "message"),
    [
        (lambda d: d.update(version=2), "version: must be 1"),
        (lambda d: d.update(style="spaghetti"), "style: must be one of"),
        (lambda d: d.update(extra=1), "unknown top-level key 'extra'"),
        (lambda d: d.update(layers=[]), "layers: required non-empty list"),
        (lambda d: d["layers"][1].update(may_import=["domian"]), "unknown layer 'domian'"),
        (lambda d: d["layers"][1].update(name="Domain"), "must be lowercase"),
        (lambda d: d["layers"][1].update(name="domain"), "duplicate layer name 'domain'"),
        (lambda d: d["layers"][0].update(paths=[]), "paths: required non-empty list"),
        (lambda d: d["layers"][0].update(paths=["/abs/**"]), "must be a relative path"),
        (lambda d: d["layers"][0].update(paths=["src/../x/**"]), "must be a relative path"),
        (lambda d: d["layers"][0].update(paths=["src/a**/x"]), "'**' must be a whole path segment"),
        (lambda d: d["layers"][0].update(paths=["src/[ab]/x"]), "is not a valid path glob"),
        (lambda d: d["layers"][0].update(external="some"), "external: must be 'any', 'none'"),
        (lambda d: d["layers"][0].update(external=[]), "allowlist is empty"),
        (lambda d: d["layers"][3].update(may_import=["*", "domain"]), "'*' must be the only entry"),
        (lambda d: d["layers"][0].update(owner="x"), "unknown key 'owner'"),
        (lambda d: d.update(modules={"paths": "src/*/x"}), "must be a literal directory followed by '/*'"),
        (lambda d: d.update(modules={"paths": "src/*", "public_entry": ["*.ts"]}), "public_entry"),
        (lambda d: d.update(rules={"no_cycles": "yes"}), "no_cycles: must be true or false"),
        (lambda d: d.update(rules={"layering": True}), "only 'no_cycles' is supported"),
        (lambda d: d.update(limits={"max_file_lines": 0}), "must be a positive integer"),
        (lambda d: d.update(limits={"max_lines": 10}), "unknown key 'max_lines'"),
        (lambda d: d.update(targets={}), "targets: required"),
        (lambda d: d.update(targets={"rust": {}}), "unknown target 'rust'"),
        (lambda d: d.update(targets={"typescript": {"strict": "x"}}), "unknown option 'strict'"),
        (lambda d: d.update(targets={"python": {"source_root": "src"}}), "root_package: required"),
    ],
)
def test_invalid_contracts(mutate, message: str) -> None:
    data = base_contract()
    mutate(data)
    assert any(message in e for e in errors_of(data)), errors_of(data)


def test_python_target_validates_paths() -> None:
    data = base_contract(targets={"python": {"root_package": "shop", "source_root": "src"}})
    errors = errors_of(data)
    assert any("layer 'domain'" in e and "inside root_package" in e for e in errors)


def test_non_mapping_contract() -> None:
    assert errors_of(["not", "a", "mapping"]) == ["contract must be a YAML mapping"]


# --------------------------------------------------------------------------- compiled output


def test_typescript_output_structure() -> None:
    data = base_contract(modules={"paths": "src/*", "public_entry": ["index.ts"]})
    data["layers"][1]["external"] = ["zod", "@scope/pkg.js"]
    files, cov = cc.compile_all(cc.parse_contract(data), ".engg/architecture.yaml")
    text = files["dependency-cruiser.cjs"]
    assert text.startswith("// GENERATED by compile_contract.py")
    config = yaml.safe_load(text.split("module.exports = ", 1)[1].rstrip().rstrip(";"))
    names = [r["name"] for r in config["forbidden"]]
    assert "domain-not-to-adapters" in names and "app-not-to-main" in names
    assert "main-not-to-domain" not in names  # may_import "*"
    assert {"domain-external-none", "app-external-allowlist", "modules-isolated", "no-circular", "no-unresolvable"} <= set(names)
    allow = next(r for r in config["forbidden"] if r["name"] == "app-external-allowlist")
    assert "(?:^|/)node_modules/@scope/pkg\\.js/" in allow["to"]["pathNot"]
    assert all(r["severity"] == "error" for r in config["forbidden"])
    for rule in config["forbidden"]:
        for side in ("from", "to"):
            for key in ("path", "pathNot"):
                for rx in ([rule[side][key]] if isinstance(rule[side].get(key), str) else rule[side].get(key, [])):
                    assert not NESTED_QUANTIFIER.search(rx), f"unsafe regex in {rule['name']}: {rx}"
    assert all(status == "covered" for _, target, status in cov.rows if target == "typescript")


def test_tsconfig_option() -> None:
    data = base_contract(targets={"typescript": {"tsconfig": "tsconfig.build.json"}})
    files, _ = cc.compile_all(cc.parse_contract(data), "c.yaml")
    assert '"fileName": "tsconfig.build.json"' in files["dependency-cruiser.cjs"]


def test_python_output_and_coverage() -> None:
    contract = cc.parse_contract(yaml.safe_load((FIXTURES / "contract-py/.engg/architecture.yaml").read_text(encoding="utf-8")))
    files, cov = cc.compile_all(contract, "c.yaml")
    ini = files["importlinter.ini"]
    assert "root_package = shop" in ini
    assert "[importlinter:contract:domain-not-to-adapters]" in ini
    assert "shop.*.domain" in ini and "allow_indirect_imports = True" in ini
    statuses = {rule: status for rule, target, status in cov.rows if target == "python"}
    assert statuses["layers.may_import"] == "covered"
    for rule in ("layers.external", "modules", "rules.no_cycles"):
        assert statuses[rule].startswith("NOT COVERED")


def test_go_output() -> None:
    data = base_contract(targets={"go": {}})
    data["layers"][0]["paths"] = ["internal/*/domain/**"]
    data["layers"][1]["external"] = ["github.com/google/uuid"]
    files, cov = cc.compile_all(cc.parse_contract(data), "c.yaml")
    config = yaml.safe_load(files["go-arch-lint.yml"])
    assert config["version"] == 3
    assert config["allow"] == {"depOnAnyVendor": False}
    assert config["components"]["domain"] == {"in": ["internal/*/domain/**"]}
    assert "mayDependOn" not in config["deps"]["domain"] and "anyVendorDeps" not in config["deps"]["domain"]
    assert config["deps"]["app"]["mayDependOn"] == ["domain"]
    assert config["deps"]["app"]["canUse"] == ["ext-github-com-google-uuid"]
    assert config["vendors"]["ext-github-com-google-uuid"]["in"] == ["github.com/google/uuid", "github.com/google/uuid/**"]
    assert config["deps"]["main"]["anyProjectDeps"] is True
    assert ("rules.no_cycles", "go", "covered by the Go compiler") in cov.rows


def test_limits_reported_not_compiled() -> None:
    data = base_contract(limits={"max_file_lines": 400})
    _, cov = cc.compile_all(cc.parse_contract(data), "c.yaml")
    assert ("limits.max_file_lines", "all", "NOT COMPILED: checked by engg-deep-audit") in cov.rows


def test_output_is_deterministic() -> None:
    contract = cc.parse_contract(base_contract(targets={"typescript": {}, "go": {}}))
    assert cc.compile_all(contract, "c.yaml")[0] == cc.compile_all(contract, "c.yaml")[0]


# --------------------------------------------------------------------------- CLI


def run_cli(cwd: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run([sys.executable, str(REPO_ROOT / "shared/scripts/compile_contract.py"), *args],
                          cwd=cwd, capture_output=True, text=True, timeout=60)


def test_cli_compile_then_check(tmp_path: Path) -> None:
    shutil.copytree(FIXTURES / "contract-ts", tmp_path / "repo")
    repo = tmp_path / "repo"
    assert run_cli(repo, "--check").returncode == 1  # nothing generated yet
    proc = run_cli(repo)
    assert proc.returncode == 0, proc.stderr
    assert "NOT COMPILED: checked by engg-deep-audit" in proc.stdout
    assert run_cli(repo, "--check").returncode == 0
    gen = repo / ".engg/generated/dependency-cruiser.cjs"
    gen.write_text(gen.read_text(encoding="utf-8") + "// hand edit\n", encoding="utf-8")
    assert run_cli(repo, "--check").returncode == 1


def test_cli_reports_invalid_contract(tmp_path: Path) -> None:
    (tmp_path / ".engg").mkdir()
    (tmp_path / ".engg/architecture.yaml").write_text("version: 2\n", encoding="utf-8")
    proc = run_cli(tmp_path)
    assert proc.returncode == 2
    assert "version: must be 1" in proc.stderr


def test_cli_missing_contract(tmp_path: Path) -> None:
    assert run_cli(tmp_path).returncode == 2


# --------------------------------------------------------------------------- real enforcers

DEPCRUISE = shutil.which("depcruise", path=str(REPO_ROOT / "node_modules" / ".bin"))
LINT_IMPORTS = shutil.which("lint-imports", path=str(Path(sys.executable).parent))


def prepare_ts(tmp_path: Path) -> Path:
    repo = tmp_path / "ts"
    shutil.copytree(FIXTURES / "contract-ts", repo)
    for name in ("zod", "left-pad"):  # stand-in npm packages, so imports resolve
        pkg = repo / "node_modules" / name
        pkg.mkdir(parents=True)
        (pkg / "package.json").write_text(f'{{"name":"{name}","version":"1.0.0","main":"index.js"}}', encoding="utf-8")
        (pkg / "index.js").write_text("module.exports = {};\n", encoding="utf-8")
    (repo / "package.json").write_text(
        '{"name":"fixture","private":true,"dependencies":{"zod":"1.0.0","left-pad":"1.0.0"}}', encoding="utf-8")
    assert run_cli(repo).returncode == 0
    return repo


def depcruise(repo: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run([DEPCRUISE, "--config", ".engg/generated/dependency-cruiser.cjs", "--output-type", "err", "src"],
                          cwd=repo, capture_output=True, text=True, timeout=180)


@pytest.mark.skipif(DEPCRUISE is None, reason="dependency-cruiser not installed (npm ci)")
def test_depcruise_clean_fixture_passes(tmp_path: Path) -> None:
    proc = depcruise(prepare_ts(tmp_path))
    assert proc.returncode == 0, proc.stdout + proc.stderr


PLANTED_TS = [
    ("src/orders/domain/leak.ts", 'import { seed } from "../adapters/order-repo";\nexport const x = seed;\n',
     "domain-not-to-adapters"),
    ("src/orders/app/io.ts", 'import { readFileSync } from "node:fs";\nexport const r = readFileSync;\n',
     "application-external-none"),
    ("src/orders/domain/pad.ts", 'import pad from "left-pad";\nexport const p = pad;\n',
     "domain-external-allowlist"),
    ("src/billing/app/peek.ts", 'import type { Order } from "../../orders/domain/order";\nexport type O = Order;\n',
     "modules-isolated"),
    ("src/orders/domain/ghost.ts", 'import { nope } from "./does-not-exist";\nexport const g = nope;\n',
     "no-unresolvable"),
]


@pytest.mark.skipif(DEPCRUISE is None, reason="dependency-cruiser not installed (npm ci)")
@pytest.mark.parametrize(("path", "source", "rule"), PLANTED_TS, ids=[p[2] for p in PLANTED_TS])
def test_depcruise_catches_planted_violation(tmp_path: Path, path: str, source: str, rule: str) -> None:
    repo = prepare_ts(tmp_path)
    (repo / path).write_text(source, encoding="utf-8")
    proc = depcruise(repo)
    assert proc.returncode == 1, proc.stdout + proc.stderr
    assert f"error {rule}: {path}" in proc.stdout


@pytest.mark.skipif(DEPCRUISE is None, reason="dependency-cruiser not installed (npm ci)")
def test_depcruise_catches_cycle(tmp_path: Path) -> None:
    repo = prepare_ts(tmp_path)
    (repo / "src/orders/domain/a.ts").write_text('import { b } from "./b";\nexport const a = () => b;\n', encoding="utf-8")
    (repo / "src/orders/domain/b.ts").write_text('import { a } from "./a";\nexport const b = () => a;\n', encoding="utf-8")
    proc = depcruise(repo)
    assert proc.returncode >= 1
    assert "error no-circular" in proc.stdout


def lint_imports(repo: Path) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ, PYTHONPATH=str(repo / "src"))
    return subprocess.run([LINT_IMPORTS, ".engg/generated/importlinter.ini"],
                          cwd=repo, env=env, capture_output=True, text=True, timeout=180)


def prepare_py(tmp_path: Path) -> Path:
    repo = tmp_path / "py"
    shutil.copytree(FIXTURES / "contract-py", repo)
    assert run_cli(repo).returncode == 0
    return repo


@pytest.mark.skipif(LINT_IMPORTS is None, reason="import-linter not installed")
def test_import_linter_clean_fixture_passes(tmp_path: Path) -> None:
    proc = lint_imports(prepare_py(tmp_path))
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "0 broken" in proc.stdout


@pytest.mark.skipif(LINT_IMPORTS is None, reason="import-linter not installed")
def test_import_linter_catches_planted_violation(tmp_path: Path) -> None:
    repo = prepare_py(tmp_path)
    (repo / "src/shop/orders/domain/leak.py").write_text("from shop.orders.adapters.repo import SEED\n", encoding="utf-8")
    proc = lint_imports(repo)
    assert proc.returncode == 1, proc.stdout + proc.stderr
    assert "Layer 'domain' must not import layer 'adapters' BROKEN" in proc.stdout
    assert "shop.orders.domain.leak -> shop.orders.adapters.repo" in proc.stdout
    assert "1 broken" in proc.stdout
