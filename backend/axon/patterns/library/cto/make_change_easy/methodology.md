# Make the Change Easy

Kent Beck's principle is deceptively simple: "First make the change easy, then make the easy change." When a feature or fix is hard to implement, the instinct is to force it into the existing structure. The better approach is to refactor the code first so that the change becomes trivial, then make the trivial change. Two small, safe steps instead of one risky leap.

Apply this pattern when you find yourself fighting the code to add a feature. If the implementation feels forced or requires touching too many files, the structure is resisting you. Listen to that resistance — it is telling you to refactor first.

**Steps:** (1) Identify the change you need to make. (2) Ask: "What would the code need to look like for this change to be easy?" (3) Refactor toward that structure in a separate commit with no behavior change. (4) Verify the refactor with tests. (5) Now make the feature change, which should be small and obvious. (6) Ship refactor and feature as separate, reviewable units.

The most common mistake is combining the refactor and the feature change into one large pull request that is hard to review and risky to deploy. Keep them separate.
