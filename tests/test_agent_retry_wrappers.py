"""Comprehensive tests for agent retry wrappers."""
import pytest
import time
from unittest.mock import Mock, patch, MagicMock

from madspark.utils.agent_retry_wrappers import (
    call_idea_generator_with_retry,
    call_critic_with_retry,
    call_advocate_with_retry,
    call_skeptic_with_retry,
    call_improve_idea_with_retry,
    exponential_backoff_with_jitter,
    MAX_RETRIES,
    INITIAL_DELAY,
    MAX_DELAY,
    BACKOFF_FACTOR
)


class TestExponentialBackoff:
    """Test exponential backoff with jitter."""
    
    def test_exponential_backoff_basic(self):
        """Test basic exponential backoff calculation."""
        # First retry
        delay = exponential_backoff_with_jitter(0)
        assert INITIAL_DELAY * 0.5 <= delay <= INITIAL_DELAY * 1.5
        
        # Second retry  
        delay = exponential_backoff_with_jitter(1)
        expected = INITIAL_DELAY * BACKOFF_FACTOR
        assert expected * 0.5 <= delay <= expected * 1.5
        
        # Third retry
        delay = exponential_backoff_with_jitter(2)
        expected = INITIAL_DELAY * (BACKOFF_FACTOR ** 2)
        assert expected * 0.5 <= delay <= expected * 1.5
    
    def test_exponential_backoff_max_delay(self):
        """Test that backoff respects maximum delay."""
        # Very high retry count
        delay = exponential_backoff_with_jitter(100)
        assert delay <= MAX_DELAY * 1.5  # Including jitter
    
    def test_exponential_backoff_jitter(self):
        """Test that jitter provides randomization."""
        delays = [exponential_backoff_with_jitter(1) for _ in range(100)]
        # All delays should be different (very high probability)
        assert len(set(delays)) > 90  # Allow for some unlikely duplicates


class TestIdeaGeneratorRetry:
    """Test retry wrapper for idea generator."""
    
    @patch('madspark.utils.agent_retry_wrappers.generate_ideas')
    def test_idea_generator_success_first_try(self, mock_generate):
        """Test successful call on first try."""
        mock_generate.return_value = "Generated ideas"
        
        result = call_idea_generator_with_retry(
            theme="Test theme",
            constraints="Test constraints",
            temperature=0.9
        )
        
        assert result == "Generated ideas"
        mock_generate.assert_called_once_with(
            theme="Test theme",
            constraints="Test constraints",
            temperature=0.9
        )
    
    @patch('madspark.utils.agent_retry_wrappers.generate_ideas')
    @patch('madspark.utils.agent_retry_wrappers.time.sleep')
    def test_idea_generator_retry_on_failure(self, mock_sleep, mock_generate):
        """Test retry on failure."""
        # Fail twice, then succeed
        mock_generate.side_effect = [
            Exception("API Error"),
            Exception("Network Error"),
            "Generated ideas"
        ]
        
        result = call_idea_generator_with_retry(
            theme="Test theme",
            constraints="Test constraints"
        )
        
        assert result == "Generated ideas"
        assert mock_generate.call_count == 3
        assert mock_sleep.call_count == 2  # Sleep between retries
    
    @patch('madspark.utils.agent_retry_wrappers.generate_ideas')
    @patch('madspark.utils.agent_retry_wrappers.time.sleep')
    def test_idea_generator_max_retries_exceeded(self, mock_sleep, mock_generate):
        """Test when max retries are exceeded."""
        mock_generate.side_effect = Exception("Persistent error")
        
        with pytest.raises(Exception) as exc_info:
            call_idea_generator_with_retry(
                theme="Test theme",
                constraints="Test constraints"
            )
        
        assert "Persistent error" in str(exc_info.value)
        assert mock_generate.call_count == MAX_RETRIES
        assert mock_sleep.call_count == MAX_RETRIES - 1
    
    @patch('madspark.utils.agent_retry_wrappers.generate_ideas')
    def test_idea_generator_with_all_parameters(self, mock_generate):
        """Test with all optional parameters."""
        mock_generate.return_value = "Ideas"
        
        result = call_idea_generator_with_retry(
            theme="Theme",
            constraints="Constraints",
            temperature=0.8,
            num_ideas=10,
            creativity_boost=True,
            focus_areas=["innovation", "feasibility"],
            example_ideas=["Example 1", "Example 2"],
            avoid_themes=["Blockchain"],
            output_format="detailed",
            language="es"
        )
        
        assert result == "Ideas"
        # Verify all parameters were passed
        call_args = mock_generate.call_args[1]
        assert call_args["temperature"] == 0.8
        assert call_args["num_ideas"] == 10
        assert call_args["creativity_boost"] == True
        assert call_args["focus_areas"] == ["innovation", "feasibility"]
        assert call_args["example_ideas"] == ["Example 1", "Example 2"]
        assert call_args["avoid_themes"] == ["Blockchain"]
        assert call_args["output_format"] == "detailed"
        assert call_args["language"] == "es"


