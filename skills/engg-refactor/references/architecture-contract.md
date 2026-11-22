# Architecture Contract (`.engg/architecture.yaml`)

The contract is the single, machine-readable statement of how a codebase must be structured: its layers, which layer may import which, what external packages a layer may use, and how feature modules talk to each other.

- `engg-architect` writes it (greenfield) or ratifies it from an as-is draft (brownfield).
- Audits and extensions check code against it.
- **Never hand-write enforcer configs.** Compile them from the contract with `scripts/compile_contract.py`, so the IDE, pre-commit and CI all enforce the same rules.

## Schema (version 1)

```yaml
version: 1                       # required; always 1 for this schema
name: shop-api                   # required; used in rule names and messages
style: hexagonal                 # required: hexagonal | clean | layered | feature-sliced | mvvm | ecs | modular-monolith

layers:                          # required; list inner -> outer
  - name: domain                 # lowercase a-z, 0-9, hyphens; unique
    paths: ["src/*/domain/**"]   # repo-relative globs (see "Globs")
    may_import: []               # other layers this one may import; its own layer is always allowed; "*" = any
    external: none               # any (default) | none | [allowlist of package names]
  - name: application
    paths: ["src/*/app/**"]
    may_import: [domain]
  - name: adapters
    paths: ["src/*/adapters/**"]
    may_import: [domain, application]
  - name: composition
    paths: ["src/main.ts"]
    may_import: ["*"]

modules:                         # optional: vertical-slice isolation
  paths: "src/*"                 # one glob ending in "/*"; the "*" is the module name
  public_entry: [index.ts]       # files (relative to a module) other modules may import

rules:
  no_cycles: true                # default true

limits:                          # optional; not compiled; checked by engg-deep-audit
  max_file_lines: 400
  max_function_complexity: 12

targets:                         # required; at least one enforcer to compile for
  typescript: { tsconfig: tsconfig.json }        # dependency-cruiser; tsconfig is optional
  python: { root_package: shop, source_root: src } # import-linter
  go: {}                                         # go-arch-lint
```

### Globs

Paths are relative to the repository root and always use `/`.

| Pattern | Meaning |
|---|---|
| `*` | Any characters within one path segment |
| `**` | Any number of segments, including none |
| `src/*/domain/**` | Everything under `domain/` in every first-level folder of `src/` |
| `src/main.ts` | Exactly that file |

Only letters, digits, `_ . - / * @` are allowed in paths.

- **Python:** each path must start with `<source_root>/<root_package>`, must end in `/**` or name a `.py` file, and may use `*` only as a whole segment. It is converted to a module pattern: `src/shop/*/domain/**` becomes `shop.*.domain`.
- **Go:** paths are package directories, as go-arch-lint expects.

## What each enforcer covers

Run `scripts/compile_contract.py` and read its **coverage report**. A rule a target can't express is reported as not covered, never silently dropped.

| Contract rule | dependency-cruiser (TS/JS) | import-linter (Python) | go-arch-lint (Go) |
|---|---|---|---|
| `may_import` between layers | ✅ forbidden rule per layer | ✅ forbidden contract per layer | ✅ `mayDependOn` |
| `external: none` / allowlist | ✅ by dependency type, plus an allowlist of paths | ❌ not covered: import-linter can only forbid named packages | ✅ vendors + `canUse` (the standard library is always allowed) |
| `modules` isolation with `public_entry` | ✅ group-matching rule | ❌ not covered: the public-entry exception isn't expressible | ❌ not covered |
| `rules.no_cycles` | ✅ `circular` rule | ❌ not covered: use the deep audit's graph | ✅ the Go compiler rejects import cycles |
| `limits` | ❌ deep-audit | ❌ deep-audit | ❌ deep-audit |

## Compile and run

```bash
python <skill-dir>/scripts/compile_contract.py                 # reads .engg/architecture.yaml, writes .engg/generated/
python <skill-dir>/scripts/compile_contract.py --check         # exit 1 if generated files are stale (use in CI)
```

The script needs Python 3.10+ and PyYAML. If PyYAML is missing, run it with `uv run --with pyyaml python <script>`; that is a tool install, so follow the tool consent protocol first.

Generated files go to `.engg/generated/`. They start with a "generated, do not edit" header and never overwrite the project's own configs:

| Target | Generated file | Run it |
|---|---|---|
| TypeScript | `.engg/generated/dependency-cruiser.cjs` | `npx depcruise --config .engg/generated/dependency-cruiser.cjs <source dirs>` |
| Python | `.engg/generated/importlinter.ini` | `lint-imports .engg/generated/importlinter.ini` (with `<source_root>` on `PYTHONPATH`) |
| Go | `.engg/generated/go-arch-lint.yml` | `go-arch-lint check --arch-file .engg/generated/go-arch-lint.yml` |

Commit `.engg/architecture.yaml` and `.engg/generated/`. Wire the run commands into pre-commit and CI as required checks.

## Writing a good contract

- **Start from reality in brownfield code.** Draft the as-is layers from the directory layout and the dependency graph, then agree the to-be contract with the owner. Existing violations go into a ratchet baseline (see the constitution); they are never hidden by loosening the contract.
- **Every source file should belong to exactly one layer.** Files in no layer escape every rule.
- **Keep `may_import` minimal.** Dependencies point inward: domain imports nothing, and composition imports everything.
- **The domain is pure.** Set `external: none` or a short allowlist (for example a validation library) for the innermost layer.
