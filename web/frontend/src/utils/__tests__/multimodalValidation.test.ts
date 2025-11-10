/**
 * Tests for multi-modal validation utilities
 */

import {
  MULTIMODAL_CONSTANTS,
  validateUrl,
  validateFile,
  formatFileSize,
  getFileExtension,
  validateMultiModalInputs,
  ValidationError
} from '../multimodalValidation';

describe('Multi-Modal Validation Constants', () => {
  it('should have correct file size limits', () => {
    expect(MULTIMODAL_CONSTANTS.MAX_IMAGE_SIZE).toBe(8_000_000); // 8MB
    expect(MULTIMODAL_CONSTANTS.MAX_PDF_SIZE).toBe(40_000_000); // 40MB
    expect(MULTIMODAL_CONSTANTS.MAX_FILE_SIZE).toBe(20_000_000); // 20MB
  });

  it('should have correct format lists', () => {
    expect(MULTIMODAL_CONSTANTS.SUPPORTED_IMAGE_FORMATS).toContain('png');
    expect(MULTIMODAL_CONSTANTS.SUPPORTED_IMAGE_FORMATS).toContain('jpg');
    expect(MULTIMODAL_CONSTANTS.SUPPORTED_IMAGE_FORMATS).toContain('jpeg');
    expect(MULTIMODAL_CONSTANTS.SUPPORTED_DOC_FORMATS).toContain('pdf');
    expect(MULTIMODAL_CONSTANTS.SUPPORTED_DOC_FORMATS).toContain('txt');
  });

  it('should have correct URL limit', () => {
    expect(MULTIMODAL_CONSTANTS.MAX_URLS).toBe(5);
  });
});

describe('validateUrl', () => {
  it('should accept valid HTTP URLs', () => {
    expect(() => validateUrl('http://example.com')).not.toThrow();
  });

  it('should accept valid HTTPS URLs', () => {
    expect(() => validateUrl('https://example.com')).not.toThrow();
  });

  it('should reject empty URLs', () => {
    expect(() => validateUrl('')).toThrow(ValidationError);
    expect(() => validateUrl('')).toThrow('URL cannot be empty');
  });

  it('should reject URLs without http/https protocol', () => {
    expect(() => validateUrl('example.com')).toThrow(ValidationError);
    expect(() => validateUrl('ftp://example.com')).toThrow(ValidationError);
  });

  it('should reject invalid URL format', () => {
    expect(() => validateUrl('not a url')).toThrow(ValidationError);
    expect(() => validateUrl('https://')).toThrow(ValidationError);
  });

  it('should trim whitespace from URLs', () => {
    expect(() => validateUrl('  https://example.com  ')).not.toThrow();
  });
});

describe('validateFile', () => {
  it('should accept valid image files within size limit', () => {
    const file = new File(['x'.repeat(1000)], 'test.png', { type: 'image/png' });
    expect(() => validateFile(file)).not.toThrow();
  });

  it('should accept valid PDF files within size limit', () => {
    const file = new File(['x'.repeat(1000)], 'test.pdf', { type: 'application/pdf' });
    expect(() => validateFile(file)).not.toThrow();
  });

  it('should reject files that are too large (images)', () => {
    const file = new File(['x'.repeat(9_000_000)], 'test.png', { type: 'image/png' });
    expect(() => validateFile(file)).toThrow(ValidationError);
    expect(() => validateFile(file)).toThrow(/Image files must be under.*MB/);
  });

  it('should reject files that are too large (PDFs)', () => {
    const file = new File(['x'.repeat(41_000_000)], 'test.pdf', { type: 'application/pdf' });
    expect(() => validateFile(file)).toThrow(ValidationError);
    expect(() => validateFile(file)).toThrow(/PDF files must be under.*MB/);
  });

  it('should reject files that are too large (documents)', () => {
    const file = new File(['x'.repeat(21_000_000)], 'test.txt', { type: 'text/plain' });
    expect(() => validateFile(file)).toThrow(ValidationError);
    expect(() => validateFile(file)).toThrow(/Document files must be under.*MB/);
  });

  it('should reject unsupported file formats', () => {
    const file = new File(['test'], 'test.exe', { type: 'application/x-msdownload' });
    expect(() => validateFile(file)).toThrow(ValidationError);
    expect(() => validateFile(file)).toThrow('Unsupported file format: exe');
  });

  it('should handle files without extensions', () => {
    const file = new File(['test'], 'noextension', { type: 'text/plain' });
    expect(() => validateFile(file)).toThrow(ValidationError);
  });

  it('should be case-insensitive for extensions', () => {
    const file = new File(['test'], 'test.PNG', { type: 'image/png' });
    expect(() => validateFile(file)).not.toThrow();
  });
});