class TestCriticRetry:
    """Test retry wrapper for critic."""
    
    @patch('madspark.utils.agent_retry_wrappers.evaluate_ideas')
    def test_critic_success_first_try(self, mock_evaluate):
        """Test successful critic call on first try."""
        mock_evaluate.return_value = "Evaluation results"
        
        result = call_critic_with_retry(
            ideas="Test ideas",
            criteria="Test criteria",
            context="Test context"
        )
        
        assert result == "Evaluation results"
        mock_evaluate.assert_called_once()
    
    @patch('madspark.utils.agent_retry_wrappers.evaluate_ideas')
    @patch('madspark.utils.agent_retry_wrappers.time.sleep')
    def test_critic_retry_logic(self, mock_sleep, mock_evaluate):
        """Test critic retry logic."""
        mock_evaluate.side_effect = [
            Exception("Temporary failure"),
            "Evaluation results"
        ]
        
        result = call_critic_with_retry(
            ideas="Ideas",
            criteria="Criteria",
            context="Context",
            temperature=0.3
        )
        
        assert result == "Evaluation results"
        assert mock_evaluate.call_count == 2
        assert mock_sleep.call_count == 1
    
    @patch('madspark.utils.agent_retry_wrappers.evaluate_ideas')
    def test_critic_with_optional_parameters(self, mock_evaluate):
        """Test critic with all optional parameters."""
        mock_evaluate.return_value = "Results"
        
        result = call_critic_with_retry(
            ideas="Ideas",
            criteria="Criteria", 
            context="Context",
            temperature=0.4,
            evaluation_style="comprehensive",
            scoring_rubric={"innovation": 0.4, "feasibility": 0.6},
            min_score=5.0,
            max_score=10.0
        )
        
        assert result == "Results"
        call_args = mock_evaluate.call_args[1]
        assert call_args["temperature"] == 0.4
        assert call_args["evaluation_style"] == "comprehensive"
        assert call_args["scoring_rubric"] == {"innovation": 0.4, "feasibility": 0.6}
        assert call_args["min_score"] == 5.0
        assert call_args["max_score"] == 10.0


class TestAdvocateRetry:
    """Test retry wrapper for advocate."""
    
    @patch('madspark.utils.agent_retry_wrappers.advocate_idea')
    def test_advocate_success_first_try(self, mock_advocate):
        """Test successful advocate call."""
        mock_advocate.return_value = "Advocacy points"
        
        result = call_advocate_with_retry(
            idea="Test idea",
            evaluation="Test evaluation",
            context="Test context"
        )
        
        assert result == "Advocacy points"
        mock_advocate.assert_called_once()
    
    @patch('madspark.utils.agent_retry_wrappers.advocate_idea')
    @patch('madspark.utils.agent_retry_wrappers.time.sleep')
    def test_advocate_exponential_backoff(self, mock_sleep, mock_advocate):
        """Test exponential backoff in advocate retry."""
        mock_advocate.side_effect = [
            Exception("Error 1"),
            Exception("Error 2"),
            Exception("Error 3"),
            "Success"
        ]
        
        result = call_advocate_with_retry(
            idea="Idea",
            evaluation="Eval",
            context="Context"
        )
        
        assert result == "Success"
        assert mock_advocate.call_count == 4
        assert mock_sleep.call_count == 3
        
        # Verify exponential backoff delays
        delays = [call[0][0] for call in mock_sleep.call_args_list]
        # Each delay should be roughly double the previous (with jitter)
        assert delays[1] > delays[0]
        assert delays[2] > delays[1]
    
    @patch('madspark.utils.agent_retry_wrappers.advocate_idea')
    def test_advocate_with_enhanced_features(self, mock_advocate):
        """Test advocate with enhanced features."""
        mock_advocate.return_value = "Enhanced advocacy"
        
        result = call_advocate_with_retry(
            idea="Idea",
            evaluation="Eval",
            context="Context",
            temperature=0.7,
            advocacy_style="passionate",
            highlight_benefits=True,
            target_audience="investors",
            emphasis_points=["ROI", "scalability"]
        )
        
        assert result == "Enhanced advocacy"
        call_args = mock_advocate.call_args[1]
        assert call_args["advocacy_style"] == "passionate"
        assert call_args["highlight_benefits"] == True
        assert call_args["target_audience"] == "investors"
        assert call_args["emphasis_points"] == ["ROI", "scalability"]


