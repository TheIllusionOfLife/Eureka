/**
 * Centralized logging utility for the MadSpark application
 * Provides structured logging with different levels and contexts
 */

export type LogLevel = 'debug' | 'info' | 'warn' | 'error';

export interface LogEntry {
  level: LogLevel;
  message: string;
  context?: string;
  data?: any;
  timestamp: string;
  sessionId: string;
}

class Logger {
  private logs: LogEntry[] = [];
  private maxLogSize = 200;
  private sessionId: string;
  private logLevel: LogLevel;

  constructor() {
    this.sessionId = this.generateSessionId();
    this.logLevel = (process.env.NODE_ENV === 'development') ? 'debug' : 'info';
  }

  private generateSessionId(): string {
    return Date.now().toString(36) + Math.random().toString(36).slice(2);
  }

  private shouldLog(level: LogLevel): boolean {
    const levels: LogLevel[] = ['debug', 'info', 'warn', 'error'];
    return levels.indexOf(level) >= levels.indexOf(this.logLevel);
  }

  private createLogEntry(level: LogLevel, message: string, context?: string, data?: any): LogEntry {
    return {
      level,
      message,
      context,
      data,
      timestamp: new Date().toISOString(),
      sessionId: this.sessionId
    };
  }

  private log(level: LogLevel, message: string, context?: string, data?: any) {
    if (!this.shouldLog(level)) return;

    const entry = this.createLogEntry(level, message, context, data);
    
    // Add to in-memory log
    this.logs.push(entry);
    if (this.logs.length > this.maxLogSize) {
      this.logs.shift();
    }

    // Format for console
    const contextStr = context ? `[${context}]` : '';
    const emoji = this.getLogEmoji(level);
    const consoleMessage = `${emoji} ${contextStr} ${message}`;

    // Console output
    switch (level) {
      case 'debug':
        console.debug(consoleMessage, data);
        break;
      case 'info':
        console.info(consoleMessage, data);
        break;
      case 'warn':
        console.warn(consoleMessage, data);
        break;
      case 'error':
        console.error(consoleMessage, data);
        break;
    }
  }

  private getLogEmoji(level: LogLevel): string {
    const emojis = {
      debug: '🔍',
      info: '📝',
      warn: '⚠️',
      error: '❌'
    };
    return emojis[level] || '📝';
  }

  debug(message: string, context?: string, data?: any) {
    this.log('debug', message, context, data);
  }

  info(message: string, context?: string, data?: any) {
    this.log('info', message, context, data);
  }

  warn(message: string, context?: string, data?: any) {
    this.log('warn', message, context, data);
  }

  error(message: string, context?: string, data?: any) {
    this.log('error', message, context, data);
  }

  // Specialized logging methods
  apiCall(method: string, url: string, status?: number, duration?: number) {
    const message = `${method.toUpperCase()} ${url}`;
    const data = { status, duration };
    
    if (status && status >= 400) {
      this.warn(message, 'API', data);
    } else {
      this.debug(message, 'API', data);
    }
  }

  userAction(action: string, details?: any) {
    this.info(`User action: ${action}`, 'USER', details);
  }

  websocketEvent(event: string, data?: any) {
    this.debug(`WebSocket: ${event}`, 'WS', data);
  }

  bookmarkAction(action: string, bookmarkId?: string, success = true) {
    const message = `Bookmark ${action}${bookmarkId ? ` (${bookmarkId})` : ''}`;
    if (success) {
      this.info(message, 'BOOKMARK');
    } else {
      this.warn(message, 'BOOKMARK');
    }
  }

  ideaGeneration(phase: string, details?: any) {
    this.info(`Idea generation: ${phase}`, 'IDEA_GEN', details);
  }

  // Utility methods
  getLogs(level?: LogLevel): LogEntry[] {
    if (level) {
      return this.logs.filter(log => log.level === level);
    }
    return [...this.logs];
  }

  getRecentLogs(count = 20): LogEntry[] {
    return this.logs.slice(-count);
  }

  clearLogs() {
    this.logs = [];
  }

  getStats() {
    const stats = {
      total: this.logs.length,
      session: this.sessionId,
      byLevel: {} as Record<LogLevel, number>,
      byContext: {} as Record<string, number>
    };

    this.logs.forEach(log => {
      stats.byLevel[log.level] = (stats.byLevel[log.level] || 0) + 1;
      if (log.context) {
        stats.byContext[log.context] = (stats.byContext[log.context] || 0) + 1;
      }
    });

    return stats;
  }

  // Export logs for debugging
  exportLogs(): string {
    return JSON.stringify(this.logs, null, 2);
  }

  setLogLevel(level: LogLevel) {
    this.logLevel = level;
    this.info(`Log level set to ${level}`, 'SYSTEM');
  }
}

// Export singleton instance
export const logger = new Logger();

// Helper functions for common logging scenarios
export const logApiCall = (method: string, url: string, status?: number, duration?: number) => {
  logger.apiCall(method, url, status, duration);
};

export const logUserAction = (action: string, details?: any) => {
  logger.userAction(action, details);
};

export const logError = (message: string, context?: string, error?: any) => {
  logger.error(message, context, error);
};

export const logInfo = (message: string, context?: string, data?: any) => {
  logger.info(message, context, data);
};

export const logWebSocketEvent = (event: string, data?: any) => {
  logger.websocketEvent(event, data);
};