# Separation of Concerns

Separation of Concerns is the principle that each module, class, or function should address exactly one concern and encapsulate it completely. When concerns are mixed — business logic tangled with UI rendering, data access woven into validation — changes to one concern ripple unpredictably into others. Clean separation means you can modify, test, and replace each piece independently.

Apply this when designing module boundaries, reviewing pull requests, or refactoring code that has become difficult to change. It is the foundational principle behind MVC, microservices, and most architectural patterns.

**Steps to apply:**
1. Identify the distinct concerns in your system — data access, business rules, presentation, communication, error handling.
2. Draw boundaries so each module owns one concern completely.
3. Define clear interfaces between modules — dependencies should flow through contracts, not direct access.
4. When a module starts handling two concerns, split it.

**Common mistakes:** Over-separating into too many tiny modules that create indirection without clarity. Leaking implementation details across boundaries through shared data structures. Splitting by technical layer (controller/service/repo) when splitting by domain (user/order/payment) would be more natural.
