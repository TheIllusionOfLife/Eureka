/**
 * Bookmark-related type definitions for the MadSpark application
 */

// Core bookmark data structures
export interface BookmarkData {
  idea: string;
  improved_idea?: string;
  topic: string;  // Renamed from 'theme' to 'topic'
  theme?: string; // Deprecated: backward compatibility
  constraints: string;
  initial_score: number;
  improved_score?: number;
  initial_critique: string;
  improved_critique?: string;
  advocacy: string;
  skepticism: string;
  tags: string[];
  notes?: string;
}

export interface SavedBookmark {
  id: string;
  text: string;
  topic: string;  // Renamed from 'theme' to 'topic'
  theme?: string; // Deprecated: backward compatibility
  constraints: string;
  score: number;
  critique: string;
  advocacy: string;
  skepticism: string;
  bookmarked_at: string;
  tags: string[];
}

// API response types
export interface BookmarkResponse {
  status: string;
  message: string;
  bookmark_id?: string;
}

export interface BookmarksListResponse {
  status: string;
  bookmarks: SavedBookmark[];
  count: number;
}

// Duplicate detection types
export interface SimilarBookmark {
  id: string;
  text: string;
  topic: string;  // Renamed from 'theme' to 'topic'
  theme?: string; // Deprecated: backward compatibility
  similarity_score: number;
  bookmarked_at?: string;
  // Backend returns both, handling both field names for compatibility
  match_type?: string;
  similarity_type?: 'exact' | 'high' | 'moderate' | 'low';
  matched_features?: string[];
}

export interface DuplicateCheckResponse {
  status: string;
  has_duplicates: boolean;
  similar_count: number;
  recommendation: 'block' | 'warn' | 'notice' | 'allow';
  similarity_threshold: number;
  similar_bookmarks: SimilarBookmark[];
  message: string;
}

export interface EnhancedBookmarkResponse {
  status: string;
  message: string;
  bookmark_id?: string;
  bookmark_created: boolean;
  duplicate_check?: {
    has_duplicates: boolean;
    similar_count: number;
    recommendation: string;
    similarity_threshold: number;
  };
  similar_bookmarks: SimilarBookmark[];
}

// Bookmark service input types
export interface CreateBookmarkInput {
  idea: string;
  improved_idea?: string;
  evaluation: string;
  scores: Record<string, number>;
  topic: string;  // Renamed from 'theme' to 'topic'
  theme?: string; // Deprecated: backward compatibility
  constraints: string;
  force_save?: boolean;
}

export interface CheckDuplicatesInput {
  text: string;
  topic: string;  // Renamed from 'theme' to 'topic'
  theme?: string; // Deprecated: backward compatibility
}