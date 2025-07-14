"""Tests for the improved idea cleaner module."""
import pytest
from mad_spark_multiagent.improved_idea_cleaner import (
    clean_improved_idea,
    clean_improved_ideas_in_results,
    META_HEADERS,
    META_PHRASES,
    COMPILED_REPLACEMENTS
)


class TestCleanMetaHeaders:
    """Test cases for cleaning meta headers from improved ideas."""
    
    def test_remove_enhanced_concept_header(self):
        """Test removal of ENHANCED CONCEPT header."""
        text = """ENHANCED CONCEPT: The "Innovation Engine"
        
This is the actual content that should remain."""
        
        result = clean_improved_idea(text)
        
        assert "ENHANCED CONCEPT:" not in result
        assert "This is the actual content that should remain." in result
    
    def test_remove_original_theme_header(self):
        """Test removal of ORIGINAL THEME header."""
        text = """ORIGINAL THEME: Test Idea
        
The main concept follows here."""
        
        result = clean_improved_idea(text)
        
        assert "ORIGINAL THEME:" not in result
        assert "The main concept follows here." in result
    
    def test_remove_multiple_meta_headers(self):
        """Test removal of multiple meta headers."""
        text = """ENHANCED CONCEPT: The "Smart System"

ORIGINAL THEME: Basic Theme

REVISED CORE PREMISE: New approach

The actual idea content starts here."""
        
        result = clean_improved_idea(text)
        
        assert "ENHANCED CONCEPT:" not in result
        assert "ORIGINAL THEME:" not in result
        assert "REVISED CORE PREMISE:" not in result
        assert "The actual idea content starts here." in result
    
    def test_remove_all_meta_header_types(self):
        """Test removal of all META_HEADERS patterns."""
        for header in META_HEADERS:
            text = f"""{header} Some meta content
            
Real content here."""
            
            result = clean_improved_idea(text)
            
            assert header not in result
            assert "Real content here." in result
    
    def test_meta_headers_case_insensitive(self):
        """Test that meta header removal is case-insensitive."""
        text = """enhanced concept: The "Test System"
        
Main content follows."""
        
        result = clean_improved_idea(text)
        
        assert "enhanced concept:" not in result.lower()
        assert "Main content follows." in result


class TestCleanImprovementReferences:
    """Test cases for cleaning improvement and enhancement references."""
    
    def test_remove_enhanced_keyword(self):
        """Test removal of 'enhanced' keyword."""
        text = "Our enhanced approach leverages advanced techniques."
        
        result = clean_improved_idea(text)
        
        assert "enhanced" not in result.lower()
        assert "This approach leverages advanced techniques." in result
    
    def test_remove_improved_keyword(self):
        """Test removal of 'improved' keyword."""
        text = "This improved solution addresses key challenges."
        
        result = clean_improved_idea(text)
        
        assert "improved" not in result.lower()
        assert "This solution addresses key challenges." in result
    
    def test_replace_enhanced_approach_phrase(self):
        """Test replacement of 'Our enhanced approach' with 'This approach'."""
        text = "Our enhanced approach transforms the industry."
        
        result = clean_improved_idea(text)
        
        assert "This approach transforms the industry." in result
        assert "enhanced" not in result.lower()
    
    def test_replace_enhanced_concept_phrase(self):
        """Test replacement of 'The enhanced concept' with 'The concept'."""
        text = "The enhanced concept revolutionizes workflows."
        
        result = clean_improved_idea(text)
        
        assert "The concept revolutionizes workflows." in result
        assert "enhanced" not in result.lower()
    
    def test_replace_enhanced_version_phrase(self):
        """Test replacement of 'This enhanced version' with 'This version'."""
        text = "This enhanced version includes new features."
        
        result = clean_improved_idea(text)
        
        assert "This version includes new features." in result
        assert "enhanced" not in result.lower()
    
    def test_remove_building_upon_phrases(self):
        """Test removal of 'Building upon' references."""
        text = "Building upon the original framework, we introduce new capabilities."
        
        result = clean_improved_idea(text)
        
        assert "Building upon" not in result
        # The entire sentence is removed by the regex pattern
        assert result.strip() == ""
    
    def test_remove_improving_upon_phrases(self):
        """Test removal of 'Improving upon' references."""
        text = "Improving upon the basic design, this adds functionality."
        
        result = clean_improved_idea(text)
        
        assert "Improving upon" not in result
        # The entire sentence is removed by the regex pattern
        assert result.strip() == ""
    
    def test_remove_addresses_previous_phrases(self):
        """Test removal of 'addresses the previous' references."""
        text = "This addresses the previous concerns about scalability."
        
        result = clean_improved_idea(text)
        
        assert "addresses the previous" not in result.lower()
        # The replacement should clean up the sentence structure
        assert len(result.strip()) > 0


