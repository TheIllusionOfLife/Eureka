/**
 * FormData Conversion Utilities
 *
 * Converts IdeaGenerationRequest to FormData for multipart/form-data uploads.
 * This is required when sending files to the backend API.
 */

import { IdeaGenerationRequest } from '../types';

/**
 * Check if the request has multi-modal inputs (URLs or files)
 */
export function hasMultiModalInputs(
  request: Partial<IdeaGenerationRequest>,
  files?: File[]
): boolean {
  const hasUrls = request.multimodal_urls && request.multimodal_urls.length > 0;
  const hasFiles = files && files.length > 0;

  return Boolean(hasUrls || hasFiles);
}

/**
 * Determine if FormData should be used instead of JSON
 */
export function shouldUseFormData(
  request: Partial<IdeaGenerationRequest>,
  files?: File[]
): boolean {
  return hasMultiModalInputs(request, files);
}

/**
 * Build FormData from IdeaGenerationRequest and files
 *
 * Converts all request fields to form data format:
 * - Primitives (string, number, boolean) → string values
 * - Arrays → JSON stringified
 * - Files → File objects
 * - null → "null" string
 * - undefined → omitted
 */
export function buildMultiModalFormData(
  request: Partial<IdeaGenerationRequest>,
  files?: File[]
): FormData {
  const formData = new FormData();

  // Convert each request field to FormData format
  Object.entries(request).forEach(([key, value]) => {
    if (value === undefined) {
      // Skip undefined values
      return;
    }

    // Handle arrays (except multimodal_urls which needs special handling)
    if (Array.isArray(value)) {
      if (key === 'multimodal_urls') {
        // Only add if not empty
        if (value.length > 0) {
          formData.append(key, JSON.stringify(value));
        }
      } else if (key === 'bookmark_ids') {
        // Bookmark IDs as JSON array
        if (value.length > 0) {
          formData.append(key, JSON.stringify(value));
        }
      } else {
        // Other arrays (future-proofing)
        formData.append(key, JSON.stringify(value));
      }
      return;
    }

    // Handle primitives and null
    if (value === null) {
      formData.append(key, 'null');
    } else if (typeof value === 'boolean') {
      formData.append(key, value.toString());
    } else if (typeof value === 'number') {
      formData.append(key, value.toString());
    } else if (typeof value === 'string') {
      formData.append(key, value);
    } else {
      // Objects (should not happen with current schema, but handle gracefully)
      formData.append(key, JSON.stringify(value));
    }
  });

  // Add files if present
  if (files && files.length > 0) {
    files.forEach(file => {
      formData.append('multimodal_files', file);
    });
  }

  return formData;
}

/**
 * Get content type header for multi-modal requests
 *
 * When using FormData, Axios will automatically set Content-Type to
 * multipart/form-data with boundary. This function is for reference.
 */
export function getMultiModalHeaders(): Record<string, string> {
  // Axios will set this automatically when FormData is used
  // We return empty object to let Axios handle it
  return {};
}
