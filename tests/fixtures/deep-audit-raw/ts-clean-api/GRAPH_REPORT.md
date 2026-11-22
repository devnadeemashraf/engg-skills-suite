# Graph Report - fixture

## Corpus Check
- 23 files · ~1,489 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 2 file(s) not represented in the graph (top: .log 1, .csv 1)

## Summary
- 85 nodes · 156 edges · 8 communities (7 shown, 1 thin omitted)
- Extraction: 96% EXTRACTED · 4% INFERRED · 0% AMBIGUOUS · INFERRED: 6 edges (avg confidence: 0.85)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `749247f7`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- architecture.yaml
- place-order.ts
- orders/index.ts
- main.ts
- shared/index.ts
- order-repo.ts
- package.json
- Response

## God Nodes (most connected - your core abstractions)
1. `placeOrder()` - 11 edges
2. `compose()` - 9 edges
3. `percentOf()` - 7 edges
4. `OrderStore` - 7 edges
5. `getOrderForUser()` - 6 edges
6. `Order` - 6 edges
7. `OrderNotFound` - 6 edges
8. `isValidEmail()` - 6 edges
9. `layers` - 5 edges
10. `register()` - 5 edges

## Surprising Connections (you probably didn't know these)
- `compose()` --indirect_call--> `placeOrder()`  [INFERRED]
  src/main.ts → src/orders/app/place-order.ts
- `compose()` --indirect_call--> `formatCurrency()`  [INFERRED]
  src/main.ts → src/shared/utils.ts
- `compose()` --indirect_call--> `register()`  [INFERRED]
  src/main.ts → src/users/app/register.ts
- `compose()` --indirect_call--> `cancelOrder()`  [INFERRED]
  src/main.ts → src/orders/app/cancel-order.ts
- `compose()` --calls--> `orderRoutes()`  [EXTRACTED]
  src/main.ts → src/orders/http/routes.ts

## Import Cycles
- None detected.

## Communities (8 total, 1 thin omitted)

### Community 0 - "architecture.yaml"
Cohesion: 0.11
Nodes (18): layers, external, may_import, name, paths, limits, max_file_lines, max_function_complexity (+10 more)

### Community 1 - "place-order.ts"
Cohesion: 0.28
Nodes (8): placeOrder(), PlaceOrderInput, taxFor(), applyCoupon(), quantityDiscountPercent(), addCents(), DEFAULT_CURRENCY, percentOf()

### Community 2 - "orders/index.ts"
Cohesion: 0.33
Nodes (6): getOrderForUser(), Order, OrderNotFound, OrderStore, orderRoutes(), Request

### Community 3 - "main.ts"
Cohesion: 0.23
Nodes (9): Config, loadConfig(), compose(), sqlOrderStore(), paymentClient(), PaymentClientOptions, PaymentDeclined, PaymentUnavailable (+1 more)

### Community 4 - "shared/index.ts"
Cohesion: 0.42
Nodes (5): isValidEmail(), formatCurrency(), normaliseName(), register(), User

### Community 5 - "order-repo.ts"
Cohesion: 0.40
Nodes (3): Db, OrderRow, OrderStatus

### Community 6 - "package.json"
Cohesion: 0.40
Nodes (4): description, name, private, type

## Knowledge Gaps
- **1 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `placeOrder()` connect `place-order.ts` to `orders/index.ts`, `main.ts`, `shared/index.ts`?**
  _High betweenness centrality (0.087) - this node is a cross-community bridge._
- **Are the 4 inferred relationships involving `compose()` (e.g. with `cancelOrder()` and `placeOrder()`) actually correct?**
  _`compose()` has 4 INFERRED edges - model-reasoned connections that need verification._
- **Should `architecture.yaml` be split into smaller, more focused modules?**
  _Cohesion score 0.10526315789473684 - nodes in this community are weakly interconnected._
- **Why does `Response` connect `Response` to `orders/index.ts`?**
  _High betweenness centrality (0.034) - this node is a cross-community bridge._
- **Why does `OrderStore` connect `orders/index.ts` to `order-repo.ts`?**
  _High betweenness centrality (0.029) - this node is a cross-community bridge._
