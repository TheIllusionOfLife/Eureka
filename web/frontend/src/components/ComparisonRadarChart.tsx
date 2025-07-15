import React from 'react';
import {
  Radar,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  ResponsiveContainer,
  Tooltip,
  Legend
} from 'recharts';

interface ComparisonData {
  dimension: string;
  original: number;
  improved: number;
  fullMark: number;
}

interface ComparisonRadarChartProps {
  data: ComparisonData[];
  title?: string;
  originalLabel?: string;
  improvedLabel?: string;
  /** Override calculated original score with actual API score */
  originalScore?: number;
  /** Override calculated improved score with actual API score */
  improvedScore?: number;
}

const ComparisonRadarChart: React.FC<ComparisonRadarChartProps> = ({ 
  data, 
  title, 
  originalLabel = "Original Idea",
  improvedLabel = "Improved Idea",
  originalScore,
  improvedScore
}) => {
  // Custom tooltip to show both scores
  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className="bg-white p-3 border border-gray-200 rounded shadow-lg">
          <p className="font-semibold text-gray-800 mb-2">{data.dimension}</p>
          <div className="space-y-1">
            <p className="text-blue-600 text-sm">
              <span className="inline-block w-3 h-3 bg-blue-500 rounded-full mr-2"></span>
              {originalLabel}: {data.original}/10
            </p>
            <p className="text-green-600 text-sm">
              <span className="inline-block w-3 h-3 bg-green-500 rounded-full mr-2"></span>
              {improvedLabel}: {data.improved}/10
            </p>
            <p className="text-xs text-gray-600 mt-2">
              Improvement: {data.improved > data.original ? '+' : ''}{(data.improved - data.original).toFixed(1)}
            </p>
          </div>
          <p className="text-xs text-gray-500 mt-2 pt-2 border-t">
            {getDimensionDescription(data.dimension)}
          </p>
        </div>
      );
    }
    return null;
  };

  // Get dimension descriptions
  const getDimensionDescription = (dimension: string): string => {
    const descriptions: { [key: string]: string } = {
      'Feasibility': 'How realistic is implementation',
      'Innovation': 'How novel and creative is the idea',
      'Impact': 'Potential positive impact',
      'Cost Effectiveness': 'Cost vs benefit ratio',
      'Scalability': 'Ability to scale up',
      'Risk Assessment': 'Risk level (higher score = lower risk)',
      'Timeline': 'Implementation timeline feasibility'
    };
    return descriptions[dimension] || '';
  };

  // Calculate overall scores (use provided scores if available, otherwise calculate from data)
  const calculatedOriginalScore = data.length > 0 ? data.reduce((sum, item) => sum + item.original, 0) / data.length : 0;
  const calculatedImprovedScore = data.length > 0 ? data.reduce((sum, item) => sum + item.improved, 0) / data.length : 0;
  
  // Validate and use override scores with range checking
  const isValidScore = (score: number | undefined): boolean => 
    score !== undefined && score !== null && score >= 0 && score <= 10 && isFinite(score);
  
  const finalOriginalScore = isValidScore(originalScore) ? originalScore! : calculatedOriginalScore;
  const finalImprovedScore = isValidScore(improvedScore) ? improvedScore! : calculatedImprovedScore;
  const improvement = finalImprovedScore - finalOriginalScore;
  
  const getScoreColor = (score: number) => 
    score >= 7 ? 'text-green-600' : score >= 5 ? 'text-yellow-600' : 'text-red-600';

  // Fix division by zero error - show 100% if improving from 0
  const improvementPercentage = finalOriginalScore > 0 
    ? ((improvement / finalOriginalScore) * 100) 
    : improvement > 0 ? 100 : 0;

  // Handle empty data case
  if (data.length === 0) {
    return (
      <div className="bg-white p-4 rounded-lg shadow">
        {title && (
          <div className="mb-4">
            <h3 className="text-lg font-semibold text-gray-900">{title}</h3>
          </div>
        )}
        <div className="flex items-center justify-center h-64 text-gray-500">
          <div className="text-center">
            <p className="text-lg mb-2">No evaluation data available</p>
            <p className="text-sm">Multi-dimensional evaluation comparison will appear here when available.</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white p-4 rounded-lg shadow">
      {title && (
        <div className="mb-4">
          <h3 className="text-lg font-semibold text-gray-900">{title}</h3>
          <div className="flex items-center space-x-6 mt-2">
            <p className={`text-sm ${getScoreColor(finalOriginalScore)} font-medium`}>
              {originalLabel}: {finalOriginalScore.toFixed(1)}/10
            </p>
            <p className={`text-sm ${getScoreColor(finalImprovedScore)} font-medium`}>
              {improvedLabel}: {finalImprovedScore.toFixed(1)}/10
            </p>
            <p className={`text-sm font-semibold ${improvement >= 0 ? 'text-green-600' : 'text-red-600'}`}>
              {improvement >= 0 ? '+' : ''}{improvement.toFixed(1)} improvement
            </p>
          </div>
        </div>
      )}
      
      <ResponsiveContainer width="100%" height={400}>
        <RadarChart data={data}>
          <PolarGrid 
            gridType="polygon"
            stroke="#e5e7eb"
            radialLines={true}
          />
          <PolarAngleAxis 
            dataKey="dimension"
            tick={{ fontSize: 12 }}
            className="text-gray-600"
          />
          <PolarRadiusAxis
            angle={90}
            domain={[0, 10]}
            tickCount={6}
            tick={{ fontSize: 10 }}
            axisLine={false}
          />
          
          {/* Original idea radar */}
          <Radar
            name={originalLabel}
            dataKey="original"
            stroke="#3b82f6"
            fill="#3b82f6"
            fillOpacity={0.3}
            strokeWidth={2}
            strokeDasharray="5 5"
          />
          
          {/* Improved idea radar */}
          <Radar
            name={improvedLabel}
            dataKey="improved"
            stroke="#10b981"
            fill="#10b981"
            fillOpacity={0.3}
            strokeWidth={3}
          />
          
          <Tooltip content={<CustomTooltip />} />
          <Legend 
            wrapperStyle={{ paddingTop: '20px' }}
            iconType="circle"
          />
        </RadarChart>
      </ResponsiveContainer>

      {/* Detailed comparison table */}
      <div className="mt-6">
        <h4 className="text-sm font-semibold text-gray-700 mb-3">Detailed Comparison</h4>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-sm">
          {data.map((item, index) => {
            const improvement = item.improved - item.original;
            return (
              <div key={index} className="flex items-center justify-between p-2 bg-gray-50 rounded">
                <span className="text-gray-700 font-medium">{item.dimension}:</span>
                <div className="flex items-center space-x-3">
                  <span className="text-blue-600">{item.original}</span>
                  <span className="text-gray-400">→</span>
                  <span className="text-green-600 font-semibold">{item.improved}</span>
                  <span className={`text-xs px-2 py-1 rounded ${
                    improvement > 0 ? 'bg-green-100 text-green-700' : 
                    improvement < 0 ? 'bg-red-100 text-red-700' : 'bg-gray-100 text-gray-700'
                  }`}>
                    {improvement > 0 ? '+' : ''}{improvement.toFixed(1)}
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Summary stats */}
      <div className="mt-4 p-3 bg-blue-50 rounded-lg">
        <div className="flex items-center justify-between text-sm">
          <span className="text-gray-700">Overall Improvement:</span>
          <div className="flex items-center space-x-2">
            <span className="text-blue-600">{finalOriginalScore.toFixed(1)}/10</span>
            <span className="text-gray-400">→</span>
            <span className="text-green-600 font-semibold">{finalImprovedScore.toFixed(1)}/10</span>
            <span className={`px-2 py-1 rounded text-xs font-semibold ${
              improvement >= 0 ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
            }`}>
              {improvementPercentage.toFixed(1)}% improvement
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ComparisonRadarChart;