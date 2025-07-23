/**
 * Hook-related type definitions for the MadSpark application
 */

// Keyboard shortcuts types
export interface KeyboardShortcut {
  key: string;
  ctrlKey?: boolean;
  metaKey?: boolean;
  altKey?: boolean;
  shiftKey?: boolean;
  description: string;
  handler: () => void;
  enabled?: boolean;
}

export interface UseKeyboardShortcutsOptions {
  enableLogging?: boolean;
  preventDefault?: boolean;
  stopPropagation?: boolean;
}

// Other hook types can be added here as needed