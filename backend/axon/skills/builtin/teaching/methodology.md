# Teaching Methodology

## 1. Assess the Learner's Current Level

Before explaining anything, determine what the learner already knows:

- **Read the context.** What have they said, asked, or built? Their vocabulary and question phrasing reveal their level.
- **Identify knowledge anchors.** What related concepts do they already understand? You will build from these.
- **Spot misconceptions early.** A wrong mental model is harder to fix later. If you detect one, address it gently before building on top of it.

Three rough levels:

| Level         | Indicators                                        | Approach                          |
|---------------|---------------------------------------------------|-----------------------------------|
| Beginner      | Asks "what is X?", unfamiliar vocabulary          | Analogy-first, minimal jargon     |
| Intermediate  | Asks "how does X work?", knows basics             | Mechanism-focused, introduce terms |
| Advanced      | Asks "why does X behave this way?", knows the API | Edge cases, trade-offs, internals |

When unsure, start at beginner and escalate based on their responses.

## 2. Start With the Simplest Accurate Mental Model

Every concept has a simplified version that is still fundamentally correct:

- **Find the core idea.** Strip away every detail until you reach the one thing that, if understood, makes everything else click.
- **State it in one sentence.** If you cannot, the mental model is still too complex.
- **Ensure accuracy.** A simplified model must not be wrong. "A function is a reusable block of code" is simple and correct. "A variable is a box that holds a value" is simple but misleading for reference types.

The goal is a foundation the learner can trust and build upon without needing to unlearn later.

## 3. Build Complexity Incrementally

Layer new information on top of the simple model, one concept at a time:

1. **Introduce one new idea per step.** Do not bundle multiple concepts.
2. **Connect each new idea to what they already know.** "Now that you understand X, here is how Y extends it..."
3. **Signal when complexity increases.** "This next part is a bit more nuanced..." helps the learner allocate attention.
4. **Pause after each layer.** Give the learner a chance to absorb before moving on.

The sequence should feel like climbing stairs, not riding an elevator. Each step is small and visible.

## 4. Use Analogies to Connect to Known Concepts

Good analogies accelerate understanding dramatically:

- **Map the familiar to the unfamiliar.** "A message queue is like a post office — messages wait in line until the recipient picks them up."
- **Be explicit about where the analogy breaks.** Every analogy has limits. State them: "Unlike a real post office, a message queue can duplicate messages."
- **Draw from the learner's domain.** If they are a chef, use kitchen analogies. If they are a musician, use music analogies. Meet them where they are.
- **Use multiple analogies for the same concept.** Different perspectives illuminate different facets.

## 5. Provide Concrete Examples Before Abstract Rules

Humans learn better from examples than from definitions:

- **Show the thing working first.** A code snippet, a scenario, a diagram, a story.
- **Then explain the rule.** "What you just saw is called X, and it works because..."
- **Use at least two examples.** One example might seem like a special case. Two examples reveal the pattern.
- **Include a counter-example.** Show what does NOT work and why. Boundaries clarify meaning.

The pattern is: Example -> Observation -> Rule -> Another example that confirms the rule.

## 6. Check Understanding

Do not assume the learner followed everything:

- **Ask probing questions.** "Given what we just covered, what would happen if...?"
- **Invite them to restate.** "Can you describe this back to me in your own words?"
- **Offer a small exercise.** A toy problem that requires applying the concept.
- **Watch for false confidence.** "That makes sense" sometimes means "I stopped processing." Push gently.

## 7. Offer Multiple Explanations

If the first explanation does not land, try a different angle:

- **Switch modality.** If you explained verbally, try a diagram or code. If you used code, try a story.
- **Change the abstraction level.** Zoom in (show the mechanism) or zoom out (show the purpose).
- **Try a different analogy.** The first one may not have resonated with this learner.

Never just repeat the same explanation louder. If they did not understand it the first time, saying it again will not help.

## 8. Close With Next Steps

End every teaching interaction with:

- A **recap** of the key takeaway (one sentence).
- **Suggested next topics** that build naturally on what was just learned.
- **Resources or exercises** for self-directed practice if applicable.
