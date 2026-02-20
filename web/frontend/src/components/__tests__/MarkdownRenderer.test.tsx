import React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import MarkdownRenderer from '../MarkdownRenderer';

describe('MarkdownRenderer', () => {
  it('renders markdown content correctly', () => {
    const content = '**Bold Text**';
    render(<MarkdownRenderer content={content} />);

    // Check for bold text content
    const boldText = screen.getByText('Bold Text');
    expect(boldText).toBeInTheDocument();
    // Verify it's wrapped in a strong tag (or has font-bold equivalent if using tailwind)
    // RTL focuses on what user sees, but we can check tagName if needed
    expect(boldText.tagName).toBe('STRONG');
  });

  it('renders headers correctly', () => {
    const content = '### Header 3';
    render(<MarkdownRenderer content={content} />);

    const h3Element = screen.getByRole('heading', { level: 3, name: /header 3/i });
    expect(h3Element).toBeInTheDocument();
  });

  it('renders lists correctly', () => {
    const content = '* List item';
    const { container } = render(<MarkdownRenderer content={content} />);

    const liElement = container.querySelector('li');
    expect(liElement).toBeInTheDocument();
    expect(liElement).toHaveTextContent('List item');
  });

  it('handles empty content gracefully', () => {
    const { container } = render(<MarkdownRenderer content="" />);
    expect(container.firstChild).toBeInTheDocument();
    expect(container.firstChild).toHaveTextContent('');
  });
});
