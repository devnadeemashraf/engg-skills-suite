# Roadmap Grill Session Question Bank

Select 5–7 sharp questions per round based on the roadmap's current maturity and repo state. Challenge vague answers directly like a Principal Engineer in a quarterly planning review.

## Round 1: Outcome Sharpness & Codebase Reality Check
- What single measurable user or engineering outcome proves the **next milestone** succeeded?
- Which items on this roadmap are already partially built in the repo, and which ones silently assume foundations (auth, schema, CI, test harness, telemetry) that do not exist yet?
- Where is the team/developer currently losing the most time each week (bugs, manual deploys, flaky tests, slow builds, unclear contracts), and why is fixing that not in Milestone 1?
- Are any roadmap items driven by sunk-cost attachment rather than real user pain or delivery leverage?

## Round 2: Scope Razor & Non-Goals
- **The 50% Timeline Razor:** If your delivery window were cut in half tomorrow, which 2–3 items survive and which ones get cut immediately?
- Which features are speculative V2 optimizations masquerading as V1 requirements (e.g., multi-region, custom plugin frameworks, complex theming, premature microservices)?
- What can be solved today with an off-the-shelf tool, standard library, or simpler manual workflow instead of custom engineering?
- What explicit **Non-Goals** must we write down so scope cannot creep back in mid-sprint?

## Round 3: Risk-First Re-Sequencing & Vertical Slicing
- What is the **single riskiest technical or product assumption** in this roadmap—and why is it sitting in Milestone 3 instead of being proven in Week 1?
- Which milestones are sliced horizontally ("build all DB schemas", "build all backend APIs", "build all UI later") instead of thin, shippable vertical slices?
- Where are hidden hard dependencies (external API limits, store review times, zero-downtime data migrations, third-party SDK quirks, hardware/frame budgets) that could stall execution?
- Which upcoming milestones can be safely decoupled behind ports/adapters or feature flags so work ships incrementally without breaking live users?

## Round 4: Quality Gates, Budgets & Suite Readiness
- What hard **numeric budgets** (latency p95/p99, Core Web Vitals, mobile cold start, 60/120fps frame time, memory/binary cap, error rate) must each milestone stay inside?
- Which milestones touch live user data, security boundaries, or billing/auth and therefore require `engg-data` zero-downtime migrations or dedicated `engg-audit` hardening before release?
- What is the concrete **release & rollback mechanism** for the next milestone (`engg-ship`)—canary, feature flag, staged store rollout, or versioned binary?
- Which external libraries, SDKs, or APIs in the next milestone need live verification via `engg-research` before committing to the timeline?

## Staff Engineer Pushback Playbook
- **"Everything on this roadmap is P0":** If everything is P0, nothing is prioritized. Force a strict stack rank of the top 3 outcomes.
- **"We will clean up tests / security / debt after launch":** Quantify the compounding drag. Insert thin, high-leverage safety-net prerequisites into Milestone 1 so every later milestone moves faster.
- **"Let's build the whole platform first, then ship features":** Reject horizontal platform-first traps. Prove the platform through one concrete vertical product slice first.
- **"Just estimate how long it will take":** Refuse guesses on fuzzy items. Sharpen the milestone contract, exit criteria, and dependencies first, then hand off to `engg-plan` for atomic chunk sizing.
