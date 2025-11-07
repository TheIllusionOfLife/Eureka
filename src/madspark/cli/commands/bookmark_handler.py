"""Bookmark management command handler."""

import argparse
from typing import List, Dict, Any

from .base import CommandHandler, CommandResult

# Import MadSpark components with fallback for local development
try:
    from madspark.utils.bookmark_system import BookmarkManager
except ImportError:
    from bookmark_system import BookmarkManager


class BookmarkHandler(CommandHandler):
    """Handles bookmark operations.

    This handler is responsible for:
    - Bookmarking workflow results
    - Listing, searching, and removing bookmarks
    - Managing tags
    """

    def execute(self, results: List[Dict[str, Any]]) -> CommandResult:
        """Bookmark workflow results.

        Args:
            results: List of workflow results to bookmark

        Returns:
            CommandResult with success status
        """
        # Skip if bookmarking is disabled
        if self.args.no_bookmark:
            return CommandResult(success=True)

        try:
            self.log_info(f"Bookmarking requested. Processing {len(results)} results...")

            manager = BookmarkManager(self.args.bookmark_file)
            bookmark_success = False

            for result in results:
                if self._bookmark_single_result(manager, result):
                    bookmark_success = True

            # Show tip if no bookmarks were created
            if not bookmark_success:
                self._show_bookmark_tip()

            return CommandResult(success=True)

        except Exception as e:
            self.log_error(f"Bookmarking failed: {e}")
            print(f"❌ Error during bookmarking: {e}")
            return CommandResult(success=False, message=str(e))

    def _bookmark_single_result(self, manager: BookmarkManager, result: Dict[str, Any]) -> bool:
        """Bookmark a single result.

        Args:
            manager: BookmarkManager instance
            result: Single result dictionary

        Returns:
            True if bookmark was successfully created
        """
        try:
            # Get the best version of the idea (improved if available, otherwise original)
            idea_text = result.get("improved_idea", "") or result.get("idea", "")
            if not idea_text:
                self.log_warning("Cannot bookmark result: missing both 'improved_idea' and 'idea' fields")
                print("⚠️  Warning: Result missing idea text, skipping bookmark")
                return False

            # Use the best score (improved if available, otherwise initial)
            score = result.get("improved_score", result.get("initial_score", 0))

            # Use the best critique (improved if available, otherwise initial)
            critique = result.get("improved_critique", result.get("initial_critique", ""))

            # Use provided tags or empty list
            bookmark_tags = self.args.bookmark_tags or []

            bookmark_id = manager.bookmark_idea(
                idea_text=idea_text,
                topic=self.args.theme,
                context=self.args.constraints,
                score=score,
                critique=critique,
                advocacy=result.get("advocacy", ""),
                skepticism=result.get("skepticism", ""),
                tags=bookmark_tags
            )

            if bookmark_id:
                print(f"✅ Bookmarked result (ID: {bookmark_id})")
                if bookmark_tags:
                    print(f"   Tags: {', '.join(bookmark_tags)}")
                self.log_info(f"Bookmarked result as {bookmark_id}")
                return True
            else:
                self.log_warning("Bookmark creation returned no ID")
                return False

        except Exception as e:
            self.log_error(f"Failed to bookmark result: {e}")
            print(f"❌ Error saving bookmark: {e}")
            return False

    def _show_bookmark_tip(self) -> None:
        """Show tip for manual bookmarking."""
        print("\n💡 Tip: To manually bookmark this result later, save the output to a file:")
        print(f"   ms \"{self.args.theme}\" \"{self.args.constraints}\" --output-file result.txt")

    @staticmethod
    def list_bookmarks(args: argparse.Namespace) -> CommandResult:
        """List all bookmarks (static method for standalone use).

        Args:
            args: Command-line arguments

        Returns:
            CommandResult with success status
        """
        try:
            manager = BookmarkManager(args.bookmark_file)
            bookmarks = manager.list_bookmarks()

            if not bookmarks:
                print("No bookmarks found.")
                return CommandResult(success=True)

            print(f"\n📚 Found {len(bookmarks)} bookmark(s):\n")
            for bm in bookmarks:
                print(f"ID: {bm.id}")
                print(f"Idea: {bm.text[:100]}..." if len(bm.text) > 100 else f"Idea: {bm.text}")
                print(f"Score: {bm.score}")
                if bm.tags:
                    print(f"Tags: {', '.join(bm.tags)}")
                print()

            return CommandResult(success=True)

        except Exception as e:
            print(f"❌ Error listing bookmarks: {e}")
            return CommandResult(success=False, exit_code=1, message=str(e))

    @staticmethod
    def search_bookmarks(args: argparse.Namespace) -> CommandResult:
        """Search bookmarks (static method for standalone use).

        Args:
            args: Command-line arguments

        Returns:
            CommandResult with success status
        """
        try:
            manager = BookmarkManager(args.bookmark_file)
            results = manager.search_bookmarks(args.search_bookmarks)

            if not results:
                print(f"No bookmarks found matching '{args.search_bookmarks}'")
                return CommandResult(success=True)

            print(f"\n🔍 Found {len(results)} matching bookmark(s):\n")
            for bm in results:
                print(f"ID: {bm.id}")
                print(f"Idea: {bm.text[:100]}..." if len(bm.text) > 100 else f"Idea: {bm.text}")
                print(f"Score: {bm.score}")
                if bm.tags:
                    print(f"Tags: {', '.join(bm.tags)}")
                print()

            return CommandResult(success=True)

        except Exception as e:
            print(f"❌ Error searching bookmarks: {e}")
            return CommandResult(success=False, exit_code=1, message=str(e))

    @staticmethod
    def remove_bookmarks(args: argparse.Namespace) -> CommandResult:
        """Remove bookmarks (static method for standalone use).

        Args:
            args: Command-line arguments

        Returns:
            CommandResult with success status
        """
        try:
            manager = BookmarkManager(args.bookmark_file)

            # Support comma-separated IDs
            bookmark_ids = [id.strip() for id in args.remove_bookmark.split(",") if id.strip()]

            removed_count = 0
            not_found = []

            for bookmark_id in bookmark_ids:
                if manager.remove_bookmark(bookmark_id):
                    print(f"✅ Removed bookmark: {bookmark_id}")
                    removed_count += 1
                else:
                    print(f"❌ Bookmark not found: {bookmark_id}")
                    not_found.append(bookmark_id)

            if removed_count > 0:
                return CommandResult(success=True)
            else:
                return CommandResult(success=False, exit_code=1)

        except Exception as e:
            print(f"❌ Error removing bookmark: {e}")
            return CommandResult(success=False, exit_code=1, message=str(e))
