import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import ResultsDisplay from '../ResultsDisplay';
import { IdeaResult, LogicalInferenceResult } from '../../types';

// Mock components and utilities
jest.mock('../MarkdownRenderer', () => ({
  __esModule: true,
  default: ({ content }: { content: string }) => <div data-testid="markdown-content">{content}</div>
}));

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

jest.mock('../../utils/ideaCleaner', () => ({
  cleanImprovedIdea: jest.fn((text: string) => text)
}));

jest.mock('../../utils/toast', () => ({
  showError: jest.fn(),
  showSuccess: jest.fn()
}));

describe('ResultsDisplay - Logical Inference Display', () => {
  const createMockLogicalInference = (): LogicalInferenceResult => ({
    inference_chain: [
      'Urban areas have limited horizontal space',
      'Vertical solutions maximize space efficiency',
      'Rooftop gardens provide local food production',
      'Community involvement ensures sustainability'
    ],
    conclusion: 'Vertical rooftop gardens are optimal for urban food security',
    confidence: 0.85,
    improvements: 'Consider hydroponic systems for higher yields in limited space',
    causal_chain: [
      'Limited space leads to vertical solutions',
      'Vertical solutions enable rooftop gardens',
      'Rooftop gardens improve food security'
    ],
    implications: [
      'Reduced transportation costs for food',
      'Improved air quality from plants',
      'Stronger community bonds through shared projects'
    ],
    constraint_satisfaction: {
      'space_efficiency': 0.9,
      'cost_effectiveness': 0.7,
      'community_acceptance': 0.8
    },
    overall_satisfaction: 0.8
  });

  const createMockResult = (withLogicalInference: boolean = false): IdeaResult => ({
    idea: 'Original urban farming idea',
    improved_idea: 'Improved urban farming concept with rooftop gardens',
    initial_score: 6,
    improved_score: 8,
    score_delta: 2,
    initial_critique: 'Initial critique of the idea',
    improved_critique: 'Improved critique with detailed analysis',
    advocacy: 'Strong points supporting the idea',
    skepticism: 'Potential challenges and concerns',
    logical_inference: withLogicalInference ? createMockLogicalInference() : undefined
  });

  it('should not display logical inference section when logical_inference is undefined', () => {
    const results = [createMockResult(false)];
    
    render(
      <ResultsDisplay 
        results={results} 
        showDetailedResults={true}
        structuredOutput={true}
      />
    );

    // Should not find logical inference section
    expect(screen.queryByText(/logical inference/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/inference chain/i)).not.toBeInTheDocument();
  });

  it('should display logical inference section when logical_inference is present', () => {
    const results = [createMockResult(true)];
    
    render(
      <ResultsDisplay 
        results={results} 
        showDetailedResults={true}
        structuredOutput={true}
      />
    );

    // Should find logical inference section header
    expect(screen.getByText(/logical inference analysis/i)).toBeInTheDocument();
  });

  it('should display inference chain steps', () => {
    const results = [createMockResult(true)];
    
    render(
      <ResultsDisplay 
        results={results} 
        showDetailedResults={true}
        structuredOutput={true}
      />
    );

    // Expand the logical inference section
    const toggleButton = screen.getByRole('button', { name: /toggle logical inference/i });
    fireEvent.click(toggleButton);

    // Should display inference chain steps
    expect(screen.getByText(/urban areas have limited horizontal space/i)).toBeInTheDocument();
    expect(screen.getByText(/vertical solutions maximize space efficiency/i)).toBeInTheDocument();
    expect(screen.getByText(/rooftop gardens provide local food production/i)).toBeInTheDocument();
  });

  it('should display conclusion and confidence', () => {
    const results = [createMockResult(true)];
    
    render(
      <ResultsDisplay 
        results={results} 
        showDetailedResults={true}
        structuredOutput={true}
      />
    );

    // Expand the logical inference section
    const toggleButton = screen.getByRole('button', { name: /toggle logical inference/i });
    fireEvent.click(toggleButton);

    // Should display conclusion
    expect(screen.getByText(/vertical rooftop gardens are optimal for urban food security/i)).toBeInTheDocument();
    
    // Should display confidence as percentage
    expect(screen.getByText(/85%/)).toBeInTheDocument();
  });

  it('should display improvements when present', () => {
    const results = [createMockResult(true)];
    
    render(
      <ResultsDisplay 
        results={results} 
        showDetailedResults={true}
        structuredOutput={true}
      />
    );

    // Expand the logical inference section
    const toggleButton = screen.getByRole('button', { name: /toggle logical inference/i });
    fireEvent.click(toggleButton);

    // Should display improvements
    expect(screen.getByText(/consider hydroponic systems for higher yields/i)).toBeInTheDocument();
  });

  it('should display causal chain when present', () => {
    const results = [createMockResult(true)];
    
    render(
      <ResultsDisplay 
        results={results} 
        showDetailedResults={true}
        structuredOutput={true}
      />
    );

    // Expand the logical inference section
    const toggleButton = screen.getByRole('button', { name: /toggle logical inference/i });
    fireEvent.click(toggleButton);

    // Should display causal chain
    expect(screen.getByText(/limited space leads to vertical solutions/i)).toBeInTheDocument();
    expect(screen.getByText(/vertical solutions enable rooftop gardens/i)).toBeInTheDocument();
  });

  it('should display implications when present', () => {
    const results = [createMockResult(true)];
    
    render(
      <ResultsDisplay 
        results={results} 
        showDetailedResults={true}
        structuredOutput={true}
      />
    );

    // Expand the logical inference section
    const toggleButton = screen.getByRole('button', { name: /toggle logical inference/i });
    fireEvent.click(toggleButton);

    // Should display implications
    expect(screen.getByText(/reduced transportation costs/i)).toBeInTheDocument();
    expect(screen.getByText(/improved air quality/i)).toBeInTheDocument();
    expect(screen.getByText(/stronger community bonds/i)).toBeInTheDocument();
  });

  it('should display constraint satisfaction scores when present', () => {
    const results = [createMockResult(true)];
    
    render(
      <ResultsDisplay 
        results={results} 
        showDetailedResults={true}
        structuredOutput={true}
      />
    );

    // Expand the logical inference section
    const toggleButton = screen.getByRole('button', { name: /toggle logical inference/i });
    fireEvent.click(toggleButton);

    // Should display constraint satisfaction with labels and percentages
    expect(screen.getByText(/constraint satisfaction/i)).toBeInTheDocument();
    expect(screen.getByText('space efficiency:')).toBeInTheDocument();
    expect(screen.getByText('cost effectiveness:')).toBeInTheDocument();
    expect(screen.getByText('community acceptance:')).toBeInTheDocument();
    // Check that percentages are displayed (there may be multiple instances due to overall satisfaction)
    expect(screen.getAllByText(/90%/)).toHaveLength(1);
    expect(screen.getAllByText(/70%/)).toHaveLength(1);
    expect(screen.getAllByText(/80%/)).toHaveLength(2); // community_acceptance + overall_satisfaction
  });

  it('should handle logical inference with missing optional fields gracefully', () => {
    const minimalLogicalInference: LogicalInferenceResult = {
      inference_chain: ['Simple step'],
      conclusion: 'Simple conclusion',
      confidence: 0.6
    };

    const results = [{
      ...createMockResult(false),
      logical_inference: minimalLogicalInference
    }];
    
    render(
      <ResultsDisplay 
        results={results} 
        showDetailedResults={true}
        structuredOutput={true}
      />
    );

    // Should display basic inference without crashing
    expect(screen.getByText(/logical inference analysis/i)).toBeInTheDocument();
    
    // Expand the logical inference section
    const toggleButton = screen.getByRole('button', { name: /toggle logical inference/i });
    fireEvent.click(toggleButton);
    
    expect(screen.getByText(/simple step/i)).toBeInTheDocument();
    expect(screen.getByText(/simple conclusion/i)).toBeInTheDocument();
    expect(screen.getByText(/60%/)).toBeInTheDocument();
  });

  it('should display error message when logical inference has error', () => {
    const errorLogicalInference: LogicalInferenceResult = {
      inference_chain: [],
      conclusion: '',
      confidence: 0,
      error: 'Analysis failed due to insufficient context'
    };

    const results = [{
      ...createMockResult(false),
      logical_inference: errorLogicalInference
    }];
    
    render(
      <ResultsDisplay 
        results={results} 
        showDetailedResults={true}
        structuredOutput={true}
      />
    );

    // Expand the logical inference section
    const toggleButton = screen.getByRole('button', { name: /toggle logical inference/i });
    fireEvent.click(toggleButton);

    // Should display error message
    expect(screen.getByText(/analysis failed due to insufficient context/i)).toBeInTheDocument();
  });

  it('should be collapsible/expandable section', () => {
    const results = [createMockResult(true)];
    
    render(
      <ResultsDisplay 
        results={results} 
        showDetailedResults={true}
        structuredOutput={true}
      />
    );

    // Should find toggle button for logical inference section
    const toggleButton = screen.getByRole('button', { name: /toggle logical inference/i });
    expect(toggleButton).toBeInTheDocument();

    // Initially collapsed state - content should not be visible
    expect(screen.queryByText(/urban areas have limited horizontal space/i)).not.toBeInTheDocument();

    // Click to expand
    fireEvent.click(toggleButton);
    
    // Content should be visible after expansion
    expect(screen.getByText(/urban areas have limited horizontal space/i)).toBeInTheDocument();

    // Click to collapse again
    fireEvent.click(toggleButton);
    
    // Content should be hidden after collapse
    expect(screen.queryByText(/urban areas have limited horizontal space/i)).not.toBeInTheDocument();
  });
});