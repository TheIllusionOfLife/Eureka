# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Eureka is a Python project currently in initial setup phase. The project is licensed under GPL-3.0.

## Development Setup

Since this is a newly initialized Python project with no existing structure, when implementing features:

1. **Python Environment**: Set up a virtual environment before installing dependencies
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Project Structure**: When creating the initial structure, follow standard Python project layout:
   - Place source code in a package directory (e.g., `eureka/`)
   - Create `tests/` directory for test files
   - Add `requirements.txt` or `pyproject.toml` for dependency management

## Important Notes

- The `.gitignore` is configured for Python projects including Django, Flask, and Jupyter patterns
- No existing codebase or architecture to follow yet - this is a blank slate
- When implementing, establish clear patterns for future development

## Development Philosophy

### Test-Driven Development (TDD)

* As an overall principle, do test-driven development.
* First, write tests based on expected input/ouput pairs. Avoid creating mock implementations, even for functionality that doesn't exist yet in the codebase.
* Second, run the tests and confirm they fail. Do not write any implementation code at this stage.
* Third, commit the test when you're satisfied with them.
* Then, write code that passes the tests. Do not modify the tests. Keep going until all tests pass.
* Finally, commit the code once only when you're satisfied with the changes.
