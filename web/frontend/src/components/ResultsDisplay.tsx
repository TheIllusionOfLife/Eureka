import React from 'react';
import { IdeaResult, SavedBookmark } from '../types';
import ResultItem from './ResultItem';

interface ResultsDisplayProps {
  results: IdeaResult[];
  showDetailedResults?: boolean;
  topic?: string;
  context?: string;
  bookmarkedIdeas?: Set<string>;
  onBookmarkToggle?: (result: IdeaResult, index: number) => void;
  savedBookmarks?: SavedBookmark[];
  structuredOutput?: boolean;
}

const ResultsDisplay: React.FC<ResultsDisplayProps> = ({
  results,
  showDetailedResults = false,
  topic = '',
  context = '',
  bookmarkedIdeas,
  onBookmarkToggle,
  savedBookmarks = [],
  structuredOutput = false
}) => {
  if (results.length === 0) {
    return (
      <div className="bg-white shadow rounded-lg p-6">
        <div className="text-center py-12">
          <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
          </svg>
          <h3 className="mt-2 text-sm font-medium text-gray-900">No ideas yet</h3>
          <p className="mt-1 text-sm text-gray-500">
            Fill out the form on the left to generate AI-powered ideas
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white shadow rounded-lg">
      <div className="px-6 py-4 border-b border-gray-200">
        <h2 className="text-lg font-medium text-gray-900">
          Generated Ideas ({results.length})
        </h2>
      </div>

      <div className="divide-y divide-gray-200">
        {results.map((result, index) => (
          <ResultItem
            key={index}
            result={result}
            index={index}
            showDetailedResults={showDetailedResults}
            savedBookmarks={savedBookmarks}
            onBookmarkToggle={onBookmarkToggle}
            structuredOutput={structuredOutput}
          />
        ))}
      </div>
    </div>
  );
};

export default ResultsDisplay;