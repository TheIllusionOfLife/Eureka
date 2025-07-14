#!/usr/bin/env python3
"""
Real-time agent monitoring - shows what each agent is doing step by step
"""

import os
import logging
import json
from datetime import datetime

# Load environment variables first
try:
    from dotenv import load_dotenv
    if os.path.exists(".env"):
        load_dotenv()
except ImportError:
    pass

# Import all agents
from agent_defs.idea_generator import generate_ideas
from agent_defs.critic import evaluate_ideas
from agent_defs.advocate import advocate_idea
from agent_defs.skeptic import criticize_idea
from novelty_filter import NoveltyFilter

class AgentMonitor:
    """Monitor and log each agent's activity in real-time"""
    
    def __init__(self):
        self.setup_logging()
        self.step_count = 0
    
    def setup_logging(self):
        """Set up real-time logging"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(message)s',
            datefmt='%H:%M:%S'
        )
        self.logger = logging.getLogger(__name__)
    
    def log_step(self, agent_name, action, details=""):
        """Log each step with visual indicators"""
        self.step_count += 1
        print(f"\n{'='*60}")
        print(f"STEP {self.step_count}: {agent_name} - {action}")
        print(f"{'='*60}")
        if details:
            print(details)
        print()
    
    def run_monitored_workflow(self, theme, constraints, num_candidates=2):
        """Run workflow with step-by-step monitoring"""
        
        print("🔍 REAL-TIME AGENT MONITORING")
        print("=" * 60)
        print(f"Theme: {theme}")
        print(f"Constraints: {constraints}")
        print(f"Target candidates: {num_candidates}")
        
        results = {}
        
        # STEP 1: Idea Generation
        self.log_step("💡 IDEA GENERATOR", "Generating creative ideas", 
                     f"Temperature: 0.9 (high creativity)\nPrompt: Generate ideas for '{theme}' with constraints '{constraints}'")
        
        try:
            raw_ideas = generate_ideas(topic=theme, context=constraints, temperature=0.9)
            parsed_ideas = [idea.strip() for idea in raw_ideas.split("\n") if idea.strip()]
            
            print(f"✅ Generated {len(parsed_ideas)} raw ideas")
            print("📝 Sample ideas:")
            for i, idea in enumerate(parsed_ideas[:3], 1):
                print(f"  {i}. {idea[:80]}...")
            
            results['raw_ideas'] = parsed_ideas
            results['raw_response'] = raw_ideas
            
        except Exception as e:
            print(f"❌ Error in idea generation: {e}")
            return results
        
        # STEP 2: Novelty Filtering
        self.log_step("🔍 NOVELTY FILTER", "Removing duplicate/similar ideas",
                     f"Similarity threshold: 0.8\nInput: {len(parsed_ideas)} ideas")
        
        try:
            novelty_filter = NoveltyFilter(similarity_threshold=0.8)
            filtered_ideas = novelty_filter.get_novel_ideas(parsed_ideas)
            removed_count = len(parsed_ideas) - len(filtered_ideas)
            
            print(f"✅ Filtered ideas: {len(filtered_ideas)} (removed {removed_count} duplicates)")
            results['filtered_ideas'] = filtered_ideas
            
        except Exception as e:
            print(f"❌ Error in novelty filtering: {e}")
            filtered_ideas = parsed_ideas
        
        # STEP 3: Critic Evaluation
        self.log_step("🔍 CRITIC AGENT", "Evaluating all ideas for feasibility",
                     f"Temperature: 0.3 (analytical mode)\nEvaluating: {len(filtered_ideas)} ideas")
        
        try:
            ideas_string = "\n".join(filtered_ideas)
            raw_evaluation = evaluate_ideas(
                ideas=ideas_string,
                criteria="feasibility, innovation, profitability, market demand",
                context=f"Theme: {theme}, Constraints: {constraints}",
                temperature=0.3
            )
            
            print(f"✅ Evaluation completed: {len(raw_evaluation)} characters")
            print("📊 Sample evaluation:")
            print(f"```\n{raw_evaluation[:200]}...\n```")
            
            results['evaluation'] = raw_evaluation
            
        except Exception as e:
            print(f"❌ Error in evaluation: {e}")
            return results
        
        # STEP 4: Select Top Candidates
        self.log_step("🎯 CANDIDATE SELECTION", "Selecting top ideas for detailed analysis",
                     f"Selecting top {num_candidates} ideas based on scores")
        
        # For demo, we'll take first few ideas
        top_ideas = filtered_ideas[:num_candidates]
        print(f"✅ Selected {len(top_ideas)} top candidates:")
        for i, idea in enumerate(top_ideas, 1):
            print(f"  {i}. {idea[:80]}...")
        
        results['top_candidates'] = top_ideas
        
        # STEP 5: Advocacy Analysis
        for i, idea in enumerate(top_ideas, 1):
            self.log_step(f"✅ ADVOCATE AGENT", f"Building case for idea #{i}",
                         f"Temperature: 0.5 (balanced persuasion)\nIdea: {idea[:100]}...")
            
            try:
                advocacy = advocate_idea(
                    idea=idea,
                    evaluation="High potential idea with good market fit",
                    context=f"Theme: {theme}, Constraints: {constraints}",
                    temperature=0.5
                )
                
                print(f"✅ Advocacy completed: {len(advocacy)} characters")
                print("💪 Sample advocacy:")
                print(f"```\n{advocacy[:200]}...\n```")
                
                results[f'advocacy_{i}'] = advocacy
                
            except Exception as e:
                print(f"❌ Error in advocacy: {e}")
        
        # STEP 6: Skeptical Analysis
        for i, idea in enumerate(top_ideas, 1):
            self.log_step(f"⚠️ SKEPTIC AGENT", f"Analyzing risks for idea #{i}",
                         f"Temperature: 0.5 (balanced skepticism)\nIdea: {idea[:100]}...")
            
            try:
                skepticism = criticize_idea(
                    idea=idea,
                    advocacy="Strong potential but needs careful consideration",
                    context=f"Theme: {theme}, Constraints: {constraints}",
                    temperature=0.5
                )
                
                print(f"✅ Skeptical analysis completed: {len(skepticism)} characters")
                print("⚠️ Sample skepticism:")
                print(f"```\n{skepticism[:200]}...\n```")
                
                results[f'skepticism_{i}'] = skepticism
                
            except Exception as e:
                print(f"❌ Error in skeptical analysis: {e}")
        
        # FINAL SUMMARY
        self.log_step("🎉 WORKFLOW COMPLETE", "All agents have completed their tasks")
        print("📊 Final Summary:")
        print(f"  • Generated: {len(parsed_ideas)} raw ideas")
        print(f"  • Filtered: {len(filtered_ideas)} novel ideas")
        print(f"  • Analyzed: {len(top_ideas)} top candidates")
        print(f"  • Total steps: {self.step_count}")
        
        return results

def main():
    """Run the monitored workflow"""
    monitor = AgentMonitor()
    
    # Run with your test parameters
    results = monitor.run_monitored_workflow(
        theme="earn money",
        constraints="no illegal activities",
        num_candidates=2
    )
    
    print(f"\n🎯 Monitoring complete! Generated {len(results)} result components.")

if __name__ == "__main__":
    main()