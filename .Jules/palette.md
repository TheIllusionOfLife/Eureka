# Palette's Journal

## 2024-05-22 - Keyboard Accessibility for Custom File Uploads
**Learning:** Custom file drop zones are often implemented as `div`s with `onClick`, making them inaccessible to keyboard users.
**Action:** When creating custom triggers for hidden inputs, always add `role="button"`, `tabIndex={0}`, and `onKeyDown` (handling Enter/Space) to ensure full accessibility.

## 2024-05-23 - [Keyboard Accessible File Dropzones]
**Learning:** Tailwind's `hidden` utility (display: none) removes elements from the accessibility tree, making standard file inputs inaccessible to keyboard users if the trigger element (drop zone) isn't explicitly made interactive.
**Action:** When using a custom drop zone with a hidden file input, always add `role="button"`, `tabIndex={0}`, and `onKeyDown` handlers (Enter/Space) to the drop zone container to ensure keyboard users can trigger the file selection dialog. Add visible focus styles (`focus:ring`) so keyboard users know where they are.
