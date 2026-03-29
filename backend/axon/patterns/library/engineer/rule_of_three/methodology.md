# Rule of Three

The Rule of Three states that you should tolerate duplication until you see the same pattern appear three times. Two instances of similar code might look like duplication, but they often diverge as requirements evolve. Three instances give you enough examples to see what is truly shared and what varies, leading to a correct abstraction. Premature abstraction based on two cases often produces the wrong interface.

Apply this when you notice duplicated code and feel the urge to refactor immediately. It is a patience discipline that leads to better abstractions.

**Steps to apply:**
1. First time you write something, just write it.
2. Second time you see something similar, note the duplication but allow it. Copy-paste is acceptable here.
3. Third time, now you have three concrete examples. Compare them to extract the true common pattern.
4. Refactor into a shared abstraction that naturally accommodates all three cases.

**Common mistakes:** Abstracting after two instances and creating a brittle, over-fitted interface. Never refactoring — the rule says wait for three, not ignore duplication forever. Creating abstractions that handle the three known cases but are not extensible to the fourth.
