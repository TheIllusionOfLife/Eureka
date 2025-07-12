import React from 'react';

interface ScoreComparisonProps {
  originalScore: number;
  improvedScore: number;
  delta: number;
}

const ScoreComparison: React.FC<ScoreComparisonProps> = ({ originalScore, improvedScore, delta }) => {
  const maxScore = 10;
  const originalPercentage = (originalScore / maxScore) * 100;
  const improvedPercentage = (improvedScore / maxScore) * 100;
  
  const getDeltaColor = () => {
    if (delta > 0) return 'text-green-600';
    if (delta < 0) return 'text-red-600';
    return 'text-gray-600';
  };
  
  const getDeltaSymbol = () => {
    if (delta > 0) return '↑';
    if (delta < 0) return '↓';
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
            <span className="font-medium">{originalScore.toFixed(1)}/10</span>
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
            <span className="font-medium">{improvedScore.toFixed(1)}/10</span>
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
          {getDeltaSymbol()} {delta > 0 ? '+' : ''}{delta.toFixed(1)} points
        </span>
        {delta > 0 && (
          <p className="text-sm text-gray-600 mt-1">
            {((delta / originalScore) * 100).toFixed(0)}% improvement
          </p>
        )}
      </div>
    </div>
  );
};

export default ScoreComparison;