class TestCleanScoreReferences:
    """Test cases for cleaning score and evaluation references."""
    
    def test_remove_score_parentheses(self):
        """Test removal of score references in parentheses."""
        text = "This solution is excellent (Score: 8.5) for implementation."
        
        result = clean_improved_idea(text)
        
        assert "(Score: 8.5)" not in result
        # The line containing a META_PHRASE is removed entirely
        assert result.strip() == ""
    
    def test_remove_addressing_score_parentheses(self):
        """Test removal of 'Addressing Score' parentheses."""
        text = "The framework (Addressing Score 7.2) provides value."
        
        result = clean_improved_idea(text)
        
        assert "(Addressing Score 7.2)" not in result
        assert "The framework provides value." in result
    
    def test_remove_score_arrows(self):
        """Test removal of score arrows and transitions."""
        text = "Score 6.0 → This improved solution works better."
        
        result = clean_improved_idea(text)
        
        assert "Score 6.0 →" not in result
        # "improved" is also removed by the regex patterns
        assert "This solution works better." in result
    
    def test_remove_meta_phrases(self):
        """Test removal of META_PHRASES patterns."""
        for phrase in META_PHRASES:
            text = f"Content with {phrase} additional content here."
            
            result = clean_improved_idea(text)
            
            # The line containing the meta phrase should be removed
            assert phrase not in result


class TestCleanTransitionLanguage:
    """Test cases for cleaning transition and transformation language."""
    
    def test_remove_shifts_from_to(self):
        """Test removal of 'shifts from X to Y' patterns."""
        text = "This shifts from basic concepts to advanced implementation."
        
        result = clean_improved_idea(text)
        
        assert "shifts from" not in result.lower()
        assert "advanced implementation." in result
    
    def test_remove_moves_beyond_to(self):
        """Test removal of 'moves beyond X to Y' patterns."""
        text = "The approach moves beyond traditional methods to innovative solutions."
        
        result = clean_improved_idea(text)
        
        assert "moves beyond" not in result.lower()
        assert "innovative solutions." in result
    
    def test_replace_transforms_into(self):
        """Test replacement of 'transforms X into Y' with 'is Y'."""
        text = "This transforms basic ideas into powerful solutions."
        
        result = clean_improved_idea(text)
        
        assert "transforms" not in result.lower()
        assert "is powerful solutions." in result
    
    def test_remove_we_shift_from(self):
        """Test removal of 'We shift from' patterns."""
        text = "We shift from simple approaches to complex methodologies."
        
        result = clean_improved_idea(text)
        
        assert "We shift from" not in result
        assert "complex methodologies." in result
    
    def test_replace_were_moving_from(self):
        """Test replacement of 'We're moving from' with 'It's'."""
        text = "We're moving from basic features to advanced capabilities."
        
        result = clean_improved_idea(text)
        
        assert "We're moving from" not in result
        assert "It's advanced capabilities." in result
    
    def test_replace_evolving_into(self):
        """Test replacement of 'is evolving into' with 'is'."""
        text = "The system is evolving into a comprehensive platform."
        
        result = clean_improved_idea(text)
        
        assert "evolving into" not in result.lower()
        assert "The system is a comprehensive platform." in result


