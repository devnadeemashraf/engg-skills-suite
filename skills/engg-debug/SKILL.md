---
name: engg-debug
description: Runs an evidence-driven scientific debugging and performance profiling loop across backend, web, mobile, game, database, and infrastructure systems. Enforces reproduction, measurement, hypothesis isolation, root-cause fixes, and permanent regression tests instead of guesswork patching. Use when investigating bugs, crashes, race conditions, memory leaks, latency spikes, frame drops, or slow queries.
license: Apache-2.0
metadata:
  version: "2.0.0"
  suite: "engg-skills-suite"
  standard: "agentskills.io"
---

# Evidence-Driven Debugging & Performance Profiling

Solve complex defects and performance bottlenecks systematically using the scientific method—never shotgun edits or unmeasured micro-optimizations.

## When to Use

- Investigating crashes, intermittent bugs, race conditions, deadlocks, memory/handle leaks, or data corruption.
- Diagnosing p99 latency spikes, N+1 queries, web jank/CLS/bundle bloat, mobile ANRs/battery drain, game frame-time/GC spikes, or infra OOMKills/cold starts.

## Non-Negotiable Rules

1. **Read playbooks first:** Load `references/profiling-playbooks.md` for the active stack before proposing fixes.
2. **Never guess-patch:** Do not edit code until you have a concrete reproduction or hard telemetry/profiler evidence proving the root cause.
3. **Measure before AND after:** Every performance optimization must report exact baseline metrics vs. post-fix metrics under identical conditions.
4. **Fix the root cause, not the symptom:** Adding `sleep()`, swallowing an exception, or slapping a cache over a broken O(N^2) query is prohibited.
5. **Lock every fix with a regression test:** Every bug fix must add an automated test that fails before the fix and passes after.
6. **Use the open-source toolchain, with consent:** run `scripts/toolcheck.sh` (Windows: `scripts/toolcheck.ps1`) from this skill's folder to see which tools in `references/toolchain.md` are installed, and prefer them over reading code by hand. Never install a missing tool without following `references/tool-consent.md`.

## Workflow

1. **Capture Symptoms & Establish Baseline:**
   - Collect exact error messages, stack traces, logs, trace IDs, repro steps, environment/version details, and quantitative baseline numbers (e.g., p99 ms, frame time ms, heap MB, query cost).
2. **Create Minimal Deterministic Reproduction:**
   - Narrow the failure into the smallest failing test, CLI command, query, or benchmark harness.
   - For intermittent/race bugs, run under stress loops, race detectors, or deterministic seeded replay.
3. **Instrument & Profile (Evidence Collection):**
   - Select the right profiler for the bottleneck (CPU flamegraph, heap/allocation profile, lock contention, `EXPLAIN (ANALYZE, BUFFERS)`, browser Performance/Memory panel, mobile systrace/Instruments, GPU/frame profiler).
   - Identify the exact hot path or failing invariant—cite file, line, and measured cost.
4. **Form & Test Ranked Hypotheses (1–3 max):**
   - State the primary hypothesis, what evidence would confirm it, and what evidence would falsify it.
   - Verify via a targeted diagnostic probe before modifying production logic. For regressions, let git find the commit: `git bisect start <bad> <good>` then `git bisect run <repro-script>`, where the script exits 0 when good and 1 when bad (125 to skip an unbuildable commit). Cite the first bad commit.
   - Use the graph for "what else does this touch?" (`graphify affected "<symbol>"`) instead of reading call sites by hand.
5. **Apply Minimal Surgical Fix + Regression Test:**
   - Write the failing regression test (or benchmark assertion) first.
   - Implement the cleanest root-cause fix upholding SOLID/KISS/ATOMIC principles.
   - Verify before/after metrics and run the full verification suite + `engg-audit` (Mode A) on the diff.
   - Report performance work as an **evidence table**: metric, baseline, after, same machine/data/load, number of runs, and the variance. A single run proves nothing. Repeat each measurement (at least 5 runs) and report the median and spread.
6. **Emit Post-Incident Note (for P0/P1 defects):**
   - Document Root Cause, Trigger Condition, Fix, Before/After Evidence, and Systemic Prevention (lint rule, invariant, or alert).

## Gotchas

- **Premature micro-optimization:** Optimizing a function accounting for 0.4% of frame/request time while ignoring a 60% I/O stall or GC spike wastes time and harms readability.
- **Observer effect:** Heavy synchronous debug logging inside a race condition or hot loop can mask the very bug you are hunting.
- **Fixing the reproduction, not the bug:** a fix that only makes the repro script pass, for example by special-casing its input, isn't a fix. The regression test must express the general invariant.
- **Dirtying the repo with debug prints:** Remove all temporary instrumentation before committing, or promote genuinely useful signals into structured observability.
