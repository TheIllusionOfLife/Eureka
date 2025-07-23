import React, { useState } from 'react';
import { SimilarBookmark } from '../types';
import { showWarning } from '../utils/toast';

interface DuplicateWarningDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onSaveAnyway: () => void;
  onCancel: () => void;
  similarBookmarks: SimilarBookmark[];
  recommendation: 'block' | 'warn' | 'notice' | 'allow';
  message: string;
  ideaText: string;
}

const DuplicateWarningDialog: React.FC<DuplicateWarningDialogProps> = ({
  isOpen,
  onClose,
  onSaveAnyway,
  onCancel,
  similarBookmarks,
  recommendation,
  message,
  ideaText
}) => {
  const [selectedBookmark, setSelectedBookmark] = useState<string | null>(null);
  const [showDetails, setShowDetails] = useState<boolean>(false);

  if (!isOpen) return null;

  const getSeverityColor = (recommendation: string): string => {
    switch (recommendation) {
      case 'block':
        return 'border-red-500 bg-red-50';
      case 'warn':
        return 'border-yellow-500 bg-yellow-50';
      case 'notice':
        return 'border-blue-500 bg-blue-50';
      default:
        return 'border-gray-300 bg-gray-50';
    }
  };

  const getSeverityIcon = (recommendation: string): string => {
    switch (recommendation) {
      case 'block':
        return '🚫';
      case 'warn':
        return '⚠️';
      case 'notice':
        return 'ℹ️';
      default:
        return '📝';
    }
  };

  const getSimilarityBadgeColor = (similarity: number): string => {
    if (similarity >= 0.9) return 'bg-red-100 text-red-800';
    if (similarity >= 0.8) return 'bg-orange-100 text-orange-800';
    if (similarity >= 0.7) return 'bg-yellow-100 text-yellow-800';
    return 'bg-gray-100 text-gray-800';
  };

  const formatSimilarity = (similarity: number): string => {
    return `${(similarity * 100).toFixed(0)}%`;
  };

  const formatMatchType = (matchType: string): string => {
    const typeMap: { [key: string]: string } = {
      'exact': 'Exact Match',
      'high': 'High Similarity',
      'medium': 'Moderate Similarity',
      'moderate': 'Moderate Similarity',
      'low': 'Low Similarity',
      'unknown': 'Unknown'
    };
    return typeMap[matchType] || matchType;
  };

  const handleViewBookmark = (bookmarkId: string) => {
    setSelectedBookmark(selectedBookmark === bookmarkId ? null : bookmarkId);
  };

  const truncateText = (text: string, maxLength: number): string => {
    if (text.length <= maxLength) return text;
    return text.substring(0, maxLength) + '...';
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className={`bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-hidden ${getSeverityColor(recommendation)}`}>
        {/* Header */}
        <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <span className="text-2xl">{getSeverityIcon(recommendation)}</span>
            <div>
              <h2 className="text-xl font-semibold text-gray-900">
                Potential Duplicate Detected
              </h2>
              <p className="text-sm text-gray-600">
                Found {similarBookmarks.length} similar bookmark{similarBookmarks.length !== 1 ? 's' : ''}
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 text-2xl font-bold"
          >
            ×
          </button>
        </div>

        {/* Content */}
        <div className="px-6 py-4 overflow-y-auto max-h-[60vh]">
          {/* Message */}
          <div className="mb-6">
            <p className="text-gray-700 text-base leading-relaxed">{message}</p>
          </div>

          {/* Your Idea Preview */}
          <div className="mb-6">
            <h3 className="text-lg font-medium text-gray-900 mb-2">Your Idea:</h3>
            <div className="bg-gray-100 p-4 rounded-lg">
              <p className="text-gray-700 text-sm">
                {showDetails ? ideaText : truncateText(ideaText, 200)}
                {ideaText.length > 200 && (
                  <button
                    onClick={() => setShowDetails(!showDetails)}
                    className="ml-2 text-blue-600 hover:text-blue-800 text-xs underline"
                  >
                    {showDetails ? 'Show less' : 'Show more'}
                  </button>
                )}
              </p>
            </div>
          </div>

          {/* Similar Bookmarks */}
          {similarBookmarks.length > 0 && (
            <div className="mb-6">
              <h3 className="text-lg font-medium text-gray-900 mb-4">Similar Bookmarks:</h3>
              <div className="space-y-4">
                {similarBookmarks.map((bookmark) => (
                  <div key={bookmark.id} className="border border-gray-200 rounded-lg p-4 hover:bg-gray-50">
                    <div className="flex items-start justify-between mb-2">
                      <div className="flex items-center space-x-2 flex-1">
                        <span className={`px-2 py-1 rounded text-xs font-medium ${getSimilarityBadgeColor(bookmark.similarity_score)}`}>
                          {formatSimilarity(bookmark.similarity_score)}
                        </span>
                        <span className="text-xs text-gray-500 bg-gray-100 px-2 py-1 rounded">
                          {formatMatchType(bookmark.match_type || bookmark.similarity_type || 'unknown')}
                        </span>
                        <div className="text-sm text-gray-600 flex-1">
                          <span className="font-medium">Theme:</span> {bookmark.theme}
                        </div>
                      </div>
                      <button
                        onClick={() => handleViewBookmark(bookmark.id)}
                        className="text-blue-600 hover:text-blue-800 text-sm underline ml-2"
                      >
                        {selectedBookmark === bookmark.id ? 'Hide' : 'View'}
                      </button>
                    </div>
                    
                    <div className="text-sm text-gray-700 mb-2">
                      {truncateText(bookmark.text, 150)}
                    </div>

                    {selectedBookmark === bookmark.id && (
                      <div className="mt-3 p-3 bg-gray-50 rounded border-l-4 border-blue-400">
                        <h4 className="font-medium text-gray-900 mb-2">Full Bookmark Text:</h4>
                        <p className="text-sm text-gray-700 whitespace-pre-wrap">{bookmark.text}</p>
                        {bookmark.matched_features && bookmark.matched_features.length > 0 && (
                          <div className="mt-3">
                            <h5 className="font-medium text-gray-700 text-xs mb-1">Matched Features:</h5>
                            <div className="flex flex-wrap gap-1">
                              {bookmark.matched_features.map((feature, index) => (
                                <span key={index} className="bg-blue-100 text-blue-800 text-xs px-2 py-1 rounded">
                                  {feature}
                                </span>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-4 bg-gray-50 border-t border-gray-200 flex justify-between items-center">
          <div className="text-sm text-gray-600">
            {recommendation === 'block' && (
              <span className="text-red-600 font-medium">⚠️ Saving this bookmark is not recommended due to high similarity.</span>
            )}
            {recommendation === 'warn' && (
              <span className="text-yellow-600 font-medium">⚠️ Please review similar bookmarks before saving.</span>
            )}
            {recommendation === 'notice' && (
              <span className="text-blue-600">ℹ️ Some similar bookmarks found for your review.</span>
            )}
          </div>
          
          <div className="flex space-x-3">
            <button
              onClick={onCancel}
              className="px-4 py-2 text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
            >
              Cancel
            </button>
            
            {recommendation !== 'block' && (
              <button
                onClick={onSaveAnyway}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
              >
                Save Anyway
              </button>
            )}

            {recommendation === 'block' && (
              <button
                onClick={() => {
                  showWarning('Are you sure? This appears to be a duplicate.');
                  setTimeout(() => onSaveAnyway(), 100);
                }}
                className="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2"
              >
                Force Save
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default DuplicateWarningDialog;