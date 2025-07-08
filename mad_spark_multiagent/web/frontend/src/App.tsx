import React, { useState, useEffect } from 'react';
import axios from 'axios';
import IdeaGenerationForm from './components/IdeaGenerationForm';
import ResultsDisplay from './components/ResultsDisplay';
import ProgressIndicator from './components/ProgressIndicator';
import './App.css';

export interface IdeaResult {
  idea: string;
  initial_score: number;
  initial_critique: string;
  advocacy: string;
  skepticism: string;
  multi_dimensional_evaluation?: {
    scores: {
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
    setIsLoading(true);
    setError(null);
    setResults([]);
    setProgress(null);

    try {
      // Use environment variable for API URL in Docker/production environments
      const apiUrl = process.env.REACT_APP_API_URL || '';
      const response = await axios.post<ApiResponse>(`${apiUrl}/api/generate-ideas`, formData);
      
      if (response.data.status === 'success') {
        setResults(response.data.results);
      } else {
        setError(response.data.message);
      }
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || err.message || 'An error occurred';
      setError(errorMessage);
    } finally {
      setIsLoading(false);
      setProgress(null);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="py-6">
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
                  <div className="ml-3">
                    <h3 className="text-sm font-medium text-red-800">
                      Error
                    </h3>
                    <div className="mt-2 text-sm text-red-700">
                      <p>{error}</p>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Right Column - Results */}
          <div>
            <ResultsDisplay results={results} />
          </div>
        </div>
      </main>
    </div>
  );
}

export default App;