class TestPreserveValidContent:
    """Test cases to ensure valid content is preserved."""
    
    def test_preserve_main_content(self):
        """Test that main idea content is preserved."""
        text = """# Innovation Framework

This framework provides a structured approach to innovation management.

## Key Features
- Strategic planning
- Resource allocation
- Performance tracking

The system enables organizations to systematically manage innovation."""
        
        result = clean_improved_idea(text)
        
        assert "Innovation Framework" in result
        assert "structured approach" in result
        assert "Key Features" in result
        assert "Strategic planning" in result
        assert "Performance tracking" in result
    
    def test_preserve_technical_details(self):
        """Test that technical implementation details are preserved."""
        text = """## Technical Architecture

The system uses microservices architecture with:
- API Gateway for routing
- Redis for caching
- PostgreSQL for data storage

Implementation follows industry best practices."""
        
        result = clean_improved_idea(text)
        
        assert "Technical Architecture" in result
        assert "microservices architecture" in result
        assert "API Gateway" in result
        assert "Redis for caching" in result
        assert "best practices" in result
    
    def test_preserve_benefits_and_features(self):
        """Test that benefits and features are preserved."""
        text = """Benefits include:
1. Increased efficiency
2. Cost reduction
3. Better user experience

Features:
- Real-time monitoring
- Automated alerts
- Customizable dashboards"""
        
        result = clean_improved_idea(text)
        
        assert "Benefits include:" in result
        assert "Increased efficiency" in result
        assert "Cost reduction" in result
        assert "Real-time monitoring" in result
        assert "Automated alerts" in result
    
    def test_preserve_legitimate_enhanced_usage(self):
        """Test that legitimate uses of 'enhanced' in context are preserved appropriately."""
        text = "The platform provides enhanced security through multi-factor authentication."
        
        result = clean_improved_idea(text)
        
        # The word 'enhanced' should be removed but the sentence should make sense
        assert "security through multi-factor" in result
        assert len(result.strip()) > 0


class TestEmptyAndEdgeCases:
    """Test cases for empty strings, None values, and edge cases."""
    
    def test_empty_string(self):
        """Test handling of empty string input."""
        result = clean_improved_idea("")
        
        assert result == ""
    
    def test_none_input(self):
        """Test handling of None input."""
        result = clean_improved_idea(None)
        
        assert result is None
    
    def test_whitespace_only(self):
        """Test handling of whitespace-only input."""
        result = clean_improved_idea("   \n\n   \t   ")
        
        assert result == ""
    
    def test_only_meta_content(self):
        """Test handling of input containing only meta content."""
        text = """ENHANCED CONCEPT: Test
        
ORIGINAL THEME: Theme

Score: 8.5"""
        
        result = clean_improved_idea(text)
        
        # Should be empty or minimal after removing all meta content
        assert len(result.strip()) == 0
    
    def test_mixed_empty_lines(self):
        """Test handling of mixed empty lines and content."""
        text = """


ENHANCED CONCEPT: Test


Real content here.


More content.


"""
        
        result = clean_improved_idea(text)
        
        assert "Real content here." in result
        assert "More content." in result
        assert "ENHANCED CONCEPT:" not in result
    
    def test_single_line_content(self):
        """Test handling of single line content."""
        text = "Simple one-line idea without any meta content."
        
        result = clean_improved_idea(text)
        
        assert result == text
    
    def test_special_characters_preserved(self):
        """Test that special characters are preserved in content."""
        text = """## The "Smart-AI" Framework: 100% Automated!

Features include:
- Cost-effective ($50/month)
- High-performance (99.9% uptime)
- User-friendly (5-star rating)"""
        
        result = clean_improved_idea(text)
        
        # The title formatting logic extracts the quoted name and reformats
        assert "Smart-AI" in result
        # The "100% Automated!" part is removed by header formatting, but other percentages preserved
        assert "$50/month" in result
        assert "99.9%" in result
        assert "5-star" in result