class TestSkepticRetry:
    """Test retry wrapper for skeptic."""
    
    @patch('madspark.utils.agent_retry_wrappers.criticize_idea')
    def test_skeptic_success_first_try(self, mock_criticize):
        """Test successful skeptic call."""
        mock_criticize.return_value = "Skeptical analysis"
        
        result = call_skeptic_with_retry(
            idea="Test idea",
            advocacy="Test advocacy",
            context="Test context"
        )
        
        assert result == "Skeptical analysis"
        mock_criticize.assert_called_once()
    
    @patch('madspark.utils.agent_retry_wrappers.criticize_idea')
    @patch('madspark.utils.agent_retry_wrappers.time.sleep')
    def test_skeptic_network_error_retry(self, mock_sleep, mock_criticize):
        """Test skeptic retry on network errors."""
        # Simulate network errors
        mock_criticize.side_effect = [
            ConnectionError("Network unreachable"),
            TimeoutError("Request timeout"),
            "Skeptical analysis"
        ]
        
        result = call_skeptic_with_retry(
            idea="Idea",
            advocacy="Advocacy",
            context="Context"
        )
        
        assert result == "Skeptical analysis"
        assert mock_criticize.call_count == 3
        assert mock_sleep.call_count == 2
    
    @patch('madspark.utils.agent_retry_wrappers.criticize_idea')
    def test_skeptic_with_analysis_parameters(self, mock_criticize):
        """Test skeptic with analysis parameters."""
        mock_criticize.return_value = "Critical analysis"
        
        result = call_skeptic_with_retry(
            idea="Idea",
            advocacy="Advocacy",
            context="Context",
            temperature=0.6,
            criticism_level="harsh",
            focus_on_risks=True,
            consider_alternatives=True,
            risk_categories=["technical", "market", "regulatory"]
        )
        
        assert result == "Critical analysis"
        call_args = mock_criticize.call_args[1]
        assert call_args["criticism_level"] == "harsh"
        assert call_args["focus_on_risks"] == True
        assert call_args["consider_alternatives"] == True
        assert call_args["risk_categories"] == ["technical", "market", "regulatory"]


class TestImproveIdeaRetry:
    """Test retry wrapper for improve idea."""
    
    @patch('madspark.utils.agent_retry_wrappers.improve_idea')
    def test_improve_idea_success_first_try(self, mock_improve):
        """Test successful improve idea call."""
        mock_improve.return_value = "Improved idea"
        
        result = call_improve_idea_with_retry(
            original_idea="Original",
            feedback="Feedback",
            constraints="Constraints"
        )
        
        assert result == "Improved idea"
        mock_improve.assert_called_once()
    
    @patch('madspark.utils.agent_retry_wrappers.improve_idea')
    @patch('madspark.utils.agent_retry_wrappers.time.sleep')
    def test_improve_idea_partial_failure_recovery(self, mock_sleep, mock_improve):
        """Test recovery from partial failures."""
        # Simulate various failure modes
        mock_improve.side_effect = [
            ValueError("Invalid input"),
            RuntimeError("Processing error"),
            MemoryError("Out of memory"),
            "Improved idea"
        ]
        
        result = call_improve_idea_with_retry(
            original_idea="Original",
            feedback="Feedback",
            constraints="Constraints"
        )
        
        assert result == "Improved idea"
        assert mock_improve.call_count == 4
        assert mock_sleep.call_count == 3
    
    @patch('madspark.utils.agent_retry_wrappers.improve_idea')
    def test_improve_idea_with_improvement_parameters(self, mock_improve):
        """Test improve idea with all parameters."""
        mock_improve.return_value = "Enhanced idea"
        
        result = call_improve_idea_with_retry(
            original_idea="Original",
            feedback="Feedback",
            constraints="Constraints",
            temperature=0.8,
            improvement_style="innovative",
            preserve_core=True,
            enhancement_areas=["scalability", "user experience"],
            avoid_changes=["core algorithm"],
            target_score=9.0
        )
        
        assert result == "Enhanced idea"
        call_args = mock_improve.call_args[1]
        assert call_args["improvement_style"] == "innovative"
        assert call_args["preserve_core"] == True
        assert call_args["enhancement_areas"] == ["scalability", "user experience"]
        assert call_args["avoid_changes"] == ["core algorithm"]
        assert call_args["target_score"] == 9.0


