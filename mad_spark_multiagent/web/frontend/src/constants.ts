/**
 * Constants used throughout the frontend application
 */

// Maximum possible score for idea evaluation
export const MAX_IDEA_SCORE = 10;

// API endpoints
export const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

// UI timing constants
export const ANIMATION_DURATION = 500; // milliseconds
export const TOAST_DURATION = 3000; // milliseconds

// Idea cleaner constants - patterns for cleaning improved idea text
export const CLEANER_META_HEADERS = [
  'ENHANCED CONCEPT:', 'ORIGINAL THEME:', 'REVISED CORE PREMISE:',
  'ORIGINAL IDEA:', 'IMPROVED VERSION:', 'ENHANCEMENT SUMMARY:'
];

export const CLEANER_META_PHRASES = [
  'Addresses Evaluation Criteria', 'Enhancing Impact Through',
  'Preserving & Amplifying Strengths', 'Addressing Concerns',
  'Score:', 'from Score', 'Building on Score', '↑↑ from', '↑ from'
];

// Additional cleaner patterns for final cleanup
export const CLEANER_FRAMEWORK_CLEANUP_PATTERN = /^[:\s]*(?:a\s+)?more\s+robust.*?system\s+/i;
export const CLEANER_TITLE_EXTRACTION_PATTERN = /"([^"]+)"/;
export const CLEANER_TITLE_REPLACEMENT_PATTERN = /^.*?"[^"]+".*?\n+/;
export const CLEANER_TITLE_KEYWORDS = ['Framework', 'System', 'Engine'];

// Regex replacement patterns for idea cleaner (pattern, replacement tuples)
// Must match Python constants.py CLEANER_REPLACEMENT_PATTERNS
export const CLEANER_REPLACEMENT_PATTERNS: Array<[RegExp, string]> = [
  // Remove improvement references
  [/Our enhanced approach/gi, 'This approach'],
  [/The enhanced concept/gi, 'The concept'],
  [/This enhanced version/gi, 'This version'],
  [/\benhanced\s+/gi, ''],
  [/\bimproved\s+/gi, ''],
  [/Building upon the original.*?\./gi, ''],
  [/Improving upon.*?\./gi, ''],
  [/addresses the previous.*?\./gi, ''],
  [/directly addresses.*?\./gi, ''],
  [/The previous concern about.*?is/gi, 'This'],
  
  // Simplify transition language
  [/shifts from.*?to\s+/gi, ''],
  [/moves beyond.*?to\s+/gi, ''],
  [/transforms.*?into\s+/gi, 'is '],
  [/We shift from.*?to\s+/gi, ''],
  [/We're moving from.*?to\s+/gi, "It's "],
  [/is evolving into\s+/gi, 'is '],
  
  // Clean up headers
  [/### \d+\.\s*/g, '## '],
  [/## The "([^"]+)".*/g, '# $1'],
  
  // Remove score references
  [/\s*\(Score:?\s*\d+\.?\d*\)/gi, ''],
  [/\s*\(Addressing Score\s*\d+\.?\d*\)/gi, ''],
  [/Score\s*\d+\.?\d*\s*→\s*/gi, ''],
  
  // Clean up separators
  [/---+\n+/g, '\n'],
  [/\n\n\n+/g, '\n\n']
];
