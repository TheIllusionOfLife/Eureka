import React, { useState, useEffect } from 'react';
import { SavedBookmark } from '../services/bookmarkService';
import MarkdownRenderer from './MarkdownRenderer';

interface BookmarkManagerProps {
  isOpen: boolean;
  onClose: () => void;
  bookmarks: SavedBookmark[];
  onDeleteBookmark: (bookmarkId: string) => void;
  onSelectBookmarks?: (bookmarkIds: string[]) => void;
  selectedBookmarkIds?: string[];
}

const BookmarkManager: React.FC<BookmarkManagerProps> = ({
  isOpen,
  onClose,
  bookmarks,
  onDeleteBookmark,
  onSelectBookmarks,
  selectedBookmarkIds = []
}) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedTag, setSelectedTag] = useState<string | null>(null);
  const [localSelectedIds, setLocalSelectedIds] = useState<Set<string>>(new Set(selectedBookmarkIds));

  useEffect(() => {
    setLocalSelectedIds(new Set(selectedBookmarkIds));
  }, [selectedBookmarkIds]);

  if (!isOpen) return null;

  // Extract all unique tags
  const allTags = Array.from(new Set(bookmarks.flatMap(b => b.tags)));

  // Filter bookmarks based on search and tag
  const filteredBookmarks = bookmarks.filter(bookmark => {
    const matchesSearch = searchQuery === '' || 
      bookmark.text.toLowerCase().includes(searchQuery.toLowerCase()) ||
      bookmark.theme.toLowerCase().includes(searchQuery.toLowerCase());
    
    const matchesTag = !selectedTag || bookmark.tags.includes(selectedTag);
    
    return matchesSearch && matchesTag;
  });

  const handleSelectToggle = (bookmarkId: string) => {
    const newSelected = new Set(localSelectedIds);
    if (newSelected.has(bookmarkId)) {
      newSelected.delete(bookmarkId);
    } else {
      newSelected.add(bookmarkId);
    }
    setLocalSelectedIds(newSelected);
    if (onSelectBookmarks) {
      onSelectBookmarks(Array.from(newSelected));
    }
  };

  const handleExportBookmarks = () => {
    const dataStr = JSON.stringify(bookmarks, null, 2);
    const dataUri = 'data:application/json;charset=utf-8,'+ encodeURIComponent(dataStr);
    
    const exportFileDefaultName = `madspark-bookmarks-${new Date().toISOString().split('T')[0]}.json`;
    
    const linkElement = document.createElement('a');
    linkElement.setAttribute('href', dataUri);
    linkElement.setAttribute('download', exportFileDefaultName);
    linkElement.click();
  };

  return (
    <div className="fixed inset-0 bg-gray-500 bg-opacity-75 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
          <h2 className="text-xl font-semibold text-gray-900">
            Bookmark Manager ({bookmarks.length} bookmarks)
          </h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-500"
          >
            <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Controls */}
        <div className="px-6 py-4 border-b border-gray-200 space-y-4">
          {/* Search */}
          <div className="relative">
            <input
              type="text"
              placeholder="Search bookmarks..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full px-4 py-2 pl-10 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
            />
            <svg className="absolute left-3 top-2.5 h-5 w-5 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
          </div>

          {/* Tag Filter */}
          {allTags.length > 0 && (
            <div className="flex items-center space-x-2">
              <span className="text-sm font-medium text-gray-700">Filter by tag:</span>
              <button
                onClick={() => setSelectedTag(null)}
                className={`px-3 py-1 text-sm rounded-full ${
                  !selectedTag ? 'bg-blue-100 text-blue-800' : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                All
              </button>
              {allTags.map(tag => (
                <button
                  key={tag}
                  onClick={() => setSelectedTag(tag)}
                  className={`px-3 py-1 text-sm rounded-full ${
                    selectedTag === tag ? 'bg-blue-100 text-blue-800' : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                >
                  {tag}
                </button>
              ))}
            </div>
          )}

          {/* Actions */}
          <div className="flex justify-between items-center">
            <button
              onClick={handleExportBookmarks}
              className="inline-flex items-center px-4 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
            >
              <svg className="h-4 w-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              Export All
            </button>
            {onSelectBookmarks && (
              <div className="text-sm text-gray-600">
                {localSelectedIds.size} selected for remix
              </div>
            )}
          </div>
        </div>

        {/* Bookmarks List */}
        <div className="flex-1 overflow-y-auto px-6 py-4">
          {filteredBookmarks.length === 0 ? (
            <div className="text-center py-12 text-gray-500">
              {searchQuery || selectedTag ? 'No bookmarks match your filters.' : 'No bookmarks yet. Start bookmarking ideas!'}
            </div>
          ) : (
            <div className="space-y-4">
              {filteredBookmarks.map((bookmark) => (
                <div key={bookmark.id} className="border rounded-lg p-4 hover:shadow-md transition-shadow">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center space-x-2 mb-2">
                        <span className="text-sm font-medium text-gray-900">Theme:</span>
                        <span className="text-sm text-gray-600">{bookmark.theme}</span>
                        <span className="text-sm text-gray-400">•</span>
                        <span className="text-sm text-gray-500">
                          Score: {bookmark.score}/10
                        </span>
                        <span className="text-sm text-gray-400">•</span>
                        <span className="text-sm text-gray-500">
                          {new Date(bookmark.bookmarked_at).toLocaleDateString()}
                        </span>
                      </div>
                      
                      <div className="mb-2">
                        <MarkdownRenderer content={bookmark.text} className="text-gray-700" />
                      </div>

                      {bookmark.tags.length > 0 && (
                        <div className="flex items-center space-x-2 mb-2">
                          {bookmark.tags.map(tag => (
                            <span key={tag} className="px-2 py-1 text-xs bg-gray-100 text-gray-700 rounded-full">
                              {tag}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>

                    <div className="flex items-center space-x-2 ml-4">
                      {onSelectBookmarks && (
                        <input
                          type="checkbox"
                          checked={localSelectedIds.has(bookmark.id)}
                          onChange={() => handleSelectToggle(bookmark.id)}
                          className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                        />
                      )}
                      <button
                        onClick={() => {
                          if (window.confirm('Are you sure you want to delete this bookmark?')) {
                            onDeleteBookmark(bookmark.id);
                          }
                        }}
                        className="text-red-600 hover:text-red-800"
                      >
                        <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                        </svg>
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default BookmarkManager;