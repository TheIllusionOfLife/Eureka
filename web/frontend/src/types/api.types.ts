/**
 * TypeScript type definitions for API interactions
 */

import { AxiosRequestConfig, AxiosError } from 'axios';

// Extended Axios request config with retry flag
export interface ExtendedAxiosRequestConfig extends AxiosRequestConfig {
  _retry?: boolean;
}

// API Error response structure
export interface ApiErrorResponse {
  detail?: string | Array<{ msg: string; loc: string[] }>;
  message?: string;
  status?: string;
}

// Extended Axios error with typed response
export type ApiError = AxiosError<ApiErrorResponse> & {
  config: ExtendedAxiosRequestConfig;
};

// Temperature preset structure
export interface TemperaturePreset {
  idea_generation: number;
  evaluation: number;
  advocacy: number;
  skepticism: number;
  description: string;
}

export interface TemperaturePresetsResponse {
  status: 'success' | 'error';
  presets: Record<string, TemperaturePreset>;
  message?: string;
}

// Bookmark API types - moved to bookmark.types.ts for consistency

// Duplicate check API types - moved to bookmark.types.ts

// Idea generation API types
export interface IdeaGenerationRequest {
  topic?: string;  // Primary field (renamed from 'theme') - optional for backward compat
  theme?: string; // Deprecated: backward compatibility (backend accepts both via alias)
  context?: string;  // Primary field (renamed from 'constraints')
  constraints?: string; // Deprecated: backward compatibility (backend accepts both via alias)
  num_top_candidates: number;
  enable_novelty_filter: boolean;
  novelty_threshold: number;
  temperature_preset?: string | null;
  temperature?: number | null;
  enhanced_reasoning: boolean;
  multi_dimensional_eval: boolean;
  logical_inference: boolean;
  verbose: boolean;
  show_detailed_results: boolean;
  bookmark_ids?: string[];
  multimodal_urls?: string[];
  // LLM Router configuration fields
  llm_provider?: 'auto' | 'ollama' | 'gemini';
  model_tier?: 'fast' | 'balanced' | 'quality';
  use_llm_cache?: boolean;
}

export interface MultiDimensionalEvaluation {
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
}

// Logical inference analysis structure based on InferenceResult
export interface LogicalInferenceResult {
  inference_chain: string[];
  conclusion: string;
  confidence: number;
  improvements?: string;
  // Analysis-specific fields
  causal_chain?: string[];
  feedback_loops?: string[];
  root_cause?: string;
  constraint_satisfaction?: Record<string, number>;
  overall_satisfaction?: number;
  trade_offs?: string[];
  contradictions?: Array<Record<string, any>>;
  resolution?: string;
  implications?: string[];
  second_order_effects?: string[];
  error?: string;
}

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
  multi_dimensional_evaluation?: MultiDimensionalEvaluation;
  improved_multi_dimensional_evaluation?: MultiDimensionalEvaluation;
  logical_inference?: LogicalInferenceResult;
}

// LLM Provider types (defined here to avoid circular dependency)
export type LLMProvider = 'auto' | 'ollama' | 'gemini';
export type ModelTier = 'fast' | 'balanced' | 'quality';

export interface LLMMetrics {
  total_requests: number;
  cache_hits: number;
  ollama_calls: number;
  gemini_calls: number;
  total_tokens: number;
  total_cost: number;
  cache_hit_rate: number;
  avg_latency_ms: number;
  fallback_triggers: number;
}

export interface LLMProviderHealth {
  available: boolean;
  latency_ms?: number;
  error?: string;
}

export interface LLMHealthStatus {
  ollama: LLMProviderHealth;
  gemini: LLMProviderHealth;
}

export interface IdeaGenerationResponse {
  status: 'success' | 'error';
  message: string;
  results: IdeaResult[];
  processing_time: number;
  timestamp: string;
  structured_output?: boolean;  // Indicates if ideas are using structured output (no cleaning needed)
  llm_metrics?: LLMMetrics;  // LLM router usage metrics (tokens, cost, cache hits, etc.)
}