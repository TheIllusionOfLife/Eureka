/**
 * Comprehensive Tests for Frontend Utilities
 * 
 * This test suite covers all frontend utility modules including:
 * - Error handling and categorization
 * - Toast notification system  
 * - Logging and structured logging
 * - Idea text cleaning and optimization
 */

// Mock react-toastify before imports
jest.mock('react-toastify', () => ({
  toast: {
    success: jest.fn(),
    error: jest.fn(),
    info: jest.fn(),
    warning: jest.fn(),
  },
  ToastOptions: {}
}));

// Mock constants module
jest.mock('../../constants', () => ({
  CLEANER_META_HEADERS: [
    'ENHANCED CONCEPT:', 'ORIGINAL THEME:', 'REVISED CORE PREMISE:',
    'ORIGINAL IDEA:', 'IMPROVED VERSION:', 'ENHANCEMENT SUMMARY:'
  ],
  CLEANER_META_PHRASES: [
    'Addresses Evaluation Criteria', 'Enhancing Impact Through',
    'Preserving & Amplifying Strengths', 'Addressing Concerns'
  ],
  CLEANER_FRAMEWORK_CLEANUP_PATTERN: /^[:\s]*(?:a\s+)?more\s+robust.*?system\s+/i,
  CLEANER_TITLE_EXTRACTION_PATTERN: /"([^"]+)"/,
  CLEANER_TITLE_REPLACEMENT_PATTERN: /^.*?"[^"]+".*?\n+/,
  CLEANER_TITLE_KEYWORDS: ['Framework', 'System', 'Engine'],
  CLEANER_REPLACEMENT_PATTERNS: [
    [/Our enhanced approach/g, 'This approach'],
    [/The enhanced concept/g, 'The concept'],
    [/enhanced /g, ''],
    [/improved /g, '']
  ]
}));

import { toast } from 'react-toastify';

// Import modules to test - using relative paths since this is a test file
const errorHandlerPath = '../errorHandler';
const toastPath = '../toast';
const loggerPath = '../logger';
const ideaCleanerPath = '../ideaCleaner';

// Mock console methods for testing
const originalConsole = global.console;
beforeEach(() => {
  global.console = {
    ...originalConsole,
    debug: jest.fn(),
    info: jest.fn(), 
    warn: jest.fn(),
    error: jest.fn(),
    log: jest.fn()
  };
});

afterEach(() => {
  global.console = originalConsole;
  jest.clearAllMocks();
});