describe('formatFileSize', () => {
  it('should format bytes correctly', () => {
    expect(formatFileSize(500)).toBe('500 B');
    expect(formatFileSize(1000)).toBe('1000 B');
  });

  it('should format kilobytes correctly', () => {
    expect(formatFileSize(1024)).toBe('1.0 KB');
    expect(formatFileSize(1536)).toBe('1.5 KB');
    expect(formatFileSize(10240)).toBe('10.0 KB');
  });

  it('should format megabytes correctly', () => {
    expect(formatFileSize(1048576)).toBe('1.0 MB');
    expect(formatFileSize(5242880)).toBe('5.0 MB');
    expect(formatFileSize(10485760)).toBe('10.0 MB');
  });

  it('should format gigabytes correctly', () => {
    expect(formatFileSize(1073741824)).toBe('1.0 GB');
    expect(formatFileSize(2147483648)).toBe('2.0 GB');
  });

  it('should handle zero bytes', () => {
    expect(formatFileSize(0)).toBe('0 B');
  });
});

describe('getFileExtension', () => {
  it('should extract extension from filename', () => {
    expect(getFileExtension('test.png')).toBe('png');
    expect(getFileExtension('document.pdf')).toBe('pdf');
    expect(getFileExtension('file.txt')).toBe('txt');
  });

  it('should handle multiple dots in filename', () => {
    expect(getFileExtension('my.file.name.jpg')).toBe('jpg');
  });

  it('should be case-insensitive', () => {
    expect(getFileExtension('TEST.PNG')).toBe('png');
    expect(getFileExtension('Document.PDF')).toBe('pdf');
  });

  it('should return empty string for files without extension', () => {
    expect(getFileExtension('noextension')).toBe('');
  });

  it('should handle dot at the beginning', () => {
    expect(getFileExtension('.hiddenfile')).toBe('hiddenfile');
  });
});

describe('validateMultiModalInputs', () => {
  it('should accept valid URLs and files', () => {
    const urls = ['https://example.com', 'https://test.com'];
    const files = [
      new File(['test'], 'test.png', { type: 'image/png' }),
      new File(['test'], 'doc.pdf', { type: 'application/pdf' })
    ];

    expect(() => validateMultiModalInputs(urls, files)).not.toThrow();
  });

  it('should reject more than 5 URLs', () => {
    const urls = [
      'https://example1.com',
      'https://example2.com',
      'https://example3.com',
      'https://example4.com',
      'https://example5.com',
      'https://example6.com'
    ];

    expect(() => validateMultiModalInputs(urls, [])).toThrow(ValidationError);
    expect(() => validateMultiModalInputs(urls, [])).toThrow('Maximum 5 URLs allowed');
  });

  it('should accept empty inputs', () => {
    expect(() => validateMultiModalInputs([], [])).not.toThrow();
  });

  it('should accept undefined inputs', () => {
    expect(() => validateMultiModalInputs(undefined, undefined)).not.toThrow();
  });

  it('should validate each URL', () => {
    const urls = ['https://valid.com', 'invalid url'];
    expect(() => validateMultiModalInputs(urls, [])).toThrow(ValidationError);
  });

  it('should validate each file', () => {
    const files = [
      new File(['test'], 'valid.png', { type: 'image/png' }),
      new File(['test'], 'invalid.exe', { type: 'application/x-msdownload' })
    ];

    expect(() => validateMultiModalInputs([], files)).toThrow(ValidationError);
  });

  it('should reject duplicate URLs', () => {
    const urls = ['https://example.com', 'https://example.com'];
    expect(() => validateMultiModalInputs(urls, [])).toThrow(ValidationError);
    expect(() => validateMultiModalInputs(urls, [])).toThrow('Duplicate URL');
  });
});

describe('ValidationError', () => {
  it('should be an instance of Error', () => {
    const error = new ValidationError('test message');
    expect(error).toBeInstanceOf(Error);
  });

  it('should have correct name', () => {
    const error = new ValidationError('test message');
    expect(error.name).toBe('ValidationError');
  });

  it('should preserve error message', () => {
    const error = new ValidationError('test message');
    expect(error.message).toBe('test message');
  });
});
