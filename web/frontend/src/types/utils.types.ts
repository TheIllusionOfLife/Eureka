/**
 * Utility type definitions for the MadSpark application
 */

// Logger types
export type LogLevel = 'debug' | 'info' | 'warn' | 'error';

export interface LogEntry {
  level: LogLevel;
  message: string;
  context?: string;
  data?: any;
  timestamp: string;
  sessionId: string;
}

// Error handling types
export interface ErrorDetails {
  message: string;
  type: 'network' | 'validation' | 'server' | 'timeout' | 'rate_limit' | 'auth' | 'unknown';
  code?: number;
  details?: any;
  timestamp: string;
  context?: string;
}

// ApiError interface moved to api.types.ts to avoid duplication

// Toast notification types
export type ToastType = 'success' | 'error' | 'info' | 'warning';

export interface ToastOptions {
  position?: 'top-right' | 'top-center' | 'top-left' | 'bottom-right' | 'bottom-center' | 'bottom-left';
  autoClose?: number | false;
  hideProgressBar?: boolean;
  closeOnClick?: boolean;
  pauseOnHover?: boolean;
  draggable?: boolean;
  className?: string;
  style?: React.CSSProperties;
}

// Idea cleaner types
export interface CompiledPatterns {
  replacementPatterns: Array<[RegExp, string]>;
  frameworkPattern: RegExp;
  titleExtractionPattern: RegExp;
  titleReplacementPattern: RegExp;
  metaHeaderPatterns: RegExp[];
  metaPhrasePatterns: RegExp[];
}

export interface CleanerOptions {
  removeFrameworks?: boolean;
  removeImprovedPrefix?: boolean;
  removeBulletPoints?: boolean;
  trimWhitespace?: boolean;
}