describe('Error Handler Utility', () => {
  let errorHandler: any;
  let handleApiError: any;
  let handleBookmarkError: any;
  let handleIdeaGenerationError: any;
  let handleWebSocketError: any;

  beforeEach(async () => {
    // Dynamic import to ensure mocks are applied
    const module = await import(errorHandlerPath);
    errorHandler = module.errorHandler;
    handleApiError = module.handleApiError;
    handleBookmarkError = module.handleBookmarkError;
    handleIdeaGenerationError = module.handleIdeaGenerationError;
    handleWebSocketError = module.handleWebSocketError;
    
    // Clear error log before each test
    errorHandler.clearErrorLog();
  });

  describe('Error Processing and Categorization', () => {
    it('should process network errors correctly', () => {
      const networkError = { code: 'NETWORK_ERROR' };
      const result = errorHandler.processError(networkError, 'test context');

      expect(result.type).toBe('network');
      expect(result.message).toContain('Network connection error');
      expect(result.context).toBe('test context');
      expect(result.timestamp).toBeDefined();
    });

    it('should process timeout errors correctly', () => {
      const timeoutError = { code: 'ECONNABORTED' };
      const result = errorHandler.processError(timeoutError);

      expect(result.type).toBe('timeout');
      expect(result.code).toBe(408);
      expect(result.message).toContain('Request timed out');
    });

    it('should process rate limiting errors correctly', () => {
      const rateLimitError = {
        response: { status: 429, data: { detail: 'Too many requests' } }
      };
      const result = errorHandler.processError(rateLimitError);

      expect(result.type).toBe('rate_limit');
      expect(result.code).toBe(429);
      expect(result.message).toContain('Too many requests');
    });

    it('should process authentication errors correctly', () => {
      const authError = {
        response: { status: 401, data: { detail: 'Unauthorized' } }
      };
      const result = errorHandler.processError(authError);

      expect(result.type).toBe('auth');
      expect(result.code).toBe(401);
      expect(result.message).toContain('Authentication required');
    });

    it('should process validation errors correctly', () => {
      const validationError = {
        response: {
          status: 422,
          data: {
            detail: [
              { msg: 'Field is required', loc: ['field_name'] }
            ]
          }
        }
      };
      const result = errorHandler.processError(validationError);

      expect(result.type).toBe('validation');
      expect(result.code).toBe(422);
      expect(result.message).toContain('field_name: Field is required');
    });

    it('should process server errors correctly', () => {
      const serverError = {
        response: {
          status: 500,
          data: { detail: 'Internal server error' }
        }
      };
      const result = errorHandler.processError(serverError);

      expect(result.type).toBe('server');
      expect(result.code).toBe(500);
      expect(result.message).toContain('Server error (500)');
    });

    it('should handle unknown errors gracefully', () => {
      const unknownError = { message: 'Something went wrong' };
      const result = errorHandler.processError(unknownError);

      expect(result.type).toBe('unknown');
      expect(result.message).toBe('Something went wrong');
    });
  });

  describe('Error Logging and Management', () => {
    it('should log errors to in-memory store', () => {
      const error = { message: 'Test error' };
      errorHandler.processError(error);

      const logs = errorHandler.getErrorLog();
      expect(logs).toHaveLength(1);
      expect(logs[0].message).toBe('Test error');
    });

    it('should limit log size and remove old entries', () => {
      // Mock max log size to be small for testing
      const originalMaxSize = errorHandler.maxLogSize;
      errorHandler.maxLogSize = 3;

      // Add more errors than max size
      for (let i = 0; i < 5; i++) {
        errorHandler.processError({ message: `Error ${i}` });
      }

      const logs = errorHandler.getErrorLog();
      expect(logs).toHaveLength(3);
      expect(logs[0].message).toBe('Error 2'); // Oldest kept
      expect(logs[2].message).toBe('Error 4'); // Most recent

      // Restore original max size
      errorHandler.maxLogSize = originalMaxSize;
    });

    it('should provide error statistics', () => {
      errorHandler.processError({ code: 'NETWORK_ERROR' });
      errorHandler.processError({ response: { status: 422 } });
      errorHandler.processError({ response: { status: 500 } });

      const stats = errorHandler.getErrorStats();
      expect(stats.total).toBe(3);
      expect(stats.byType.network).toBe(1);
      expect(stats.byType.validation).toBe(1);
      expect(stats.byType.server).toBe(1);
      expect(stats.recent).toHaveLength(3);
    });

    it('should clear error log', () => {
      errorHandler.processError({ message: 'Test error' });
      expect(errorHandler.getErrorLog()).toHaveLength(1);

      errorHandler.clearErrorLog();
      expect(errorHandler.getErrorLog()).toHaveLength(0);
    });
  });

  describe('Error Handling with Toast Notifications', () => {
    it('should show toast notification by default', () => {
      const error = { message: 'Test error' };
      errorHandler.handleError(error);

      expect(toast.error).toHaveBeenCalledWith('Test error');
    });

    it('should not show toast when disabled', () => {
      const error = { message: 'Test error' };
      errorHandler.handleError(error, 'test context', false);

      expect(toast.error).not.toHaveBeenCalled();
    });
  });

  describe('Helper Functions', () => {
    it('should handle API errors with context', () => {
      const apiError = { response: { status: 404 } };
      const result = handleApiError(apiError, 'API test');

      expect(result.context).toBe('API test');
      expect(toast.error).toHaveBeenCalled();
    });

    it('should handle bookmark errors with action context', () => {
      const error = { message: 'Bookmark failed' };
      const result = handleBookmarkError(error, 'creation');

      expect(result.context).toBe('Bookmark creation');
      expect(result.message).toBe('Bookmark failed');
    });

    it('should handle idea generation errors', () => {
      const error = { message: 'Generation failed' };
      const result = handleIdeaGenerationError(error);

      expect(result.context).toBe('Idea Generation');
      expect(result.message).toBe('Generation failed');
    });

    it('should handle WebSocket errors without toast', () => {
      const error = { message: 'Connection lost' };
      handleWebSocketError(error);

      expect(toast.error).not.toHaveBeenCalled();
    });
  });
});

