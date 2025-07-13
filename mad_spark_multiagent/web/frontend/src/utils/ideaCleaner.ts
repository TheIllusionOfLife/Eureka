/**
 * Utility to clean up improved idea text for better presentation.
 * Removes meta-commentary and references to original ideas.
 * 
 * Performance optimized with compiled regex patterns and caching.
 */

import {
  CLEANER_META_HEADERS,
  CLEANER_META_PHRASES,
  CLEANER_FRAMEWORK_CLEANUP_PATTERN,
  CLEANER_TITLE_EXTRACTION_PATTERN,
  CLEANER_TITLE_REPLACEMENT_PATTERN,
  CLEANER_TITLE_KEYWORDS
} from '../constants';

// Legacy aliases for backward compatibility
const META_HEADERS = CLEANER_META_HEADERS;
const META_PHRASES = CLEANER_META_PHRASES;

// Compiled regex patterns cache
interface CompiledPatterns {
  replacementPatterns: Array<[RegExp, string]>;
  frameworkPattern: RegExp;
  titleExtractionPattern: RegExp;
  titleReplacementPattern: RegExp;
  metaHeaderPatterns: RegExp[];
  metaPhrasePatterns: RegExp[];
}

let compiledPatternsCache: CompiledPatterns | null = null;

/**
 * Get compiled regex patterns with caching for optimal performance.
 * 
 * This function compiles all patterns once and caches them for reuse,
 * significantly improving performance for large text processing.
 */
function getCompiledPatterns(): CompiledPatterns {
  if (compiledPatternsCache === null) {
    compiledPatternsCache = {
      replacementPatterns: [
        // Remove improvement references
        [/Our enhanced approach/gi, 'This approach'],
        [/The enhanced concept/gi, 'The concept'],
        [/This enhanced version/gi, 'This version'],
        [/enhanced /gi, ''],
        [/improved /gi, ''],
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
      ],
      frameworkPattern: new RegExp(CLEANER_FRAMEWORK_CLEANUP_PATTERN, 'i'),
      titleExtractionPattern: new RegExp(CLEANER_TITLE_EXTRACTION_PATTERN),
      titleReplacementPattern: new RegExp(CLEANER_TITLE_REPLACEMENT_PATTERN),
      metaHeaderPatterns: CLEANER_META_HEADERS.map(header => 
        new RegExp(header.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), 'i')
      ),
      metaPhrasePatterns: CLEANER_META_PHRASES.map(phrase => 
        new RegExp(phrase.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), 'i')
      )
    };
  }
  return compiledPatternsCache;
}

export function cleanImprovedIdea(text: string): string {
  if (!text) return text;

  // Get compiled patterns for optimal performance
  const patterns = getCompiledPatterns();

  // Remove meta-commentary sections at the beginning
  const lines = text.split('\n');
  const cleanedLines: string[] = [];
  let skipUntilEmpty = false;

  for (const line of lines) {
    // Skip meta headers using compiled patterns
    if (patterns.metaHeaderPatterns.some(pattern => pattern.test(line))) {
      skipUntilEmpty = true;
      continue;
    }

    // Skip until we hit an empty line after meta headers
    if (skipUntilEmpty) {
      if (line.trim() === '') {
        skipUntilEmpty = false;
      }
      continue;
    }

    // Skip lines that are pure meta-commentary using compiled patterns
    if (patterns.metaPhrasePatterns.some(pattern => pattern.test(line))) {
      continue;
    }

    cleanedLines.push(line);
  }

  let cleaned = cleanedLines.join('\n');

  // Apply cached compiled regex patterns for optimal performance
  for (const [pattern, replacement] of patterns.replacementPatterns) {
    cleaned = cleaned.replace(pattern, replacement);
  }

  // Clean up the beginning if it starts with a framework name using cached pattern
  cleaned = cleaned.replace(patterns.frameworkPattern, '');

  // Final cleanup
  cleaned = cleaned.trim();

  // If there's a clear title at the beginning, format it properly using cached patterns
  const firstLine = cleaned.split('\n')[0] || '';
  if (CLEANER_TITLE_KEYWORDS.some(word => firstLine.includes(word))) {
    // Extract the main concept name
    const titleMatch = firstLine.match(patterns.titleExtractionPattern);
    if (titleMatch) {
      const title = titleMatch[1];
      cleaned = cleaned.replace(patterns.titleReplacementPattern, `# ${title}\n\n`);
    }
  }

  return cleaned;
}

/**
 * Clean improved ideas in a list of results with optimized batch processing.
 * 
 * Performance optimized for batch processing with pre-warmed pattern cache.
 */
export function cleanImprovedIdeasInResults(results: Array<{ improved_idea?: string; [key: string]: any }>): Array<{ improved_idea?: string; [key: string]: any }> {
  // Pre-warm the pattern cache for batch processing
  getCompiledPatterns();
  
  return results.map(result => {
    if (result.improved_idea) {
      return {
        ...result,
        improved_idea: cleanImprovedIdea(result.improved_idea)
      };
    }
    return result;
  });
}