class TestRetryWrapperEdgeCases:
    """Test edge cases for retry wrappers."""
    
    @patch('madspark.utils.agent_retry_wrappers.generate_ideas')
    def test_retry_with_none_result(self, mock_generate):
        """Test handling when agent returns None."""
        mock_generate.return_value = None
        
        result = call_idea_generator_with_retry(
            theme="Theme",
            constraints="Constraints"
        )
        
        assert result is None
        mock_generate.assert_called_once()
    
    @patch('madspark.utils.agent_retry_wrappers.evaluate_ideas')
    def test_retry_with_empty_result(self, mock_evaluate):
        """Test handling when agent returns empty string."""
        mock_evaluate.return_value = ""
        
        result = call_critic_with_retry(
            ideas="Ideas",
            criteria="Criteria",
            context="Context"
        )
        
        assert result == ""
        mock_evaluate.assert_called_once()
    
    @patch('madspark.utils.agent_retry_wrappers.generate_ideas')
    @patch('madspark.utils.agent_retry_wrappers.time.sleep')
    def test_retry_with_keyboard_interrupt(self, mock_sleep, mock_generate):
        """Test handling KeyboardInterrupt during retry."""
        mock_generate.side_effect = [
            Exception("Error"),
            KeyboardInterrupt("User cancelled")
        ]
        
        with pytest.raises(KeyboardInterrupt):
            call_idea_generator_with_retry(
                theme="Theme",
                constraints="Constraints"
            )
        
        # Should not retry after KeyboardInterrupt
        assert mock_generate.call_count == 2
        assert mock_sleep.call_count == 1
    
    @patch('madspark.utils.agent_retry_wrappers.advocate_idea')
    @patch('madspark.utils.agent_retry_wrappers.time.sleep')
    def test_retry_with_system_exit(self, mock_sleep, mock_advocate):
        """Test handling SystemExit during retry."""
        mock_advocate.side_effect = [
            Exception("Error"),
            SystemExit(1)
        ]
        
        with pytest.raises(SystemExit):
            call_advocate_with_retry(
                idea="Idea",
                evaluation="Eval",
                context="Context"
            )
        
        # Should not retry after SystemExit
        assert mock_advocate.call_count == 2
        assert mock_sleep.call_count == 1
    
    @patch('madspark.utils.agent_retry_wrappers.improve_idea')
    @patch('madspark.utils.agent_retry_wrappers.time.sleep')
    @patch('madspark.utils.agent_retry_wrappers.logger')
    def test_retry_logging(self, mock_logger, mock_sleep, mock_improve):
        """Test that retries are properly logged."""
        mock_improve.side_effect = [
            Exception("First error"),
            Exception("Second error"),
            "Success"
        ]
        
        result = call_improve_idea_with_retry(
            original_idea="Original",
            feedback="Feedback",
            constraints="Constraints"
        )
        
        assert result == "Success"
        # Verify logging occurred
        assert mock_logger.warning.call_count >= 2  # At least 2 retry warnings
        
        # Check log messages contain error info
        log_calls = mock_logger.warning.call_args_list
        assert any("First error" in str(call) for call in log_calls)
        assert any("Second error" in str(call) for call in log_calls)


class TestRetryMechanismConsistency:
    """Test consistency across all retry wrappers."""
    
    def test_all_wrappers_have_same_retry_config(self):
        """Test that all wrappers use consistent retry configuration."""
        # This is more of a code inspection test
        # Verify constants are used consistently
        assert MAX_RETRIES > 0
        assert INITIAL_DELAY > 0
        assert MAX_DELAY > INITIAL_DELAY
        assert BACKOFF_FACTOR > 1
    
    @patch('madspark.utils.agent_retry_wrappers.time.sleep')
    def test_all_wrappers_respect_max_retries(self, mock_sleep):
        """Test that all wrappers respect MAX_RETRIES."""
        wrappers_and_mocks = [
            ('madspark.utils.agent_retry_wrappers.generate_ideas', call_idea_generator_with_retry, 
             {"theme": "T", "constraints": "C"}),
            ('madspark.utils.agent_retry_wrappers.evaluate_ideas', call_critic_with_retry,
             {"ideas": "I", "criteria": "C", "context": "X"}),
            ('madspark.utils.agent_retry_wrappers.advocate_idea', call_advocate_with_retry,
             {"idea": "I", "evaluation": "E", "context": "C"}),
            ('madspark.utils.agent_retry_wrappers.criticize_idea', call_skeptic_with_retry,
             {"idea": "I", "advocacy": "A", "context": "C"}),
            ('madspark.utils.agent_retry_wrappers.improve_idea', call_improve_idea_with_retry,
             {"original_idea": "O", "feedback": "F", "constraints": "C"})
        ]
        
        for mock_path, wrapper_func, kwargs in wrappers_and_mocks:
            with patch(mock_path) as mock_func:
                mock_func.side_effect = Exception("Persistent error")
                
                with pytest.raises(Exception):
                    wrapper_func(**kwargs)
                
                assert mock_func.call_count == MAX_RETRIES