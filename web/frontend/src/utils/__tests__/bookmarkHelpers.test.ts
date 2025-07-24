import { truncateField, truncateRequiredField, mapBookmarkToApiFormat } from '../bookmarkHelpers';

describe('bookmarkHelpers', () => {
  describe('truncateField', () => {
    it('returns undefined for undefined input', () => {
      expect(truncateField(undefined)).toBeUndefined();
    });

    it('returns undefined for empty string input', () => {
      expect(truncateField('')).toBeUndefined();
    });

    it('returns short strings unchanged', () => {
      expect(truncateField('short text')).toBe('short text');
    });

    it('truncates long strings with ellipsis', () => {
      const longString = 'a'.repeat(10005);
      const result = truncateField(longString);
      expect(result).toHaveLength(10000);
      expect(result?.endsWith('...')).toBe(true);
      expect(result).toBe('a'.repeat(9997) + '...');
    });

    it('respects custom max length', () => {
      const result = truncateField('hello world', 5);
      expect(result).toBe('he...');
    });
  });

  describe('truncateRequiredField', () => {
    it('returns empty string for undefined input', () => {
      expect(truncateRequiredField(undefined)).toBe('');
    });

    it('returns empty string for empty string input', () => {
      expect(truncateRequiredField('')).toBe('');
    });

    it('returns short strings unchanged', () => {
      expect(truncateRequiredField('short text')).toBe('short text');
    });

    it('truncates long strings with ellipsis', () => {
      const longString = 'b'.repeat(10005);
      const result = truncateRequiredField(longString);
      expect(result).toHaveLength(10000);
      expect(result.endsWith('...')).toBe(true);
      expect(result).toBe('b'.repeat(9997) + '...');
    });

    it('respects custom max length', () => {
      const result = truncateRequiredField('hello world', 5);
      expect(result).toBe('he...');
    });
  });

  describe('mapBookmarkToApiFormat', () => {
    it('maps theme to topic and constraints to context', () => {
      const input = {
        theme: 'Science',
        constraints: 'Must be practical',
        idea: 'Test idea',
        otherField: 'value'
      };

      const result = mapBookmarkToApiFormat(input);
      
      expect(result).toEqual({
        topic: 'Science',
        context: 'Must be practical',
        idea: 'Test idea',
        otherField: 'value'
      });
      expect(result).not.toHaveProperty('theme');
      expect(result).not.toHaveProperty('constraints');
    });

    it('handles missing theme and constraints', () => {
      const input = {
        idea: 'Test idea'
      };

      const result = mapBookmarkToApiFormat(input);
      
      expect(result).toEqual({
        topic: undefined,
        context: undefined,
        idea: 'Test idea'
      });
    });
  });
});