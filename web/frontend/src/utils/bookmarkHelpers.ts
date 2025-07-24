/**
 * Bookmark helper utilities for field truncation and data transformation
 */

/**
 * Truncates a string to a maximum length, adding ellipsis if truncated
 * @param str - The string to truncate
 * @param maxLength - Maximum allowed length (default: 10000)
 * @returns Truncated string or undefined if input was undefined
 */
export const truncateField = (str: string | undefined, maxLength: number = 10000): string | undefined => {
  if (!str) return undefined;  // Convert falsy values (including empty strings) to undefined
  if (str.length <= maxLength) return str;
  
  // Handle edge case where maxLength is too small for ellipsis
  if (maxLength < 3) return str.substring(0, maxLength);
  
  return str.substring(0, maxLength - 3) + '...';
};

/**
 * Truncates a required field, ensuring it returns a string
 * @param str - The string to truncate
 * @param maxLength - Maximum allowed length (default: 10000)
 * @returns Truncated string, empty string if input was falsy
 */
export const truncateRequiredField = (str: string | undefined, maxLength: number = 10000): string => {
  if (!str) return '';
  if (str.length <= maxLength) return str;
  
  // Handle edge case where maxLength is too small for ellipsis
  if (maxLength < 3) return str.substring(0, maxLength);
  
  return str.substring(0, maxLength - 3) + '...';
};

/**
 * Maps frontend bookmark data to backend API format
 * Transforms 'theme' to 'topic' and 'constraints' to 'context'
 * @param bookmarkData - Frontend bookmark data
 * @returns API-formatted data with proper field names
 */
export const mapBookmarkToApiFormat = (bookmarkData: any): any => {
  const { theme, constraints, ...rest } = bookmarkData;
  
  return {
    ...rest,
    topic: theme,           // Backend expects 'topic' not 'theme'
    context: constraints,   // Backend expects 'context' not 'constraints'
  };
};