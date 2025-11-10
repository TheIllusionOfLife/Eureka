#!/usr/bin/env python3
"""
Run MadSpark with detailed logging to see all agent processes
"""

import os
import logging
import sys
from datetime import datetime

# Load environment variables first
try:
    from dotenv import load_dotenv
    if os.path.exists(".env"):
        load_dotenv()
except ImportError:
    pass

# Configure detailed logging
def setup_detailed_logging(log_level=logging.DEBUG):
    """Set up comprehensive logging for all agents"""
    
    # Create logs directory if it doesn't exist
    os.makedirs("logs", exist_ok=True)
    
    # Create timestamped log file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = f"logs/madspark_detailed_{timestamp}.log"
    
    # Configure logging with both file and console output
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(funcName)s() - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    return log_file

def run_with_logging():
    """Run MadSpark workflow with detailed logging"""
    
    print("🔍 MadSpark Production Run with Detailed Logging")
    print("=" * 60)
    
    # Set up logging
    log_file = setup_detailed_logging(logging.DEBUG)
    print(f"📁 Detailed logs saved to: {log_file}")
    print()
    
    # Import after logging is configured
    from coordinator import run_workflow
    
    # Test parameters
    theme = "earn money"
    constraints = "no illegal activities"
    num_candidates = 2
    
    print(f"🎯 Theme: {theme}")
    print(f"📋 Constraints: {constraints}")
    print(f"📊 Number of candidates: {num_candidates}")
    print()
    print("🚀 Starting detailed workflow...")
    print("=" * 60)
    
    try:
        # Run the complete workflow with detailed logging
        results = run_workflow(
            theme=theme,
            constraints=constraints,
            num_candidates=num_candidates,
            idea_temp=0.9,
            eval_temp=0.3,
            advocacy_temp=0.5,
            skepticism_temp=0.5,
            enable_novelty_filter=True,
            novelty_threshold=0.8
        )
        
        print("=" * 60)
        print("✅ Workflow completed successfully!")
        print(f"📁 Check detailed logs in: {log_file}")
        print(f"📊 Generated {len(results)} final ideas")
        
        return results, log_file
        
    except Exception as e:
        logging.error(f"Workflow failed: {str(e)}")
        print(f"❌ Error: {e}")
        return None, log_file

if __name__ == "__main__":
    results, log_file = run_with_logging()
    
    if results:
        print("\n💡 Final Results Summary:")
        for i, result in enumerate(results, 1):
            print(f"{i}. {result.get('idea', 'N/A')[:100]}...")
    
    print("\n📖 View complete logs with:")
    print(f"   cat {log_file}")
    print(f"   tail -f {log_file}  # For real-time monitoring")