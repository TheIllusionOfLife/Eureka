import React from 'react';
import {
  Radar,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  ResponsiveContainer,
  Tooltip
} from 'recharts';

interface RadarChartProps {
  data: {
    dimension: string;
    score: number;
    fullMark: number;
  }[];
  title?: string;
}

const RadarChartComponent: React.FC<RadarChartProps> = ({ data, title }) => {
  // Custom tooltip to show dimension details
  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className="bg-white p-3 border border-gray-200 rounded shadow-lg">
          <p className="font-semibold text-gray-800">{data.dimension}</p>
          <p className="text-blue-600">Score: {data.score}/10</p>
          <p className="text-xs text-gray-500 mt-1">{getDimensionDescription(data.dimension)}</p>
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

  // Calculate overall score (handle empty data)
  const overallScore = data.length > 0 ? data.reduce((sum, item) => sum + item.score, 0) / data.length : 0;
  const scoreColor = overallScore >= 7 ? 'text-green-600' : overallScore >= 5 ? 'text-yellow-600' : 'text-red-600';

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
            <p className="text-sm">Multi-dimensional evaluation will appear here when available.</p>
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
          <p className={`text-sm ${scoreColor} font-medium`}>
            Overall Score: {overallScore.toFixed(1)}/10
          </p>
        </div>
      )}
      
      <ResponsiveContainer width="100%" height={300}>
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
          <Radar
            name="Score"
            dataKey="score"
            stroke="#3b82f6"
            fill="#3b82f6"
            fillOpacity={0.6}
            strokeWidth={2}
          />
          <Tooltip content={<CustomTooltip />} />
        </RadarChart>
      </ResponsiveContainer>

      {/* Legend with scores */}
      <div className="mt-4 grid grid-cols-2 gap-2 text-sm">
        {data.map((item, index) => (
          <div key={index} className="flex items-center justify-between">
            <span className="text-gray-600">{item.dimension}:</span>
            <span className="font-medium text-gray-900 ml-2">{item.score}/10</span>
          </div>
        ))}
      </div>
    </div>
  );
};

export default RadarChartComponent;