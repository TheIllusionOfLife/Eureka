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

export interface BookmarksListResponse {
  status: string;
  bookmarks: SavedBookmark[];
  count: number;
}

class BookmarkService {
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
        initial_critique: result.initial_critique || undefined,  // Optional field - handle empty strings as undefined
        improved_critique: result.improved_critique || undefined,  // Optional field - handle empty strings as undefined
        advocacy: result.advocacy || undefined,  // Optional field - handle empty strings as undefined
        skepticism: result.skepticism || undefined,  // Optional field - handle empty strings as undefined
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