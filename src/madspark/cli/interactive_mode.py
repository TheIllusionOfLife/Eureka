"""Interactive CLI mode for MadSpark Multi-Agent System.

This module provides a step-by-step guided workflow for users who prefer
an interactive experience over command-line arguments.
"""

import os
import sys
import json
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

try:
    from madspark.utils.temperature_control import TemperatureManager, TemperatureConfig
    from madspark.utils.bookmark_system import BookmarkManager
    from madspark.utils.constants import (
        DEFAULT_IDEA_TEMPERATURE,
        DEFAULT_NUM_TOP_CANDIDATES,
        DEFAULT_NOVELTY_THRESHOLD
    )
except ImportError:
    from ..utils.temperature_control import TemperatureManager, TemperatureConfig
    from ..utils.bookmark_system import BookmarkManager
    from ..utils.constants import (
        DEFAULT_IDEA_TEMPERATURE,
        DEFAULT_NUM_TOP_CANDIDATES,
        DEFAULT_NOVELTY_THRESHOLD
    )

logger = logging.getLogger(__name__)


class InteractiveSession:
    """Manages an interactive CLI session for idea generation."""
    
    def __init__(self):
        """Initialize the interactive session."""
        self.config = {}
        self.temp_manager = TemperatureManager()
        self.current_preset = None  # Track current preset
        self.bookmark_manager = BookmarkManager()
        
    def clear_screen(self):
        """Clear the terminal screen."""
        # Use ANSI escape sequences for safer screen clearing
        print('\033[2J\033[H', end='')
        
    def print_header(self):
        """Print the MadSpark header."""
        self.clear_screen()
        print("=" * 80)
        print("🚀 MadSpark Multi-Agent System - Interactive Mode")
        print("=" * 80)
        print("Welcome! I'll guide you through generating AI-powered ideas step by step.")
        print()
        
    def print_section(self, title: str):
        """Print a section header."""
        print(f"\n{'─' * 40}")
        print(f"📌 {title}")
        print(f"{'─' * 40}\n")
        
    def get_input_with_default(self, prompt: str, default: str = "") -> str:
        """Get user input with optional default value."""
        if default:
            prompt = f"{prompt} [{default}]: "
        else:
            prompt = f"{prompt}: "
            
        try:
            value = input(prompt).strip()
            return value if value else default
        except EOFError:
            print("\n\n👋 Session ended by user. Goodbye!")
            sys.exit(0)
        except KeyboardInterrupt:
            print("\n\n⚠️  Session interrupted by user. Goodbye!")
            sys.exit(0)
        
    def get_yes_no(self, prompt: str, default: bool = True) -> bool:
        """Get yes/no input from user."""
        default_str = "Y" if default else "N"
        prompt = f"{prompt} [{'Y/n' if default else 'y/N'}]: "
        
        while True:
            try:
                value = input(prompt).strip().lower()
                if not value:
                    return default
                if value in ('y', 'yes'):
                    return True
                if value in ('n', 'no'):
                    return False
                print("Please enter 'y' for yes or 'n' for no.")
            except EOFError:
                print("\n\n👋 Session ended by user. Goodbye!")
                sys.exit(0)
            except KeyboardInterrupt:
                print("\n\n⚠️  Session interrupted by user. Goodbye!")
                sys.exit(0)
            
    def get_choice(self, prompt: str, options: List[Tuple[str, str]], default: int = 0) -> str:
        """Get user choice from a list of options."""
        print(f"\n{prompt}")
        for i, (value, description) in enumerate(options):
            marker = "→" if i == default else " "
            print(f"{marker} {i+1}. {description}")
            
        while True:
            choice = self.get_input_with_default("\nEnter your choice", str(default + 1))
            try:
                idx = int(choice) - 1
                if 0 <= idx < len(options):
                    return options[idx][0]
                print(f"Please enter a number between 1 and {len(options)}.")
            except ValueError:
                print("Please enter a valid number.")
                
    def collect_theme_and_constraints(self) -> Tuple[str, str]:
        """Collect theme and constraints from user."""
        self.print_section("Step 1: Define Your Idea Generation Topic")
        
        # Show examples
        print("💡 Examples:")
        print("   - Theme: 'AI applications in healthcare'")
        print("     Constraints: 'Budget-friendly, implementable within 6 months'")
        print("   - Theme: 'Sustainable urban farming'")
        print("     Constraints: 'Small spaces, minimal water usage'")
        print("   - Theme: 'Educational technology'")
        print("     Constraints: 'For K-12 students, accessible offline'\n")
        
        # Get theme
        while True:
            theme = self.get_input_with_default("Enter your theme/topic")
            if theme:
                break
            print("❗ Theme cannot be empty. Please enter a topic for idea generation.")
            
        # Get constraints
        print("\n💡 Constraints help focus the ideas (optional).")
        constraints = self.get_input_with_default(
            "Enter any constraints or requirements",
            "No specific constraints"
        )
        
        # Confirm
        print(f"\n📋 Summary:")
        print(f"   Theme: {theme}")
        print(f"   Constraints: {constraints}")
        
        if not self.get_yes_no("\nIs this correct?"):
            return self.collect_theme_and_constraints()
            
        return theme, constraints
        
    def configure_temperature(self) -> TemperatureManager:
        """Configure temperature settings."""
        self.print_section("Step 2: Set Creativity Level (Temperature)")
        
        print("🌡️  Temperature controls how creative vs conservative the ideas will be.\n")
        
        # Show preset options
        options = [
            ("conservative", "Conservative (0.5) - Safe, practical ideas"),
            ("balanced", "Balanced (0.7) - Mix of practical and creative"),
            ("creative", "Creative (0.9) - More innovative, some unconventional"),
            ("wild", "Wild (1.2) - Highly creative, experimental ideas"),
            ("custom", "Custom - Set your own temperature values")
        ]
        
        choice = self.get_choice("Select a creativity preset", options, default=1)
        
        if choice == "custom":
            print("\n🎛️  Set custom temperatures (0.0 = very conservative, 1.5 = very creative)")
            
            # Helper function to get validated temperature
            def get_valid_temperature(prompt: str, default: float) -> float:
                while True:
                    try:
                        value = self.get_input_with_default(prompt, str(default))
                        temp = float(value)
                        if not (0.0 <= temp <= 2.0):
                            print("❌ Temperature must be between 0.0 and 2.0")
                            continue
                        return temp
                    except ValueError:
                        print("❌ Invalid number. Please enter a valid temperature value.")
            
            idea_temp = get_valid_temperature(
                "Idea generation temperature",
                DEFAULT_IDEA_TEMPERATURE
            )
            
            eval_temp = get_valid_temperature(
                "Evaluation temperature",
                self.temp_manager.get_temperature_for_stage('evaluation')
            )
            
            advocacy_temp = get_valid_temperature(
                "Advocacy temperature",
                self.temp_manager.get_temperature_for_stage('advocacy')
            )
            
            skepticism_temp = get_valid_temperature(
                "Skepticism temperature",
                self.temp_manager.get_temperature_for_stage('skepticism')
            )
            
            # Create custom temperature configuration
            custom_config = TemperatureConfig(
                base_temperature=(idea_temp + eval_temp + advocacy_temp + skepticism_temp) / 4,
                idea_generation=idea_temp,
                evaluation=eval_temp,
                advocacy=advocacy_temp,
                skepticism=skepticism_temp
            )
            self.temp_manager = TemperatureManager(custom_config)
            self.current_preset = 'custom'
        else:
            self.temp_manager = TemperatureManager.from_preset(choice)
            self.current_preset = choice
            preset_config = TemperatureManager.PRESETS[choice]
            print(f"\n✅ Applied '{choice}' preset (overall temperature: {preset_config.base_temperature})")
            
        return self.temp_manager
        
    def configure_workflow_options(self) -> Dict[str, Any]:
        """Configure workflow options."""
        self.print_section("Step 3: Configure Workflow Options")
        
        config = {}
        
        # Number of top candidates
        print("🎯 How many top ideas should be fully analyzed?")
        config['num_top_candidates'] = int(self.get_input_with_default(
            "Number of top candidates",
            str(DEFAULT_NUM_TOP_CANDIDATES)
        ))
        
        # Novelty filter
        if self.get_yes_no("\n🔍 Enable novelty filter to remove similar ideas?"):
            config['enable_novelty_filter'] = True
            config['novelty_threshold'] = float(self.get_input_with_default(
                "Similarity threshold (0.0-1.0, higher = stricter)",
                str(DEFAULT_NOVELTY_THRESHOLD)
            ))
        else:
            config['enable_novelty_filter'] = False
            config['novelty_threshold'] = DEFAULT_NOVELTY_THRESHOLD
            
        # Enhanced features
        print("\n🧠 Enhanced Features (Phase 2.1):")
        config['enhanced_reasoning'] = self.get_yes_no(
            "Enable enhanced reasoning with context awareness?",
            default=False
        )
        
        config['multi_dimensional_eval'] = self.get_yes_no(
            "Enable multi-dimensional evaluation (7 criteria)?",
            default=False
        )
        
        config['logical_inference'] = self.get_yes_no(
            "Enable logical inference chains?",
            default=False
        )
        
        # Async execution
        config['async'] = self.get_yes_no(
            "\n⚡ Use async execution for better performance?",
            default=True
        )
        
        # Caching
        config['enable_cache'] = self.get_yes_no(
            "🗄️  Enable Redis caching (requires Redis)?",
            default=False
        )
        
        return config
        
    def configure_output_options(self) -> Dict[str, Any]:
        """Configure output and export options."""
        self.print_section("Step 4: Output & Export Options")
        
        config = {}
        
        # Output format
        formats = [
            ("json", "JSON - Machine-readable format"),
            ("text", "Text - Human-readable format"),
            ("summary", "Summary - Brief overview only")
        ]
        config['output_format'] = self.get_choice(
            "Select output format",
            formats,
            default=1
        )
        
        # Export options
        if self.get_yes_no("\n📁 Export results to file?"):
            export_formats = [
                ("json", "JSON format"),
                ("csv", "CSV spreadsheet"),
                ("markdown", "Markdown document"),
                ("pdf", "PDF report"),
                ("all", "All formats")
            ]
            config['export'] = self.get_choice(
                "Select export format",
                export_formats,
                default=0
            )
            
            config['export_dir'] = self.get_input_with_default(
                "Export directory",
                "exports"
            )
        else:
            config['export'] = None
            
        # Bookmarking
        if self.get_yes_no("\n🔖 Bookmark results for future reference?"):
            config['bookmark_results'] = True
            tags_input = self.get_input_with_default(
                "Enter tags (comma-separated)",
                ""
            )
            config['bookmark_tags'] = [tag.strip() for tag in tags_input.split(",")] if tags_input else []
        else:
            config['bookmark_results'] = False
            config['bookmark_tags'] = []
            
        # Verbose mode
        config['verbose'] = self.get_yes_no(
            "\n📝 Enable verbose output for debugging?",
            default=False
        )
        
        return config
        
    def show_summary(self, theme: str, constraints: str, config: Dict[str, Any]):
        """Show configuration summary before execution."""
        self.print_section("Configuration Summary")
        
        print("📋 Your Settings:")
        print(f"\n🎯 Topic:")
        print(f"   Theme: {theme}")
        print(f"   Constraints: {constraints}")
        
        print(f"\n🌡️  Temperature:")
        print(f"   Overall: {self.temp_manager.config.base_temperature}")
        print(f"   Preset: {self.current_preset or 'custom'}")
        
        print(f"\n⚙️  Workflow:")
        print(f"   Top candidates: {config['num_top_candidates']}")
        print(f"   Novelty filter: {'Yes' if config['enable_novelty_filter'] else 'No'}")
        if config['enable_novelty_filter']:
            print(f"   Similarity threshold: {config['novelty_threshold']}")
        print(f"   Enhanced reasoning: {'Yes' if config['enhanced_reasoning'] else 'No'}")
        print(f"   Multi-dimensional eval: {'Yes' if config['multi_dimensional_eval'] else 'No'}")
        print(f"   Logical inference: {'Yes' if config['logical_inference'] else 'No'}")
        print(f"   Async execution: {'Yes' if config['async'] else 'No'}")
        print(f"   Caching: {'Yes' if config['enable_cache'] else 'No'}")
        
        print(f"\n📤 Output:")
        print(f"   Format: {config['output_format']}")
        if config.get('export'):
            print(f"   Export: {config['export']} to {config['export_dir']}/")
        if config['bookmark_results']:
            print(f"   Bookmarking: Yes with tags {config['bookmark_tags']}")
        print(f"   Verbose: {'Yes' if config['verbose'] else 'No'}")
        
    def save_session_config(self, theme: str, constraints: str, config: Dict[str, Any]):
        """Save session configuration for reuse."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"session_config_{timestamp}.json"
        
        session_data = {
            "theme": theme,
            "constraints": constraints,
            "config": config,
            "temperature_settings": {
                "overall": self.temp_manager.config.base_temperature,
                "preset": self.current_preset,
                "stages": {
                    "idea_generation": self.temp_manager.config.idea_generation,
                    "evaluation": self.temp_manager.config.evaluation,
                    "advocacy": self.temp_manager.config.advocacy,
                    "skepticism": self.temp_manager.config.skepticism
                }
            },
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            with open(filename, 'w') as f:
                json.dump(session_data, f, indent=2)
            print(f"\n💾 Session configuration saved to: {filename}")
        except IOError as e:
            print(f"\n❌ Failed to save session configuration: {e}")
            logger.error(f"Failed to save session to {filename}: {e}")
        
    def run(self) -> Dict[str, Any]:
        """Run the interactive session and return configuration."""
        self.print_header()
        
        # Check if user wants to load previous session
        if os.path.exists("last_session.json"):
            if self.get_yes_no("📂 Load previous session configuration?", default=False):
                try:
                    with open("last_session.json", 'r') as f:
                        session_data = json.load(f)
                    print("✅ Previous session loaded!")
                    return session_data
                except (IOError, json.JSONDecodeError) as e:
                    print(f"❌ Failed to load previous session: {e}")
                    logger.error(f"Failed to load last_session.json: {e}")
        
        # Collect configuration
        theme, constraints = self.collect_theme_and_constraints()
        self.configure_temperature()
        workflow_config = self.configure_workflow_options()
        output_config = self.configure_output_options()
        
        # Merge configurations
        config = {**workflow_config, **output_config}
        config['temperature_manager'] = self.temp_manager
        
        # Show summary
        self.show_summary(theme, constraints, config)
        
        # Confirm execution
        if not self.get_yes_no("\n🚀 Ready to generate ideas?"):
            print("\n❌ Generation cancelled.")
            sys.exit(0)
            
        # Save configuration
        if self.get_yes_no("\n💾 Save this configuration for future use?", default=False):
            self.save_session_config(theme, constraints, config)
            
            # Also save as last session
            try:
                # Create a serializable copy of the config
                serializable_config = config.copy()
                # The TemperatureManager object is not serializable, so remove it
                serializable_config.pop('temperature_manager', None)
                
                with open("last_session.json", 'w') as f:
                    json.dump({
                        "theme": theme,
                        "constraints": constraints,
                        "config": serializable_config
                    }, f)
            except IOError as e:
                logger.error(f"Failed to save last_session.json: {e}")
        
        return {
            "theme": theme,
            "constraints": constraints,
            "config": config
        }


def run_interactive_mode():
    """Entry point for interactive mode."""
    session = InteractiveSession()
    return session.run()