import { IdeaResult } from '../App';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://127.0.0.1:8000';

export interface BookmarkData {
  idea: string;
  improved_idea?: string;
  theme: string;
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
  theme: string;
  constraints: string;
  score: number;
  critique: string;
  advocacy: string;
  skepticism: string;
  bookmarked_at: string;
  tags: string[];
}

export interface BookmarkResponse {
  status: string;
  message: string;
  bookmark_id?: string;
}

export interface SimilarBookmark {
  id: string;
  text: string;
  theme: string;
  similarity_score: number;
  match_type: string;
  matched_features: string[];
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

export interface BookmarksListResponse {
  status: string;
  bookmarks: SavedBookmark[];
  count: number;
}

class BookmarkService {
  async checkForDuplicates(idea: string, theme: string, similarityThreshold?: number): Promise<DuplicateCheckResponse> {
    try {
      const requestData = {
        idea: idea,
        topic: theme,  // Using new terminology
        similarity_threshold: similarityThreshold
      };

      const response = await fetch(`${API_BASE_URL}/api/bookmarks/check-duplicates`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestData),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => null);
        const errorMessage = errorData?.detail || response.statusText;
        throw new Error(`Failed to check duplicates: ${errorMessage}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error checking duplicates:', error);
      throw error;
    }
  }

  async createBookmarkWithDuplicateCheck(
    result: IdeaResult, 
    theme: string, 
    constraints: string,
    forceSave: boolean = false
  ): Promise<EnhancedBookmarkResponse> {
    try {
      console.log('Creating bookmark with duplicate check:', { result, theme, constraints, forceSave });
      
      // Ensure all required fields meet minimum requirements
      const bookmarkData: BookmarkData = {
        idea: result.idea || 'No idea text provided',
        improved_idea: result.improved_idea || undefined,
        theme: theme || 'General',
        constraints: constraints ?? '',
        initial_score: result.initial_score ?? 0,
        improved_score: result.improved_score ?? undefined,
        initial_critique: result.initial_critique || '',
        improved_critique: result.improved_critique || undefined,
        advocacy: result.advocacy || '',
        skepticism: result.skepticism || '',
        tags: [],
      };

      // Add duplicate check parameters
      const url = new URL(`${API_BASE_URL}/api/bookmarks`);
      url.searchParams.append('check_duplicates', 'true');
      if (forceSave) {
        url.searchParams.append('force_save', 'true');
      }

      const response = await fetch(url.toString(), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(bookmarkData),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => null);
        const errorMessage = errorData?.detail || response.statusText;
        console.error('Full error response:', errorData);
        throw new Error(`Failed to create bookmark: ${errorMessage}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error creating bookmark with duplicate check:', error);
      throw error;
    }
  }

  async findSimilarBookmarks(idea: string, theme: string, maxResults: number = 5): Promise<{
    status: string;
    similar_bookmarks: SimilarBookmark[];
    total_found: number;
    search_idea: string;
  }> {
    try {
      const url = new URL(`${API_BASE_URL}/api/bookmarks/similar`);
      url.searchParams.append('idea', idea);
      url.searchParams.append('theme', theme);
      url.searchParams.append('max_results', maxResults.toString());

      const response = await fetch(url.toString());

      if (!response.ok) {
        const errorData = await response.json().catch(() => null);
        const errorMessage = errorData?.detail || response.statusText;
        throw new Error(`Failed to find similar bookmarks: ${errorMessage}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error finding similar bookmarks:', error);
      throw error;
    }
  }

  async createBookmark(result: IdeaResult, theme: string, constraints: string): Promise<BookmarkResponse> {
    try {
      console.log('Creating bookmark with:', { result, theme, constraints });
      
      // Ensure all required fields meet minimum requirements
      const bookmarkData: BookmarkData = {
        idea: result.idea || 'No idea text provided',  // Required field with min_length - handle empty strings
        improved_idea: result.improved_idea || undefined,  // Optional field - handle empty strings as undefined
        theme: theme || 'General',  // Required field with min_length - handle empty strings
        constraints: constraints ?? '',  // Allows empty strings - only handle null/undefined
        initial_score: result.initial_score ?? 0,  // Numeric field - preserve 0, handle null/undefined
        improved_score: result.improved_score ?? undefined,  // Numeric field - preserve 0, handle null/undefined
        initial_critique: result.initial_critique || '',  // Optional field, sent as empty string if falsy
        improved_critique: result.improved_critique || undefined,  // Optional field - handle empty strings as undefined
        advocacy: result.advocacy || '',  // Optional field, sent as empty string if falsy
        skepticism: result.skepticism || '',  // Optional field, sent as empty string if falsy
        tags: [], // Can be enhanced to allow user-defined tags
      };

      // Log bookmark data for debugging purposes before sending to the API.
      console.log('Bookmark data to be sent:', JSON.stringify(bookmarkData, null, 2));

      const response = await fetch(`${API_BASE_URL}/api/bookmarks`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(bookmarkData),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => null);
        const errorMessage = errorData?.detail || response.statusText;
        console.error('Full error response:', errorData);
        throw new Error(`Failed to create bookmark: ${errorMessage}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error creating bookmark:', error);
      throw error;
    }
  }

  async getBookmarks(tags?: string[]): Promise<SavedBookmark[]> {
    try {
      const url = new URL(`${API_BASE_URL}/api/bookmarks`);
      if (tags && tags.length > 0) {
        url.searchParams.append('tags', tags.join(','));
      }

      const response = await fetch(url.toString());

      if (!response.ok) {
        throw new Error(`Failed to fetch bookmarks: ${response.statusText}`);
      }

      const data: BookmarksListResponse = await response.json();
      return data.bookmarks;
    } catch (error) {
      console.error('Error fetching bookmarks:', error);
      throw error;
    }
  }

  async deleteBookmark(bookmarkId: string): Promise<void> {
    try {
      const response = await fetch(`${API_BASE_URL}/api/bookmarks/${bookmarkId}`, {
        method: 'DELETE',
      });

      if (!response.ok) {
        throw new Error(`Failed to delete bookmark: ${response.statusText}`);
      }
    } catch (error) {
      console.error('Error deleting bookmark:', error);
      throw error;
    }
  }
}

export const bookmarkService = new BookmarkService();