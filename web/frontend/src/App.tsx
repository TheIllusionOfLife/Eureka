import React, { useState, useEffect } from 'react';
import api from './api';
import IdeaGenerationForm from './components/IdeaGenerationForm';
import ResultsDisplay from './components/ResultsDisplay';
import ProgressIndicator from './components/ProgressIndicator';
import BookmarkManager from './components/BookmarkManager';
import { bookmarkService, SavedBookmark } from './services/bookmarkService';
import './App.css';

export interface IdeaResult {
  idea: string;
  initial_score: number;
  initial_critique: string;
  advocacy: string;
  skepticism: string;
  improved_idea: string;
  improved_score: number;
  improved_critique: string;
  score_delta: number;
  multi_dimensional_evaluation?: {
    dimension_scores: {
      feasibility: number;
      innovation: number;
      impact: number;
      cost_effectiveness: number;
      scalability: number;
      risk_assessment: number;
      timeline: number;
    };
    overall_score: number;
    confidence_interval: {
      lower: number;
      upper: number;
    };
  };
  improved_multi_dimensional_evaluation?: {
    dimension_scores: {
      feasibility: number;
      innovation: number;
      impact: number;
      cost_effectiveness: number;
      scalability: number;
      risk_assessment: number;
      timeline: number;
    };
    overall_score: number;
    confidence_interval: {
      lower: number;
      upper: number;
    };
  };
}

export interface ApiResponse {
  status: string;
  message: string;
  results: IdeaResult[];
  processing_time: number;
  timestamp: string;
}

export interface ProgressUpdate {
  type: string;
  message: string;
  progress: number;
  timestamp: string;
}

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

  // Load bookmarks on mount
  useEffect(() => {
    loadBookmarks();
  }, []);

  const loadBookmarks = async () => {
    try {
      const bookmarks = await bookmarkService.getBookmarks();
      setSavedBookmarks(bookmarks);
      // Create a set of bookmark IDs for quick lookup
      const bookmarkIds = new Set(bookmarks.map(b => b.id));
      setBookmarkedIdeas(bookmarkIds);
    } catch (error) {
      console.error('Failed to load bookmarks:', error);
    }
  };
  
  const handleDeleteBookmark = async (bookmarkId: string) => {
    try {
      await bookmarkService.deleteBookmark(bookmarkId);
      await loadBookmarks(); // Reload bookmarks
      alert('Bookmark deleted successfully!');
    } catch (error) {
      console.error('Failed to delete bookmark:', error);
      alert('Failed to delete bookmark. Please try again.');
    }
  };

  // Initialize WebSocket connection
  useEffect(() => {
    const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsHost = window.location.hostname;
    const wsPort = process.env.REACT_APP_WS_PORT || '8000';
    const ws = new WebSocket(`${wsProtocol}//${wsHost}:${wsPort}/ws/progress`);
    
    ws.onopen = () => {
      console.log('WebSocket connected');
    };
    
    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.type === 'progress') {
          setProgress(data);
        }
      } catch (e) {
        console.log('WebSocket message:', event.data);
      }
    };
    
    ws.onclose = () => {
      console.log('WebSocket disconnected');
    };
    
    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };
    
    return () => {
      ws.close();
    };
  }, []);

  const handleIdeaGeneration = async (formData: any) => {
    setLastFormData(formData); // Store for retry functionality
    setShowDetailedResults(formData.show_detailed_results || false); // Store the preference
    setIsLoading(true);
    setError(null);
    setResults([]);
    setProgress(null);

    try {
      console.log('Starting idea generation with data:', formData);
      const response = await api.post<ApiResponse>('/api/generate-ideas', formData);
      
      console.log('API response received:', response.status, response.data?.status);
      
      if (response.data.status === 'success') {
        console.log('Setting results:', response.data.results?.length, 'ideas');
        setResults(response.data.results || []);
        
        // Validate that we actually have results
        if (!response.data.results || response.data.results.length === 0) {
          setError('No ideas were generated. Please try with different parameters.');
        }
      } else {
        setError(response.data.message || 'Failed to generate ideas');
      }
    } catch (err: any) {
      console.error('Idea generation error:', err);
      
      let errorMessage = 'An unexpected error occurred';
      
      if (err.code === 'ECONNABORTED' || err.message.includes('timeout')) {
        errorMessage = 'Request timed out. The idea generation is taking longer than expected. Please try with fewer candidates or simpler constraints.';
      } else if (err.response?.status === 408) {
        errorMessage = 'Request timed out after 10 minutes. Please try with fewer candidates or simpler constraints.';
      } else if (err.response?.status >= 500) {
        errorMessage = `Server error (${err.response.status}): ${err.response?.data?.detail || err.response?.data?.error || 'Internal server error'}`;
      } else if (err.response?.data?.detail) {
        if (typeof err.response.data.detail === 'object') {
          errorMessage = `Error: ${err.response.data.detail.error || err.response.data.detail.type || 'Unknown error'}`;
        } else {
          errorMessage = err.response.data.detail;
        }
      } else if (err.message) {
        errorMessage = err.message;
      }
      
      setError(errorMessage);
    } finally {
      setIsLoading(false);
      setProgress(null);
    }
  };

  const handleRetry = () => {
    if (lastFormData) {
      handleIdeaGeneration(lastFormData);
    }
  };

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
                </div>
              </div>
              <button
                onClick={() => setShowBookmarkManager(true)}
                className="relative inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
              >
                <svg className="h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
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
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Left Column - Input Form */}
          <div className="space-y-6">
            <IdeaGenerationForm 
              onSubmit={handleIdeaGeneration}
              isLoading={isLoading}
              savedBookmarks={savedBookmarks}
              onOpenBookmarkManager={() => setShowBookmarkManager(true)}
              selectedBookmarkIds={selectedBookmarkIds}
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
          <div>
            <ResultsDisplay 
              results={results} 
              showDetailedResults={showDetailedResults}
              theme={lastFormData?.theme || ''}
              constraints={lastFormData?.constraints || ''}
              bookmarkedIdeas={bookmarkedIdeas}
              onBookmarkToggle={async (result: IdeaResult, index: number) => {
                try {
                  // Create a unique ID for this result
                  const tempId = `temp-${index}-${Date.now()}`;
                  
                  if (bookmarkedIdeas.has(tempId)) {
                    // TODO: Remove bookmark when we have persistent IDs
                    alert('Bookmark removal coming soon!');
                  } else {
                    // Create bookmark via API
                    const response = await bookmarkService.createBookmark(
                      result, 
                      lastFormData?.theme || 'Unknown Theme',
                      lastFormData?.constraints || ''
                    );
                    
                    if (response.status === 'success' && response.bookmark_id) {
                      setBookmarkedIdeas(new Set([...bookmarkedIdeas, response.bookmark_id]));
                      await loadBookmarks(); // Reload to get the full bookmark data
                      alert('Idea bookmarked successfully!');
                    }
                  }
                } catch (error) {
                  console.error('Bookmark operation failed:', error);
                  alert('Failed to bookmark idea. Please try again.');
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
    </div>
  );
}

export default App;