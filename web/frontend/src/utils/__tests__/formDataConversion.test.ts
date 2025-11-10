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

    it('should create FormData with all JSON fields', () => {
      const formData = buildMultiModalFormData(baseRequest, []);

      expect(formData.get('theme')).toBe('Test Theme');
      expect(formData.get('constraints')).toBe('Test Constraints');
      expect(formData.get('num_top_candidates')).toBe('3');
      expect(formData.get('enable_novelty_filter')).toBe('true');
      expect(formData.get('novelty_threshold')).toBe('0.7');
    });

    it('should handle null and undefined values', () => {
      const request = {
        ...baseRequest,
        constraints: undefined,
        temperature_preset: null
      };

      const formData = buildMultiModalFormData(request, []);

      // Undefined should be omitted
      expect(formData.has('constraints')).toBe(false);
      // Null should be included
      expect(formData.get('temperature_preset')).toBe('null');
    });

    it('should handle boolean values', () => {
      const formData = buildMultiModalFormData(baseRequest, []);

      expect(formData.get('enable_novelty_filter')).toBe('true');
      expect(formData.get('enhanced_reasoning')).toBe('false');
    });

    it('should handle number values', () => {
      const formData = buildMultiModalFormData(baseRequest, []);

      expect(formData.get('num_top_candidates')).toBe('3');
      expect(formData.get('novelty_threshold')).toBe('0.7');
    });

    it('should add URLs as JSON array when present', () => {
      const request = {
        ...baseRequest,
        multimodal_urls: ['https://example1.com', 'https://example2.com']
      };

      const formData = buildMultiModalFormData(request, []);

      const urlsValue = formData.get('multimodal_urls');
      expect(urlsValue).toBeTruthy();
      expect(JSON.parse(urlsValue as string)).toEqual([
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

      expect(formData.get('multimodal_urls')).toBeTruthy();
      expect(formData.getAll('multimodal_files')).toHaveLength(1);
    });

    it('should handle empty URLs and files arrays', () => {
      const request = {
        ...baseRequest,
        multimodal_urls: []
      };

      const formData = buildMultiModalFormData(request, []);

      // Empty arrays should result in no multimodal fields
      expect(formData.has('multimodal_urls')).toBe(false);
      expect(formData.has('multimodal_files')).toBe(false);
    });

    it('should handle bookmark_ids array', () => {
      const request = {
        ...baseRequest,
        bookmark_ids: ['bookmark-1', 'bookmark-2']
      };

      const formData = buildMultiModalFormData(request, []);

      const bookmarkIds = formData.get('bookmark_ids');
      expect(bookmarkIds).toBeTruthy();
      expect(JSON.parse(bookmarkIds as string)).toEqual(['bookmark-1', 'bookmark-2']);
    });

    it('should convert all fields to strings appropriately', () => {
      const request = {
        ...baseRequest,
        num_top_candidates: 5,
        novelty_threshold: 0.85,
        enable_novelty_filter: false
      };

      const formData = buildMultiModalFormData(request, []);

      // FormData stores everything as strings
      expect(typeof formData.get('num_top_candidates')).toBe('string');
      expect(typeof formData.get('novelty_threshold')).toBe('string');
      expect(typeof formData.get('enable_novelty_filter')).toBe('string');

      // But values should be correct
      expect(formData.get('num_top_candidates')).toBe('5');
      expect(formData.get('novelty_threshold')).toBe('0.85');
      expect(formData.get('enable_novelty_filter')).toBe('false');
    });

    it('should return a valid FormData object', () => {
      const formData = buildMultiModalFormData(baseRequest, []);

      expect(formData).toBeInstanceOf(FormData);
      expect(formData.get('theme')).toBe('Test Theme');
    });
  });
});
