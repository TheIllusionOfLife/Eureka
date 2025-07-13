/**
 * Utility to clean up improved idea text for better presentation.
 * Removes meta-commentary and references to original ideas.
 */

// Constants for better maintainability
const META_HEADERS = [
  'ENHANCED CONCEPT:', 'ORIGINAL THEME:', 'REVISED CORE PREMISE:',
  'ORIGINAL IDEA:', 'IMPROVED VERSION:', 'ENHANCEMENT SUMMARY:'
];

const META_PHRASES = [
  'Addresses Evaluation Criteria', 'Enhancing Impact Through',
  'Preserving & Amplifying Strengths', 'Addressing Concerns',
  'Score:', 'from Score', 'Building on Score', '↑↑ from', '↑ from'
];

export function cleanImprovedIdea(text: string): string {
  if (!text) return text;

  // Remove meta-commentary sections at the beginning
  const lines = text.split('\n');
  const cleanedLines: string[] = [];
  let skipUntilEmpty = false;

  for (const line of lines) {
    // Skip meta headers
    if (META_HEADERS.some(pattern => line.includes(pattern))) {
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
    if (META_PHRASES.some(phrase => line.includes(phrase))) {
      continue;
    }

    cleanedLines.push(line);
  }

  let cleaned = cleanedLines.join('\n');

  // Apply consistent replacements for better maintainability
  // Remove improvement references
  cleaned = cleaned.replace(/Our enhanced approach/gi, 'This approach');
  cleaned = cleaned.replace(/The enhanced concept/gi, 'The concept');
  cleaned = cleaned.replace(/This enhanced version/gi, 'This version');
  cleaned = cleaned.replace(/enhanced /gi, '');
  cleaned = cleaned.replace(/improved /gi, '');
  cleaned = cleaned.replace(/Building upon the original.*?\./gi, '');
  cleaned = cleaned.replace(/Improving upon.*?\./gi, '');
  cleaned = cleaned.replace(/addresses the previous.*?\./gi, '');
  cleaned = cleaned.replace(/directly addresses.*?\./gi, '');
  cleaned = cleaned.replace(/The previous concern about.*?is/gi, 'This');

  // Simplify transition language
  cleaned = cleaned.replace(/shifts from.*?to\s+/gi, '');
  cleaned = cleaned.replace(/moves beyond.*?to\s+/gi, '');
  cleaned = cleaned.replace(/transforms.*?into\s+/gi, 'is ');
  cleaned = cleaned.replace(/We shift from.*?to\s+/gi, '');
  cleaned = cleaned.replace(/We're moving from.*?to\s+/gi, "It's ");
  cleaned = cleaned.replace(/is evolving into\s+/gi, 'is ');

  // Clean up headers
  cleaned = cleaned.replace(/### \d+\.\s*/g, '## ');
  cleaned = cleaned.replace(/## The "([^"]+)".*/g, '# $1');

  // Remove score references
  cleaned = cleaned.replace(/\s*\(Score:?\s*\d+\.?\d*\)/gi, '');
  cleaned = cleaned.replace(/\s*\(Addressing Score\s*\d+\.?\d*\)/gi, '');
  cleaned = cleaned.replace(/Score\s*\d+\.?\d*\s*→\s*/gi, '');

  // Clean up separators
  cleaned = cleaned.replace(/---+\n+/g, '\n');
  cleaned = cleaned.replace(/\n\n\n+/g, '\n\n');

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