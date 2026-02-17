import React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import MarkdownRenderer from '../MarkdownRenderer';

describe('MarkdownRenderer', () => {
  it('renders markdown content correctly', () => {
    const content = '**Bold Text**';
    const { container } = render(<MarkdownRenderer content={content} />);

    // Check for strong tag
    const strongElement = container.querySelector('strong');
    expect(strongElement).toBeInTheDocument();
    expect(strongElement).toHaveTextContent('Bold Text');
  });

  it('renders headers correctly', () => {
    const content = '### Header 3';
    const { container } = render(<MarkdownRenderer content={content} />);

    const h3Element = container.querySelector('h3');
    expect(h3Element).toBeInTheDocument();
    expect(h3Element).toHaveTextContent('Header 3');
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
  });
});
