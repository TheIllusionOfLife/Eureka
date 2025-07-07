#!/usr/bin/env python3
"""
Phase 2.2 Web Interface Demo - MadSpark Multi-Agent System

This script demonstrates the new Phase 2.2 features including:
- Web interface capabilities
- Export functionality
- Enhanced CLI options

Run this demo to see the new features in action.
"""
import os
import sys
import subprocess
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from export_utils import ExportManager, create_metadata_from_args
from coordinator import run_multistep_workflow


def demo_export_functionality():
    """Demonstrate the new export functionality."""
    print("🔍 Phase 2.2 Export Demo")
    print("=" * 50)
    
    # Sample theme and constraints
    theme = "Sustainable Urban Transportation"
    constraints = "Cost-effective, environmentally friendly, implementable within 3 years"
    
    print(f"Theme: {theme}")
    print(f"Constraints: {constraints}")
    print("\n🚀 Generating ideas with enhanced reasoning...")
    
    # Run workflow with enhanced features
    results = run_multistep_workflow(
        theme=theme,
        constraints=constraints,
        num_top_candidates=2,
        enhanced_reasoning=True,
        multi_dimensional_eval=True,
        verbose=False
    )
    
    if not results:
        print("❌ No results generated")
        return
    
    print(f"✅ Generated {len(results)} ideas")
    
    # Demo export functionality
    print("\n📁 Demonstrating export functionality...")
    
    # Create export manager
    export_manager = ExportManager("demo_exports")
    
    # Create metadata
    metadata = {
        "theme": theme,
        "constraints": constraints,
        "enhanced_reasoning": True,
        "multi_dimensional_eval": True,
        "logical_inference": False,
        "demo_run": True
    }
    
    # Export to all formats
    try:
        exported_files = export_manager.export_all_formats(results, metadata, "demo_export")
        
        print("\n📄 Export Results:")
        for format_name, file_path in exported_files.items():
            if file_path.startswith("Error:") or file_path.startswith("Not available"):
                print(f"  {format_name.upper()}: {file_path}")
            else:
                print(f"  {format_name.upper()}: ✅ {file_path}")
                
        # Show sample content from markdown export
        if 'markdown' in exported_files and not exported_files['markdown'].startswith("Error"):
            print(f"\n📝 Sample Markdown Content:")
            print("-" * 30)
            with open(exported_files['markdown'], 'r', encoding='utf-8') as f:
                lines = f.readlines()
                for line in lines[:15]:  # Show first 15 lines
                    print(line.rstrip())
                if len(lines) > 15:
                    print("... (content truncated)")
            print("-" * 30)
                
    except Exception as e:
        print(f"❌ Export demo failed: {e}")


def demo_cli_export():
    """Demonstrate CLI export functionality."""
    print("\n🖥️  CLI Export Demo")
    print("=" * 50)
    
    # Demo CLI command with export
    cli_command = [
        sys.executable, "cli.py",
        "Smart City Technology",
        "Budget-friendly, citizen-focused",
        "--num-candidates", "1",
        "--enhanced-reasoning",
        "--export", "markdown",
        "--export-filename", "cli_demo_export"
    ]
    
    print("Running CLI command:")
    print(" ".join(cli_command))
    print()
    
    try:
        # Run CLI command
        result = subprocess.run(
            cli_command,
            capture_output=True,
            text=True,
            timeout=60  # 1 minute timeout
        )
        
        if result.returncode == 0:
            print("✅ CLI export successful!")
            print("\nCLI Output:")
            print(result.stdout)
        else:
            print("❌ CLI export failed:")
            print(result.stderr)
            
    except subprocess.TimeoutExpired:
        print("⏰ CLI command timed out")
    except Exception as e:
        print(f"❌ CLI demo failed: {e}")


def demo_web_interface_setup():
    """Show how to set up the web interface."""
    print("\n🌐 Web Interface Setup Demo")
    print("=" * 50)
    
    web_dir = Path("web")
    
    if web_dir.exists():
        print("✅ Web interface files are available!")
        print("\nTo start the web interface:")
        print("\n1. Backend (Terminal 1):")
        print("   cd web/backend")
        print("   pip install -r requirements.txt")
        print("   python main.py")
        print("   # API will be available at http://localhost:8000")
        
        print("\n2. Frontend (Terminal 2):")
        print("   cd web/frontend")
        print("   npm install")
        print("   npm start")
        print("   # Web interface will be available at http://localhost:3000")
        
        print("\n📚 Features available in web interface:")
        print("   • Real-time idea generation with progress updates")
        print("   • Interactive forms with all CLI features")
        print("   • Enhanced reasoning toggles")
        print("   • Multi-dimensional evaluation")
        print("   • Responsive design for desktop and mobile")
        
        # Check if backend/frontend files exist
        backend_main = web_dir / "backend" / "main.py"
        frontend_package = web_dir / "frontend" / "package.json"
        
        if backend_main.exists():
            print("   ✅ Backend files ready")
        else:
            print("   ❌ Backend files missing")
            
        if frontend_package.exists():
            print("   ✅ Frontend files ready")
        else:
            print("   ❌ Frontend files missing")
    else:
        print("❌ Web interface directory not found")
        print("Make sure you're running this from the MadSpark directory")


def main():
    """Run all Phase 2.2 demos."""
    print("🧠 MadSpark Phase 2.2 Feature Demo")
    print("=" * 60)
    print("This demo showcases the new Phase 2.2 features:")
    print("• Export functionality (JSON, CSV, Markdown, PDF)")
    print("• Enhanced CLI options")
    print("• Web interface setup guide")
    print("=" * 60)
    
    try:
        # Demo 1: Export functionality
        demo_export_functionality()
        
        # Demo 2: CLI export
        demo_cli_export()
        
        # Demo 3: Web interface setup
        demo_web_interface_setup()
        
        print("\n🎉 Phase 2.2 Demo Complete!")
        print("\nNext steps:")
        print("1. Try the export functionality: python cli.py 'Your theme' 'Your constraints' --export all")
        print("2. Set up the web interface following the instructions above")
        print("3. Explore the new features in examples/README.md")
        
    except KeyboardInterrupt:
        print("\n\n⏹️  Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()