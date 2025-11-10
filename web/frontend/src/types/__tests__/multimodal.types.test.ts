/**
 * Tests for multi-modal type definitions
 */

import { IdeaGenerationRequest, FormData } from '../index';

describe('Multi-Modal Type Definitions', () => {
  describe('IdeaGenerationRequest', () => {
    it('should allow multimodal_urls field', () => {
      const request: IdeaGenerationRequest = {
        theme: 'Test theme',
        constraints: 'Test constraints',
        num_top_candidates: 3,
        enable_novelty_filter: true,
        novelty_threshold: 0.7,
        enhanced_reasoning: false,
        multi_dimensional_eval: false,
        logical_inference: false,
        verbose: false,
        show_detailed_results: false,
        multimodal_urls: ['https://example.com', 'https://test.com']
      };

      expect(request.multimodal_urls).toHaveLength(2);
      expect(request.multimodal_urls?.[0]).toBe('https://example.com');
    });

    it('should allow multimodal_urls to be optional', () => {
      const request: IdeaGenerationRequest = {
        theme: 'Test theme',
        num_top_candidates: 3,
        enable_novelty_filter: true,
        novelty_threshold: 0.7,
        enhanced_reasoning: false,
        multi_dimensional_eval: false,
        logical_inference: false,
        verbose: false,
        show_detailed_results: false
      };

      expect(request.multimodal_urls).toBeUndefined();
    });

    it('should allow empty multimodal_urls array', () => {
      const request: IdeaGenerationRequest = {
        theme: 'Test theme',
        num_top_candidates: 3,
        enable_novelty_filter: true,
        novelty_threshold: 0.7,
        enhanced_reasoning: false,
        multi_dimensional_eval: false,
        logical_inference: false,
        verbose: false,
        show_detailed_results: false,
        multimodal_urls: []
      };

      expect(request.multimodal_urls).toHaveLength(0);
    });

    it('should handle maximum 5 URLs', () => {
      const request: IdeaGenerationRequest = {
        theme: 'Test theme',
        num_top_candidates: 3,
        enable_novelty_filter: true,
        novelty_threshold: 0.7,
        enhanced_reasoning: false,
        multi_dimensional_eval: false,
        logical_inference: false,
        verbose: false,
        show_detailed_results: false,
        multimodal_urls: [
          'https://example1.com',
          'https://example2.com',
          'https://example3.com',
          'https://example4.com',
          'https://example5.com'
        ]
      };

      expect(request.multimodal_urls).toHaveLength(5);
    });
  });

  describe('FormData', () => {
    it('should allow multimodal_urls field', () => {
      const formData: FormData = {
        theme: 'Test theme',
        constraints: 'Test constraints',
        num_top_candidates: 3,
        enable_novelty_filter: true,
        novelty_threshold: 0.7,
        temperature_preset: null,
        temperature: null,
        enhanced_reasoning: false,
        multi_dimensional_eval: false,
        logical_inference: false,
        verbose: false,
        show_detailed_results: false,
        multimodal_urls: ['https://example.com']
      };

      expect(formData.multimodal_urls).toHaveLength(1);
    });

    it('should allow multimodal_files field', () => {
      const mockFile = new File(['test'], 'test.pdf', { type: 'application/pdf' });

      const formData: FormData = {
        theme: 'Test theme',
        constraints: 'Test constraints',
        num_top_candidates: 3,
        enable_novelty_filter: true,
        novelty_threshold: 0.7,
        temperature_preset: null,
        temperature: null,
        enhanced_reasoning: false,
        multi_dimensional_eval: false,
        logical_inference: false,
        verbose: false,
        show_detailed_results: false,
        multimodal_files: [mockFile]
      };

      expect(formData.multimodal_files).toHaveLength(1);
      expect(formData.multimodal_files?.[0].name).toBe('test.pdf');
    });

    it('should allow both URLs and files together', () => {
      const mockFile = new File(['test'], 'test.pdf', { type: 'application/pdf' });

      const formData: FormData = {
        theme: 'Test theme',
        constraints: 'Test constraints',
        num_top_candidates: 3,
        enable_novelty_filter: true,
        novelty_threshold: 0.7,
        temperature_preset: null,
        temperature: null,
        enhanced_reasoning: false,
        multi_dimensional_eval: false,
        logical_inference: false,
        verbose: false,
        show_detailed_results: false,
        multimodal_urls: ['https://example.com'],
        multimodal_files: [mockFile]
      };

      expect(formData.multimodal_urls).toHaveLength(1);
      expect(formData.multimodal_files).toHaveLength(1);
    });

    it('should allow multimodal fields to be optional', () => {
      const formData: FormData = {
        theme: 'Test theme',
        constraints: 'Test constraints',
        num_top_candidates: 3,
        enable_novelty_filter: true,
        novelty_threshold: 0.7,
        temperature_preset: null,
        temperature: null,
        enhanced_reasoning: false,
        multi_dimensional_eval: false,
        logical_inference: false,
        verbose: false,
        show_detailed_results: false
      };

      expect(formData.multimodal_urls).toBeUndefined();
      expect(formData.multimodal_files).toBeUndefined();
    });
  });
});
