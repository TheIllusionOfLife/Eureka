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
  // Remove AI response prefixes and meta-commentary  
  [/^[Hh]ere's the\s+(?:improved\s+)?version\s+(?:of\s+)?(?:your\s+)?(?:idea)?.*?[:.]?\s*/gm, ''],
  [/^[Hh]ere's an?\s+(?:improved|enhanced|better)\s+version.*?[:.]?\s*/gm, ''],
  [/^[Hh]ere's\s+your\s+(?:improved|enhanced)\s+idea\s+(?:with\s+)?(?:better\s+)?(?:focus\s*[:.]?\s*)?/gm, ''],
  [/^[Hh]ere's the\s+(?:refined|polished|optimized)\s+(?:version|idea).*?[:.]?\s*/gm, ''],
  [/^Based on.*?feedback.*?here\s+(?:is\s+)?(?:the\s+)?(?:refined\s+)?(?:concept\s*[:.]?\s*)?/gm, ''],
  [/^Taking into account.*?here\s+(?:is\s+)?(?:the\s+)?(?:refined\s+)?[:.]?\s*/gm, ''],
  [/^Incorporating.*?feedback.*?[:.]?\s*/gm, ''],
  [/^\s*\*\*Updated\s+(?:version|idea)\*\*[:.]?\s*/gm, ''],
  [/^\s*\*\*(?:Improved|Enhanced|Refined)\s+(?:concept|idea|version)\*\*[:.]?\s*/gm, ''],
  
  // Remove mock-generated phrases and headers
  [/^[Ii]mproved version of:\s*/gm, ''],
  [/^[Ee]nhanced version of:\s*/gm, ''],
  [/^[Vv]ersion of:\s*/gm, ''],
  [/\n\nEnhancements based on feedback:\s*.*/g, ''],
  [/- Addressed critique points\s*\n?/g, ''],
  [/- Incorporated advocacy strengths\s*\n?/g, ''],
  [/- Resolved skeptical concerns\s*\n?/g, ''],
  
  // Remove improvement references
  [/Our enhanced approach/gi, 'This approach'],
  [/The enhanced concept/gi, 'The concept'],
  [/This enhanced version/gi, 'This version'],
  [/The revised approach/gi, 'The approach'],
  [/\benhanced\s+/gi, ''],
  [/\bimproved\s+/gi, ''],
  [/\brevised\s+/gi, ''],
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
