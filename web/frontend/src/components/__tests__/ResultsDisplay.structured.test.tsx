import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import ResultsDisplay from '../ResultsDisplay';
import { IdeaResult } from '../../types';
import * as ideaCleaner from '../../utils/ideaCleaner';

// Mock the ideaCleaner module
jest.mock('../../utils/ideaCleaner');

// Mock the MarkdownRenderer component
jest.mock('../MarkdownRenderer', () => ({
  __esModule: true,
  default: ({ content }: { content: string }) => <div data-testid="markdown-content">{content}</div>
}));

// Mock other components
jest.mock('../RadarChart', () => ({
  __esModule: true,
  default: () => <div data-testid="radar-chart">Radar Chart</div>
}));

jest.mock('../ComparisonRadarChart', () => ({
  __esModule: true,
  default: () => <div data-testid="comparison-radar-chart">Comparison Radar Chart</div>
}));

jest.mock('../ScoreComparison', () => ({
  __esModule: true,
  default: () => <div data-testid="score-comparison">Score Comparison</div>
}));

jest.mock('../../utils/toast', () => ({
  showError: jest.fn(),
  showSuccess: jest.fn()
}));

describe('ResultsDisplay - Structured Output Support', () => {
  const mockCleanImprovedIdea = ideaCleaner.cleanImprovedIdea as jest.MockedFunction<typeof ideaCleaner.cleanImprovedIdea>;

  beforeEach(() => {
    jest.clearAllMocks();
    mockCleanImprovedIdea.mockImplementation((text: string) => `CLEANED: ${text}`);
  });

  const createMockResult = (improvedIdea: string): IdeaResult => ({
    idea: 'Original idea',
    improved_idea: improvedIdea,
    initial_score: 6,
    improved_score: 8,
    initial_critique: 'Initial critique',
    improved_critique: 'Improved critique',
    advocacy: 'Advocacy points',
    skepticism: 'Skepticism points',
    score_delta: 2
  });

  it('should apply cleaning when structured_output is false', () => {
    const results = [createMockResult('Here is the improved version of the idea: Better idea')];
    
    render(
      <ResultsDisplay 
        results={results} 
        showDetailedResults={true}
        structuredOutput={false}
      />
    );

    // Expand the improved idea section
    const toggleButton = screen.getByRole('button', { name: /toggle improved idea/i });
    fireEvent.click(toggleButton);

    // Verify cleanImprovedIdea was called
    expect(mockCleanImprovedIdea).toHaveBeenCalledWith('Here is the improved version of the idea: Better idea');
    expect(mockCleanImprovedIdea).toHaveBeenCalledTimes(1);
    
    // Verify cleaned content is displayed (get the second markdown content which is the improved idea)
    const contents = screen.getAllByTestId('markdown-content');
    expect(contents[1]).toHaveTextContent('CLEANED: Here is the improved version of the idea: Better idea');
  });

  it('should apply cleaning when structured_output is undefined (backward compatibility)', () => {
    const results = [createMockResult('This is an idea with meta-commentary')];
    
    render(
      <ResultsDisplay 
        results={results} 
        showDetailedResults={true}
        // structuredOutput prop not provided
      />
    );

    // Expand the improved idea section
    const toggleButton = screen.getByRole('button', { name: /toggle improved idea/i });
    fireEvent.click(toggleButton);

    // Verify cleanImprovedIdea was called
    expect(mockCleanImprovedIdea).toHaveBeenCalledWith('This is an idea with meta-commentary');
    expect(mockCleanImprovedIdea).toHaveBeenCalledTimes(1);
  });

  it('should skip cleaning when structured_output is true', () => {
    const results = [createMockResult('Clean JSON improved idea without meta-commentary')];
    
    render(
      <ResultsDisplay 
        results={results} 
        showDetailedResults={true}
        structuredOutput={true}
      />
    );

    // Expand the improved idea section
    const toggleButton = screen.getByRole('button', { name: /toggle improved idea/i });
    fireEvent.click(toggleButton);

    // Verify cleanImprovedIdea was NOT called
    expect(mockCleanImprovedIdea).not.toHaveBeenCalled();
    
    // Verify original content is displayed without cleaning (get the second markdown content which is the improved idea)
    const contents = screen.getAllByTestId('markdown-content');
    expect(contents[1]).toHaveTextContent('Clean JSON improved idea without meta-commentary');
    expect(contents[1]).not.toHaveTextContent('CLEANED:');
  });

  it('should handle multiple results with structured output', () => {
    const results = [
      createMockResult('First clean idea'),
      createMockResult('Second clean idea'),
      createMockResult('Third clean idea')
    ];
    
    render(
      <ResultsDisplay 
        results={results} 
        showDetailedResults={true}
        structuredOutput={true}
      />
    );

    // Expand all improved idea sections
    const toggleButtons = screen.getAllByRole('button', { name: /toggle improved idea/i });
    toggleButtons.forEach(button => fireEvent.click(button));

    // Verify cleanImprovedIdea was never called
    expect(mockCleanImprovedIdea).not.toHaveBeenCalled();
    
    // Verify all ideas are displayed without cleaning
    const contents = screen.getAllByTestId('markdown-content');
    // 6 total: 3 original ideas + 3 improved ideas
    expect(contents).toHaveLength(6);
    // Check improved ideas (odd indices)
    expect(contents[1]).toHaveTextContent('First clean idea');
    expect(contents[3]).toHaveTextContent('Second clean idea');
    expect(contents[5]).toHaveTextContent('Third clean idea');
  });

  it('should handle empty improved_idea gracefully', () => {
    const results = [
      {
        ...createMockResult(''),
        improved_idea: ''
      }
    ];
    
    render(
      <ResultsDisplay 
        results={results} 
        showDetailedResults={true}
        structuredOutput={true}
      />
    );

    // Expand the improved idea section
    const toggleButton = screen.getByRole('button', { name: /toggle improved idea/i });
    fireEvent.click(toggleButton);

    // Should not crash and should render empty content
    const contents = screen.getAllByTestId('markdown-content');
    // Second element is the improved idea
    expect(contents[1]).toBeEmptyDOMElement();
  });
});