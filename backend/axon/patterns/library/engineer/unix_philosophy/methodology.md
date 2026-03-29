# Unix Philosophy

The Unix Philosophy holds that software should be built as small, focused programs that each do one thing well, communicate through simple text interfaces, and compose together into larger workflows. Instead of building monolithic tools that try to handle every case, you build sharp primitives and let users chain them. This produces systems that are easier to understand, test, replace, and extend.

Apply this when designing modules, APIs, CLI tools, or services. It is especially valuable when you feel tempted to add "just one more feature" to an existing component.

**Steps to apply:**
1. Define the single responsibility of each component — if you cannot state it in one sentence, it does too much.
2. Design clean inputs and outputs (stdin/stdout in Unix, well-defined interfaces in code).
3. Avoid hidden side effects — a component should be predictable given its inputs.
4. Build composition points — make it easy to chain components together (pipes, middleware, event streams).

**Common mistakes:** Building a "Swiss Army knife" module that handles many concerns. Using complex binary protocols where simple text or JSON would suffice. Coupling components so tightly that they cannot be used or tested independently.
