# Cross-Stack Debugging & Profiling Playbooks

## 1. Backend Latency, Leaks & Concurrency
- **Tools:** Language CPU/heap/goroutine/mutex profilers (`pprof`, `py-spy`, `async-profiler`, `perf`, Node `--cpu-prof`/`--heap-prof`), race detectors (`-race`, TSAN), distributed traces.
- **Top Suspects:** Unbounded goroutines/tasks, connection pool exhaustion, lock held across I/O, N+1 DB calls, JSON reflection on huge payloads, missing HTTP keep-alive, DNS/TLS handshake per request, high-cardinality metric OOMs.
- **Rule:** Separate *on-CPU time* from *off-CPU wait time* (I/O, locks, scheduling) before optimizing.

## 2. Web Client Jank, Memory & Bundle Bloat
- **Tools:** Browser DevTools Performance flamegraph, Memory heap snapshot diff (detached DOM nodes), Coverage/bundle analyzer, Lighthouse / Web Vitals traces.
- **Top Suspects:** Layout thrashing (interleaved DOM reads/writes), cascading state re-renders, unvirtualized large lists, uncancelled listeners/timers/observers, synchronous heavy parsing on main thread, unsplit third-party bundles.
- **Rule:** Check INP/long tasks (>50ms) and forced synchronous layouts first; verify detached DOM counts across repeated mount/unmount cycles.

## 3. Mobile Client ANRs, Jank & Battery
- **Tools:** Android Studio Profiler / Perfetto / StrictMode; Xcode Instruments (Time Profiler, Allocations, Leaks, Energy Log).
- **Top Suspects:** Main-thread disk/DB/JSON I/O, unbounded bitmap/image decoding, retained Activity/ViewModel closures, excessive wake locks or aggressive background polling, chatty network payloads.
- **Rule:** Enable strict main-thread violation detection in debug builds; measure cold start and 95th-percentile frame build time on low-end target hardware.

## 4. Game Client Frame Drops, Stutters & Desyncs
- **Tools:** Engine frame/CPU/GPU profilers, RenderDoc/PIX/Metal Debugger, allocation/GC trackers, deterministic state-hash logger.
- **Top Suspects:** Shader compilation hitches, synchronous asset/texture streaming, per-frame GC allocations, draw-call/overdraw spikes, physics tunneling or non-deterministic float order, unpooled particle/projectile spawns.
- **Rule:** Determine whether the frame is **CPU-bound (main/render thread)** or **GPU-bound (vertex/fragment/bandwidth)** first; hunt 99th-percentile *frame spikes*, not just average FPS.

## 5. Database Slow Queries & Contention
- **Tools:** `EXPLAIN (ANALYZE, BUFFERS)`, slow query logs, lock/wait-event views (`pg_stat_activity`, `pg_locks`), index bloat/usage stats.
- **Top Suspects:** Sequential scans from missing/unusable indexes, implicit cast preventing index use, bad join cardinality estimates (stale stats), deep `OFFSET`, lock contention from long transactions, unindexed foreign keys causing slow cascading deletes.
- **Rule:** Compare estimated vs. actual rows in query plans; optimize buffer reads (`shared hit/read`), not just cached wall time.

## 6. Infrastructure & Containers
- **Tools:** Container metrics (`cgroup` CPU throttling vs. OOMKill exit 137), kernel logs (`dmesg`), network packet/DNS checks, IaC state diff.
- **Top Suspects:** Tight CPU limits causing CFS throttling latency spikes, memory leaks triggering OOMKill loops, misconfigured readiness probes causing traffic drops, DNS `ndots` amplification, ephemeral disk exhaustion.
