## 2025-05-23 - Interactive List Item Re-renders
**Learning:** In `ResultsDisplay`, interacting with a single result (expanding sections, bookmarking) triggered a re-render of the entire list. This is because the state was held in the parent component and items were not memoized.
**Action:** Always extract list items into separate memoized components (`ResultItem`) when they contain interactive local state to prevent O(n) re-renders on user interaction.
