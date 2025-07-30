import React, { useState, useEffect, useRef } from 'react';
import api from './api';
import IdeaGenerationForm from './components/IdeaGenerationForm';
import ResultsDisplay from './components/ResultsDisplay';
import ProgressIndicator from './components/ProgressIndicator';
import BookmarkManager from './components/BookmarkManager';
import DuplicateWarningDialog from './components/DuplicateWarningDialog';
import KeyboardShortcutsDialog from './components/KeyboardShortcutsDialog';
import { bookmarkService } from './services/bookmarkService';
import { ToastContainer } from 'react-toastify';
import { showSuccess, showInfo } from './utils/toast';
import { handleBookmarkError, handleIdeaGenerationError, handleWebSocketError } from './utils/errorHandler';
import { logger, logUserAction, logWebSocketEvent, logApiCall } from './utils/logger';
import { useKeyboardShortcuts } from './hooks/useKeyboardShortcuts';
import './App.css';
import 'react-toastify/dist/ReactToastify.css';

import { 
  IdeaResult, 
  IdeaGenerationResponse, 
  ProgressUpdate, 
  ConnectionStatus,
  SavedBookmark,
  SimilarBookmark,
  KeyboardShortcut
} from './types';

function App() {
  const [results, setResults] = useState<IdeaResult[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [progress, setProgress] = useState<ProgressUpdate | null>(null);
  const [lastFormData, setLastFormData] = useState<any>(null);
  const [showDetailedResults, setShowDetailedResults] = useState(false);
  const [bookmarkedIdeas, setBookmarkedIdeas] = useState<Set<string>>(new Set());
  const [savedBookmarks, setSavedBookmarks] = useState<SavedBookmark[]>([]);
  const [showBookmarkManager, setShowBookmarkManager] = useState(false);
  const [selectedBookmarkIds, setSelectedBookmarkIds] = useState<string[]>([]);
  
  // WebSocket connection status
  const [wsConnectionStatus, setWsConnectionStatus] = useState<ConnectionStatus>('connecting');
  
  // Keyboard shortcuts dialog
  const [showKeyboardShortcuts, setShowKeyboardShortcuts] = useState(false);
  
  // Refs for keyboard shortcut targets
  const formRef = useRef<HTMLDivElement>(null);
  const resultsRef = useRef<HTMLDivElement>(null);
  
  // Duplicate warning dialog state
  const [showDuplicateWarning, setShowDuplicateWarning] = useState(false);
  const [duplicateWarningData, setDuplicateWarningData] = useState<{
    result: IdeaResult;
    index: number;
    theme: string;
    constraints: string;
    similarBookmarks: SimilarBookmark[];
    recommendation: 'block' | 'warn' | 'notice' | 'allow';
    message: string;
  } | null>(null);

  // Load bookmarks on mount
  useEffect(() => {
    loadBookmarks();
  }, []);

  const loadBookmarks = async () => {
    try {
      logger.info('Loading bookmarks', 'BOOKMARK');
      const bookmarks = await bookmarkService.getBookmarks();
      setSavedBookmarks(bookmarks);
      // Create a set of bookmark IDs for quick lookup
      const bookmarkIds = new Set(bookmarks.map(b => b.id));
      setBookmarkedIdeas(bookmarkIds);
      logger.info(`Loaded ${bookmarks.length} bookmarks`, 'BOOKMARK');
    } catch (error: any) {
      // Don't show error alerts for bookmark loading failures during initial load
      // as this would be annoying for users. Just handle the error silently.
      const errorDetails = handleBookmarkError(error, 'loading');
      
      // Set empty arrays so UI doesn't break
      setSavedBookmarks([]);
      setBookmarkedIdeas(new Set());
      
      // Only log, don't show toast for initial load failures
      logger.warn('Bookmark loading failed but UI continues', 'BOOKMARK', errorDetails);
    }
  };
  
  const handleDeleteBookmark = async (bookmarkId: string) => {
    try {
      logUserAction('delete_bookmark', { bookmarkId });
      await bookmarkService.deleteBookmark(bookmarkId);
      
      // Reload bookmarks with error handling
      try {
        await loadBookmarks();
        showSuccess('Bookmark deleted successfully!');
        logger.bookmarkAction('delete', bookmarkId, true);
      } catch (reloadError) {
        handleBookmarkError(reloadError, 'reloading after deletion');
        // Still show success since deletion worked
        showSuccess('Bookmark deleted successfully! Please refresh to see updated list.');
      }
    } catch (error: any) {
      handleBookmarkError(error, 'deletion');
      logger.bookmarkAction('delete', bookmarkId, false);
      
      // Special handling for 404 - bookmark may have been deleted already
      if (error.response?.status === 404) {
        // Reload bookmarks to sync state
        await loadBookmarks().catch(err => handleBookmarkError(err, 'sync after 404'));
      }
    }
  };

  // Helper function to create bookmark without duplicate checking
  const createBookmarkDirect = async (result: IdeaResult, theme: string, constraints: string, forceSave: boolean) => {
    logger.bookmarkAction('create', undefined, false);
    
    const response = await bookmarkService.createBookmarkWithDuplicateCheck(
      result, 
      theme,
      constraints,
      forceSave
    );
    
    if (response.bookmark_created && response.bookmark_id) {
      setBookmarkedIdeas(new Set(Array.from(bookmarkedIdeas).concat(response.bookmark_id)));
      
      // Reload bookmarks with error handling
      try {
        await loadBookmarks();
        showSuccess('Idea bookmarked successfully!');
        logger.bookmarkAction('create', response.bookmark_id, true);
      } catch (reloadError) {
        handleBookmarkError(reloadError, 'reloading after creation');
        showSuccess('Idea bookmarked successfully! Please refresh to see updated list.');
        logger.bookmarkAction('create', response.bookmark_id, true);
      }
    } else {
      throw new Error(response.message || 'Failed to create bookmark');
    }
  };

  // Duplicate warning dialog handlers
  const handleSaveBookmarkAnyway = async () => {
    if (!duplicateWarningData) return;
    
    try {
      await createBookmarkDirect(
        duplicateWarningData.result, 
        duplicateWarningData.theme, 
        duplicateWarningData.constraints, 
        true // force save
      );
      
      showSuccess('Bookmark saved successfully despite similar content found.');
      setShowDuplicateWarning(false);
      setDuplicateWarningData(null);
    } catch (error) {
      handleBookmarkError(error, 'force save');
      setShowDuplicateWarning(false);
      setDuplicateWarningData(null);
    }
  };

  const handleCancelDuplicateWarning = () => {
    if (duplicateWarningData) {
      logUserAction('cancel_duplicate_warning', { 
        ideaIndex: duplicateWarningData.index, 
        recommendation: duplicateWarningData.recommendation 
      });
    }
    setShowDuplicateWarning(false);
    setDuplicateWarningData(null);
  };

  // Initialize WebSocket connection with reconnection logic
  useEffect(() => {
    let ws: WebSocket | null = null;
    let reconnectAttempts = 0;
    let reconnectInterval: NodeJS.Timeout | null = null;
    let pingInterval: NodeJS.Timeout | null = null;
    const maxReconnectAttempts = 5;
    const reconnectDelay = 3000; // 3 seconds
    
    const connectWebSocket = () => {
      try {
        const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsHost = window.location.hostname;
        const wsPort = process.env.REACT_APP_WS_PORT || '8000';
        const wsUrl = `${wsProtocol}//${wsHost}:${wsPort}/ws/progress`;
        
        logger.debug(`Connecting to WebSocket: ${wsUrl}`, 'WS');
        setWsConnectionStatus(reconnectAttempts > 0 ? 'reconnecting' : 'connecting');
        ws = new WebSocket(wsUrl);
        
        ws.onopen = () => {
          logWebSocketEvent('connected');
          setWsConnectionStatus('connected');
          reconnectAttempts = 0; // Reset counter on successful connection
          
          // Set up ping interval for keep-alive
          pingInterval = setInterval(() => {
            if (ws && ws.readyState === WebSocket.OPEN) {
              ws.send('ping');
              logWebSocketEvent('ping_sent');
            }
          }, 25000); // Ping every 25 seconds
        };
        
        ws.onmessage = (event) => {
          try {
            // Handle pong response
            if (event.data === 'pong') {
              logWebSocketEvent('pong_received');
              return;
            }
            
            const data = JSON.parse(event.data);
            if (data.type === 'progress') {
              setProgress(data);
              logWebSocketEvent('progress_update', { progress: data.progress, message: data.message });
            } else if (data.type === 'connection') {
              logWebSocketEvent('connection_confirmed', { message: data.message });
            } else {
              logWebSocketEvent('unknown_message', data);
            }
          } catch (e) {
            // Handle non-JSON messages (like plain pong)
            if (event.data !== 'pong') {
              logWebSocketEvent('parse_error', { data: event.data, error: e });
            }
          }
        };
        
        ws.onclose = (event) => {
          logWebSocketEvent('disconnected', { code: event.code, reason: event.reason });
          
          // Clear ping interval
          if (pingInterval) {
            clearInterval(pingInterval);
            pingInterval = null;
          }
          
          // Attempt reconnection if not manually closed and under max attempts
          if (event.code !== 1000 && reconnectAttempts < maxReconnectAttempts) {
            reconnectAttempts++;
            setWsConnectionStatus('reconnecting');
            logger.info(`Attempting WebSocket reconnection ${reconnectAttempts}/${maxReconnectAttempts}`, 'WS');
            reconnectInterval = setTimeout(connectWebSocket, reconnectDelay);
          } else if (reconnectAttempts >= maxReconnectAttempts) {
            setWsConnectionStatus('disconnected');
            logger.warn('Max WebSocket reconnection attempts reached', 'WS');
          } else {
            setWsConnectionStatus('disconnected');
          }
        };
        
        ws.onerror = (error) => {
          handleWebSocketError(error);
        };
        
      } catch (error) {
        handleWebSocketError(error);
      }
    };
    
    connectWebSocket();
    
    return () => {
      // Cleanup on unmount
      if (reconnectInterval) {
        clearTimeout(reconnectInterval);
      }
      if (pingInterval) {
        clearInterval(pingInterval);
      }
      if (ws) {
        ws.close(1000, 'Component unmounting');
      }
    };
  }, []);

  const handleIdeaGeneration = async (formData: any) => {
    setLastFormData(formData); // Store for retry functionality
    setShowDetailedResults(formData.show_detailed_results || false); // Store the preference
    setIsLoading(true);
    setError(null);
    setResults([]);
    setProgress(null);

    const startTime = Date.now();
    logUserAction('generate_ideas', { theme: formData.theme, numCandidates: formData.num_top_candidates });
    logger.ideaGeneration('started', formData);

    try {
      const response = await api.post<IdeaGenerationResponse>('/api/generate-ideas', formData);
      const duration = Date.now() - startTime;
      
      logApiCall('POST', '/api/generate-ideas', response.status, duration);
      
      if (response.data.status === 'success') {
        const resultsCount = response.data.results?.length || 0;
        logger.ideaGeneration('completed', { resultsCount, duration });
        setResults(response.data.results || []);
        
        // Validate that we actually have results
        if (!response.data.results || response.data.results.length === 0) {
          setError('No ideas were generated. Please try with different parameters.');
          logger.warn('No ideas generated despite success status', 'IDEA_GEN');
        } else {
          showInfo(`Generated ${resultsCount} ideas in ${(duration / 1000).toFixed(1)}s`);
        }
      } else {
        const errorMessage = response.data.message || 'Failed to generate ideas';
        setError(errorMessage);
        logger.ideaGeneration('failed', { error: errorMessage });
      }
    } catch (err: any) {
      const duration = Date.now() - startTime;
      const errorDetails = handleIdeaGenerationError(err);
      
      logApiCall('POST', '/api/generate-ideas', err.response?.status, duration);
      logger.ideaGeneration('error', { error: errorDetails, duration });
      
      setError(errorDetails.message);
    } finally {
      setIsLoading(false);
      setProgress(null);
    }
  };

  const handleRetry = () => {
    if (lastFormData) {
      logUserAction('retry_idea_generation');
      handleIdeaGeneration(lastFormData);
    }
  };

  // Define keyboard shortcuts
  const shortcuts: KeyboardShortcut[] = [
    {
      key: '?',
      description: 'Show keyboard shortcuts help',
      handler: () => setShowKeyboardShortcuts(true)
    },
    {
      key: 'g',
      ctrlKey: true,
      description: 'Focus on idea generation form',
      handler: () => {
        const themeInput = document.querySelector('input[name="theme"]') as HTMLInputElement;
        themeInput?.focus();
        formRef.current?.scrollIntoView({ behavior: 'smooth' });
      }
    },
    {
      key: 'Enter',
      ctrlKey: true,
      description: 'Generate ideas (submit form)',
      handler: () => {
        const submitButton = document.querySelector('button[type="submit"]') as HTMLButtonElement;
        if (submitButton && !submitButton.disabled) {
          submitButton.click();
        }
      }
    },
    {
      key: 'Escape',
      description: 'Close dialogs',
      handler: () => {
        if (showKeyboardShortcuts) setShowKeyboardShortcuts(false);
        else if (showBookmarkManager) setShowBookmarkManager(false);
        else if (showDuplicateWarning) handleCancelDuplicateWarning();
      }
    }
  ];

  // Use keyboard shortcuts hook
  const activeShortcuts = useKeyboardShortcuts(shortcuts);

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="py-6">
            <div className="flex items-center justify-between">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <h1 className="text-3xl font-bold text-gray-900">
                    🧠 MadSpark
                  </h1>
                </div>
                <div className="ml-4">
                  <p className="text-sm text-gray-600">
                    AI-Powered Multi-Agent Idea Generation System
                  </p>
                  {/* WebSocket Connection Status */}
                  <div className="flex items-center mt-1">
                    <div className={`inline-flex items-center text-xs px-2 py-1 rounded-full ${
                      wsConnectionStatus === 'connected' 
                        ? 'bg-green-100 text-green-800' 
                        : wsConnectionStatus === 'connecting' 
                          ? 'bg-yellow-100 text-yellow-800'
                          : wsConnectionStatus === 'reconnecting'
                            ? 'bg-orange-100 text-orange-800'
                            : 'bg-red-100 text-red-800'
                    }`}>
                      <div className={`w-2 h-2 rounded-full mr-2 ${
                        wsConnectionStatus === 'connected' 
                          ? 'bg-green-400' 
                          : wsConnectionStatus === 'connecting' 
                            ? 'bg-yellow-400 animate-pulse'
                            : wsConnectionStatus === 'reconnecting'
                              ? 'bg-orange-400 animate-pulse'
                              : 'bg-red-400'
                      }`}></div>
                      <span>
                        {wsConnectionStatus === 'connected' && 'Connected'}
                        {wsConnectionStatus === 'connecting' && 'Connecting...'}
                        {wsConnectionStatus === 'reconnecting' && 'Reconnecting...'}
                        {wsConnectionStatus === 'disconnected' && 'Disconnected'}
                      </span>
                    </div>
                  </div>
                </div>
              </div>
              <div className="flex items-center space-x-2">
                <button
                  type="button"
                  onClick={() => setShowKeyboardShortcuts(true)}
                  className="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-500"
                  title="Keyboard shortcuts (press ? anytime)"
                >
                  <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                  </svg>
                  <span className="ml-2">
                    <kbd className="px-1.5 py-0.5 text-xs font-semibold text-gray-800 bg-gray-100 border border-gray-200 rounded">?</kbd>
                  </span>
                </button>
                
                <button
                  type="button"
                  onClick={() => setShowBookmarkManager(true)}
                  className="relative inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                >
                  <svg className="h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-label="Bookmark icon">
                    <title>Bookmark icon</title>
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z" />
                  </svg>
                  Bookmarks
                  {savedBookmarks.length > 0 && (
                    <span className="ml-2 inline-flex items-center justify-center px-2 py-1 text-xs font-bold leading-none text-blue-100 bg-blue-800 rounded-full">
                      {savedBookmarks.length}
                    </span>
                  )}
                </button>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Left Column - Input Form */}
          <div className="space-y-6" ref={formRef}>
            <IdeaGenerationForm 
              onSubmit={handleIdeaGeneration}
              isLoading={isLoading}
              savedBookmarks={savedBookmarks}
              onOpenBookmarkManager={() => setShowBookmarkManager(true)}
              selectedBookmarkIds={selectedBookmarkIds}
              onSelectedBookmarkIdsChange={setSelectedBookmarkIds}
            />
            
            {/* Progress Indicator */}
            {(isLoading || progress) && (
              <ProgressIndicator 
                progress={progress}
                isLoading={isLoading}
              />
            )}

            {/* Error Display */}
            {error && (
              <div className="bg-red-50 border border-red-200 rounded-md p-4">
                <div className="flex">
                  <div className="flex-shrink-0">
                    <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                      <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                    </svg>
                  </div>
                  <div className="ml-3 flex-1">
                    <h3 className="text-sm font-medium text-red-800">
                      Error
                    </h3>
                    <div className="mt-2 text-sm text-red-700">
                      <p>{error}</p>
                    </div>
                    {lastFormData && (
                      <div className="mt-3">
                        <button
                          type="button"
                          onClick={handleRetry}
                          disabled={isLoading}
                          className="inline-flex items-center px-3 py-2 border border-transparent text-sm leading-4 font-medium rounded-md text-red-700 bg-red-100 hover:bg-red-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                          <svg className="mr-2 h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                          </svg>
                          {isLoading ? 'Retrying...' : 'Try Again'}
                        </button>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Right Column - Results */}
          <div ref={resultsRef}>
            <ResultsDisplay 
              results={results} 
              showDetailedResults={showDetailedResults}
              theme={lastFormData?.theme || ''}
              constraints={lastFormData?.constraints || ''}
              bookmarkedIdeas={bookmarkedIdeas}
              onBookmarkToggle={async (result: IdeaResult, index: number) => {
                try {
                  // Check if this result is already bookmarked
                  const existingBookmark = savedBookmarks.find(bookmark => 
                    bookmark.text === result.idea || 
                    (result.improved_idea && bookmark.text === result.improved_idea)
                  );
                  
                  if (existingBookmark) {
                    // Remove existing bookmark
                    logUserAction('remove_bookmark', { bookmarkId: existingBookmark.id, ideaIndex: index });
                    await handleDeleteBookmark(existingBookmark.id);
                  } else {
                    // Create bookmark with duplicate detection
                    const bookmarkTheme = lastFormData?.theme || 'General';
                    const bookmarkConstraints = lastFormData?.constraints || 'No specific constraints';
                    
                    logUserAction('create_bookmark_with_duplicate_check', { ideaIndex: index, theme: bookmarkTheme });
                    
                    try {
                      // First check for duplicates using improved idea if available
                      const ideaToCheck = result.improved_idea || result.idea;
                      const duplicateCheck = await bookmarkService.checkForDuplicates(ideaToCheck, bookmarkTheme);
                      
                      if (duplicateCheck.has_duplicates && duplicateCheck.recommendation !== 'allow') {
                        // Show duplicate warning dialog
                        setDuplicateWarningData({
                          result,
                          index,
                          theme: bookmarkTheme,
                          constraints: bookmarkConstraints,
                          similarBookmarks: duplicateCheck.similar_bookmarks,
                          recommendation: duplicateCheck.recommendation,
                          message: duplicateCheck.message
                        });
                        setShowDuplicateWarning(true);
                      } else {
                        // No significant duplicates or user preference to skip check, save directly
                        await createBookmarkDirect(result, bookmarkTheme, bookmarkConstraints, false);
                      }
                    } catch (duplicateCheckError) {
                      // If duplicate check fails, fall back to regular bookmark creation with warning
                      console.warn('Duplicate check failed, proceeding with regular bookmark creation:', duplicateCheckError);
                      showInfo('Duplicate detection unavailable, saving bookmark normally.');
                      await createBookmarkDirect(result, bookmarkTheme, bookmarkConstraints, false);
                    }
                  }
                } catch (error: any) {
                  handleBookmarkError(error, 'toggle operation');
                }
              }}
              savedBookmarks={savedBookmarks}
            />
          </div>
        </div>
      </main>
      
      {/* Bookmark Manager Modal */}
      <BookmarkManager
        isOpen={showBookmarkManager}
        onClose={() => setShowBookmarkManager(false)}
        bookmarks={savedBookmarks}
        onDeleteBookmark={handleDeleteBookmark}
        onSelectBookmarks={setSelectedBookmarkIds}
        selectedBookmarkIds={selectedBookmarkIds}
      />
      
      {/* Duplicate Warning Dialog */}
      <DuplicateWarningDialog
        isOpen={showDuplicateWarning}
        onClose={handleCancelDuplicateWarning}
        onSaveAnyway={handleSaveBookmarkAnyway}
        onCancel={handleCancelDuplicateWarning}
        similarBookmarks={duplicateWarningData?.similarBookmarks || []}
        recommendation={duplicateWarningData?.recommendation || 'allow'}
        message={duplicateWarningData?.message || ''}
        ideaText={duplicateWarningData ? (duplicateWarningData.result.improved_idea || duplicateWarningData.result.idea) : ''}
      />
      
      {/* Keyboard Shortcuts Dialog */}
      <KeyboardShortcutsDialog
        isOpen={showKeyboardShortcuts}
        onClose={() => setShowKeyboardShortcuts(false)}
        shortcuts={activeShortcuts}
      />
      
      {/* Toast Container */}
      <ToastContainer />
    </div>
  );
}

export default App;