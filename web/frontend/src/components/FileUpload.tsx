/**
 * FileUpload Component
 *
 * File upload component with drag-and-drop support for multi-modal inputs.
 * Features:
 * - Drag and drop file upload
 * - Click to browse files
 * - File validation (type, size)
 * - Visual feedback for drag state
 * - File list with remove functionality
 * - File size display
 */

import React, { useState, useRef } from 'react';
import { validateFile, formatFileSize, getFileExtension } from '../utils/multimodalValidation';
import { showError } from '../utils/toast';

interface FileUploadProps {
  files: File[];
  onChange: (files: File[]) => void;
  label?: string;
  helpText?: string;
  disabled?: boolean;
}

const FileUpload: React.FC<FileUploadProps> = ({
  files,
  onChange,
  label,
  helpText,
  disabled = false
}) => {
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  /**
   * Validate and add files to the list
   */
  const handleFiles = (newFiles: FileList | null) => {
    if (!newFiles || newFiles.length === 0 || disabled) return;

    const validFiles: File[] = [];
    const errors: string[] = [];

    // Check for duplicates and validate each file
    Array.from(newFiles).forEach(file => {
      // Check for duplicates
      const isDuplicate = files.some(existing => existing.name === file.name);
      if (isDuplicate) {
        errors.push(`${file.name} has already been added`);
        return;
      }

      // Validate file
      try {
        validateFile(file);
        validFiles.push(file);
      } catch (error) {
        if (error instanceof Error) {
          errors.push(`${file.name}: ${error.message}`);
        } else {
          errors.push(`${file.name}: Invalid file`);
        }
      }
    });

    // Show errors if any
    if (errors.length > 0) {
      showError(errors.join('\n'));
    }

    // Add valid files
    if (validFiles.length > 0) {
      onChange([...files, ...validFiles]);
    }
  };

  /**
   * Handle file input change
   */
  const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    handleFiles(e.target.files);
    // Reset input so the same file can be selected again if removed
    e.target.value = '';
  };

  /**
   * Handle drag over event
   */
  const handleDragOver = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();

    if (disabled) return;

    // Only show drag state if files are being dragged
    if (e.dataTransfer.types.includes('Files')) {
      setIsDragging(true);
    }
  };

  /**
   * Handle drag leave event
   */
  const handleDragLeave = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  };

  /**
   * Handle drop event
   */
  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);

    if (disabled) return;

    handleFiles(e.dataTransfer.files);
  };

  /**
   * Handle remove file
   */
  const handleRemoveFile = (fileToRemove: File) => {
    onChange(files.filter(file => file !== fileToRemove));
  };

  /**
   * Handle click on drop zone
   */
  const handleDropZoneClick = () => {
    if (!disabled && fileInputRef.current) {
      fileInputRef.current.click();
    }
  };

  /**
   * Handle keyboard interactions for drop zone
   */
  const handleKeyDown = (e: React.KeyboardEvent<HTMLDivElement>) => {
    if (disabled) return;
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      fileInputRef.current?.click();
    }
  };

  /**
   * Get file icon based on extension
   */
  const getFileIcon = (file: File): string => {
    const ext = getFileExtension(file.name);

    if (['png', 'jpg', 'jpeg', 'webp', 'gif', 'bmp'].includes(ext)) {
      return '🖼️';
    } else if (ext === 'pdf') {
      return '📄';
    } else {
      return '📝';
    }
  };

  return (
    <div className="space-y-3">
      {/* Label */}
      {label && (
        <label className="block text-sm font-medium text-gray-700">
          {label}
          {files.length > 0 && (
            <span className="ml-2 text-xs text-gray-500">
              ({files.length} {files.length === 1 ? 'file' : 'files'})
            </span>
          )}
        </label>
      )}

      {/* Hidden File Input */}
      <input
        ref={fileInputRef}
        data-testid="file-input"
        type="file"
        multiple
        accept=".png,.jpg,.jpeg,.webp,.gif,.bmp,.pdf,.txt,.md,.doc,.docx"
        onChange={handleFileInputChange}
        disabled={disabled}
        className="hidden"
      />

      {/* Drop Zone */}
      <div
        role="button"
        tabIndex={disabled ? -1 : 0}
        aria-disabled={disabled}
        aria-labelledby="drop-zone-label drop-zone-description drop-zone-restrictions"
        onKeyDown={handleKeyDown}
        onClick={handleDropZoneClick}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        className={`
          border-2 border-dashed rounded-lg p-6 text-center cursor-pointer
          transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2
          ${isDragging
            ? 'border-blue-500 bg-blue-50'
            : 'border-gray-300 hover:border-blue-400'
          }
          ${disabled
            ? 'opacity-50 cursor-not-allowed bg-gray-100'
            : 'bg-white'
          }
        `}
      >
        <div className="space-y-2">
          <div className="text-4xl" aria-hidden="true">{isDragging ? '📥' : '📎'}</div>
          <p id="drop-zone-description" className="text-sm text-gray-600">
            Click to upload or drag files here
          </p>
          <p id="drop-zone-restrictions" className="text-xs text-gray-500">
            <span className="font-medium">Images:</span> PNG, JPG, WebP, GIF (max 8MB)
            <br />
            <span className="font-medium">Documents:</span> PDF (max 40MB), TXT/MD/DOC/DOCX (max 20MB)
          </p>
        </div>
      </div>

      {/* Help Text */}
      {helpText && (
        <p id="drop-zone-label" className="text-xs text-gray-500">
          {helpText}
        </p>
      )}

      {/* File List */}
      {files.length > 0 && (
        <div className="space-y-2" role="list">
          {files.map((file, index) => (
            <div
              key={`${file.name}-${index}`}
              className="flex items-center justify-between bg-gray-50 p-3 rounded-lg border border-gray-200"
              role="listitem"
            >
              <div className="flex items-center gap-2 flex-1 min-w-0">
                <span className="text-xl flex-shrink-0" aria-hidden="true">
                  {getFileIcon(file)}
                </span>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-gray-900 truncate">
                    {file.name}
                  </p>
                  <p className="text-xs text-gray-500">
                    {formatFileSize(file.size)}
                  </p>
                </div>
              </div>
              <button
                type="button"
                onClick={() => handleRemoveFile(file)}
                disabled={disabled}
                className="ml-2 px-2 py-1 text-sm text-red-600 hover:text-red-800 hover:bg-red-50 rounded focus:outline-none focus:ring-2 focus:ring-red-500 disabled:opacity-50 disabled:cursor-not-allowed"
                aria-label={`Remove ${file.name}`}
              >
                Remove
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default FileUpload;
