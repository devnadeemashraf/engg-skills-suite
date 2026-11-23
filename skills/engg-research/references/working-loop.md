# The Working Loop

The project's files tell every session, and every model, where the work stands, what comes next, and which rules apply. Then nothing depends on a previous conversation. Read the section your step needs, not the whole file.

## 1. Files

| File | Written by | Holds |
|---|---|---|
| `AGENTS.md` (+ `CLAUDE.md` containing `@AGENTS.md`) | `engg-plan` (§4) | Commands, the loops, coding rules, the never-list. Agents read it at session start. |
| `docs/HANDOFF.md` | every skill, at the end of its step | The pointer: stage, in progress, fix first, questions for the human, gotchas, next. At most 60 lines. |
| `docs/CHARTER.md` | `engg-ideate` | Problem, users, V1 scope, non-goals, success criteria. |
| `docs/EDD.md` | `engg-architect` | The big picture and the living handbook: modules, contracts, data, budgets. Numbered sections (`## 3. Contracts`), so chunks can cite `EDD §3`. |
| `docs/decisions/NNNN-<slug>.md` | `engg-architect`, any skill making a lasting decision | ADRs. |
| `docs/ROADMAP.md` | `engg-roadmap` | Milestones. |
| `docs/BLUEPRINT.md` | `engg-plan` | Ordered chunk cards; finished chunks collapse to one `## Done` line. |
| `.engg/delivery.yaml` · `.engg/architecture.yaml` · `.engg/check.toml` | the skill that decides them | Mode and baseline · the architecture contract · the gate commands. |

**A project that already has its own loop** (an agent file plus its own pointer or plan docs) keeps it. Map each role above onto its files, follow its commands, and never add a parallel set of documents.

## 2. Start of every session

1. Run `python <skill-dir>/scripts/brief.py` from the repo root. It prints the handoff, then the one thing to do next: the In progress entry, else the first Fix first entry, else the next chunk whose dependencies are done, with the EDD and charter sections it cites and its Follow files. It also says when a wave gate is due. With no `docs/HANDOFF.md` yet, start from the user's request.
2. **Find before you read.** Run `python <skill-dir>/scripts/map.py [path]` (files with their exported symbols; `--dirs` for the shape of a large repo), then search (`rg`, or `graphify` when installed). Open only the files the chunk names, its Follow files, or what the search points to. Read a long file by range.
3. Never open lockfiles, generated files, build output, coverage or vendored code. Never re-read a file you already read this session unless it changed.
4. Before using an API you haven't seen used in this repo, check its pinned version's docs (`engg-research`). Never rely on memory for signatures, flags or defaults.
5. Run the gates with `python <skill-dir>/scripts/check.py`: one line per passing stage, and only the tail of a failing one. Use the project's own single check command instead, if it has one.

## 3. Finish a step

1. **Close the chunk** in `docs/BLUEPRINT.md`: delete its card and add `- <ID> <title> — Wave <W> — <commit or PR>` under `## Done`. When a wave's last chunk closes, the wave gate is due: compare what was built against the EDD, split only the next wave's chunks in detail, and record `- Gate <W> — <date>` under Done.
2. **Update `docs/HANDOFF.md`** only where its content changed: clear In progress, delete a fixed Fix first line, add a gotcha that cost time, set Next. A bug found outside the current chunk becomes one Fix first line (`- FIX-<n> <path>:<line> — <what is wrong>`) and is left alone.
3. **Update `docs/EDD.md`** only on a trigger: a new module, component or external service, a data-model change, a non-obvious flow, or a lasting decision (then also an ADR).
4. Commit with a Conventional Commit that describes the change, not how it was produced.
5. **Report in at most 8 lines:** what changed, the real tail of the gate output, how a human checks it by hand (exact commands), and the risks. Stop every process you started first.

## 4. Set it up (`engg-plan`; any skill when `docs/HANDOFF.md` is missing)

- Create `docs/HANDOFF.md` from this template:

```markdown
# Handoff

Stage: <ideate | architect | plan | build | audit | ship> · Mode: <mvp-first | full-sequence> · Baseline: <greenfield | existing | redo>

## In progress
None.

## Fix first
None.

## Questions for the human
None.

## Gotchas
None.

## Next
<one line: the next step and the skill that runs it, e.g. "Approve docs/EDD.md, then engg-plan">
```

- `engg-plan` writes `AGENTS.md` from `assets/agents-template.md`, filling in the project's real commands, layers and naming rules, plus `CLAUDE.md` containing `@AGENTS.md`. When either file already exists, add only the missing sections, and ask before changing the user's text.
- `engg-plan` writes `.engg/check.toml`, one stage per gate, fastest first:

```toml
[[stage]]
name = "format"
run = "npx biome format ."
[[stage]]
name = "test"
run = "npm test"
timeout = 900   # seconds, optional
```

## 5. Rules for every agent

1. **The user's explicit request wins.** These skills set defaults. When the user asks for something a default here would block, such as a document early, a redesign, or skipping a gate they own, do it, or name the exact rule and ask one question. Never silently refuse, and never quietly do less than was asked. Only the safety rules in rule 4 need a separate, explicit yes.
2. **Documents are always allowed.** The charter, EDD, ADRs, blueprint, handoff, agent file, README and any document the user asks for are written when their step needs them. The delivery mode only defers optional polish documentation.
3. **When a live check isn't possible** (no network, no tool), still produce the work. Mark each unchecked version or API claim `unverified` and list it under Questions for the human. Don't refuse, and don't present a guess as fact.
4. **Ask before anything hard to undo or public:** installs (`tool-consent.md`), force-pushes, deleting data or branches, editing secrets or CI permissions, releases, tags and repository settings. Work on a branch; never commit to the default branch or merge a PR yourself. The human merges.
5. **No AI attribution, anywhere.** No `Co-Authored-By` or `Generated-by` trailer naming an AI tool or model, no "generated with" line in a PR, and no mention of an AI tool in code, comments, commits, docs or release notes. This holds even when a tool's default adds one. Write as the project's own engineer. Before a push, run `python <skill-dir>/scripts/attribution_check.py --range origin/main..HEAD`.
6. **Stop and ask** instead of guessing when the next step is ambiguous, a test expectation looks wrong, or a change needs a decision or dependency nobody made. Write the question under Questions for the human, then stop.
7. **Output:** don't echo file contents, restate the chunk or narrate your steps. Show code, the command results that matter, and the report.
