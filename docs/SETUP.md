# Setting Up engg-skills-suite

This guide takes you from a fresh clone to your first session, in about five minutes. It covers every supported tool, the optional open-source tools, updating, uninstalling and troubleshooting.

- [1. Requirements](#1-requirements)
- [2. Choose where to install](#2-choose-where-to-install)
- [3. Install](#3-install)
- [4. Set up your tool](#4-set-up-your-tool)
- [5. Check that it worked](#5-check-that-it-worked)
- [6. Your first session in a project](#6-your-first-session-in-a-project)
- [7. Optional open-source tools](#7-optional-open-source-tools)
- [8. Update, uninstall](#8-update-uninstall)
- [9. Troubleshooting](#9-troubleshooting)

---

## 1. Requirements

| Needed for | Requirement |
|---|---|
| Installing | `git`, plus **bash** (macOS, Linux) or **PowerShell 5.1+** (Windows) |
| Using the skills | An agent that supports Agent Skills: Claude Code, Codex, Cursor, GitHub Copilot or Antigravity (see [section 4](#4-set-up-your-tool)) |
| The helper scripts | **Python 3.10+**. The contract compiler and the deep audit's map and ledger also need **PyYAML**. `ratchet.py` and `toolcheck` need nothing extra. |

Nothing else is required. Open-source tools such as graphify or gitleaks are optional, and the agent asks before installing any of them ([section 7](#7-optional-open-source-tools)).

## 2. Choose where to install

| Scope | Skills live in | Choose it when |
|---|---|---|
| **Global** | Your home folder, available in every project on this machine | You want the suite everywhere, in every repository you open |
| **Project** | Inside one repository, versioned with it | A team should share the same skills, or you want them only in one repo |

What the installer creates:

| Scope | Master copy | Linked into |
|---|---|---|
| Global | `~/.engg-skills-suite/skills/` | `~/.claude/skills/` (Claude Code, and Cursor and Copilot through compatibility), `~/.codex/skills/` (Codex) and `~/.gemini/config/skills/` (Antigravity) |
| Project | `<repo>/.agents/skills/` (the open standard: Antigravity, Cursor, Copilot) | `<repo>/.claude/skills/` (Claude Code, and Cursor and Copilot through compatibility) and `<repo>/.codex/skills/` (Codex) |

There is one master copy, and the tool folders link to it, so updating the master updates every tool at once. Use `--copy` if your environment doesn't allow links.

## 3. Install

```bash
git clone https://github.com/devnadeemashraf/engg-skills-suite.git
cd engg-skills-suite
```

### macOS and Linux

```bash
./install.sh --global                          # every project on this machine
./install.sh --project /path/to/your-repo      # one repository
```

| Option | Does |
|---|---|
| `--copy` | Copy files instead of creating symlinks |
| `--dry-run` | Print every step without changing anything |
| `--uninstall` | Remove only this suite's skills; anything else in those folders is left alone |

### Windows (PowerShell)

```powershell
.\install.ps1 -Scope Global
.\install.ps1 -Scope Project -ProjectPath "C:\path\to\your-repo"
```

| Option | Does |
|---|---|
| `-Copy` | Copy files instead of linking |
| `-DryRun` | Print every step without changing anything |
| `-Uninstall` | Remove only this suite's skills |
| `-HomeDir <path>` | Install globally into another home folder |

Links are symbolic links when Windows allows them (Developer Mode or admin). Otherwise they're directory junctions, which need no special rights. Use `install.ps1` on Windows, not `install.sh` in Git Bash: Git Bash's `ln -s` silently makes copies unless native symlinks are enabled.

If PowerShell refuses to run the script, allow it for this one session only: `Set-ExecutionPolicy -Scope Process Bypass`.

## 4. Set up your tool

### Claude Code

Works after either install, with nothing more to do. Start a new session in your project, then type `/` and the skill name (for example `/engg-plan`), or describe the task and Claude picks the matching skill.

### Antigravity

Works after either install: project skills come from `<repo>/.agents/skills/`, global skills from `~/.gemini/config/skills/`. Open the agent side panel's customizations to see what loaded. Restart the window once after a fresh global install.

### Cursor

Works after either install. Cursor reads `.agents/skills/` and `.cursor/skills/`, and also, for compatibility, `.claude/skills/` and `~/.claude/skills/`, which the installer always fills. If a skill doesn't appear in the agent CLI, a project install covers it through `.claude/skills/`.

### GitHub Copilot

Works after either install. Copilot reads project skills from `.github/skills/`, `.claude/skills/` or `.agents/skills/`, and personal skills from `~/.copilot/skills/`, `~/.agents/skills/` or `~/.claude/skills/`.
- In the Copilot CLI, run `/skills reload` after installing, and `/skills info engg-plan` to confirm a skill loaded.
- For Copilot's cloud agent, use a **project** install: personal skills may not be available to an agent running in the cloud.

### Codex

Works after either install. Codex reads `~/.codex/skills/` (personal) and `<repo>/.codex/skills/` (repository), and the installer links both. Run `/skills`, or type `$`, in Codex to pick a skill. Restart Codex after changing `~/.codex/config.toml`.

### A web chat with no file access

Paste or upload a skill's `SKILL.md` and its `references/*.md` files into a project, custom-instruction or knowledge space. The scripts (`compile_contract.py`, `ratchet.py`, the deep audit's map and ledger) need a real file system, so the tool-driven parts work only in a coding agent.

## 5. Check that it worked

```bash
ls ~/.claude/skills | grep engg-          # global install: 13 skills
ls /path/to/your-repo/.agents/skills      # project install
```

Then ask your agent: *"Which engg skills do you have?"* It should list all thirteen, from `engg-ideate` to `engg-ship`.

## 6. Your first session in a project

1. **Open your project** in your agent and start with the skill that fits (see [Which Skill When](../README.md#which-skill-when)). For an existing project, `/engg-plan` or `/engg-deep-audit` is a good first step.
2. **Answer the delivery-mode question.** The first planning or building skill asks:
   - `mvp-first` (the core flow first, then increments) or `full-sequence` (everything in order)
   - whether your current architecture and tooling are fixed (`baseline: existing`)

   The answer is saved in `.engg/delivery.yaml`, so later sessions don't ask again. Change it any time by saying so.
3. **Keep audit output out of git.** The deep audit writes its working files to `.engg/audit/`, and graphify writes `graphify-out/`. The agent adds both to `.git/info/exclude`, which is local to your clone and changes no tracked file, or asks before editing `.gitignore`.
4. **Commit the rest of `.engg/`:** the delivery mode, the architecture contract, the compiled checker configs, the ratchet baseline and the approved tool versions. They're your project's engineering memory.

## 7. Optional open-source tools

The skills work without any extra tools, but they're faster and more accurate with them. When a task needs a tool you don't have, the agent:
- runs a read-only check
- asks you **once**, with what the tool does, why this task needs it, whether any data leaves your machine, and the install and remove commands
- prefers installs that are user-scoped and easy to undo
- never uses `sudo` or global system packages without a separate yes

If you decline, it says what accuracy is lost.

To see what you already have, run the read-only check yourself:

```bash
bash ~/.claude/skills/engg-deep-audit/scripts/toolcheck.sh                         # everything it knows
bash ~/.claude/skills/engg-deep-audit/scripts/toolcheck.sh graphify gitleaks rg    # just these
```

```powershell
& "$HOME\.claude\skills\engg-deep-audit\scripts\toolcheck.ps1"
```

The tools that help most, by job (full list with licences: [toolchain registry](../shared/references/toolchain.md)):

| Job | Tools |
|---|---|
| Understand a codebase without reading every file | graphify (code graph, offline), ripgrep, ast-grep, scc |
| Read the web with fewer tokens | only-cli (`oc`) |
| Enforce the architecture | dependency-cruiser (JS/TS), import-linter (Python), go-arch-lint (Go) |
| Find complexity, duplication and dead code | lizard, jscpd, knip, vulture |
| Security | gitleaks, osv-scanner, opengrep, zizmor, actionlint |

## 8. Update, uninstall

- **Update:** `git pull` in your clone, then run the installer again with the same scope. Global installs refresh the master copy, which updates every linked tool. Project installs are refreshed one repository at a time.
- **Uninstall:** `./install.sh --global --uninstall` (or `--project <path> --uninstall`), or `.\install.ps1 -Scope Global -Uninstall`. It removes only this suite's skills, from every folder the installer filled.

## 9. Troubleshooting

| Symptom | Fix |
|---|---|
| The agent doesn't list the skills | Start a new session (most tools read skills at startup). Check that the folder holds `<skill>/SKILL.md` exactly as named. Run the check in [section 5](#5-check-that-it-worked). |
| Skills appear in one tool but not another | Each tool reads different folders: see [section 4](#4-set-up-your-tool). A project install covers the most tools at once. |
| On Windows, skills installed but empty or stale | You probably ran `install.sh` in Git Bash, which copies instead of linking. Run `install.ps1` instead. |
| `PyYAML is required` from a script | The agent asks before installing it. The quickest, easy-to-undo option is `uv run --with pyyaml python <script>`, or install it into your project's virtual environment. |
| `toolcheck` reports `oc` as `conflict` | Another program (often OpenShift's CLI) owns the name `oc`. Use `npx @only-cli/oc` instead; the skills fall back to it automatically. |
| A `graphify-out/` folder appeared in the repo | It's graphify's output. Keep it out of git with `.git/info/exclude`, or delete it after an audit. |
| The architecture checker can't read TypeScript 7 code | dependency-cruiser 18.8 needs the `swc` parser for TypeScript 7.0. Set `parser: 'swc'` in its options and install `@swc/core`. |

Still stuck? Open an issue with your tool, operating system, install scope, and what the agent says when you ask *"Which engg skills do you have?"*.
