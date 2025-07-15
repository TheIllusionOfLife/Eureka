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
      const bookmarkData: BookmarkData = {
        idea: result.idea,
        improved_idea: result.improved_idea,
        theme: theme,
        constraints: constraints,
        initial_score: result.initial_score,
        improved_score: result.improved_score,
        initial_critique: result.initial_critique,
        improved_critique: result.improved_critique,
        advocacy: result.advocacy,
        skepticism: result.skepticism,
        tags: [], // Can be enhanced to allow user-defined tags
      };

      const response = await fetch(`${API_BASE_URL}/api/bookmarks`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(bookmarkData),
      });

      if (!response.ok) {
        throw new Error(`Failed to create bookmark: ${response.statusText}`);
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