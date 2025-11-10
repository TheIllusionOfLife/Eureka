/**
 * Multi-modal input validation utilities
 *
 * Validates URLs and files for multi-modal context inputs.
 * Matches backend validation rules from execution_constants.py
 */

// ============================================
// Constants (matching backend configuration)
// ============================================

export const MULTIMODAL_CONSTANTS = {
  // File size limits (bytes) - matching backend MultiModalConfig
  MAX_IMAGE_SIZE: 8_000_000,      // 8MB
  MAX_PDF_SIZE: 40_000_000,       // 40MB
  MAX_FILE_SIZE: 20_000_000,      // 20MB (for other documents)

  // Supported formats (matching backend)
  SUPPORTED_IMAGE_FORMATS: new Set(['png', 'jpg', 'jpeg', 'webp', 'gif', 'bmp']),
  SUPPORTED_DOC_FORMATS: new Set(['pdf', 'txt', 'md', 'doc', 'docx']),

  // URL limits (matching backend Pydantic validation)
  MAX_URLS: 5,
  MAX_URL_CONTENT_LENGTH: 5_000_000  // 5MB
} as const;

// ============================================
// Custom Error Class
// ============================================

export class ValidationError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'ValidationError';
  }
}

// ============================================
// Utility Functions
// ============================================

/**
 * Extract file extension from filename (lowercase)
 */
export function getFileExtension(filename: string): string {
  const parts = filename.split('.');
  if (parts.length === 1) return '';
  return (parts[parts.length - 1] || '').toLowerCase();
}

/**
 * Format file size in human-readable format
 */
export function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 B';

  const units = ['B', 'KB', 'MB', 'GB'];
  const k = 1024;
  const i = Math.floor(Math.log(bytes) / Math.log(k));

  if (i === 0) {
    return `${bytes} ${units[0]}`;
  }

  return `${(bytes / Math.pow(k, i)).toFixed(1)} ${units[i]}`;
}

// ============================================
// Validation Functions
// ============================================

/**
 * Validate URL format and protocol
 * @throws {ValidationError} if URL is invalid
 */
export function validateUrl(url: string): void {
  const trimmedUrl = url.trim();

  if (!trimmedUrl) {
    throw new ValidationError('URL cannot be empty');
  }

  // Check protocol
  if (!trimmedUrl.startsWith('http://') && !trimmedUrl.startsWith('https://')) {
    throw new ValidationError('URL must start with http:// or https://');
  }

  // Validate URL format
  try {
    new URL(trimmedUrl);
  } catch (error) {
    throw new ValidationError('Invalid URL format');
  }
}

/**
 * Validate file type and size
 * @throws {ValidationError} if file is invalid
 */
export function validateFile(file: File): void {
  const extension = getFileExtension(file.name);

  if (!extension) {
    throw new ValidationError('File must have an extension');
  }

  // Check if format is supported
  const isImage = MULTIMODAL_CONSTANTS.SUPPORTED_IMAGE_FORMATS.has(extension);
  const isDocument = MULTIMODAL_CONSTANTS.SUPPORTED_DOC_FORMATS.has(extension);

  if (!isImage && !isDocument) {
    throw new ValidationError(`Unsupported file format: ${extension}`);
  }

  // Check file size based on type
  if (isImage) {
    if (file.size > MULTIMODAL_CONSTANTS.MAX_IMAGE_SIZE) {
      throw new ValidationError(
        `Image files must be under ${formatFileSize(MULTIMODAL_CONSTANTS.MAX_IMAGE_SIZE)} (current: ${formatFileSize(file.size)})`
      );
    }
  } else if (extension === 'pdf') {
    if (file.size > MULTIMODAL_CONSTANTS.MAX_PDF_SIZE) {
      throw new ValidationError(
        `PDF files must be under ${formatFileSize(MULTIMODAL_CONSTANTS.MAX_PDF_SIZE)} (current: ${formatFileSize(file.size)})`
      );
    }
  } else {
    if (file.size > MULTIMODAL_CONSTANTS.MAX_FILE_SIZE) {
      throw new ValidationError(
        `Document files must be under ${formatFileSize(MULTIMODAL_CONSTANTS.MAX_FILE_SIZE)} (current: ${formatFileSize(file.size)})`
      );
    }
  }
}

/**
 * Validate all multi-modal inputs (URLs and files)
 * @throws {ValidationError} if any input is invalid
 */
export function validateMultiModalInputs(
  urls?: string[],
  files?: File[]
): void {
  // Validate URLs
  if (urls && urls.length > 0) {
    // Check URL count
    if (urls.length > MULTIMODAL_CONSTANTS.MAX_URLS) {
      throw new ValidationError(`Maximum ${MULTIMODAL_CONSTANTS.MAX_URLS} URLs allowed`);
    }

    // Check for duplicates
    const uniqueUrls = new Set(urls.map(url => url.trim()));
    if (uniqueUrls.size !== urls.length) {
      throw new ValidationError('Duplicate URLs are not allowed');
    }

    // Validate each URL
    for (const url of urls) {
      validateUrl(url);
    }
  }

  // Validate files
  if (files && files.length > 0) {
    for (const file of files) {
      validateFile(file);
    }
  }
}
