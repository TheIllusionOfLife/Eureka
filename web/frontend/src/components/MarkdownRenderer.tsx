import React, { useMemo } from 'react';

interface MarkdownRendererProps {
  content: string;
  className?: string;
}

// Pure text-to-HTML transformer at module scope — stable reference, no closure over props
const renderMarkdown = (text: string): { __html: string } => {
  // Basic XSS protection: escape potentially dangerous characters
  // '&' must come first to avoid double-encoding the entities added below
  let safeText = text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#x27;')
    .replace(/\//g, '&#x2F;');
  // Preserve line breaks
  let html = safeText.replace(/\n\n/g, '</p><p>').replace(/\n/g, '<br />');

  // Bold text
  html = html.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');

  // Italic text
  html = html.replace(/\*(.*?)\*/g, '<em>$1</em>');

  // Headers
  html = html.replace(/^### (.*?)$/gm, '<h3 class="text-lg font-semibold mt-4 mb-2">$1</h3>');
  html = html.replace(/^## (.*?)$/gm, '<h2 class="text-xl font-semibold mt-4 mb-2">$1</h2>');
  html = html.replace(/^# (.*?)$/gm, '<h1 class="text-2xl font-bold mt-4 mb-2">$1</h1>');

  // Lists
  html = html.replace(/^\* (.*?)$/gm, '<li class="ml-4">• $1</li>');
  html = html.replace(/^\d+\. (.*?)$/gm, '<li class="ml-4">$1</li>');

  // Wrap in paragraph tags
  html = '<p>' + html + '</p>';

  // Clean up empty paragraphs
  html = html.replace(/<p><\/p>/g, '');

  return { __html: html };
};

const MarkdownRenderer: React.FC<MarkdownRendererProps> = ({ content, className = '' }) => {
  // Handle undefined or null content
  const safeContent = content || '';

  const renderedHtml = useMemo(() => renderMarkdown(safeContent), [safeContent]);

  return (
    <div
      className={`prose prose-sm max-w-none ${className}`}
      dangerouslySetInnerHTML={renderedHtml}
    />
  );
};

// Memoized to prevent expensive regex re-rendering when parent components update
export default React.memo(MarkdownRenderer);
