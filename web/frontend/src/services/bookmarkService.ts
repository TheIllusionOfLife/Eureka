import { 
  IdeaResult,
  BookmarkData,
  SavedBookmark,
  BookmarkResponse,
  SimilarBookmark,
  DuplicateCheckResponse,
  EnhancedBookmarkResponse,
  BookmarksListResponse
} from '../types';
import { truncateField, truncateRequiredField, mapBookmarkToApiFormat } from '../utils/bookmarkHelpers';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://127.0.0.1:8000';

class BookmarkService {
  async checkForDuplicates(idea: string, theme: string, similarityThreshold?: number): Promise<DuplicateCheckResponse> {
    try {
      const requestData = {
        idea: truncateRequiredField(idea),
        topic: truncateRequiredField(theme),  // Using new terminology, also truncate theme
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
      // Creating bookmark with duplicate check
      const bookmarkData: BookmarkData = {
        idea: truncateRequiredField(result.idea || 'No idea text provided'),
        improved_idea: truncateField(result.improved_idea),
        theme: truncateRequiredField(theme || 'General'),
        constraints: truncateRequiredField(constraints ?? ''),
        initial_score: result.initial_score ?? 0,
        improved_score: result.improved_score ?? undefined,
        initial_critique: truncateRequiredField(result.initial_critique),
        improved_critique: truncateField(result.improved_critique),
        advocacy: truncateRequiredField(result.advocacy),
        skepticism: truncateRequiredField(result.skepticism),
        tags: [],
      };

      // Add duplicate check parameters
      const url = new URL(`${API_BASE_URL}/api/bookmarks`);
      url.searchParams.append('check_duplicates', 'true');
      if (forceSave) {
        url.searchParams.append('force_save', 'true');
      }

      // Transform frontend field names to backend field names
      const apiData = mapBookmarkToApiFormat(bookmarkData);

      const response = await fetch(url.toString(), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(apiData),
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
      // Limit URL parameter length to avoid exceeding URL limits (typically ~2048 chars)
      // Use more aggressive truncation for URL parameters
      const maxUrlParamLength = 500;  // Conservative limit for URL parameters
      url.searchParams.append('idea', truncateRequiredField(idea, maxUrlParamLength));
      url.searchParams.append('topic', truncateRequiredField(theme, maxUrlParamLength));  // Backend expects 'topic' not 'theme'
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
      // Creating bookmark
      const bookmarkData: BookmarkData = {
        idea: truncateRequiredField(result.idea || 'No idea text provided'),  // Required field with min_length - handle empty strings
        improved_idea: truncateField(result.improved_idea),  // Optional field - handle empty strings as undefined
        theme: truncateRequiredField(theme || 'General'),  // Required field with min_length - handle empty strings
        constraints: truncateRequiredField(constraints ?? ''),  // Allows empty strings - only handle null/undefined
        initial_score: result.initial_score ?? 0,  // Numeric field - preserve 0, handle null/undefined
        improved_score: result.improved_score ?? undefined,  // Numeric field - preserve 0, handle null/undefined
        initial_critique: truncateRequiredField(result.initial_critique),  // Optional field, sent as empty string if falsy
        improved_critique: truncateField(result.improved_critique),  // Optional field - handle empty strings as undefined
        advocacy: truncateRequiredField(result.advocacy),  // Optional field, sent as empty string if falsy
        skepticism: truncateRequiredField(result.skepticism),  // Optional field, sent as empty string if falsy
        tags: [], // Can be enhanced to allow user-defined tags
      };

      // Log bookmark data for debugging purposes before sending to the API.
      // Bookmark data prepared for transmission

      // Transform frontend field names to backend field names
      const apiData = mapBookmarkToApiFormat(bookmarkData);

      const response = await fetch(`${API_BASE_URL}/api/bookmarks`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(apiData),
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