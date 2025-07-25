import React from 'react';
import { MAX_IDEA_SCORE } from '../constants';

interface ScoreComparisonProps {
  originalScore: number;
  improvedScore: number;
  delta: number;
}

const ScoreComparison: React.FC<ScoreComparisonProps> = ({ originalScore, improvedScore, delta }) => {
  const maxScore = MAX_IDEA_SCORE;
  const safeOriginalScore = originalScore || 0;
  const safeImprovedScore = improvedScore || 0;
  const safeDelta = delta || 0;
  const originalPercentage = (safeOriginalScore / maxScore) * 100;
  const improvedPercentage = (safeImprovedScore / maxScore) * 100;
  
  const getDeltaColor = () => {
    if (safeDelta > 0) return 'text-green-600';
    if (safeDelta < 0) return 'text-red-600';
    return 'text-gray-600';
  };
  
  const getDeltaSymbol = () => {
    if (safeDelta > 0) return '↑';
    if (safeDelta < 0) return '↓';
    return '—';
  };

  return (
    <div className="mt-4 p-4 bg-gray-50 rounded-lg">
      <h4 className="text-sm font-medium text-gray-700 mb-3">Score Comparison</h4>
      
      {/* Score bars */}
      <div className="space-y-3">
        {/* Original score */}
        <div>
          <div className="flex justify-between text-sm mb-1">
            <span className="text-gray-600">Original</span>
            <span className="font-medium">{safeOriginalScore.toFixed(1)}/10</span>
          </div>
          <div className="h-6 bg-gray-200 rounded-full overflow-hidden">
            <div 
              className="h-full bg-blue-500 transition-all duration-500 ease-out"
              style={{ width: `${originalPercentage}%` }}
            />
          </div>
        </div>
        
        {/* Improved score */}
        <div>
          <div className="flex justify-between text-sm mb-1">
            <span className="text-gray-600">Improved</span>
            <span className="font-medium">{safeImprovedScore.toFixed(1)}/10</span>
          </div>
          <div className="h-6 bg-gray-200 rounded-full overflow-hidden">
            <div 
              className="h-full bg-green-500 transition-all duration-500 ease-out"
              style={{ width: `${improvedPercentage}%` }}
            />
          </div>
        </div>
      </div>
      
      {/* Delta indicator */}
      <div className="mt-3 text-center">
        <span className={`text-lg font-semibold ${getDeltaColor()}`}>
          {getDeltaSymbol()} {safeDelta > 0 ? '+' : ''}{safeDelta.toFixed(1)} points
        </span>
        {safeDelta > 0 && safeOriginalScore > 0 && (
          <p className="text-sm text-gray-600 mt-1">
            {((safeDelta / safeOriginalScore) * 100).toFixed(0)}% improvement
          </p>
        )}
      </div>
    </div>
  );
};

export default ScoreComparison;