import React from 'react';
import { LLMMetrics } from '../types';

interface LLMMetricsDisplayProps {
  metrics: LLMMetrics | null;
}

const LLMMetricsDisplay: React.FC<LLMMetricsDisplayProps> = ({ metrics }) => {
  if (!metrics) {
    return null;
  }

  const formatCost = (cost: number): string => {
    if (cost === 0) return 'Free';
    if (cost < 0.01) return `$${(cost * 100).toFixed(4)}¢`;
    return `$${cost.toFixed(4)}`;
  };

  const formatLatency = (ms: number): string => {
    if (ms < 1000) return `${ms.toFixed(0)}ms`;
    return `${(ms / 1000).toFixed(2)}s`;
  };

  const formatPercentage = (rate: number): string => {
    return `${(rate * 100).toFixed(1)}%`;
  };

  return (
    <div className="bg-gray-50 rounded-lg p-4 mt-4">
      <div className="flex items-center mb-3">
        <svg
          className="h-5 w-5 text-gray-600 mr-2"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
          />
        </svg>
        <h3 className="text-sm font-medium text-gray-700">LLM Usage Statistics</h3>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {/* Total Requests */}
        <div className="bg-white rounded p-3 shadow-sm">
          <div className="text-xs text-gray-500 uppercase tracking-wide">Total Requests</div>
          <div className="text-lg font-semibold text-gray-900">{metrics.total_requests}</div>
        </div>

        {/* Provider Usage */}
        <div className="bg-white rounded p-3 shadow-sm">
          <div className="text-xs text-gray-500 uppercase tracking-wide">Provider Usage</div>
          <div className="text-sm">
            <span className="text-green-600 font-medium">Ollama: {metrics.ollama_calls}</span>
            <span className="text-gray-400 mx-1">|</span>
            <span className="text-blue-600 font-medium">Gemini: {metrics.gemini_calls}</span>
          </div>
        </div>

        {/* Cache Performance */}
        <div className="bg-white rounded p-3 shadow-sm">
          <div className="text-xs text-gray-500 uppercase tracking-wide">Cache Hit Rate</div>
          <div className="text-lg font-semibold text-gray-900">
            {formatPercentage(metrics.cache_hit_rate)}
          </div>
          <div className="text-xs text-gray-500">
            {metrics.cache_hits} / {metrics.total_requests} hits
          </div>
        </div>

        {/* Cost */}
        <div className="bg-white rounded p-3 shadow-sm">
          <div className="text-xs text-gray-500 uppercase tracking-wide">Total Cost</div>
          <div className={`text-lg font-semibold ${metrics.total_cost === 0 ? 'text-green-600' : 'text-gray-900'}`}>
            {formatCost(metrics.total_cost)}
          </div>
        </div>

        {/* Tokens Used */}
        <div className="bg-white rounded p-3 shadow-sm">
          <div className="text-xs text-gray-500 uppercase tracking-wide">Tokens Used</div>
          <div className="text-lg font-semibold text-gray-900">
            {metrics.total_tokens.toLocaleString()}
          </div>
        </div>

        {/* Average Latency */}
        <div className="bg-white rounded p-3 shadow-sm">
          <div className="text-xs text-gray-500 uppercase tracking-wide">Avg Latency</div>
          <div className="text-lg font-semibold text-gray-900">
            {formatLatency(metrics.avg_latency_ms)}
          </div>
        </div>
      </div>

      {/* Cost Savings Info */}
      {metrics.ollama_calls > 0 && metrics.total_cost === 0 && (
        <div className="mt-3 text-xs text-green-600 bg-green-50 p-2 rounded">
          💡 Using local Ollama inference saved you money! All {metrics.ollama_calls} requests were processed locally for free.
        </div>
      )}
    </div>
  );
};

export default LLMMetricsDisplay;
