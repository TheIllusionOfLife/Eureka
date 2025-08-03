import { IdeaGenerationResponse } from '../api.types';

describe('IdeaGenerationResponse', () => {
  it('should include structured_output field', () => {
    const response: IdeaGenerationResponse = {
      status: 'success',
      message: 'Test',
      results: [],
      processing_time: 1.0,
      timestamp: '2025-08-01T00:00:00Z',
      structured_output: false
    };
    
    expect(response.structured_output).toBe(false);
  });

  it('should allow structured_output to be optional', () => {
    const response: IdeaGenerationResponse = {
      status: 'success',
      message: 'Test',
      results: [],
      processing_time: 1.0,
      timestamp: '2025-08-01T00:00:00Z'
    };
    
    expect(response.structured_output).toBeUndefined();
  });

  it('should handle structured_output true case', () => {
    const response: IdeaGenerationResponse = {
      status: 'success',
      message: 'Test',
      results: [{
        idea: 'Test idea',
        improved_idea: 'Clean JSON improved idea without meta-commentary',
        initial_score: 7,
        improved_score: 9,
        initial_critique: 'Test critique',
        advocacy: 'Test advocacy',
        skepticism: 'Test skepticism',
        improved_critique: 'Improved critique',
        score_delta: 2
      }],
      processing_time: 1.0,
      timestamp: '2025-08-01T00:00:00Z',
      structured_output: true
    };
    
    expect(response.structured_output).toBe(true);
    expect(response.results[0].improved_idea).not.toContain('Here is');
    expect(response.results[0].improved_idea).not.toContain('improved version');
  });
});