describe('Toast Notification Utility', () => {
  let showSuccess: any;
  let showError: any;
  let showInfo: any;
  let showWarning: any;
  let showToast: any;

  beforeEach(async () => {
    const module = await import(toastPath);
    showSuccess = module.showSuccess;
    showError = module.showError;
    showInfo = module.showInfo;
    showWarning = module.showWarning;
    showToast = module.showToast;
  });

  describe('Individual Toast Functions', () => {
    it('should show success toast', () => {
      showSuccess('Success message');
      
      expect(toast.success).toHaveBeenCalledWith('Success message', expect.objectContaining({
        position: 'top-right',
        autoClose: 5000,
        hideProgressBar: false
      }));
    });

    it('should show error toast', () => {
      showError('Error message');
      
      expect(toast.error).toHaveBeenCalledWith('Error message', expect.objectContaining({
        position: 'top-right',
        autoClose: 5000
      }));
    });

    it('should show info toast', () => {
      showInfo('Info message');
      
      expect(toast.info).toHaveBeenCalledWith('Info message', expect.objectContaining({
        position: 'top-right',
        autoClose: 5000
      }));
    });

    it('should show warning toast', () => {
      showWarning('Warning message');
      
      expect(toast.warning).toHaveBeenCalledWith('Warning message', expect.objectContaining({
        position: 'top-right',
        autoClose: 5000
      }));
    });
  });

  describe('Custom Options', () => {
    it('should override default options', () => {
      showSuccess('Custom message', { autoClose: 3000, position: 'bottom-left' });
      
      expect(toast.success).toHaveBeenCalledWith('Custom message', expect.objectContaining({
        autoClose: 3000,
        position: 'bottom-left',
        hideProgressBar: false // Should still have defaults
      }));
    });
  });

  describe('Generic Toast Function', () => {
    it('should show success toast when type is success', () => {
      showToast('Generic success', 'success');
      
      expect(toast.success).toHaveBeenCalledWith('Generic success', expect.any(Object));
    });

    it('should show error toast when type is error', () => {
      showToast('Generic error', 'error');
      
      expect(toast.error).toHaveBeenCalledWith('Generic error', expect.any(Object));
    });

    it('should show info toast by default', () => {
      showToast('Default message');
      
      expect(toast.info).toHaveBeenCalledWith('Default message', expect.any(Object));
    });

    it('should pass through custom options', () => {
      showToast('Custom generic', 'warning', { autoClose: 1000 });
      
      expect(toast.warning).toHaveBeenCalledWith('Custom generic', expect.objectContaining({
        autoClose: 1000
      }));
    });
  });
});

