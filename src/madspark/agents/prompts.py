"""Prompts for the Idea Generator agent."""

from typing import Optional, Dict

try:
    from madspark.utils.constants import IDEA_GENERATION_INSTRUCTION, LANGUAGE_CONSISTENCY_INSTRUCTION
except ImportError:
    # Fallback for local development/testing
    from constants import IDEA_GENERATION_INSTRUCTION, LANGUAGE_CONSISTENCY_INSTRUCTION


def build_generation_prompt(topic: str, context: str, use_structured_output: bool = False) -> str:
  """Builds a prompt for generating ideas based on user input and context.

  Args:
    topic: The user's prompt/request for idea generation (can be questions, 
           statements, requests, or simple topics).
    context: Additional context or constraints for the idea generation process.
    use_structured_output: Whether to use structured JSON output.

  Returns:
    A formatted prompt string to be used by the idea generator agent.
  """
  # Detect broad/philosophical topics that need simplification
  broad_topic_keywords = ['humanity', 'future of', 'meaning of', 'philosophy', 'existence', 
                         'universe', 'consciousness', 'life', 'death', 'reality', 'truth']
  is_broad_topic = any(keyword in topic.lower() for keyword in broad_topic_keywords)
  
  # Add extra guidance for broad topics
  broad_topic_guidance = ""
  if is_broad_topic:
      broad_topic_guidance = """
SPECIAL GUIDANCE FOR BROAD TOPICS:
- Focus on CONCRETE, SPECIFIC ideas that people can actually implement
- Avoid philosophical abstractions or theoretical concepts
- Each idea should suggest a clear action, project, or initiative
- Think "What can someone DO about this?" rather than "What does this mean?"

"""
  
  # Use different prompts for structured vs unstructured output
  if use_structured_output:
    # Simpler prompt when using structured output - no formatting instructions needed
    prompt_template = f"""{LANGUAGE_CONSISTENCY_INSTRUCTION}Generate creative and innovative ideas based on the topic and context provided.
Focus on practical, actionable ideas that address the user's needs.
{broad_topic_guidance}
Topic:
{topic}

Context:
{context}

Generate 5 diverse ideas that are innovative, practical, and directly address the topic within the given context."""
  else:
    # Legacy prompt with formatting instructions for text output
    prompt_template = f"""{LANGUAGE_CONSISTENCY_INSTRUCTION}Use the user's main prompt and context below to {IDEA_GENERATION_INSTRUCTION}.
Make sure the ideas are actionable and innovative.

IMPORTANT FORMAT REQUIREMENTS:
- Generate exactly 5 diverse ideas
- Start your response directly with "1." (no introductory text)
- Keep each idea concise (2-3 sentences maximum)
- Number each idea clearly (1., 2., 3., 4., 5.)
- For broad or philosophical topics, focus on specific, actionable ideas
{broad_topic_guidance}
User's main prompt:
{topic}

Context:
{context}

Start your response here with idea #1:
"""
  return prompt_template


