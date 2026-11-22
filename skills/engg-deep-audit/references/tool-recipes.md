# Tool Recipes (Phase 1: the machine map)

Run from the repository root. `RUN=.engg/audit/<run-id>` and `mkdir -p $RUN/raw $RUN/findings`. Each command writes one file in `$RUN/raw/` that `scripts/build_map.py` reads.

- **Only `files.txt` is required.** Skip any tool that is missing or declined. `build_map.py` records it as "not run", and the report must say that check wasn't done.
- `SRC` means the source directories, for example `src` or `src lib`.
- Commands were verified against the versions listed in `toolchain.md`. If a flag fails, check `<tool> --help` and say what changed.

| Raw file | Command | Exit codes |
|---|---|---|
| `files.txt` (**required**) | `git ls-files > $RUN/raw/files.txt` | 0 |
| `churn.txt` | `git log --since=12.months --numstat --format= > $RUN/raw/churn.txt` | 0 |
| `scc.json` | `scc --by-file --format json -o $RUN/raw/scc.json .` (respects `.gitignore`) | 0 |
| `lizard.csv` | `lizard --csv SRC > $RUN/raw/lizard.csv` (CSV with no header row) | 0 |
| `jscpd/jscpd-report.json` | `npx jscpd --reporters json --output $RUN/raw/jscpd --silent SRC` | 0 |
| `graph.json`, `GRAPH_REPORT.md` | `graphify update .` then copy `graphify-out/graph.json` and `graphify-out/GRAPH_REPORT.md` into `$RUN/raw/`. Code-only and offline; **never** run graphify's semantic (model) pass without consent. | 0 |
| `depcruise.json` (TS/JS) | `python scripts/compile_contract.py` then `npx depcruise --config .engg/generated/dependency-cruiser.cjs --output-type json SRC > $RUN/raw/depcruise.json` | 0 with JSON output; violations are in the file |
| `import-linter.txt` (Python) | `lint-imports .engg/generated/importlinter.ini > $RUN/raw/import-linter.txt` (source root on `PYTHONPATH`) | 0 kept, 1 broken |
| `gitleaks.json` | `gitleaks git . --redact --report-format json --report-path $RUN/raw/gitleaks.json --no-banner` | 0 none, 1 leaks found |
| `osv.json` | `osv-scanner scan source -r --format json --output-file $RUN/raw/osv.json .` | 0 none, 1 vulnerabilities, **128 = no lockfiles found** (record "not applicable") |
| `*.sarif` | Any SARIF-producing scanner: opengrep, a linter's SARIF output. Save as `$RUN/raw/<tool>.sarif`. Check the exact flags with `<tool> --help` first. | tool-specific |

Then:

```bash
python scripts/build_map.py --run-dir $RUN            # writes $RUN/map.json and $RUN/map.md
python scripts/ledger.py init --run-dir $RUN
```

## Safety rules for this phase

- **gitleaks always runs with `--redact`.** Without it, the report stores the secret itself in plain text on disk.
- Scan **git history** (`gitleaks git`), not just the working tree: a secret deleted from the code is still in history, and must be rotated.
- **graphify writes `graphify-out/` into the repo.** Ignore it locally:
  `printf '.engg/audit/\n.engg/generated/\ngraphify-out/\n' >> .git/info/exclude` (local to this clone; changes no tracked file).
- Keep `$RUN/` out of git the same way. It holds paths, findings, and (redacted) leak locations.
- Tools that aren't parsed into the map (import-linter, osv-scanner, knip, vulture) still go in `raw/`. Read them during the units they concern, and cite them in findings as `tool:<name>`.