describe('Logger Utility', () => {
  let logger: any;
  let logApiCall: any;
  let logUserAction: any;
  let logError: any;
  let logInfo: any;
  let logWebSocketEvent: any;

  beforeEach(async () => {
    const module = await import(loggerPath);
    logger = module.logger;
    logApiCall = module.logApiCall;
    logUserAction = module.logUserAction;
    logError = module.logError;
    logInfo = module.logInfo;
    logWebSocketEvent = module.logWebSocketEvent;
    
    // Clear logs before each test
    logger.clearLogs();
  });

  describe('Basic Logging', () => {
    it('should log debug messages', () => {
      logger.debug('Debug message', 'TEST_CONTEXT', { key: 'value' });
      
      const logs = logger.getLogs();
      expect(logs).toHaveLength(1);
      expect(logs[0].level).toBe('debug');
      expect(logs[0].message).toBe('Debug message');
      expect(logs[0].context).toBe('TEST_CONTEXT');
      expect(logs[0].data).toEqual({ key: 'value' });
    });

    it('should log info messages', () => {
      logger.info('Info message', 'INFO_CONTEXT');
      
      const logs = logger.getLogs();
      expect(logs).toHaveLength(1);
      expect(logs[0].level).toBe('info');
      expect(logs[0].message).toBe('Info message');
    });

    it('should log warning messages', () => {
      logger.warn('Warning message', 'WARN_CONTEXT');
      
      const logs = logger.getLogs();
      expect(logs).toHaveLength(1);
      expect(logs[0].level).toBe('warn');
      expect(logs[0].message).toBe('Warning message');
    });

    it('should log error messages', () => {
      logger.error('Error message', 'ERROR_CONTEXT');
      
      const logs = logger.getLogs();
      expect(logs).toHaveLength(1);
      expect(logs[0].level).toBe('error');
      expect(logs[0].message).toBe('Error message');
    });
  });

  describe('Log Level Filtering', () => {
    it('should respect log level settings', () => {
      logger.setLogLevel('warn');
      
      logger.debug('Debug message');
      logger.info('Info message'); 
      logger.warn('Warning message');
      logger.error('Error message');
      
      const logs = logger.getLogs();
      expect(logs).toHaveLength(3); // warn, error, and setLogLevel info
      expect(logs.find((log: any) => log.message === 'Warning message')).toBeDefined();
      expect(logs.find((log: any) => log.message === 'Error message')).toBeDefined();
      expect(logs.find((log: any) => log.message === 'Debug message')).toBeUndefined();
    });
  });

  describe('Specialized Logging Methods', () => {
    it('should log API calls', () => {
      logger.apiCall('GET', '/api/test', 200, 150);
      
      const logs = logger.getLogs();
      expect(logs).toHaveLength(1);
      expect(logs[0].message).toBe('GET /api/test');
      expect(logs[0].context).toBe('API');
      expect(logs[0].data).toEqual({ status: 200, duration: 150 });
      expect(logs[0].level).toBe('debug'); // Success API calls are debug level
    });

    it('should log failed API calls as warnings', () => {
      logger.apiCall('POST', '/api/error', 400, 200);
      
      const logs = logger.getLogs();
      expect(logs).toHaveLength(1);
      expect(logs[0].level).toBe('warn');
      expect(logs[0].context).toBe('API');
    });

    it('should log user actions', () => {
      logger.userAction('button_click', { buttonId: 'submit' });
      
      const logs = logger.getLogs();
      expect(logs).toHaveLength(1);
      expect(logs[0].message).toBe('User action: button_click');
      expect(logs[0].context).toBe('USER');
      expect(logs[0].data).toEqual({ buttonId: 'submit' });
    });

    it('should log WebSocket events', () => {
      logger.websocketEvent('connection_opened', { url: 'ws://test' });
      
      const logs = logger.getLogs();
      expect(logs).toHaveLength(1);
      expect(logs[0].message).toBe('WebSocket: connection_opened');
      expect(logs[0].context).toBe('WS');
      expect(logs[0].level).toBe('debug');
    });

    it('should log bookmark actions', () => {
      logger.bookmarkAction('create', 'bookmark-123', true);
      
      const logs = logger.getLogs();
      expect(logs).toHaveLength(1);
      expect(logs[0].message).toBe('Bookmark create (bookmark-123)');
      expect(logs[0].context).toBe('BOOKMARK');
      expect(logs[0].level).toBe('info');
    });

    it('should log failed bookmark actions as warnings', () => {
      logger.bookmarkAction('delete', 'bookmark-456', false);
      
      const logs = logger.getLogs();
      expect(logs).toHaveLength(1);
      expect(logs[0].level).toBe('warn');
      expect(logs[0].context).toBe('BOOKMARK');
    });

    it('should log idea generation phases', () => {
      logger.ideaGeneration('started', { theme: 'AI' });
      
      const logs = logger.getLogs();
      expect(logs).toHaveLength(1);
      expect(logs[0].message).toBe('Idea generation: started');
      expect(logs[0].context).toBe('IDEA_GEN');
      expect(logs[0].data).toEqual({ theme: 'AI' });
    });
  });

  describe('Log Management', () => {
    it('should filter logs by level', () => {
      logger.debug('Debug message');
      logger.info('Info message');
      logger.warn('Warning message');
      logger.error('Error message');
      
      const errorLogs = logger.getLogs('error');
      expect(errorLogs).toHaveLength(1);
      expect(errorLogs[0].level).toBe('error');
    });

    it('should get recent logs', () => {
      for (let i = 0; i < 10; i++) {
        logger.info(`Message ${i}`);
      }
      
      const recentLogs = logger.getRecentLogs(3);
      expect(recentLogs).toHaveLength(3);
      expect(recentLogs[2].message).toBe('Message 9'); // Most recent
    });

    it('should provide logging statistics', () => {
      logger.debug('Debug');
      logger.info('Info', 'API');
      logger.warn('Warning', 'USER');
      logger.error('Error', 'API');
      
      const stats = logger.getStats();
      expect(stats.total).toBe(4);
      expect(stats.byLevel.debug).toBe(1);
      expect(stats.byLevel.info).toBe(1);
      expect(stats.byLevel.warn).toBe(1);
      expect(stats.byLevel.error).toBe(1);
      expect(stats.byContext.API).toBe(2);
      expect(stats.byContext.USER).toBe(1);
    });

    it('should export logs as JSON', () => {
      logger.info('Test message');
      
      const exported = logger.exportLogs();
      const parsedLogs = JSON.parse(exported);
      
      expect(Array.isArray(parsedLogs)).toBe(true);
      expect(parsedLogs).toHaveLength(1);
      expect(parsedLogs[0].message).toBe('Test message');
    });

    it('should maintain log size limit', () => {
      const originalMaxSize = logger.maxLogSize;
      logger.maxLogSize = 3;
      
      for (let i = 0; i < 5; i++) {
        logger.info(`Message ${i}`);
      }
      
      const logs = logger.getLogs();
      expect(logs).toHaveLength(3);
      
      // Restore original size
      logger.maxLogSize = originalMaxSize;
    });
  });

  describe('Helper Functions', () => {
    it('should log API calls using helper', () => {
      logApiCall('POST', '/api/helper', 201, 100);
      
      const logs = logger.getLogs();
      expect(logs).toHaveLength(1);
      expect(logs[0].message).toBe('POST /api/helper');
    });

    it('should log user actions using helper', () => {
      logUserAction('helper_action', { source: 'test' });
      
      const logs = logger.getLogs();
      expect(logs).toHaveLength(1);
      expect(logs[0].message).toBe('User action: helper_action');
    });

    it('should log errors using helper', () => {
      logError('Helper error', 'TEST');
      
      const logs = logger.getLogs();
      expect(logs).toHaveLength(1);
      expect(logs[0].level).toBe('error');
      expect(logs[0].message).toBe('Helper error');
    });

    it('should log info using helper', () => {
      logInfo('Helper info', 'TEST');
      
      const logs = logger.getLogs();
      expect(logs).toHaveLength(1);
      expect(logs[0].level).toBe('info');
      expect(logs[0].message).toBe('Helper info');
    });

    it('should log WebSocket events using helper', () => {
      logWebSocketEvent('helper_event', { data: 'test' });
      
      const logs = logger.getLogs();
      expect(logs).toHaveLength(1);
      expect(logs[0].message).toBe('WebSocket: helper_event');
    });
  });
});