def build_improvement_prompt(
    original_idea: str,
    critique: str,
    advocacy_points: str,
    skeptic_points: str,
    topic: str,
    context: str,
    logical_inference: Optional[str] = None,
    initial_score: Optional[float] = None,
    dimension_scores: Optional[Dict[str, float]] = None
) -> str:
  """Builds a prompt for improving an idea based on feedback.

  Args:
    original_idea: The original idea to improve.
    critique: The critic's evaluation of the idea.
    advocacy_points: The advocate's structured bullet points.
    skeptic_points: The skeptic's structured concerns.
    topic: The main topic/theme for the idea.
    context: The constraints or additional context for improvement.
    logical_inference: Optional logical analysis results to inform improvement.
    initial_score: Optional initial score from critic (0-10 scale).
    dimension_scores: Optional dict of dimension scores (feasibility, innovation, etc.).

  Returns:
    A formatted prompt string for idea improvement.
  """
  # Build score section if provided (Issue #219)
  score_section = ""
  if initial_score is not None:
    score_section = f"INITIAL SCORE: {initial_score}/10\n"
    if dimension_scores:
      score_section += "DIMENSION SCORES:\n"
      # Find weak dimensions to prioritize (score < 7)
      weak_dims = [k for k, v in dimension_scores.items() if v < 7]
      for dim, score in dimension_scores.items():
        dim_name = dim.replace('_', ' ').title()
        marker = " [PRIORITY]" if dim in weak_dims else ""
        score_section += f"  - {dim_name}: {score}/10{marker}\n"
      score_section += "\n"

  # Build logical inference section if provided
  logical_section = ""
  if logical_inference:
    logical_section = f"LOGICAL INFERENCE ANALYSIS:\n{logical_inference}\n\n"

  # Build logical inference guidance if provided
  logical_guidance = ""
  if logical_inference:
    logical_guidance = "- Use logical reasoning insights to enhance coherence and address any logical gaps\n"

  # Build logical inference instruction if provided
  logical_instruction = ""
  if logical_inference:
    logical_instruction = "6. Incorporates insights from the logical inference analysis\n"

  return (
      "You are helping to enhance an innovative idea based on comprehensive feedback.\n" +
      LANGUAGE_CONSISTENCY_INSTRUCTION +
      f"TOPIC: {topic}\n"
      f"CONTEXT: {context}\n\n"
      f"{score_section}"
      f"ORIGINAL IDEA:\n{original_idea}\n\n"
      f"EVALUATION CRITERIA AND FEEDBACK:\n{critique}\n"
      f"Pay special attention to the specific scores and criteria mentioned above. "
      f"Your improved version should directly address any low-scoring areas while maintaining high-scoring aspects.\n\n"
      f"{logical_section}"
      f"STRENGTHS TO PRESERVE AND BUILD UPON:\n{advocacy_points}\n\n"
      f"CONCERNS TO ADDRESS WITH SOLUTIONS:\n{skeptic_points}\n\n"
      f"Generate an IMPROVED version of this idea that:\n"
      f"1. SPECIFICALLY addresses each evaluation criterion from the professional review\n"
      f"2. Maintains and amplifies the identified strengths\n"
      f"3. Provides concrete solutions for each concern raised\n"
      f"4. Remains bold, creative, and ambitious\n"
      f"5. Shows clear improvements in the areas that scored lower\n"
      f"{logical_instruction}\n"
      f"IMPORTANT GUIDELINES:\n"
      f"- If feasibility scored low, add specific implementation steps\n"
      f"- If innovation scored low, add unique differentiating features\n"
      f"- If cost-effectiveness scored low, optimize resource usage\n"
      f"- If scalability scored low, design for growth\n"
      f"- Keep all positive aspects while fixing weaknesses\n"
      f"{logical_guidance}"
      f"FORMAT REQUIREMENTS:\n"
      f"- Start directly with your improved idea (no meta-commentary)\n"
      f"- Present the idea in 2-3 clear, focused paragraphs\n"
      f"- Keep the total response under 500 words\n"
      f"- Make the first sentence compelling and complete\n\n"
      f"Present your improved idea below:"
  )


def generate_fallback_improvement(original_idea: str, reason: str, advocacy_points: str = "") -> str:
  """Generate a fallback improvement message based on the reason for fallback.
  
  Args:
    original_idea: The original idea to improve.
    reason: The reason for using fallback ('safety', 'recitation', 'empty', etc.).
    advocacy_points: Optional advocacy points to include in some templates.
    
  Returns:
    A formatted fallback improvement message.
  """
  templates = {
      "safety": f"Enhanced version of: {original_idea}\n\nKey improvements based on multi-agent feedback:\n- Preserved strengths: {advocacy_points[:100]}{'...' if len(advocacy_points) > 100 else ''}\n- Incorporated professional insights for enhancement\n- Enhanced practical implementation approach\n- Addressed thoughtful considerations with solutions",
      "recitation": f"Refined approach: {original_idea}\n\nOptimizations based on feedback:\n- Leveraged identified strengths\n- Incorporated professional insights\n- Enhanced practical implementation\n- Improved scalability and resource efficiency",
      "empty": f"Improved: {original_idea}\n\nEnhancements based on analysis:\n- Built upon positive strengths\n- Incorporated professional insights\n- Optimized implementation approach\n- Enhanced cost-effectiveness and viability",
      "no_candidates": f"Enhanced: {original_idea}\n\nKey improvements from multi-agent analysis:\n- Preserved core innovation strengths\n- Addressed thoughtful considerations\n- Enhanced practical implementation\n- Improved scalability and cost optimization",
      "content_filtered": f"Optimized version: {original_idea}\n\nImprovements based on multi-agent feedback:\n- Enhanced feasibility with thoughtful considerations\n- Better resource efficiency from positive insights\n- Practical implementation approach incorporating professional analysis",
      "value_error": f"Modified: {original_idea}\n\nEnhancements from feedback synthesis:\n- Improved approach based on professional insights\n- Better implementation incorporating strengths\n- Enhanced viability addressing opportunities",
      "general_error": f"Updated: {original_idea}\n\nImprovements from multi-agent analysis:\n- Refined implementation based on professional insights\n- Enhanced approach incorporating positive strengths\n- Better execution strategy addressing thoughtful considerations"
  }
  return templates.get(reason, templates["general_error"])
