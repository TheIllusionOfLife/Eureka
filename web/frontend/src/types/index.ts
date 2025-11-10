/**
 * Central type definitions for the MadSpark application
 * Re-exports all types from individual type files
 */

// Re-export all type modules
export * from './api.types';
export * from './bookmark.types';
export * from './utils.types';
export * from './hooks.types';

// WebSocket types
export interface ProgressUpdate {
  type: 'progress' | 'connection' | 'error';
  message: string;
  progress?: number;
  timestamp: string;
}

// Application state types
export type ConnectionStatus = 'connecting' | 'connected' | 'disconnected' | 'reconnecting';

// Form types
export interface FormData {
  theme: string;
  constraints: string;
  num_top_candidates: number;
  enable_novelty_filter: boolean;
  novelty_threshold: number;
  temperature_preset: string | null;
  temperature: number | null;
  enhanced_reasoning: boolean;
  multi_dimensional_eval: boolean;
  logical_inference: boolean;
  verbose: boolean;
  show_detailed_results: boolean;
  bookmark_ids?: string[];
  multimodal_urls?: string[];
  multimodal_files?: File[];
}

// Component prop types
export interface WithClassName {
  className?: string;
}

export interface WithChildren {
  children?: React.ReactNode;
}

// Utility types
export type Nullable<T> = T | null;
export type Optional<T> = T | undefined;

// Event handler types
export type ClickHandler = (event: React.MouseEvent<HTMLElement>) => void;
export type FormSubmitHandler = (event: React.FormEvent<HTMLFormElement>) => void;
export type InputChangeHandler = (event: React.ChangeEvent<HTMLInputElement>) => void;
export type TextAreaChangeHandler = (event: React.ChangeEvent<HTMLTextAreaElement>) => void;
export type SelectChangeHandler = (event: React.ChangeEvent<HTMLSelectElement>) => void;