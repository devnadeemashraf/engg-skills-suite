# Graph Report - fixture

## Corpus Check
- 21 files · ~1,666 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 2 file(s) not represented in the graph (top: .log 1, .csv 1)

## Summary
- 74 nodes · 114 edges · 10 communities (8 shown, 2 thin omitted)
- Extraction: 93% EXTRACTED · 7% INFERRED · 0% AMBIGUOUS · INFERRED: 8 edges (avg confidence: 0.85)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `41a3dd73`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- architecture.yaml
- order-repo.ts
- main.ts
- place-order.ts
- order.ts
- layers
- package.json
- payment-client.ts
- Response

## God Nodes (most connected - your core abstractions)
1. `Order` - 7 edges
2. `placeOrder()` - 6 edges
3. `layers` - 5 edges
4. `findOrder()` - 4 edges
5. `getOrder()` - 4 edges
6. `normaliseName()` - 4 edges
7. `register()` - 4 edges
8. `modules` - 3 edges
9. `limits` - 3 edges
10. `Db` - 3 edges

## Surprising Connections (you probably didn't know these)
- `User` --references--> `Order`  [EXTRACTED]
  src/users/app/register.ts → src/orders/domain/order.ts
- `getOrder()` --calls--> `findOrder()`  [EXTRACTED]
  src/orders/http/routes.ts → src/orders/adapters/order-repo.ts
- `migrateAll()` --calls--> `toRow()`  [EXTRACTED]
  src/scratch/tmp-migrate.ts → src/orders/adapters/order-repo.ts
- `placeOrder()` --calls--> `taxFor()`  [EXTRACTED]
  src/orders/app/place-order.ts → src/orders/app/pricing.ts
- `placeOrder()` --calls--> `addCents()`  [EXTRACTED]
  src/orders/app/place-order.ts → src/orders/domain/money.ts

## Import Cycles
- 2-file cycle: `src/orders/app/place-order.ts -> src/orders/app/pricing.ts -> src/orders/app/place-order.ts`

## Communities (10 total, 2 thin omitted)

### Community 0 - "architecture.yaml"
Cohesion: 0.14
Nodes (13): limits, max_file_lines, max_function_complexity, modules, paths, public_entry, name, rules (+5 more)

### Community 1 - "order-repo.ts"
Cohesion: 0.26
Nodes (9): Db, findOrder(), findOrdersByStatus(), OrderRow, toRow(), fromRow(), getOrder(), Request (+1 more)

### Community 2 - "main.ts"
Cohesion: 0.33
Nodes (6): app, formatCurrency(), normaliseName(), isValidEmail(), register(), User

### Community 3 - "place-order.ts"
Cohesion: 0.39
Nodes (6): DEFAULT_CURRENCY, isValidEmail(), placeOrder(), PlaceOrderInput, taxFor(), addCents()

### Community 4 - "order.ts"
Cohesion: 0.67
Nodes (3): cancelOrder(), isValidEmail(), Order

### Community 5 - "layers"
Cohesion: 0.40
Nodes (5): layers, external, may_import, name, paths

### Community 6 - "package.json"
Cohesion: 0.40
Nodes (4): description, name, private, type

### Community 7 - "payment-client.ts"
Cohesion: 0.50
Nodes (3): payment_api_secret, PAYMENT_URL, charge()

## Knowledge Gaps
- **2 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `placeOrder()` connect `place-order.ts` to `main.ts`, `order.ts`?**
  _High betweenness centrality (0.039) - this node is a cross-community bridge._
- **Should `architecture.yaml` be split into smaller, more focused modules?**
  _Cohesion score 0.14285714285714285 - nodes in this community are weakly interconnected._
- **Why does `Response` connect `Response` to `order-repo.ts`?**
  _High betweenness centrality (0.034) - this node is a cross-community bridge._
- **Why does `Order` connect `order.ts` to `order-repo.ts`, `main.ts`, `place-order.ts`?**
  _High betweenness centrality (0.032) - this node is a cross-community bridge._
