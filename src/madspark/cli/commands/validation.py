"""Workflow validation command handler."""

from typing import TYPE_CHECKING

from .base import CommandHandler, CommandResult

# Import MadSpark components with fallback for local development
try:
    from madspark.utils.temperature_control import create_temperature_manager_from_args
    from madspark.utils.bookmark_system import remix_with_bookmarks
    from madspark.utils.errors import ValidationError
    if TYPE_CHECKING:
        from madspark.utils.temperature_control import TemperatureManager
except ImportError:
    from temperature_control import create_temperature_manager_from_args
    from bookmark_system import remix_with_bookmarks
    from errors import ValidationError
    if TYPE_CHECKING:
        from temperature_control import TemperatureManager


class WorkflowValidator(CommandHandler):
    """Validates and prepares workflow arguments.

    This handler is responsible for:
    - Validating theme and constraints arguments
    - Setting up temperature management
    - Handling remix mode integration with bookmarks
    """

    def execute(self) -> CommandResult:
        """Validate workflow arguments and setup temperature manager.

        Returns:
            CommandResult with success status and data containing:
                - temp_manager: Temperature manager instance
                - theme: Validated theme string
                - constraints: Validated constraints string
        """
        try:
            # Validate theme and constraints
            self._validate_theme_and_constraints()

            # Validate multi-modal inputs if provided
            self._validate_multimodal_inputs()

            # Setup temperature manager
            temp_manager = self._setup_temperature_manager()

            # Handle remix mode if enabled
            if self.args.remix:
                self._handle_remix_mode()

            return CommandResult(
                success=True,
                data={
                    'temp_manager': temp_manager,
                    'theme': self.args.theme,
                    'constraints': self.args.constraints
                }
            )

        except (ValueError, ValidationError) as e:
            self.log_error(f"Validation failed: {e}")
            print(f"Error: {e}")
            return CommandResult(success=False, exit_code=1, message=str(e))
        except Exception as e:
            self.log_error(f"Unexpected error during validation: {e}")
            print(f"Error: {e}")
            return CommandResult(success=False, exit_code=1, message=str(e))

    def _validate_theme_and_constraints(self) -> None:
        """Validate theme and constraints arguments.

        Raises:
            ValueError: If theme is missing and not in remix mode
        """
        # Validate theme requirement
        if not self.args.theme:
            if self.args.remix:
                # For remix mode, use a default theme if not provided
                self.args.theme = "Creative Innovation"
                self.args.constraints = self.args.constraints or "Generate novel ideas based on previous concepts"
                self.log_info("Using default theme for remix mode")
            else:
                raise ValueError("Theme is required for idea generation")

        # Provide default constraints if missing
        if not self.args.constraints:
            self.args.constraints = "Generate practical and innovative ideas"
            self.log_info("Using default constraints")

    def _setup_temperature_manager(self) -> "TemperatureManager":
        """Setup temperature manager from args.

        Returns:
            TemperatureManager instance

        Raises:
            ValidationError: If temperature configuration is invalid
        """
        try:
            temp_manager = create_temperature_manager_from_args(self.args)
            self.log_info(temp_manager.describe_settings())
            return temp_manager
        except (ValueError, ValidationError) as e:
            self.log_error(f"Temperature manager setup failed: {e}")
            raise

    def _handle_remix_mode(self) -> None:
        """Handle remix mode integration with bookmarks.

        Updates self.args.constraints with enhanced version including bookmarked ideas.

        Raises:
            Exception: If remix mode setup fails
        """
        self.log_info("Running in remix mode - incorporating bookmarked ideas")
        try:
            self.args.constraints = remix_with_bookmarks(
                theme=self.args.theme,
                additional_constraints=self.args.constraints,
                bookmark_ids=self.args.remix_ids,
                bookmark_tags=self.args.bookmark_tags,
                bookmark_file=self.args.bookmark_file
            )
            self.log_info("Successfully enhanced constraints with bookmarked ideas")
        except Exception as e:
            self.log_error(f"Failed to setup remix mode: {e}")
            raise

    def _validate_multimodal_inputs(self) -> None:
        """Validate multi-modal inputs if provided.

        Validates files and URLs using MultiModalInput utility.

        Raises:
            ValidationError: If any file or URL validation fails
        """
        # Check if any multi-modal inputs provided
        has_multimodal = (
            (hasattr(self.args, 'multimodal_urls') and self.args.multimodal_urls) or
            (hasattr(self.args, 'multimodal_files') and self.args.multimodal_files) or
            (hasattr(self.args, 'multimodal_images') and self.args.multimodal_images)
        )

        if not has_multimodal:
            return  # No multi-modal inputs to validate

        # Import multi-modal utilities
        try:
            from madspark.utils.multimodal_input import MultiModalInput
        except ImportError:
            # Fallback for local development
            from utils.multimodal_input import MultiModalInput

        mm_input = MultiModalInput()

        # Combine files and images into single list
        all_files = []
        if hasattr(self.args, 'multimodal_files') and self.args.multimodal_files:
            all_files.extend(self.args.multimodal_files)
        if hasattr(self.args, 'multimodal_images') and self.args.multimodal_images:
            all_files.extend(self.args.multimodal_images)

        # Validate files
        for file_path in all_files:
            try:
                mm_input.validate_file(file_path)
            except (ValueError, FileNotFoundError) as e:
                raise ValidationError(f"Invalid file '{file_path}': {e}")

        # Validate URLs
        if hasattr(self.args, 'multimodal_urls') and self.args.multimodal_urls:
            for url in self.args.multimodal_urls:
                try:
                    mm_input.validate_url(url)
                except ValueError as e:
                    raise ValidationError(f"Invalid URL '{url}': {e}")

        # Log success
        if all_files or (hasattr(self.args, 'multimodal_urls') and self.args.multimodal_urls):
            file_count = len(all_files)
            url_count = len(self.args.multimodal_urls) if hasattr(self.args, 'multimodal_urls') and self.args.multimodal_urls else 0
            self.log_info(f"Multi-modal validation passed: {file_count} file(s), {url_count} URL(s)")