class TestTitleFormatting:
    """Test cases for title and header formatting."""
    
    def test_extract_framework_title(self):
        """Test extraction of framework titles with quotes."""
        text = '''### 1. The "Innovation Engine" Framework: Advanced Solution
        
Content follows here.'''
        
        result = clean_improved_idea(text)
        
        # Should format the title properly
        assert "Innovation Engine" in result
        assert "Content follows here." in result
    
    def test_extract_system_title(self):
        """Test extraction of system titles with quotes."""
        text = '''## The "Smart Learning" System for Education
        
Educational content here.'''
        
        result = clean_improved_idea(text)
        
        assert "Smart Learning" in result
        assert "Educational content here." in result
    
    def test_no_title_extraction_without_quotes(self):
        """Test that titles without quotes are handled normally."""
        text = """## The Innovation Framework Without Quotes
        
Standard content processing."""
        
        result = clean_improved_idea(text)
        
        assert "Innovation Framework Without Quotes" in result
        assert "Standard content processing." in result


class TestCleanImprovedIdeasInResults:
    """Test cases for batch processing function."""
    
    def test_clean_single_result(self):
        """Test cleaning a single result with improved_idea."""
        results = [
            {
                "original_idea": "Basic concept",
                "improved_idea": "ENHANCED CONCEPT: Better approach\n\nThis improved solution works well.",
                "score": 8
            }
        ]
        
        cleaned = clean_improved_ideas_in_results(results)
        
        assert len(cleaned) == 1
        assert "ENHANCED CONCEPT:" not in cleaned[0]["improved_idea"]
        assert "This solution works well." in cleaned[0]["improved_idea"]
        assert cleaned[0]["score"] == 8  # Other fields preserved
    
    def test_clean_multiple_results(self):
        """Test cleaning multiple results."""
        results = [
            {
                "improved_idea": "Our enhanced approach is better.",
                "id": 1
            },
            {
                "improved_idea": "ORIGINAL THEME: Test\n\nReal content here.",
                "id": 2
            },
            {
                "other_field": "No improved_idea field",
                "id": 3
            }
        ]
        
        cleaned = clean_improved_ideas_in_results(results)
        
        assert len(cleaned) == 3
        assert "enhanced" not in cleaned[0]["improved_idea"].lower()
        assert "This approach is better." in cleaned[0]["improved_idea"]
        assert "ORIGINAL THEME:" not in cleaned[1]["improved_idea"]
        assert "Real content here." in cleaned[1]["improved_idea"]
        assert cleaned[2]["other_field"] == "No improved_idea field"  # Unchanged
    
    def test_preserve_original_structure(self):
        """Test that original result structure is preserved."""
        results = [
            {
                "improved_idea": "Enhanced content here.",
                "metadata": {"author": "test", "timestamp": "2024-01-01"},
                "scores": [7, 8, 9],
                "tags": ["innovation", "tech"]
            }
        ]
        
        cleaned = clean_improved_ideas_in_results(results)
        
        assert len(cleaned) == 1
        assert cleaned[0]["metadata"]["author"] == "test"
        assert cleaned[0]["scores"] == [7, 8, 9]
        assert cleaned[0]["tags"] == ["innovation", "tech"]
        assert "content here." in cleaned[0]["improved_idea"]
    
    def test_empty_results_list(self):
        """Test handling of empty results list."""
        results = []
        
        cleaned = clean_improved_ideas_in_results(results)
        
        assert cleaned == []
    
    def test_results_without_improved_idea(self):
        """Test handling of results without improved_idea field."""
        results = [
            {"original_idea": "Basic idea", "score": 7},
            {"title": "Test", "content": "Some content"}
        ]
        
        cleaned = clean_improved_ideas_in_results(results)
        
        assert len(cleaned) == 2
        assert cleaned[0]["original_idea"] == "Basic idea"
        assert cleaned[0]["score"] == 7
        assert cleaned[1]["title"] == "Test"
        assert cleaned[1]["content"] == "Some content"


