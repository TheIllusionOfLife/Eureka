"""Workflow validation command handler."""

from typing import TYPE_CHECKING

from .base import CommandHandler, CommandResult

# Multi-modal input limits for safety and resource management
MAX_MULTIMODAL_FILES = 20  # Maximum number of files per request
MAX_MULTIMODAL_URLS = 10   # Maximum number of URLs per request

# Reserved keywords that might collide with special CLI commands
RESERVED_KEYWORDS = ['test', 'coordinator', 'config', 'pytest', 'help', 'version']

# Import MadSpark components with fallback for local development
try:
    from madspark.utils.temperature_control import create_temperature_manager_from_args
    from madspark.utils.bookmark_system import remix_with_bookmarks
    from madspark.utils.errors import ValidationError
    from madspark.utils.multimodal_input import MultiModalInput
    if TYPE_CHECKING:
        from madspark.utils.temperature_control import TemperatureManager
except ImportError:
    from temperature_control import create_temperature_manager_from_args
    from bookmark_system import remix_with_bookmarks
    from errors import ValidationError
    from utils.multimodal_input import MultiModalInput
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
                    'topic': self.args.topic,
                    'context': self.args.context
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
        """Validate topic and context arguments.

        Raises:
            ValueError: If topic is missing and not in remix mode
        """
        # Check for reserved keywords that might collide with special commands
        if self.args.topic and self.args.topic.lower() in RESERVED_KEYWORDS:
            keyword = self.args.topic.lower()
            print(f"\n💡 Note: Topic '{self.args.topic}' matches a reserved keyword.")
            print(f"   You're generating ideas about '{self.args.topic}'.")

            # Special case for 'test' - it runs pytest, not idea generation
            if keyword == "test":
                print("   To run the test suite instead, use: ms test (without quotes)\n")
            else:
                print(f"   If you intended a special command, use: ms {keyword}\n")

        # Validate topic requirement
        if not self.args.topic:
            if self.args.remix:
                # For remix mode, use a default topic if not provided
                self.args.topic = "Creative Innovation"
                self.args.context = self.args.context or "Generate novel ideas based on previous concepts"
                self.log_info("Using default topic for remix mode")
            else:
                raise ValueError("Topic is required for idea generation")

        # Provide default context if missing
        if not self.args.context:
            self.args.context = "Generate practical and innovative ideas"
            self.log_info("Using default context")

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

        Updates self.args.context with enhanced version including bookmarked ideas.

        Raises:
            Exception: If remix mode setup fails
        """
        self.log_info("Running in remix mode - incorporating bookmarked ideas")
        try:
            self.args.context = remix_with_bookmarks(
                theme=self.args.topic,
                additional_constraints=self.args.context,
                bookmark_ids=self.args.remix_ids,
                bookmark_tags=self.args.bookmark_tags,
                bookmark_file=self.args.bookmark_file
            )
            self.log_info("Successfully enhanced context with bookmarked ideas")
        except Exception as e:
            self.log_error(f"Failed to setup remix mode: {e}")
            raise

    def _validate_multimodal_inputs(self) -> None:
        """Validate multi-modal inputs if provided.

        Validates files and URLs using MultiModalInput utility.

        Raises:
            ValidationError: If any file or URL validation fails or limits are exceeded
        """
        # Use getattr with defaults for cleaner code (follows DRY principle)
        multimodal_urls = getattr(self.args, 'multimodal_urls', None) or []
        multimodal_files = getattr(self.args, 'multimodal_files', None) or []
        multimodal_images = getattr(self.args, 'multimodal_images', None) or []
        all_files = multimodal_files + multimodal_images

        if not (multimodal_urls or all_files):
            return  # No multi-modal inputs to validate

        # Check file count limits
        if len(all_files) > MAX_MULTIMODAL_FILES:
            raise ValidationError(
                f"Too many files: {len(all_files)} files provided, "
                f"maximum allowed is {MAX_MULTIMODAL_FILES}"
            )

        # Check URL count limits
        if len(multimodal_urls) > MAX_MULTIMODAL_URLS:
            raise ValidationError(
                f"Too many URLs: {len(multimodal_urls)} URLs provided, "
                f"maximum allowed is {MAX_MULTIMODAL_URLS}"
            )

        mm_input = MultiModalInput()

        # Validate files
        for file_path in all_files:
            try:
                mm_input.validate_file(file_path)
            except (ValueError, FileNotFoundError) as e:
                raise ValidationError(f"Invalid file '{file_path}': {e}")

        # Validate URLs
        for url in multimodal_urls:
            try:
                mm_input.validate_url(url)
            except ValueError as e:
                raise ValidationError(f"Invalid URL '{url}': {e}")

        # Log success (only if verbose mode is enabled)
        if getattr(self.args, 'verbose', False):
            self.log_info(f"Multi-modal validation passed: {len(all_files)} file(s), {len(multimodal_urls)} URL(s)")
