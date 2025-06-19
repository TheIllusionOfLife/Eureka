# MadSpark Multi-Agent System

This project implements a multi-agent system for idea generation and refinement using the Google ADK (Agent Development Kit). It includes agents for idea generation, criticism, advocacy, and skepticism, orchestrated by a coordinator.

## Prerequisites

- Python 3.x (e.g., Python 3.9 or newer recommended)
- Access to Google Gemini API (or other compatible models configured via ADK)

## Setup

1.  **Clone the repository (if applicable).**
    If you have cloned a repository containing this project, navigate into the `mad_spark_multiagent` directory. If you received the files directly, ensure they are all within a directory named `mad_spark_multiagent`.

2.  **Create a virtual environment (recommended):**
    From within the `mad_spark_multiagent` directory:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **API Key Configuration:**
    This application requires a Google API Key for accessing the configured generative models.
    - Create a file named `.env` in the `mad_spark_multiagent` project directory (i.e., alongside `coordinator.py`).
    - Add your API key and the model name to the `.env` file. For example:
      ```env
      GOOGLE_API_KEY="YOUR_API_KEY_HERE"
      GOOGLE_GENAI_MODEL="gemini-pro"
      ```
      Replace `"YOUR_API_KEY_HERE"` with your actual API key. You can choose a different model compatible with the Google AI SDK if desired (e.g., "gemini-1.5-flash-latest").

    **Important Security Note:** Storing API keys in `.env` files is suitable for local development. For production environments, it is strongly recommended to use a dedicated secret management service (e.g., Google Cloud Secret Manager, HashiCorp Vault) to protect your API keys. Do not commit `.env` files containing sensitive keys to version control (the provided `.gitignore` file in the parent directory should prevent this if this project is part of a larger repository structure, or you should ensure a local `.gitignore` also lists `.env`).

## Running the System

The main coordinator script can be run to test the workflow:
From within the `mad_spark_multiagent` directory:
```bash
python coordinator.py
```
This will use the sample `theme` and `constraints` defined in the `if __name__ == "__main__":` block of `coordinator.py`. You can modify these to test different scenarios. The output will be a JSON representation of the processed ideas.

## Project Structure

- `agent_defs/`: Contains the definitions for individual agents (`idea_generator.py`, `critic.py`, `advocate.py`, `skeptic.py`).
  - `__init__.py`: Exports the agent instances.
- `coordinator.py`: Orchestrates the agents and manages the overall workflow.
- `requirements.txt`: Lists project dependencies (`google-adk`, `python-dotenv`).
- `.env` (create this file locally, gitignored): For storing your `GOOGLE_API_KEY` and `GOOGLE_GENAI_MODEL`.
- `README.md`: This file.

## How it Works

1.  The `Coordinator` (`coordinator.py`) takes a `theme` and `constraints` (both strings) as input.
2.  The `IdeaGeneratorAgent` (`agent_defs/idea_generator.py`) generates a list of ideas based on this input.
3.  The `CriticAgent` (`agent_defs/critic.py`) evaluates these ideas, providing a score (1-10) and a textual comment for each. The evaluations are requested as newline-separated JSON strings.
4.  The `Coordinator` parses these evaluations. If parsing fails for an idea, defaults are used, and a warning is logged. It then selects the top-scoring ideas (default is top 2, configurable).
5.  For each selected top idea:
    - The `AdvocateAgent` (`agent_defs/advocate.py`) generates arguments highlighting the idea's strengths and potential.
    - The `SkepticAgent` (`agent_defs/skeptic.py`) critically analyzes the idea and its advocacy, pointing out potential weaknesses or risks.
    - Failures in advocacy or skepticism for one idea are logged as warnings, and placeholder text is used, allowing the workflow to continue for other ideas.
6.  The `Coordinator` compiles and returns (prints as JSON) the final list of candidates with all collected information (original idea, score, critique, advocacy, and skepticism).
7.  Critical errors, such as failure to generate any initial ideas or a complete failure of the critic agent, will result in an empty list of results. API key and model configuration issues are checked before agent initialization and will cause the script to exit with an error if not configured.
