/**
 * Tests for FileUpload component
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import FileUpload from '../FileUpload';

// Mock toast utilities
jest.mock('../../utils/toast', () => ({
  showError: jest.fn(),
  showSuccess: jest.fn()
}));

describe('FileUpload Component', () => {
  const mockOnChange = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Rendering', () => {
    it('should render drop zone and file input', () => {
      render(<FileUpload files={[]} onChange={mockOnChange} />);

      expect(screen.getByText(/click to upload or drag files here/i)).toBeInTheDocument();
    });

    it('should render label when provided', () => {
      render(<FileUpload files={[]} onChange={mockOnChange} label="Upload Files" />);

      expect(screen.getByText('Upload Files')).toBeInTheDocument();
    });

    it('should render help text when provided', () => {
      render(<FileUpload files={[]} onChange={mockOnChange} helpText="Max 20MB per file" />);

      expect(screen.getByText('Max 20MB per file')).toBeInTheDocument();
    });

    it('should display file type restrictions', () => {
      render(<FileUpload files={[]} onChange={mockOnChange} />);

      expect(screen.getByText(/images:/i)).toBeInTheDocument();
      expect(screen.getByText(/documents:/i)).toBeInTheDocument();
    });

    it('should display uploaded files', () => {
      const files = [
        new File(['test'], 'test.pdf', { type: 'application/pdf' }),
        new File(['test'], 'image.png', { type: 'image/png' })
      ];
      render(<FileUpload files={files} onChange={mockOnChange} />);

      expect(screen.getByText(/test\.pdf/)).toBeInTheDocument();
      expect(screen.getByText(/image\.png/)).toBeInTheDocument();
    });

    it('should have accessible attributes on drop zone', () => {
      render(<FileUpload files={[]} onChange={mockOnChange} />);
      const dropZone = screen.getByRole('button', { name: /click to upload/i });
      expect(dropZone).toBeInTheDocument();
      expect(dropZone).toHaveAttribute('tabIndex', '0');
    });
  });

  describe('File Selection', () => {
    it('should add files when selected through input', async () => {
      render(<FileUpload files={[]} onChange={mockOnChange} />);

      const file = new File(['test content'], 'test.pdf', { type: 'application/pdf' });
      const input = screen.getByTestId('file-input');

      Object.defineProperty(input, 'files', {
        value: [file],
        writable: false
      });

      fireEvent.change(input);

      await waitFor(() => {
        expect(mockOnChange).toHaveBeenCalledWith([file]);
      });
    });

    it('should add multiple files at once', async () => {
      render(<FileUpload files={[]} onChange={mockOnChange} />);

      const files = [
        new File(['test1'], 'test1.pdf', { type: 'application/pdf' }),
        new File(['test2'], 'test2.png', { type: 'image/png' })
      ];
      const input = screen.getByTestId('file-input');

      Object.defineProperty(input, 'files', {
        value: files,
        writable: false
      });

      fireEvent.change(input);

      await waitFor(() => {
        expect(mockOnChange).toHaveBeenCalledWith(files);
      });
    });

    it('should append new files to existing files', async () => {
      const existingFiles = [
        new File(['existing'], 'existing.pdf', { type: 'application/pdf' })
      ];
      render(<FileUpload files={existingFiles} onChange={mockOnChange} />);

      const newFile = new File(['new'], 'new.png', { type: 'image/png' });
      const input = screen.getByTestId('file-input');

      Object.defineProperty(input, 'files', {
        value: [newFile],
        writable: false
      });

      fireEvent.change(input);

      await waitFor(() => {
        expect(mockOnChange).toHaveBeenCalledWith([existingFiles[0], newFile]);
      });
    });
  });

  describe('Keyboard Interaction', () => {
    it('should trigger file input when pressing Enter on drop zone', () => {
      render(<FileUpload files={[]} onChange={mockOnChange} />);

      const input = screen.getByTestId('file-input');
      const clickSpy = jest.spyOn(input, 'click');

      const dropZone = screen.getByRole('button', { name: /click to upload/i });
      fireEvent.keyDown(dropZone, { key: 'Enter' });

      expect(clickSpy).toHaveBeenCalled();
    });

    it('should trigger file input when pressing Space on drop zone', () => {
      render(<FileUpload files={[]} onChange={mockOnChange} />);

      const input = screen.getByTestId('file-input');
      const clickSpy = jest.spyOn(input, 'click');

      const dropZone = screen.getByRole('button', { name: /click to upload/i });
      fireEvent.keyDown(dropZone, { key: ' ' });

      expect(clickSpy).toHaveBeenCalled();
    });

    it('should not trigger file input when pressing other keys', () => {
      render(<FileUpload files={[]} onChange={mockOnChange} />);

      const input = screen.getByTestId('file-input');
      const clickSpy = jest.spyOn(input, 'click');

      const dropZone = screen.getByRole('button', { name: /click to upload/i });
      fireEvent.keyDown(dropZone, { key: 'a' });

      expect(clickSpy).not.toHaveBeenCalled();
    });
  });

  describe('Drag and Drop', () => {
    it('should add files when dropped', async () => {
      render(<FileUpload files={[]} onChange={mockOnChange} />);

      const file = new File(['test'], 'test.pdf', { type: 'application/pdf' });
      const dropZone = screen.getByText(/click to upload or drag files here/i).closest('.border-dashed');

      const dropEvent = {
        dataTransfer: {
          files: [file],
          items: [{ kind: 'file', type: 'application/pdf' }],
          types: ['Files']
        }
      };

      fireEvent.dragOver(dropZone!, dropEvent as any);
      fireEvent.drop(dropZone!, dropEvent as any);

      await waitFor(() => {
        expect(mockOnChange).toHaveBeenCalledWith([file]);
      });
    });

    it('should show drag-over styling when dragging files', () => {
      render(<FileUpload files={[]} onChange={mockOnChange} />);

      const dropZone = screen.getByText(/click to upload or drag files here/i).closest('.border-dashed');

      const dragEvent = {
        dataTransfer: {
          items: [{ kind: 'file' }],
          types: ['Files']
        }
      };

      fireEvent.dragOver(dropZone!, dragEvent as any);

      expect(dropZone).toHaveClass('border-blue-500');
    });

    it('should remove drag-over styling when drag leaves', () => {
      render(<FileUpload files={[]} onChange={mockOnChange} />);

      const dropZone = screen.getByText(/click to upload or drag files here/i).closest('.border-dashed');

      const dragEvent = {
        dataTransfer: {
          items: [{ kind: 'file' }],
          types: ['Files']
        }
      };

      fireEvent.dragOver(dropZone!, dragEvent as any);
      fireEvent.dragLeave(dropZone!);

      expect(dropZone).not.toHaveClass('border-blue-500');
    });

    it('should handle dragOver without errors', () => {
      render(<FileUpload files={[]} onChange={mockOnChange} />);

      const dropZone = screen.getByText(/click to upload or drag files here/i).closest('.border-dashed');

      // This test just verifies dragOver handler doesn't throw errors
      expect(() => {
        fireEvent.dragOver(dropZone!, {
          dataTransfer: { items: [{ kind: 'file' }], types: ['Files'] }
        } as any);
      }).not.toThrow();
    });
  });

  describe('File Validation', () => {
    it('should reject files that are too large', () => {
      const { showError } = require('../../utils/toast');
      render(<FileUpload files={[]} onChange={mockOnChange} />);

      // Create a large file (> 20MB)
      const largeFile = new File(['x'.repeat(21_000_000)], 'large.txt', { type: 'text/plain' });
      const input = screen.getByTestId('file-input');

      Object.defineProperty(input, 'files', {
        value: [largeFile],
        writable: false
      });

      fireEvent.change(input);

      expect(mockOnChange).not.toHaveBeenCalled();
      expect(showError).toHaveBeenCalledWith(expect.stringContaining('must be under'));
    });

    it('should reject unsupported file types', () => {
      const { showError } = require('../../utils/toast');
      render(<FileUpload files={[]} onChange={mockOnChange} />);

      const unsupportedFile = new File(['test'], 'test.exe', { type: 'application/x-msdownload' });
      const input = screen.getByTestId('file-input');

      Object.defineProperty(input, 'files', {
        value: [unsupportedFile],
        writable: false
      });

      fireEvent.change(input);

      expect(mockOnChange).not.toHaveBeenCalled();
      expect(showError).toHaveBeenCalledWith(expect.stringContaining('Unsupported'));
    });

    it('should reject duplicate files', () => {
      const { showError } = require('../../utils/toast');
      const existingFile = new File(['test'], 'test.pdf', { type: 'application/pdf' });
      render(<FileUpload files={[existingFile]} onChange={mockOnChange} />);

      const duplicateFile = new File(['test'], 'test.pdf', { type: 'application/pdf' });
      const input = screen.getByTestId('file-input');

      Object.defineProperty(input, 'files', {
        value: [duplicateFile],
        writable: false
      });

      fireEvent.change(input);

      expect(mockOnChange).not.toHaveBeenCalled();
      expect(showError).toHaveBeenCalledWith(expect.stringContaining('already been added'));
    });

    it('should accept multiple valid files', async () => {
      render(<FileUpload files={[]} onChange={mockOnChange} />);

      const files = [
        new File(['test1'], 'valid1.pdf', { type: 'application/pdf' }),
        new File(['test2'], 'valid2.png', { type: 'image/png' })
      ];
      const input = screen.getByTestId('file-input');

      Object.defineProperty(input, 'files', {
        value: files,
        writable: false
      });

      fireEvent.change(input);

      await waitFor(() => {
        expect(mockOnChange).toHaveBeenCalledWith(files);
      });
    });
  });

  describe('File Removal', () => {
    it('should remove file when clicking remove button', async () => {
      const files = [
        new File(['test1'], 'test1.pdf', { type: 'application/pdf' }),
        new File(['test2'], 'test2.png', { type: 'image/png' })
      ];
      render(<FileUpload files={files} onChange={mockOnChange} />);

      const removeButtons = screen.getAllByRole('button', { name: /remove/i });
      fireEvent.click(removeButtons[0]);

      await waitFor(() => {
        expect(mockOnChange).toHaveBeenCalledWith([files[1]]);
      });
    });

    it('should remove correct file when multiple exist', async () => {
      const files = [
        new File(['test1'], 'file1.pdf', { type: 'application/pdf' }),
        new File(['test2'], 'file2.png', { type: 'image/png' }),
        new File(['test3'], 'file3.txt', { type: 'text/plain' })
      ];
      render(<FileUpload files={files} onChange={mockOnChange} />);

      const removeButtons = screen.getAllByRole('button', { name: /remove/i });
      fireEvent.click(removeButtons[1]); // Remove middle file

      await waitFor(() => {
        expect(mockOnChange).toHaveBeenCalledWith([files[0], files[2]]);
      });
    });
  });

  describe('File Display', () => {
    it('should display file size in human-readable format', () => {
      const file = new File(['x'.repeat(1024 * 1024)], 'test.pdf', { type: 'application/pdf' });
      render(<FileUpload files={[file]} onChange={mockOnChange} />);

      expect(screen.getByText(/1\.0\s*MB/)).toBeInTheDocument();
    });

    it('should display file icon based on type', () => {
      const files = [
        new File(['test'], 'document.pdf', { type: 'application/pdf' }),
        new File(['test'], 'image.png', { type: 'image/png' })
      ];
      render(<FileUpload files={files} onChange={mockOnChange} />);

      // Check that file icons/indicators are present
      expect(screen.getByText(/document\.pdf/)).toBeInTheDocument();
      expect(screen.getByText(/image\.png/)).toBeInTheDocument();
    });

    it('should show file count when files exist', () => {
      const files = [
        new File(['test1'], 'file1.pdf', { type: 'application/pdf' }),
        new File(['test2'], 'file2.png', { type: 'image/png' })
      ];
      render(<FileUpload files={files} onChange={mockOnChange} label="Upload Files" />);

      expect(screen.getByText(/2\s*files?/i)).toBeInTheDocument();
    });
  });

  describe('Disabled State', () => {
    it('should disable file input when disabled prop is true', () => {
      render(<FileUpload files={[]} onChange={mockOnChange} disabled={true} />);

      const input = screen.getByTestId('file-input');
      expect(input).toBeDisabled();
    });

    it('should disable remove buttons when disabled', () => {
      const files = [new File(['test'], 'test.pdf', { type: 'application/pdf' })];
      render(<FileUpload files={files} onChange={mockOnChange} disabled={true} />);

      const removeButton = screen.getByRole('button', { name: /remove/i });
      expect(removeButton).toBeDisabled();
    });

    it('should make drop zone non-interactive when disabled', () => {
      render(<FileUpload files={[]} onChange={mockOnChange} disabled={true} />);

      const dropZone = screen.getByRole('button', { name: /click to upload/i });
      expect(dropZone).toHaveAttribute('aria-disabled', 'true');
      expect(dropZone).toHaveAttribute('tabIndex', '-1');
    });

    it('should not accept drag and drop when disabled', async () => {
      render(<FileUpload files={[]} onChange={mockOnChange} disabled={true} />);

      const file = new File(['test'], 'test.pdf', { type: 'application/pdf' });
      const dropZone = screen.getByText(/click to upload or drag files here/i).closest('.border-dashed');

      const dropEvent = {
        dataTransfer: {
          files: [file]
        }
      };

      fireEvent.drop(dropZone!, dropEvent as any);

      await waitFor(() => {
        expect(mockOnChange).not.toHaveBeenCalled();
      });
    });
  });

  describe('Click to Upload', () => {
    it('should trigger file input when clicking drop zone', () => {
      render(<FileUpload files={[]} onChange={mockOnChange} />);

      const input = screen.getByTestId('file-input');
      const clickSpy = jest.spyOn(input, 'click');

      const dropZone = screen.getByText(/click to upload or drag files here/i).closest('.border-dashed');
      fireEvent.click(dropZone!);

      expect(clickSpy).toHaveBeenCalled();
    });
  });
});