describe('Idea Cleaner Utility', () => {
  let cleanImprovedIdea: any;
  let cleanImprovedIdeasInResults: any;

  beforeEach(async () => {
    const module = await import(ideaCleanerPath);
    cleanImprovedIdea = module.cleanImprovedIdea;
    cleanImprovedIdeasInResults = module.cleanImprovedIdeasInResults;
  });

  describe('Basic Text Cleaning', () => {
    it('should remove meta headers', () => {
      const messyText = `
ENHANCED CONCEPT: Better Solution
ORIGINAL THEME: Test Theme

This is the actual content that should remain.
      `.trim();

      const cleaned = cleanImprovedIdea(messyText);
      expect(cleaned).toBe('This is the actual content that should remain.');
      expect(cleaned).not.toContain('ENHANCED CONCEPT');
      expect(cleaned).not.toContain('ORIGINAL THEME');
    });

    it('should remove meta phrases', () => {
      const messyText = `
This solution addresses evaluation criteria.
Enhancing Impact Through better design.
The core functionality remains intact.
      `.trim();

      const cleaned = cleanImprovedIdea(messyText);
      expect(cleaned).toContain('The core functionality remains intact.');
      expect(cleaned).not.toContain('addresses evaluation criteria');
      expect(cleaned).not.toContain('Enhancing Impact Through');
    });

    it('should apply replacement patterns', () => {
      const messyText = 'Our enhanced approach creates improved solutions.';
      
      const cleaned = cleanImprovedIdea(messyText);
      expect(cleaned).toBe('This approach creates solutions.');
    });

    it('should handle empty or null input', () => {
      expect(cleanImprovedIdea('')).toBe('');
      expect(cleanImprovedIdea(null as any)).toBe(null);
      expect(cleanImprovedIdea(undefined as any)).toBe(undefined);
    });

    it('should preserve clean text unchanged', () => {
      const cleanText = 'This is already clean text with no meta-commentary.';
      
      const result = cleanImprovedIdea(cleanText);
      expect(result).toBe(cleanText);
    });
  });

  describe('Complex Cleaning Scenarios', () => {
    it('should handle multiple meta sections', () => {
      const messyText = `
ENHANCED CONCEPT: The Solution
ORIGINAL THEME: Innovation
REVISED CORE PREMISE: Better approach

Addresses Evaluation Criteria for improvement.
Enhancing Impact Through new methods.

This is the actual content.
More content here.
      `.trim();

      const cleaned = cleanImprovedIdea(messyText);
      expect(cleaned).toContain('This is the actual content.');
      expect(cleaned).toContain('More content here.');
      expect(cleaned).not.toContain('ENHANCED CONCEPT');
      expect(cleaned).not.toContain('Addresses Evaluation Criteria');
    });

    it('should handle framework cleanup patterns', () => {
      const messyText = ': a more robust system for handling data\nThis is the main content.';
      
      const cleaned = cleanImprovedIdea(messyText);
      expect(cleaned).toBe('This is the main content.');
    });

    it('should format titles properly', () => {
      const messyText = `
The "Innovation Framework" System for productivity
## Main Features
- Feature 1
- Feature 2
      `.trim();

      const cleaned = cleanImprovedIdea(messyText);
      expect(cleaned).toContain('# Innovation Framework');
      expect(cleaned).toContain('## Main Features');
    });
  });

  describe('Batch Processing', () => {
    it('should clean multiple results efficiently', () => {
      const results = [
        {
          id: 1,
          improved_idea: 'ENHANCED CONCEPT: Solution 1\nThis is solution 1.'
        },
        {
          id: 2,
          improved_idea: 'Our enhanced approach for solution 2.'
        },
        {
          id: 3,
          idea: 'Regular idea without improvement'
        }
      ];

      const cleanedResults = cleanImprovedIdeasInResults(results);
      
      expect(cleanedResults).toHaveLength(3);
      expect(cleanedResults[0].improved_idea).toBe('This is solution 1.');
      expect(cleanedResults[1].improved_idea).toBe('This approach for solution 2.');
      expect(cleanedResults[2]).toEqual(results[2]); // Unchanged
    });

    it('should handle results without improved_idea field', () => {
      const results = [
        { id: 1, idea: 'Regular idea' },
        { id: 2, improved_idea: 'enhanced solution' }
      ];

      const cleanedResults = cleanImprovedIdeasInResults(results);
      
      expect(cleanedResults).toHaveLength(2);
      expect(cleanedResults[0]).toEqual(results[0]);
      expect(cleanedResults[1].improved_idea).toBe(' solution');
    });

    it('should handle empty results array', () => {
      const results: any[] = [];
      const cleanedResults = cleanImprovedIdeasInResults(results);
      
      expect(cleanedResults).toEqual([]);
    });
  });

  describe('Performance Optimization', () => {
    it('should cache compiled patterns for efficiency', () => {
      // Test multiple calls to ensure pattern caching works
      const testTexts = [
        'ENHANCED CONCEPT: Test 1\nContent 1',
        'ENHANCED CONCEPT: Test 2\nContent 2',
        'ENHANCED CONCEPT: Test 3\nContent 3'
      ];

      const start = Date.now();
      testTexts.forEach(text => cleanImprovedIdea(text));
      const duration = Date.now() - start;

      // Should complete quickly (under 50ms for 3 cleanings)
      expect(duration).toBeLessThan(50);
    });

    it('should pre-warm cache for batch processing', () => {
      const largeResults = Array.from({ length: 100 }, (_, i) => ({
        id: i,
        improved_idea: `ENHANCED CONCEPT: Solution ${i}\nThis is solution ${i}.`
      }));

      const start = Date.now();
      const cleaned = cleanImprovedIdeasInResults(largeResults);
      const duration = Date.now() - start;

      expect(cleaned).toHaveLength(100);
      // Should complete efficiently (under 200ms for 100 items)
      expect(duration).toBeLessThan(200);
    });
  });
});

