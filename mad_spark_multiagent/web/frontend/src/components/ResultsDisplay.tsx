import React, { useState } from 'react';
import { IdeaResult } from '../App';
import RadarChartComponent from './RadarChart';

interface ResultsDisplayProps {
  results: IdeaResult[];
}

const ResultsDisplay: React.FC<ResultsDisplayProps> = ({ results }) => {
  const [selectedTab, setSelectedTab] = useState<number>(0);
  const [expandedSections, setExpandedSections] = useState<{[key: string]: boolean}>({});

  const toggleSection = (ideaIndex: number, section: string) => {
    const key = `${ideaIndex}-${section}`;
    setExpandedSections(prev => ({
      ...prev,
      [key]: !prev[key]
    }));
  };

  const getScoreColor = (score: number) => {
    if (score >= 8) return 'bg-green-500';
    if (score >= 6) return 'bg-yellow-500';
    if (score >= 4) return 'bg-orange-500';
    return 'bg-red-500';
  };

  const getScoreLabel = (score: number) => {
    if (score >= 8) return 'Excellent';
    if (score >= 6) return 'Good';
    if (score >= 4) return 'Fair';
    return 'Needs Work';
  };

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
          <div key={index} className="p-6 fade-in">
            {/* Idea Header */}
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <h3 className="text-lg font-medium text-gray-900 mb-2">
                  💡 Idea #{index + 1}
                </h3>
                <p className="text-gray-700 mb-4 leading-relaxed">
                  {result.idea}
                </p>
              </div>
              
              {/* Score Badge */}
              <div className="ml-4 flex-shrink-0">
                <div className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium text-white ${getScoreColor(result.initial_score)}`}>
                  <span className="mr-1">⭐</span>
                  {result.initial_score}/10
                </div>
                <div className="text-xs text-gray-500 mt-1 text-center">
                  {getScoreLabel(result.initial_score)}
                </div>
              </div>
            </div>

            {/* Expandable Sections */}
            <div className="space-y-3">
              {/* Initial Critique */}
              <div className="border rounded-lg">
                <button
                  type="button"
                  onClick={() => toggleSection(index, 'critique')}
                  className="w-full px-4 py-3 text-left flex items-center justify-between hover:bg-gray-50 transition-colors"
                  aria-expanded={expandedSections[`${index}-critique`]}
                  aria-controls={`critique-content-${index}`}
                >
                  <span className="font-medium text-gray-900">
                    🔍 Initial Critique
                  </span>
                  <svg
                    className={`h-5 w-5 text-gray-500 transition-transform ${
                      expandedSections[`${index}-critique`] ? 'rotate-180' : ''
                    }`}
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                    aria-label="Toggle initial critique section"
                  >
                    <title>Toggle initial critique section</title>
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                  </svg>
                </button>
                {expandedSections[`${index}-critique`] && (
                  <div id={`critique-content-${index}`} className="px-4 pb-3 text-gray-700 critique-text">
                    {result.initial_critique}
                  </div>
                )}
              </div>

              {/* Advocacy */}
              <div className="border rounded-lg">
                <button
                  type="button"
                  onClick={() => toggleSection(index, 'advocacy')}
                  className="w-full px-4 py-3 text-left flex items-center justify-between hover:bg-gray-50 transition-colors"
                  aria-expanded={expandedSections[`${index}-advocacy`]}
                  aria-controls={`advocacy-content-${index}`}
                >
                  <span className="font-medium text-gray-900">
                    ✅ Advocacy
                  </span>
                  <svg
                    className={`h-5 w-5 text-gray-500 transition-transform ${
                      expandedSections[`${index}-advocacy`] ? 'rotate-180' : ''
                    }`}
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                    aria-label="Toggle advocacy section"
                  >
                    <title>Toggle advocacy section</title>
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                  </svg>
                </button>
                {expandedSections[`${index}-advocacy`] && (
                  <div id={`advocacy-content-${index}`} className="px-4 pb-3 text-gray-700 critique-text">
                    {result.advocacy}
                  </div>
                )}
              </div>

              {/* Skepticism */}
              <div className="border rounded-lg">
                <button
                  type="button"
                  onClick={() => toggleSection(index, 'skepticism')}
                  className="w-full px-4 py-3 text-left flex items-center justify-between hover:bg-gray-50 transition-colors"
                  aria-expanded={expandedSections[`${index}-skepticism`]}
                  aria-controls={`skepticism-content-${index}`}
                >
                  <span className="font-medium text-gray-900">
                    ⚠️ Skeptical Analysis
                  </span>
                  <svg
                    className={`h-5 w-5 text-gray-500 transition-transform ${
                      expandedSections[`${index}-skepticism`] ? 'rotate-180' : ''
                    }`}
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                    aria-label="Toggle skeptical analysis section"
                  >
                    <title>Toggle skeptical analysis section</title>
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                  </svg>
                </button>
                {expandedSections[`${index}-skepticism`] && (
                  <div id={`skepticism-content-${index}`} className="px-4 pb-3 text-gray-700 critique-text">
                    {result.skepticism}
                  </div>
                )}
              </div>

              {/* Multi-dimensional Evaluation */}
              {result.multi_dimensional_evaluation && (
                <div className="border rounded-lg">
                  <button
                    type="button"
                    onClick={() => toggleSection(index, 'multidim')}
                    className="w-full px-4 py-3 text-left flex items-center justify-between hover:bg-gray-50 transition-colors"
                  >
                    <span className="font-medium text-gray-900">
                      📊 Multi-Dimensional Evaluation
                    </span>
                    <svg
                      className={`h-5 w-5 text-gray-500 transition-transform ${
                        expandedSections[`${index}-multidim`] ? 'rotate-180' : ''
                      }`}
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                      aria-label="Toggle multi-dimensional evaluation section"
                    >
                      <title>Toggle multi-dimensional evaluation section</title>
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                    </svg>
                  </button>
                  {expandedSections[`${index}-multidim`] && (
                    <div className="p-4">
                      <RadarChartComponent
                        data={[
                          { dimension: 'Feasibility', score: result.multi_dimensional_evaluation.scores.feasibility, fullMark: 10 },
                          { dimension: 'Innovation', score: result.multi_dimensional_evaluation.scores.innovation, fullMark: 10 },
                          { dimension: 'Impact', score: result.multi_dimensional_evaluation.scores.impact, fullMark: 10 },
                          { dimension: 'Cost Effectiveness', score: result.multi_dimensional_evaluation.scores.cost_effectiveness, fullMark: 10 },
                          { dimension: 'Scalability', score: result.multi_dimensional_evaluation.scores.scalability, fullMark: 10 },
                          { dimension: 'Risk Assessment', score: result.multi_dimensional_evaluation.scores.risk_assessment, fullMark: 10 },
                          { dimension: 'Timeline', score: result.multi_dimensional_evaluation.scores.timeline, fullMark: 10 }
                        ]}
                      />
                      <div className="mt-3 text-sm text-gray-600">
                        <p>
                          <strong>Overall Score:</strong> {result.multi_dimensional_evaluation.overall_score.toFixed(1)}/10
                        </p>
                        <p>
                          <strong>Confidence Interval:</strong> {result.multi_dimensional_evaluation.confidence_interval.lower.toFixed(1)} - {result.multi_dimensional_evaluation.confidence_interval.upper.toFixed(1)}
                        </p>
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>

            {/* Action Buttons */}
            <div className="mt-4 flex space-x-3">
              <button className="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500">
                <svg className="h-4 w-4 mr-1.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z" />
                </svg>
                Bookmark
              </button>
              
              <button className="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500">
                <svg className="h-4 w-4 mr-1.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.684 13.342C8.886 12.938 9 12.482 9 12c0-.482-.114-.938-.316-1.342m0 2.684a3 3 0 110-2.684m0 2.684l6.632 3.316m-6.632-6l6.632-3.316m0 0a3 3 0 105.367-2.684 3 3 0 00-5.367 2.684zm0 9.316a3 3 0 105.367 2.684 3 3 0 00-5.367-2.684z" />
                </svg>
                Share
              </button>
              
              <button className="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500">
                <svg className="h-4 w-4 mr-1.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
                Export
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default ResultsDisplay;