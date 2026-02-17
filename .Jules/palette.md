# Palette's Journal

## 2024-05-22 - Keyboard Accessibility for Custom File Uploads
**Learning:** Custom file drop zones are often implemented as `div`s with `onClick`, making them inaccessible to keyboard users.
**Action:** When creating custom triggers for hidden inputs, always add `role="button"`, `tabIndex={0}`, and `onKeyDown` (handling Enter/Space) to ensure full accessibility.
