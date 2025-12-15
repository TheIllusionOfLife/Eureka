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

    it('handles edge case when maxLength is 0', () => {
      const result = truncateField('hello', 0);
      expect(result).toBe('');
      expect(result).toHaveLength(0);
    });

    it('handles edge case when maxLength is 1', () => {
      const result = truncateField('hello', 1);
      expect(result).toBe('h');
      expect(result).toHaveLength(1);
    });

    it('handles edge case when maxLength is 2', () => {
      const result = truncateField('hello', 2);
      expect(result).toBe('he');
      expect(result).toHaveLength(2);
    });

    it('adds ellipsis only when maxLength is 3 or more', () => {
      const result = truncateField('hello world', 3);
      expect(result).toBe('...');
      expect(result).toHaveLength(3);
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

    it('handles edge case when maxLength is 0', () => {
      const result = truncateRequiredField('hello', 0);
      expect(result).toBe('');
      expect(result).toHaveLength(0);
    });

    it('handles edge case when maxLength is 1', () => {
      const result = truncateRequiredField('hello', 1);
      expect(result).toBe('h');
      expect(result).toHaveLength(1);
    });

    it('handles edge case when maxLength is 2', () => {
      const result = truncateRequiredField('hello', 2);
      expect(result).toBe('he');
      expect(result).toHaveLength(2);
    });

    it('adds ellipsis only when maxLength is 3 or more', () => {
      const result = truncateRequiredField('hello world', 3);
      expect(result).toBe('...');
      expect(result).toHaveLength(3);
    });
  });

  describe('mapBookmarkToApiFormat', () => {
    it('passes through topic and context fields unchanged', () => {
      const input = {
        topic: 'Science',
        context: 'Must be practical',
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
    });

    it('handles missing topic and context', () => {
      const input = {
        idea: 'Test idea'
      };

      const result = mapBookmarkToApiFormat(input);

      expect(result).toEqual({
        idea: 'Test idea'
      });
    });
  });
});