class TestCompiledReplacementPatterns:
    """Test cases for compiled regex replacement patterns."""
    
    def test_all_patterns_are_compiled(self):
        """Test that all replacement patterns are properly compiled."""
        assert len(COMPILED_REPLACEMENTS) > 0
        
        for pattern, replacement in COMPILED_REPLACEMENTS:
            assert hasattr(pattern, 'sub'), f"Pattern {pattern} is not compiled"
            assert isinstance(replacement, str), f"Replacement {replacement} is not string"
    
    def test_header_cleanup_patterns(self):
        """Test header cleanup regex patterns."""
        text = """### 1. The "Test Framework" - Advanced Solution
        
## The "Another System" for Testing"""
        
        result = clean_improved_idea(text)
        
        # Should clean up numbered headers and format titles
        assert "Test Framework" in result
        assert "Another System" in result
    
    def test_separator_cleanup(self):
        """Test cleanup of separator patterns."""
        text = """Content here.
        
---

More content.


---


Final content."""
        
        result = clean_improved_idea(text)
        
        # Should clean up excessive separators and line breaks
        assert "Content here." in result
        assert "More content." in result
        assert "Final content." in result
        # Should not have excessive line breaks
        assert "\n\n\n" not in result


class TestIntegrationScenarios:
    """Integration test cases with realistic examples."""
    
    def test_complete_cleaning_scenario(self):
        """Test complete cleaning with multiple patterns."""
        text = """## ENHANCED CONCEPT: The "Smart Analytics" Framework – Advanced Data Processing

**ORIGINAL THEME:** Basic Analytics

**REVISED CORE PREMISE:** Our enhanced approach leverages machine learning algorithms.

### 1. The "Smart Analytics" Framework: Enhanced Processing

Building upon the original concept, this improved solution addresses previous concerns about scalability.

Score: 8.5 → This framework provides:
- Real-time processing
- Enhanced accuracy (Score: 9.2)
- Cost-effective implementation

We shift from traditional batch processing to real-time streaming architecture."""
        
        result = clean_improved_idea(text)
        
        # Verify meta content removal
        assert "ENHANCED CONCEPT:" not in result
        assert "ORIGINAL THEME:" not in result
        assert "REVISED CORE PREMISE:" not in result
        
        # Verify improvement references cleaned
        assert "enhanced approach" not in result.lower()
        assert "improved solution" not in result.lower()
        assert "Building upon" not in result
        
        # Verify score references removed
        assert "Score: 8.5 →" not in result
        assert "(Score: 9.2)" not in result
        
        # Verify transition language cleaned
        assert "We shift from" not in result
        
        # Verify content preserved
        assert "Smart Analytics" in result
        assert "Real-time processing" in result
        assert "Cost-effective implementation" in result
        assert "streaming architecture" in result
    
    def test_japanese_content_preserved(self):
        """Test that Japanese content is properly preserved."""
        text = """ENHANCED CONCEPT: 革新的なアプローチ

この改良されたソリューションは、次の特徴を提供します：
- 効率的な処理
- 高い精度
- コスト効果"""
        
        result = clean_improved_idea(text)
        
        assert "ENHANCED CONCEPT:" not in result
        # The meta header line is removed, but content after empty line is preserved
        assert "この改良されたソリューションは、次の特徴を提供します：" in result
        assert "効率的な処理" in result
        assert "高い精度" in result
        assert "コスト効果" in result
    
    def test_mixed_language_content(self):
        """Test handling of mixed language content."""
        text = """ENHANCED CONCEPT: Multi-language System

この enhanced システムは、improved functionality を提供します。

Features include:
- 多言語サポート
- Enhanced user experience
- Improved performance metrics"""
        
        result = clean_improved_idea(text)
        
        assert "ENHANCED CONCEPT:" not in result
        # The header is removed but content after empty line is preserved
        assert "システム" in result
        assert "多言語サポート" in result
        assert "user experience" in result
        assert "performance metrics" in result
        # Enhanced and improved keywords should be removed
        assert "enhanced" not in result.lower()
        assert "improved" not in result.lower()