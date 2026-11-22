# Tool Consent Protocol

Open-source tools compute in seconds what reading code by hand gets wrong or misses: dependency graphs, dead code, duplication, secrets, vulnerable dependencies. Use them, but **never install anything without the user's explicit yes.**

## 1. Detect (read-only)

Run the toolcheck script that ships in this skill's `scripts/` folder, naming the tools the task needs:

```bash
bash <skill-dir>/scripts/toolcheck.sh graphify rg gitleaks        # macOS / Linux / Git Bash
pwsh -File <skill-dir>/scripts/toolcheck.ps1 graphify rg gitleaks # Windows (or: powershell -File ...)
```

- No arguments: reports every known tool and exits 0.
- With arguments: exits 1 if any named tool is missing, 2 for an unknown name.
- `--json` (bash) or `-Json` (PowerShell) prints machine-readable output.
- Status `conflict` means a different program owns that command name. Example: OpenShift's `oc` instead of only-cli's `oc`. Use the fallback the registry gives (e.g. `npx @only-cli/oc`).

## 2. Propose (one grouped question)

For the missing tools, ask **once**, with one entry per tool in this format:

> **<tool>** (<licence>, <runtime>): <what it does in one line>.
> **Why now:** <what this task gains: fewer tokens, a check reading can't do, higher accuracy>.
> **Data:** <runs offline | sends X to Y>.
> **Install:** `<user-scoped command>` · **Remove:** `<uninstall command>`

Then offer: install all, pick some, or none.

- Group the request: one question per task, not one per tool.
- Only propose tools the current task actually needs.
- Say plainly when a tool sends data off the machine.

## 3. Verify before running the install

Before you run an approved install command:

1. Confirm the package name, current stable version, and install command from a live primary source (registry CLI such as `npm view`, `pip index versions`, or `go list -m -versions`, or the project's release page). The registry in `toolchain.md` is a starting point, not proof. Names collide: for example, PyPI hosts unaffiliated `graphify*` packages.
2. Check the release for known advisories (OSV) and check the licence is acceptable for the user.
3. Prefer installs that are **user-scoped and easy to undo**, in this order:
   - a project dev-dependency or ephemeral runner (`npx`, `uvx`, `pipx run`)
   - a per-user tool manager (`uv tool`, `pipx`, `mise`, `go install`, `cargo install`)
   - a system package manager (`brew`, `scoop`, `winget`)
   - a checksum-verified release binary
4. Never use `sudo`, admin rights, `curl | sh`, or global system packages without asking separately and getting a yes.

## 4. Record

Write what was installed to `.engg/toolchain.lock` in the target repo, so CI and other machines use the same versions:

```yaml
# .engg/toolchain.lock
graphify:  { version: "<x.y.z>", via: "uv tool install graphifyy==<x.y.z>", verified: "<YYYY-MM-DD>" }
gitleaks:  { version: "<x.y.z>", via: "brew install gitleaks", verified: "<YYYY-MM-DD>" }
```

## 5. If the user declines

Use the fallback listed for that tool in `toolchain.md`: usually `git`, `ripgrep`, or the language's own tooling. **State which accuracy is lost.** Example: "Without a dependency-graph tool, layer violations are found by import search only; dynamic imports and re-exports may be missed." Never silently pretend the tool's check was done.
