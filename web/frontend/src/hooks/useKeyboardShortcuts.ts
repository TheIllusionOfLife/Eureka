/**
 * Custom React hook for managing keyboard shortcuts in the application
 * Provides a declarative way to register and handle keyboard shortcuts
 */

import { useEffect, useCallback, useRef } from 'react';
import { KeyboardShortcut, UseKeyboardShortcutsOptions } from '../types';
import { logUserAction } from '../utils/logger';

/**
 * Custom hook for managing keyboard shortcuts
 * 
 * @param shortcuts - Array of keyboard shortcut definitions
 * @param options - Configuration options
 */
export function useKeyboardShortcuts(
  shortcuts: KeyboardShortcut[],
  options: UseKeyboardShortcutsOptions = {}
) {
  const { enableLogging = true, preventDefault = true } = options;
  const shortcutsRef = useRef(shortcuts);

  // Update shortcuts ref when shortcuts change
  useEffect(() => {
    shortcutsRef.current = shortcuts;
  }, [shortcuts]);

  const handleKeyDown = useCallback((event: KeyboardEvent) => {
    // Don't trigger shortcuts when typing in input fields
    const target = event.target as HTMLElement;
    const isInputField = 
      target.tagName === 'INPUT' || 
      target.tagName === 'TEXTAREA' || 
      target.isContentEditable;

    if (isInputField && !event.ctrlKey && !event.metaKey) {
      return;
    }

    // Find matching shortcut
    const matchingShortcut = shortcutsRef.current.find(shortcut => {
      if (shortcut.enabled === false) return false;

      const keyMatches = event.key.toLowerCase() === shortcut.key.toLowerCase();
      const ctrlMatches = shortcut.ctrlKey ? (event.ctrlKey || event.metaKey) : true;
      const shiftMatches = shortcut.shiftKey ? event.shiftKey : !event.shiftKey;
      const altMatches = shortcut.altKey ? event.altKey : !event.altKey;

      return keyMatches && ctrlMatches && shiftMatches && altMatches;
    });

    if (matchingShortcut) {
      if (preventDefault) {
        event.preventDefault();
        event.stopPropagation();
      }

      if (enableLogging) {
        logUserAction('keyboard_shortcut', {
          key: matchingShortcut.key,
          modifiers: {
            ctrl: matchingShortcut.ctrlKey,
            shift: matchingShortcut.shiftKey,
            alt: matchingShortcut.altKey
          },
          description: matchingShortcut.description
        });
      }

      matchingShortcut.handler();
    }
  }, [enableLogging, preventDefault]);

  useEffect(() => {
    window.addEventListener('keydown', handleKeyDown);
    
    return () => {
      window.removeEventListener('keydown', handleKeyDown);
    };
  }, [handleKeyDown]);

  // Return shortcuts for display in help dialog
  return shortcuts.filter(s => s.enabled !== false);
}

/**
 * Format keyboard shortcut for display
 */
export function formatShortcut(shortcut: KeyboardShortcut): string {
  const parts: string[] = [];
  
  if (shortcut.ctrlKey) {
    parts.push(navigator.platform.includes('Mac') ? '⌘' : 'Ctrl');
  }
  if (shortcut.shiftKey) parts.push('Shift');
  if (shortcut.altKey) parts.push('Alt');
  parts.push(shortcut.key.toUpperCase());
  
  return parts.join('+');
}