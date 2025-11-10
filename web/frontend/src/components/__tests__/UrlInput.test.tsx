/**
 * Tests for UrlInput component
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import UrlInput from '../UrlInput';

// Mock toast utilities
jest.mock('../../utils/toast', () => ({
  showError: jest.fn(),
  showSuccess: jest.fn()
}));

describe('UrlInput Component', () => {
  const mockOnChange = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Rendering', () => {
    it('should render input field and add button', () => {
      render(<UrlInput urls={[]} onChange={mockOnChange} />);

      expect(screen.getByPlaceholderText(/https:\/\/example.com/i)).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /add url/i })).toBeInTheDocument();
    });

    it('should render label when provided', () => {
      render(<UrlInput urls={[]} onChange={mockOnChange} label="Test Label" />);

      expect(screen.getByText('Test Label')).toBeInTheDocument();
    });

    it('should render help text when provided', () => {
      render(<UrlInput urls={[]} onChange={mockOnChange} helpText="Test help text" />);

      expect(screen.getByText('Test help text')).toBeInTheDocument();
    });

    it('should display existing URLs as tags', () => {
      const urls = ['https://example.com', 'https://test.com'];
      render(<UrlInput urls={urls} onChange={mockOnChange} />);

      expect(screen.getByText(/example.com/i)).toBeInTheDocument();
      expect(screen.getByText(/test.com/i)).toBeInTheDocument();
    });
  });

  describe('Adding URLs', () => {
    it('should add URL when clicking add button', async () => {
      render(<UrlInput urls={[]} onChange={mockOnChange} />);

      const input = screen.getByPlaceholderText(/https:\/\/example.com/i);
      const addButton = screen.getByRole('button', { name: /add url/i });

      fireEvent.change(input, { target: { value: 'https://example.com' } });
      fireEvent.click(addButton);

      await waitFor(() => {
        expect(mockOnChange).toHaveBeenCalledWith(['https://example.com']);
      });
    });

    it('should add URL when pressing Enter', async () => {
      render(<UrlInput urls={[]} onChange={mockOnChange} />);

      const input = screen.getByPlaceholderText(/https:\/\/example.com/i);

      fireEvent.change(input, { target: { value: 'https://example.com' } });
      fireEvent.keyPress(input, { key: 'Enter', code: 'Enter', charCode: 13 });

      await waitFor(() => {
        expect(mockOnChange).toHaveBeenCalledWith(['https://example.com']);
      });
    });

    it('should clear input after adding URL', async () => {
      render(<UrlInput urls={[]} onChange={mockOnChange} />);

      const input = screen.getByPlaceholderText(/https:\/\/example.com/i) as HTMLInputElement;
      const addButton = screen.getByRole('button', { name: /add url/i });

      fireEvent.change(input, { target: { value: 'https://example.com' } });
      fireEvent.click(addButton);

      await waitFor(() => {
        expect(input.value).toBe('');
      });
    });

    it('should trim whitespace from URLs', async () => {
      render(<UrlInput urls={[]} onChange={mockOnChange} />);

      const input = screen.getByPlaceholderText(/https:\/\/example.com/i);
      const addButton = screen.getByRole('button', { name: /add url/i });

      fireEvent.change(input, { target: { value: '  https://example.com  ' } });
      fireEvent.click(addButton);

      await waitFor(() => {
        expect(mockOnChange).toHaveBeenCalledWith(['https://example.com']);
      });
    });
  });

  describe('Validation', () => {
    it('should not add empty URL', async () => {
      const { showError } = require('../../utils/toast');
      render(<UrlInput urls={[]} onChange={mockOnChange} />);

      const addButton = screen.getByRole('button', { name: /add url/i });
      fireEvent.click(addButton);

      await waitFor(() => {
        expect(mockOnChange).not.toHaveBeenCalled();
        expect(showError).toHaveBeenCalledWith(expect.stringContaining('empty'));
      });
    });

    it('should not add URL without http/https protocol', async () => {
      const { showError } = require('../../utils/toast');
      render(<UrlInput urls={[]} onChange={mockOnChange} />);

      const input = screen.getByPlaceholderText(/https:\/\/example.com/i);
      const addButton = screen.getByRole('button', { name: /add url/i });

      fireEvent.change(input, { target: { value: 'example.com' } });
      fireEvent.click(addButton);

      await waitFor(() => {
        expect(mockOnChange).not.toHaveBeenCalled();
        expect(showError).toHaveBeenCalledWith(expect.stringContaining('http'));
      });
    });

    it('should not add invalid URL format', async () => {
      const { showError } = require('../../utils/toast');
      render(<UrlInput urls={[]} onChange=  {mockOnChange} />);

      const input = screen.getByPlaceholderText(/https:\/\/example.com/i);
      const addButton = screen.getByRole('button', { name: /add url/i });

      fireEvent.change(input, { target: { value: 'not a url' } });
      fireEvent.click(addButton);

      await waitFor(() => {
        expect(mockOnChange).not.toHaveBeenCalled();
        expect(showError).toHaveBeenCalled();
      });
    });

    it('should not add duplicate URL', () => {
      const { showError } = require('../../utils/toast');
      const existingUrls = ['https://example.com'];
      render(<UrlInput urls={existingUrls} onChange={mockOnChange} />);

      const input = screen.getByPlaceholderText(/https:\/\/example.com/i);
      const addButton = screen.getByRole('button', { name: /add url/i });

      fireEvent.change(input, { target: { value: 'https://example.com' } });
      fireEvent.click(addButton);

      expect(mockOnChange).not.toHaveBeenCalled();
      expect(showError).toHaveBeenCalledWith(expect.stringContaining('already been added'));
    });

    it('should disable add button when maximum URL count reached', () => {
      const existingUrls = [
        'https://example1.com',
        'https://example2.com',
        'https://example3.com',
        'https://example4.com',
        'https://example5.com'
      ];
      render(<UrlInput urls={existingUrls} onChange={mockOnChange} maxUrls={5} />);

      const addButton = screen.getByRole('button', { name: /add url/i });

      expect(addButton).toBeDisabled();
    });

    it('should show URL count indicator when label is provided', () => {
      const urls = ['https://example1.com', 'https://example2.com'];
      render(<UrlInput urls={urls} onChange={mockOnChange} maxUrls={5} label="Test Label" />);

      expect(screen.getByText(/2.*\/.*5/)).toBeInTheDocument();
    });
  });

  describe('Removing URLs', () => {
    it('should remove URL when clicking remove button', async () => {
      const urls = ['https://example.com', 'https://test.com'];
      render(<UrlInput urls={urls} onChange={mockOnChange} />);

      const removeButtons = screen.getAllByRole('button', { name: /remove/i });
      fireEvent.click(removeButtons[0]);

      await waitFor(() => {
        expect(mockOnChange).toHaveBeenCalledWith(['https://test.com']);
      });
    });

    it('should remove correct URL when multiple exist', async () => {
      const urls = ['https://example1.com', 'https://example2.com', 'https://example3.com'];
      render(<UrlInput urls={urls} onChange={mockOnChange} />);

      const removeButtons = screen.getAllByRole('button', { name: /remove/i });
      fireEvent.click(removeButtons[1]); // Remove middle one

      await waitFor(() => {
        expect(mockOnChange).toHaveBeenCalledWith(['https://example1.com', 'https://example3.com']);
      });
    });
  });

  describe('URL Display', () => {
    it('should truncate long URLs in tags', () => {
      const longUrl = 'https://example.com/very/long/path/that/should/be/truncated/for/display';
      render(<UrlInput urls={[longUrl]} onChange={mockOnChange} />);

      const tag = screen.getByText(/example\.com/);
      expect(tag.textContent).not.toBe(longUrl);
      expect(tag.textContent!.length).toBeLessThan(longUrl.length);
    });

    it('should show full URL on hover/title attribute', () => {
      const url = 'https://example.com/very/long/path';
      render(<UrlInput urls={[url]} onChange={mockOnChange} />);

      const tag = screen.getByText(/example\.com/);
      expect(tag.closest('[title]')).toHaveAttribute('title', url);
    });
  });

  describe('Disabled State', () => {
    it('should disable input and button when disabled prop is true', () => {
      render(<UrlInput urls={[]} onChange={mockOnChange} disabled={true} />);

      const input = screen.getByPlaceholderText(/https:\/\/example.com/i);
      const addButton = screen.getByRole('button', { name: /add url/i });

      expect(input).toBeDisabled();
      expect(addButton).toBeDisabled();
    });

    it('should disable remove buttons when disabled prop is true', () => {
      const urls = ['https://example.com'];
      render(<UrlInput urls={urls} onChange={mockOnChange} disabled={true} />);

      const removeButton = screen.getByRole('button', { name: /remove/i });
      expect(removeButton).toBeDisabled();
    });
  });
});
