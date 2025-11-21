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
 *
 * Only use FormData when actual files need to be uploaded.
 * URLs can be sent via regular JSON requests.
 */
export function shouldUseFormData(
  request: Partial<IdeaGenerationRequest>,
  files?: File[]
): boolean {
  // Only use FormData if there are actual files to upload
  // URLs can be sent via regular JSON without multipart encoding
  return Boolean(files && files.length > 0);
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

  // FastAPI with mixed Body and File parameters expects the JSON data
  // to be sent as a single JSON string in a form field called 'idea_request'
  // when files are present (multipart/form-data)

  // Clean the request object: remove undefined values
  const cleanedRequest: Partial<IdeaGenerationRequest> = {};
  Object.entries(request).forEach(([key, value]) => {
    if (value !== undefined) {
      // Type assertion needed because we're dynamically assigning properties
      (cleanedRequest as any)[key] = value;
    }
  });

  // Send the entire request as a JSON string in 'idea_request' field
  formData.append('idea_request', JSON.stringify(cleanedRequest));

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
