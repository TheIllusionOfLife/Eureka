/**
 * Utility for consistent number formatting across the application.
 */

/**
 * Formats a score to one decimal place with consistent rounding.
 * Uses Math.round to avoid toFixed rounding inconsistencies for .5 values.
 * 
 * @param score The numeric score to format
 * @returns Formatted string (e.g., "8.5")
 */
export const formatScore = (score: number | null | undefined): string => {
  if (score === null || score === undefined) return '0.0';
  
  // Multiply by 10, round to nearest integer, then divide by 10
  // to get consistent 1-decimal place rounding.
  const rounded = Math.round(score * 10) / 10;
  return rounded.toFixed(1);
};
