/**
 * Tests for FormData conversion utilities
 */

import {
  buildMultiModalFormData,
  hasMultiModalInputs,
  shouldUseFormData
} from '../formDataConversion';
import { IdeaGenerationRequest } from '../../types';

describe('FormData Conversion Utilities', () => {
  describe('hasMultiModalInputs', () => {
    it('should return true when URLs are present', () => {
      const request: Partial<IdeaGenerationRequest> = {
        multimodal_urls: ['https://example.com']
      };

      expect(hasMultiModalInputs(request, [])).toBe(true);
    });

    it('should return true when files are present', () => {
      const files = [new File(['test'], 'test.pdf', { type: 'application/pdf' })];

      expect(hasMultiModalInputs({}, files)).toBe(true);
    });

    it('should return true when both URLs and files are present', () => {
      const request: Partial<IdeaGenerationRequest> = {
        multimodal_urls: ['https://example.com']
      };
      const files = [new File(['test'], 'test.pdf', { type: 'application/pdf' })];

      expect(hasMultiModalInputs(request, files)).toBe(true);
    });

    it('should return false when neither URLs nor files are present', () => {
      expect(hasMultiModalInputs({}, [])).toBe(false);
    });

    it('should return false when arrays are empty', () => {
      const request: Partial<IdeaGenerationRequest> = {
        multimodal_urls: []
      };

      expect(hasMultiModalInputs(request, [])).toBe(false);
    });

    it('should return false when arrays are undefined', () => {
      expect(hasMultiModalInputs({}, undefined)).toBe(false);
    });
  });

  describe('shouldUseFormData', () => {
    it('should return true when hasMultiModalInputs returns true', () => {
      const request: Partial<IdeaGenerationRequest> = {
        multimodal_urls: ['https://example.com']
      };

      expect(shouldUseFormData(request, [])).toBe(true);
    });

    it('should return false when hasMultiModalInputs returns false', () => {
      expect(shouldUseFormData({}, [])).toBe(false);
    });
  });

  describe('buildMultiModalFormData', () => {
    const baseRequest: IdeaGenerationRequest = {
      theme: 'Test Theme',
      constraints: 'Test Constraints',
      num_top_candidates: 3,
      enable_novelty_filter: true,
      novelty_threshold: 0.7,
      temperature_preset: 'balanced',
      temperature: null,
      enhanced_reasoning: false,
      multi_dimensional_eval: true,
      logical_inference: false,
      verbose: false,
      show_detailed_results: false
    };

    it('should create FormData with idea_request as JSON string', () => {
      const formData = buildMultiModalFormData(baseRequest, []);

      const ideaRequestStr = formData.get('idea_request');
      expect(ideaRequestStr).toBeTruthy();
      expect(typeof ideaRequestStr).toBe('string');

      const parsed = JSON.parse(ideaRequestStr as string);
      expect(parsed.theme).toBe('Test Theme');
      expect(parsed.constraints).toBe('Test Constraints');
      expect(parsed.num_top_candidates).toBe(3);
      expect(parsed.enable_novelty_filter).toBe(true);
      expect(parsed.novelty_threshold).toBe(0.7);
    });

    it('should handle null and undefined values', () => {
      const request = {
        ...baseRequest,
        constraints: undefined,
        temperature_preset: null
      };

      const formData = buildMultiModalFormData(request, []);
      const parsed = JSON.parse(formData.get('idea_request') as string);

      // Undefined should be omitted
      expect(parsed.constraints).toBeUndefined();
      // Null should be included
      expect(parsed.temperature_preset).toBe(null);
    });

    it('should handle boolean values', () => {
      const formData = buildMultiModalFormData(baseRequest, []);
      const parsed = JSON.parse(formData.get('idea_request') as string);

      expect(parsed.enable_novelty_filter).toBe(true);
      expect(parsed.enhanced_reasoning).toBe(false);
    });

    it('should handle number values', () => {
      const formData = buildMultiModalFormData(baseRequest, []);
      const parsed = JSON.parse(formData.get('idea_request') as string);

      expect(parsed.num_top_candidates).toBe(3);
      expect(parsed.novelty_threshold).toBe(0.7);
    });

    it('should add URLs as array when present', () => {
      const request = {
        ...baseRequest,
        multimodal_urls: ['https://example1.com', 'https://example2.com']
      };

      const formData = buildMultiModalFormData(request, []);
      const parsed = JSON.parse(formData.get('idea_request') as string);

      expect(parsed.multimodal_urls).toEqual([
        'https://example1.com',
        'https://example2.com'
      ]);
    });

    it('should add files with correct field names', () => {
      const file1 = new File(['test1'], 'test1.pdf', { type: 'application/pdf' });
      const file2 = new File(['test2'], 'test2.png', { type: 'image/png' });
      const files = [file1, file2];

      const formData = buildMultiModalFormData(baseRequest, files);

      const formDataFiles = formData.getAll('multimodal_files');
      expect(formDataFiles).toHaveLength(2);
      expect(formDataFiles[0]).toBe(file1);
      expect(formDataFiles[1]).toBe(file2);
    });

    it('should handle both URLs and files together', () => {
      const request = {
        ...baseRequest,
        multimodal_urls: ['https://example.com']
      };
      const files = [new File(['test'], 'test.pdf', { type: 'application/pdf' })];

      const formData = buildMultiModalFormData(request, files);
      const parsed = JSON.parse(formData.get('idea_request') as string);

      expect(parsed.multimodal_urls).toEqual(['https://example.com']);
      expect(formData.getAll('multimodal_files')).toHaveLength(1);
    });

    it('should handle empty URLs array', () => {
      const request = {
        ...baseRequest,
        multimodal_urls: []
      };

      const formData = buildMultiModalFormData(request, []);
      const parsed = JSON.parse(formData.get('idea_request') as string);

      // Empty arrays should be included in JSON
      expect(parsed.multimodal_urls).toEqual([]);
    });

    it('should handle bookmark_ids array', () => {
      const request = {
        ...baseRequest,
        bookmark_ids: ['bookmark-1', 'bookmark-2']
      };

      const formData = buildMultiModalFormData(request, []);
      const parsed = JSON.parse(formData.get('idea_request') as string);

      expect(parsed.bookmark_ids).toEqual(['bookmark-1', 'bookmark-2']);
    });

    it('should return a valid FormData object', () => {
      const formData = buildMultiModalFormData(baseRequest, []);

      expect(formData).toBeInstanceOf(FormData);
      expect(formData.get('idea_request')).toBeTruthy();
    });

    it('should create valid JSON that can be parsed', () => {
      const formData = buildMultiModalFormData(baseRequest, []);
      const ideaRequestStr = formData.get('idea_request') as string;

      // Should not throw
      expect(() => JSON.parse(ideaRequestStr)).not.toThrow();
    });
  });
});
