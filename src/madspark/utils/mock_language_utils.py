"""Utilities for language detection and mock response generation.

This module provides shared utilities for detecting language in text and
generating appropriate mock responses in different languages.
"""

from typing import Dict


def detect_language(text: str) -> str:
    """Detect the language of the given text based on character analysis.
    
    Args:
        text: The text to analyze
        
    Returns:
        Language code: 'ja' for Japanese, 'fr' for French, 'es' for Spanish,
                      'de' for German, 'en' for English (default)
    """
    # Check for Japanese characters
    if any(char >= '\u3040' and char <= '\u309F' or  # Hiragana
           char >= '\u30A0' and char <= '\u30FF' or  # Katakana
           char >= '\u4E00' and char <= '\u9FAF'     # Kanji
           for char in text):
        return 'ja'
    
    # Check for French characters/diacritics
    if any(char in 'àâäæéèêëïîôöùûüÿ' for char in text.lower()):
        return 'fr'
    
    # Check for Spanish characters
    if any(char in 'ñáíóúç' for char in text.lower()):
        return 'es'
    
    # Check for German characters
    if any(char in 'äöüß' for char in text.lower()):
        return 'de'
    
    # Default to English
    return 'en'


# Mock response templates for different agents and languages
MOCK_RESPONSES: Dict[str, Dict[str, str]] = {
    'advocate': {
        'en': "STRENGTHS:\n• Mock strength 1\n• Mock strength 2\n\n"
              "OPPORTUNITIES:\n• Mock opportunity 1\n• Mock opportunity 2\n\n"
              "ADDRESSING CONCERNS:\n• Mock mitigation 1\n• Mock mitigation 2",
        
        'ja': "強み:\n• モック強み1\n• モック強み2\n\n"
              "機会:\n• モック機会1\n• モック機会2\n\n"
              "懸念への対処:\n• モック軽減策1\n• モック軽減策2",
        
        'fr': "FORCES:\n• Force factice 1\n• Force factice 2\n\n"
              "OPPORTUNITÉS:\n• Opportunité factice 1\n• Opportunité factice 2\n\n"
              "RÉPONSE AUX PRÉOCCUPATIONS:\n• Atténuation factice 1\n• Atténuation factice 2",
        
        'es': "FORTALEZAS:\n• Fortaleza simulada 1\n• Fortaleza simulada 2\n\n"
              "OPORTUNIDADES:\n• Oportunidad simulada 1\n• Oportunidad simulada 2\n\n"
              "ABORDANDO PREOCUPACIONES:\n• Mitigación simulada 1\n• Mitigación simulada 2",
        
        'de': "STÄRKEN:\n• Mock-Stärke 1\n• Mock-Stärke 2\n\n"
              "CHANCEN:\n• Mock-Chance 1\n• Mock-Chance 2\n\n"
              "BEDENKEN ANSPRECHEN:\n• Mock-Milderung 1\n• Mock-Milderung 2"
    },
    
    'skeptic': {
        'en': "CRITICAL FLAWS:\n• Mock flaw 1\n• Mock flaw 2\n\n"
              "RISKS AND CHALLENGES:\n• Mock risk 1\n• Mock risk 2\n\n"
              "QUESTIONABLE ASSUMPTIONS:\n• Mock assumption 1\n• Mock assumption 2\n\n"
              "MISSING CONSIDERATIONS:\n• Mock missing 1\n• Mock missing 2",
        
        'ja': "重大な欠陥:\n• モック欠陥1\n• モック欠陥2\n\n"
              "リスクと課題:\n• モックリスク1\n• モックリスク2\n\n"
              "疑わしい仮定:\n• モック仮定1\n• モック仮定2\n\n"
              "欠けている考慮事項:\n• モック欠落1\n• モック欠落2",
        
        'fr': "DÉFAUTS CRITIQUES:\n• Défaut factice 1\n• Défaut factice 2\n\n"
              "RISQUES ET DÉFIS:\n• Risque factice 1\n• Risque factice 2\n\n"
              "HYPOTHÈSES DOUTEUSES:\n• Hypothèse factice 1\n• Hypothèse factice 2\n\n"
              "CONSIDÉRATIONS MANQUANTES:\n• Manquant factice 1\n• Manquant factice 2",
        
        'es': "DEFECTOS CRÍTICOS:\n• Defecto simulado 1\n• Defecto simulado 2\n\n"
              "RIESGOS Y DESAFÍOS:\n• Riesgo simulado 1\n• Riesgo simulado 2\n\n"
              "SUPOSICIONES CUESTIONABLES:\n• Suposición simulada 1\n• Suposición simulada 2\n\n"
              "CONSIDERACIONES FALTANTES:\n• Faltante simulado 1\n• Faltante simulado 2",
        
        'de': "KRITISCHE MÄNGEL:\n• Mock-Mangel 1\n• Mock-Mangel 2\n\n"
              "RISIKEN UND HERAUSFORDERUNGEN:\n• Mock-Risiko 1\n• Mock-Risiko 2\n\n"
              "FRAGWÜRDIGE ANNAHMEN:\n• Mock-Annahme 1\n• Mock-Annahme 2\n\n"
              "FEHLENDE ÜBERLEGUNGEN:\n• Mock-Fehlt 1\n• Mock-Fehlt 2"
    }
}


def get_mock_response(agent_type: str, text: str) -> str:
    """Get a mock response appropriate for the agent type and detected language.
    
    Args:
        agent_type: Type of agent ('advocate', 'skeptic', etc.)
        text: The input text to analyze for language detection
        
    Returns:
        Mock response in the appropriate language
    """
    language = detect_language(text)
    
    # Get the template for this agent type
    agent_templates = MOCK_RESPONSES.get(agent_type, {})
    
    # Return the language-specific template or English default
    return agent_templates.get(language, agent_templates.get('en', 'Mock response'))