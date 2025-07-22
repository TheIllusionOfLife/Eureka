/**
 * Centralized error handling utility for the MadSpark application
 * Provides consistent error processing, logging, and user-friendly error messages
 */

import { showError } from './toast';
import { ErrorDetails, ApiError } from '../types';

class ErrorHandler {
  private errorLog: ErrorDetails[] = [];
  private maxLogSize = 100;

  /**
   * Process and categorize an error, returning user-friendly details
   */
  processError(error: any, context?: string): ErrorDetails {
    const timestamp = new Date().toISOString();
    const apiError = error as ApiError;
    
    let errorDetails: ErrorDetails = {
      message: 'An unexpected error occurred',
      type: 'unknown',
      timestamp,
      context
    };

    // Network/Connection errors
    if (error.code === 'NETWORK_ERROR') {
      errorDetails = {
        message: 'Network connection error. Please check your internet connection and try again.',
        type: 'network',
        code: 0,
        timestamp,
        context
      };
    }
    // Timeout errors (ECONNABORTED typically indicates timeout)
    else if (error.code === 'ECONNABORTED' || error.message?.includes('timeout')) {
      errorDetails = {
        message: 'Request timed out. The operation is taking longer than expected. Please try again or use simpler parameters.',
        type: 'timeout',
        code: 408,
        timestamp,
        context
      };
    }
    // Rate limiting
    else if (apiError.response?.status === 429) {
      errorDetails = {
        message: 'Too many requests. Please wait a moment before trying again.',
        type: 'rate_limit',
        code: 429,
        timestamp,
        context
      };
    }
    // Authentication errors
    else if (apiError.response?.status === 401) {
      errorDetails = {
        message: 'Authentication required. Please refresh the page and try again.',
        type: 'auth',
        code: 401,
        timestamp,
        context
      };
    }
    // Validation errors
    else if (apiError.response?.status === 422) {
      const detail = apiError.response.data?.detail;
      errorDetails = {
        message: this.extractValidationMessage(detail) || 'Invalid input data. Please check your inputs and try again.',
        type: 'validation',
        code: 422,
        details: detail,
        timestamp,
        context
      };
    }
    // Server errors
    else if (apiError.response?.status && apiError.response.status >= 500) {
      const detail = apiError.response.data?.detail || apiError.response.data?.message;
      errorDetails = {
        message: `Server error (${apiError.response.status}): ${detail || 'Internal server error. Please try again later.'}`,
        type: 'server',
        code: apiError.response.status,
        details: detail,
        timestamp,
        context
      };
    }
    // API response errors with details
    else if (apiError.response?.data?.detail) {
      const detail = apiError.response.data.detail;
      errorDetails = {
        message: typeof detail === 'string' ? 
          detail : 
          Array.isArray(detail) ? 
            detail.map(d => d.msg).join(', ') : 
            'Unknown error',
        type: 'server',
        code: apiError.response.status,
        details: detail,
        timestamp,
        context
      };
    }
    // Generic error with message
    else if (error.message) {
      errorDetails = {
        message: error.message,
        type: 'unknown',
        timestamp,
        context
      };
    }

    // Log the error
    this.logError(errorDetails, error);
    
    return errorDetails;
  }

  /**
   * Extract meaningful message from validation errors
   */
  private extractValidationMessage(detail: any): string | null {
    if (!detail) return null;
    
    if (typeof detail === 'string') {
      return detail;
    }
    
    if (Array.isArray(detail)) {
      // Handle FastAPI validation errors
      const firstError = detail[0];
      if (firstError?.msg) {
        const field = firstError.loc?.join('.') || 'field';
        return `${field}: ${firstError.msg}`;
      }
    }
    
    if (typeof detail === 'object' && !Array.isArray(detail) && 'error' in detail) {
      return (detail as any).error;
    }
    
    return null;
  }

  /**
   * Log error details for debugging
   */
  private logError(errorDetails: ErrorDetails, originalError: any) {
    // Add to in-memory log
    this.errorLog.push(errorDetails);
    
    // Keep log size manageable
    if (this.errorLog.length > this.maxLogSize) {
      this.errorLog.shift();
    }
    
    // Console logging with context
    const logData = {
      message: errorDetails.message,
      type: errorDetails.type,
      code: errorDetails.code,
      context: errorDetails.context,
      timestamp: errorDetails.timestamp,
      original: originalError
    };
    
    if (errorDetails.type === 'server' || errorDetails.type === 'network') {
      console.error('🔴 Error:', logData);
    } else if (errorDetails.type === 'validation') {
      console.warn('🟡 Validation Error:', logData);
    } else {
      // Log structured error data for debugging (removed console.log for production)
    }
  }

  /**
   * Handle error and optionally show toast notification
   */
  handleError(error: any, context?: string, showToast = true): ErrorDetails {
    const errorDetails = this.processError(error, context);
    
    if (showToast) {
      showError(errorDetails.message);
    }
    
    return errorDetails;
  }

  /**
   * Get error log for debugging
   */
  getErrorLog(): ErrorDetails[] {
    return [...this.errorLog];
  }

  /**
   * Clear error log
   */
  clearErrorLog() {
    this.errorLog = [];
  }

  /**
   * Get error statistics
   */
  getErrorStats() {
    const stats = {
      total: this.errorLog.length,
      byType: {} as Record<string, number>,
      recent: this.errorLog.slice(-10)
    };
    
    this.errorLog.forEach(error => {
      stats.byType[error.type] = (stats.byType[error.type] || 0) + 1;
    });
    
    return stats;
  }
}

// Export singleton instance
export const errorHandler = new ErrorHandler();

// Helper functions for common error scenarios
export const handleApiError = (error: any, context?: string) => {
  return errorHandler.handleError(error, context);
};

export const handleBookmarkError = (error: any, action: string) => {
  return errorHandler.handleError(error, `Bookmark ${action}`);
};

export const handleIdeaGenerationError = (error: any) => {
  return errorHandler.handleError(error, 'Idea Generation');
};

export const handleWebSocketError = (error: any) => {
  return errorHandler.handleError(error, 'WebSocket', false); // Don't show toast for WebSocket errors
};