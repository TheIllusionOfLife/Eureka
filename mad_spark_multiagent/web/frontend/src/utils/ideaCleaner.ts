/**
 * Utility to clean up improved idea text for better presentation.
 * Removes meta-commentary and references to original ideas.
 */

export function cleanImprovedIdea(text: string): string {
  if (!text) return text;

  // Remove meta-commentary sections at the beginning
  const lines = text.split('\n');
  const cleanedLines: string[] = [];
  let skipUntilEmpty = false;

  for (const line of lines) {
    // Skip meta headers
    if ([
      'ENHANCED CONCEPT:', 'ORIGINAL THEME:', 'REVISED CORE PREMISE:',
      'ORIGINAL IDEA:', 'IMPROVED VERSION:', 'ENHANCEMENT SUMMARY:'
    ].some(pattern => line.includes(pattern))) {
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

    // Skip lines that are pure meta-commentary
    if ([
      'Addresses Evaluation Criteria', 'Enhancing Impact Through',
      'Preserving & Amplifying Strengths', 'Addressing Concerns',
      'Score:', 'from Score', 'Building on Score', '↑↑ from', '↑ from'
    ].some(phrase => line.includes(phrase))) {
      continue;
    }

    cleanedLines.push(line);
  }

  let cleaned = cleanedLines.join('\n');

  // Remove or replace specific patterns
  const replacements: [RegExp, string][] = [
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
    [/\n\n\n+/g, '\n\n'],
  ];

  for (const [pattern, replacement] of replacements) {
    cleaned = cleaned.replace(pattern, replacement);
  }

  // Clean up the beginning if it starts with a framework name
  cleaned = cleaned.replace(/^[:\s]*(?:a\s+)?more\s+robust.*?system\s+/i, '');

  // Final cleanup
  cleaned = cleaned.trim();

  // If there's a clear title at the beginning, format it properly
  const firstLine = cleaned.split('\n')[0] || '';
  if (['Framework', 'System', 'Engine'].some(word => firstLine.includes(word))) {
    // Extract the main concept name
    const titleMatch = firstLine.match(/"([^"]+)"/);
    if (titleMatch) {
      const title = titleMatch[1];
      cleaned = cleaned.replace(/^.*?"[^"]+".*?\n+/, `# ${title}\n\n`);
    }
  }

  return cleaned;
}