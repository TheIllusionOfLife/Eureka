/**
 * UrlInput Component
 *
 * Allows users to add multiple URLs for multi-modal context input.
 * Features:
 * - URL validation
 * - Tag-based display
 * - Add/remove functionality
 * - Maximum URL limit
 * - Duplicate detection
 */

import React, { useState } from 'react';
import { validateUrl, MULTIMODAL_CONSTANTS } from '../utils/multimodalValidation';
import { showError } from '../utils/toast';

interface UrlInputProps {
  urls: string[];
  onChange: (urls: string[]) => void;
  label?: string;
  helpText?: string;
  maxUrls?: number;
  disabled?: boolean;
}

const UrlInput: React.FC<UrlInputProps> = ({
  urls,
  onChange,
  label,
  helpText,
  maxUrls = MULTIMODAL_CONSTANTS.MAX_URLS,
  disabled = false
}) => {
  const [inputValue, setInputValue] = useState('');

  /**
   * Truncate URL for display (keep protocol + domain + short path)
   */
  const truncateUrl = (url: string, maxLength: number = 50): string => {
    if (url.length <= maxLength) return url;

    try {
      const urlObj = new URL(url);
      const domain = urlObj.hostname;
      const path = urlObj.pathname + urlObj.search;

      if (path.length > 15) {
        return `${urlObj.protocol}//${domain}${path.substring(0, 12)}...`;
      }

      return `${urlObj.protocol}//${domain}${path}`;
    } catch {
      // Fallback for invalid URLs
      return url.substring(0, maxLength - 3) + '...';
    }
  };

  /**
   * Add URL to list
   */
  const handleAddUrl = () => {
    const trimmedUrl = inputValue.trim();

    // Check if empty
    if (!trimmedUrl) {
      showError('URL cannot be empty');
      return;
    }

    // Check maximum limit
    if (urls.length >= maxUrls) {
      showError(`Maximum ${maxUrls} URLs allowed`);
      return;
    }

    // Check for duplicates
    if (urls.includes(trimmedUrl)) {
      showError('This URL has already been added');
      return;
    }

    // Validate URL
    try {
      validateUrl(trimmedUrl);
    } catch (error) {
      if (error instanceof Error) {
        showError(error.message);
      } else {
        showError('Invalid URL format');
      }
      return;
    }

    // Add URL and clear input
    onChange([...urls, trimmedUrl]);
    setInputValue('');
  };

  /**
   * Remove URL from list
   */
  const handleRemoveUrl = (urlToRemove: string) => {
    onChange(urls.filter(url => url !== urlToRemove));
  };

  /**
   * Handle Enter key press
   */
  const handleKeyPress = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      handleAddUrl();
    }
  };

  return (
    <div className="space-y-3">
      {/* Label */}
      {label && (
        <label className="block text-sm font-medium text-gray-700">
          {label}
          {urls.length > 0 && (
            <span className="ml-2 text-xs text-gray-500">
              ({urls.length} / {maxUrls})
            </span>
          )}
        </label>
      )}

      {/* Input and Add Button */}
      <div className="flex gap-2">
        <input
          type="url"
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder="https://example.com"
          disabled={disabled}
          className="flex-1 border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
        />
        <button
          type="button"
          onClick={handleAddUrl}
          disabled={disabled || urls.length >= maxUrls}
          className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
          aria-label="Add URL"
        >
          Add URL
        </button>
      </div>

      {/* Help Text */}
      {helpText && (
        <p className="text-xs text-gray-500">
          {helpText}
        </p>
      )}

      {/* URL Tags */}
      {urls.length > 0 && (
        <div className="flex flex-wrap gap-2" role="list">
          {urls.map((url, index) => (
            <div
              key={index}
              title={url}
              className="inline-flex items-center gap-1 px-3 py-1 text-sm bg-blue-100 text-blue-800 rounded-full"
              role="listitem"
            >
              <span className="max-w-xs truncate">
                {truncateUrl(url)}
              </span>
              <button
                type="button"
                onClick={() => handleRemoveUrl(url)}
                disabled={disabled}
                className="ml-1 text-blue-600 hover:text-blue-800 focus:outline-none disabled:opacity-50 disabled:cursor-not-allowed"
                aria-label="Remove URL"
              >
                ×
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default UrlInput;