describe('Frontend Utilities Integration', () => {
  it('should work together - error handler with logger and toast', async () => {
    // Import all modules
    const errorModule = await import(errorHandlerPath);
    const loggerModule = await import(loggerPath);
    
    // Clear logs
    loggerModule.logger.clearLogs();
    errorModule.errorHandler.clearErrorLog();
    
    // Test integrated error handling
    const testError = { response: { status: 500, data: { detail: 'Server error' } } };
    errorModule.errorHandler.handleError(testError, 'Integration Test');
    
    // Verify error was processed
    const errorLog = errorModule.errorHandler.getErrorLog();
    expect(errorLog).toHaveLength(1);
    expect(errorLog[0].type).toBe('server');
    
    // Verify toast was called
    expect(toast.error).toHaveBeenCalled();
  });

  it('should handle complex error scenarios with all utilities', async () => {
    const errorModule = await import(errorHandlerPath);
    const loggerModule = await import(loggerPath);
    const ideaCleanerModule = await import(ideaCleanerPath);
    
    // Test error in idea processing workflow
    try {
      // Simulate idea processing
      const result = {
        improved_idea: 'ENHANCED CONCEPT: Failed Idea\nThis idea had an error.'
      };
      
      const cleaned = ideaCleanerModule.cleanImprovedIdea(result.improved_idea);
      expect(cleaned).toBe('This idea had an error.');
      
      // Log the processing
      loggerModule.logger.ideaGeneration('processing_complete', { result: cleaned });
      
      // Simulate an error
      throw new Error('Processing failed after cleaning');
      
    } catch (error) {
      // Handle error with integrated system
      errorModule.errorHandler.handleError(error, 'Idea Processing');
      
      // Verify error was logged
      const logs = loggerModule.logger.getLogs();
      const errorLogs = errorModule.errorHandler.getErrorLog();
      
      expect(logs.length).toBeGreaterThan(0);
      expect(errorLogs.length).toBeGreaterThan(0);
    }
  });
});