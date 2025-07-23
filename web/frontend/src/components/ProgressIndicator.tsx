import React from 'react';
import { ProgressUpdate } from '../types';

interface ProgressIndicatorProps {
  progress: ProgressUpdate | null;
  isLoading: boolean;
}

const ProgressIndicator: React.FC<ProgressIndicatorProps> = ({ progress, isLoading }) => {
  const getProgressPercentage = () => {
    if (progress && progress.progress !== undefined) {
      return Math.round(progress.progress * 100);
    }
    return 0;
  };

  const getProgressMessage = () => {
    if (progress) {
      return progress.message;
    }
    if (isLoading) {
      return "Initializing...";
    }
    return "";
  };

  if (!isLoading && !progress) {
    return null;
  }

  return (
    <div className="bg-white shadow rounded-lg p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-medium text-gray-900">
          🚀 Generating Ideas
        </h3>
        <span className="text-sm text-gray-500">
          {getProgressPercentage()}%
        </span>
      </div>

      {/* Progress Bar */}
      <div className="w-full bg-gray-200 rounded-full h-2.5 mb-4">
        <div 
          className="bg-blue-600 h-2.5 rounded-full progress-bar transition-all duration-300 ease-out"
          style={{ width: `${getProgressPercentage()}%` }}
        ></div>
      </div>

      {/* Progress Message */}
      <div className="flex items-center space-x-3">
        {isLoading && (
          <div className="flex-shrink-0">
            <svg className="animate-spin h-5 w-5 text-blue-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
          </div>
        )}
        <div className="flex-1">
          <p className="text-sm text-gray-700">
            {getProgressMessage()}
          </p>
          {progress && progress.timestamp && (
            <p className="text-xs text-gray-500 mt-1">
              {new Date(progress.timestamp).toLocaleTimeString()}
            </p>
          )}
        </div>
      </div>

      {/* Progress Steps */}
      <div className="mt-6 space-y-2">
        <div className="flex items-center text-sm">
          <div className={`flex-shrink-0 w-4 h-4 rounded-full mr-3 ${
            getProgressPercentage() > 10 ? 'bg-green-500' : 'bg-gray-300'
          }`}>
            {getProgressPercentage() > 10 && (
              <svg className="w-4 h-4 text-white" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
              </svg>
            )}
          </div>
          <span className={getProgressPercentage() > 10 ? 'text-gray-900' : 'text-gray-500'}>
            Initialize workflow
          </span>
        </div>

        <div className="flex items-center text-sm">
          <div className={`flex-shrink-0 w-4 h-4 rounded-full mr-3 ${
            getProgressPercentage() > 40 ? 'bg-green-500' : 'bg-gray-300'
          }`}>
            {getProgressPercentage() > 40 && (
              <svg className="w-4 h-4 text-white" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
              </svg>
            )}
          </div>
          <span className={getProgressPercentage() > 40 ? 'text-gray-900' : 'text-gray-500'}>
            Generate initial ideas
          </span>
        </div>

        <div className="flex items-center text-sm">
          <div className={`flex-shrink-0 w-4 h-4 rounded-full mr-3 ${
            getProgressPercentage() > 70 ? 'bg-green-500' : 'bg-gray-300'
          }`}>
            {getProgressPercentage() > 70 && (
              <svg className="w-4 h-4 text-white" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
              </svg>
            )}
          </div>
          <span className={getProgressPercentage() > 70 ? 'text-gray-900' : 'text-gray-500'}>
            Evaluate and refine
          </span>
        </div>

        <div className="flex items-center text-sm">
          <div className={`flex-shrink-0 w-4 h-4 rounded-full mr-3 ${
            getProgressPercentage() >= 100 ? 'bg-green-500' : 'bg-gray-300'
          }`}>
            {getProgressPercentage() >= 100 && (
              <svg className="w-4 h-4 text-white" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
              </svg>
            )}
          </div>
          <span className={getProgressPercentage() >= 100 ? 'text-gray-900' : 'text-gray-500'}>
            Complete analysis
          </span>
        </div>
      </div>
    </div>
  );
};

export default ProgressIndicator;