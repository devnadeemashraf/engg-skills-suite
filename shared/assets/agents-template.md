# <Project>: agent instructions

Read this file in full at the start of every session and follow it step by step. If anything else (tool defaults, memory, another file) disagrees with it, this file wins. Only a direct instruction from the human overrides it.

## 1. Commands

Run every command from the repo root. `<skills>` is the folder the engg skills are installed in (for example `~/.claude/skills/engg-build`).

| Command | What it does |
| --- | --- |
| `python <skills>/scripts/brief.py` | Prints the handoff and the one next thing to do, with the EDD sections it cites. **Always start here.** |
| `python <skills>/scripts/map.py [path]` | Files with their exported symbols. `--dirs` shows the shape of the repo. Use it before searching. |
| `<check command>` | Runs every gate CI runs (or `python <skills>/scripts/check.py`, which reads `.engg/check.toml`). Green: one line per stage. Red: only the failing stage's tail. |
| `<format command>` | Formats files and applies safe lint fixes. |
| `<dev command>` | Starts the app locally. |
| `python <skills>/scripts/attribution_check.py --range origin/main..HEAD` | Fails if any commit or added line carries AI attribution. |

## 2. Reading and output rules

1. Start from `brief.py`. It prints everything the next step needs.
2. Find before you read: run `map.py` and search, then open only the files the chunk names, its Follow files, or what the search points to. Read long files by range.
3. Never open lockfiles, generated files, build output, coverage or vendored code: `<paths>`. Never re-read a file you already read this session unless it changed.
4. Before using an API you haven't seen used in this repo, read the pinned version's docs or type definitions. Never rely on memory for signatures, flags or defaults.
5. Don't echo file contents, restate the chunk or narrate your steps. Output the code, the command results asked for, and the final report.

## 3. The chunk loop

1. Run `brief.py`. Resume an In progress entry first, then Fix first entries, then the next chunk.
2. Read only the files the chunk names, including its Follow files.
3. `git switch <main> && git pull`, then `git switch -c <type>/<ID>-<short-slug>`.
4. Tier T2 or T3: write the approach and one rejected alternative in at most 5 lines, for the PR description.
5. Turn every test case on the card into a test named `[<ID> #<n>] <case>`, with the expectation exactly as written. Run them and watch them fail for the right reason.
6. Make the smallest change that passes, in the structure and style of the Follow files.
7. Run the check until it is green. On any failure, use the debug loop (§4). If the chunk can't pass without touching a file outside its scope, stop and ask (§10).
8. A bug outside the chunk's scope: add one line to HANDOFF Fix first (`- FIX-<n> <path>:<line> — <what is wrong>`) and leave it alone.
9. Go through the self-review checklist (§8).
10. Update docs in the same change, only where content changed: HANDOFF; `docs/EDD.md` on a trigger (new module, component or external service, data-model change, non-obvious flow, lasting decision); an ADR for a lasting decision.
11. Commit with Conventional Commits. Push the branch and open the PR: what changed, why this way (non-obvious points only, at most 5 lines), and manual check steps as exact commands a human can paste, starting with `git fetch origin && git switch <branch>` and ending with `git switch <main>`.
12. Close the chunk in `docs/BLUEPRINT.md`: delete its card and add `- <ID> <title> — Wave <W> — #<PR>` under Done.
13. Switch back to `<main>`. Stop every process you started. Report in at most 8 lines: what changed, the last lines of the real check output, the manual check, risks.

## 4. The debug loop (any failure)

1. Reproduce it on a fresh process, with the exact command and its full output. If you can't reproduce it, stop and report.
2. Read the whole error. Find the first frame in our own code, and trace back to where the wrong value first appears.
3. Write one hypothesis in one line: what is wrong, why, and the evidence. No evidence, no change.
4. Write a test that fails for this reason, if none does.
5. Make one change that fixes the cause, not the symptom. Run again.
6. If it didn't work, revert it, note what it ruled out, and go back to step 2. After three ruled-out hypotheses, stop and ask, listing what you learned.

Never change several things at once, re-run hoping for a different result, or change dependency versions as a guess. Remove temporary logging before committing.

## 5. The review loop (T2 and T3 chunks)

Run it in a fresh session, on a different model from the implementer's where possible: `engg-audit` Mode A on the PR's diff. Check that every test case exists with its expectation unchanged, that failure cases really reach the failure path, that the code follows the Follow files, and that nothing outside scope changed. Report findings with file and line, at most 15 lines. Edit nothing; the implementing session fixes them.

## 6. The wave gate

`brief.py` prints `WAVE GATE DUE` when a wave has no open chunks. On branch `docs/gate-<wave>`: compare what was built against `docs/EDD.md` and report drift; turn each recurring mistake into a lint rule or check (only if that's impossible, add a line to this file); split the next wave's chunks in detail; record `- Gate <W> — <date>` under Done; open the PR. The human runs the main flows by hand before the next wave starts.

## 7. Coding rules (tooling enforces the rest)

<Fill from `.engg/architecture.yaml` and the EDD. One numbered line each; the examples show the level of detail.>

1. Layers: `<domain>` → `<application>` → `<adapters>` and `<transport>`. Another module is imported only through its `<public entry>`. The check enforces this.
2. Names: `<file case>`; one use case per file, named verb-noun; ports are interfaces in `<path>`; adapters are named `<Tech><Port>`.
3. Errors: expected failures use `<error type>` from the module's `<errors file>`. Catch only to add context or translate a driver error at the boundary. Never catch to ignore.
4. Logging: the injected logger only. Never log bodies, tokens, passwords, secrets or personal data.
5. Input: every external input is validated by a strict schema at the boundary.
6. Time, ids and config: injected clock and id generator in the core; read the environment only in `<config path>`.
7. Data: migrations are forward-only (expand → backfill → contract); never edit an applied migration. Money is integer minor units plus a currency.
8. Tests: `<unit test location and naming>`; integration `<pattern>`; property-based tests for parsers, money and invariants. Never mock the thing under test.

## 8. Self-review checklist

1. Every test case on the card exists as `[<ID> #<n>]`, with its expectation unchanged.
2. Each failure test asserts the specific error or status, not just "throws".
3. The diff touches only the chunk's files in scope.
4. Structure and naming mirror the Follow files.
5. No secrets or personal data in logs, errors or responses.
6. No debug logging, commented-out code, or TODO without a chunk ID.
7. Any new dependency is named by the chunk and pinned exactly.
8. The EDD trigger, if any, is handled.
9. The commit message and PR text describe the change, not how it was produced, and carry no AI attribution.

## 9. Never

- Commit to or merge into `<main>`. The human merges.
- Edit generated or vendored files, or lockfiles by hand.
- Read secrets (`.env`, keys, tokens).
- Change or delete an existing test's expectation.
- Add a dependency the chunk doesn't name, or change a version it doesn't mention.
- Leave a TODO without a chunk ID.
- Add AI attribution anywhere: no `Co-Authored-By` or `Generated-by` trailer naming an AI tool or model, no "generated with" line in a PR, no mention of an AI tool in code, comments, commits, docs or release notes, even when a tool adds one by default.
- Silence a failure to get to green: skip a test, widen a timeout, swallow an error, loosen a type, add a lint ignore, or raise a threshold.

## 10. Stop and ask instead of guessing

Ask the human when the chunk is ambiguous or conflicts with the EDD; a listed test expectation looks wrong; the work needs a dependency or decision the chunk doesn't state; the debug loop has ruled out three causes; the change would touch auth, payments, deletion, migrations or secrets beyond what the chunk says; or the EDD seems to need a change. Write the question under HANDOFF "Questions for the human", then stop.
