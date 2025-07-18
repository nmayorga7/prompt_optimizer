# Prompt Optimizer

A tool to optimize user prompts through automated task identification and CRISPO-inspired single candidate optimization techniques (He et al., 2025).

## Overview

This tool helps improve prompt effectiveness by:
1. **Task Classification**: Automatically identifies the type of task (summarization, question-answering, code-generation, etc.)
2. **Prompt Clarification**: Enhances prompts based on their identified task type
3. **CRISPO Optimization**: Applies critique-based optimization to generate improved prompts

## Quick Start with UV (Recommended)

[uv](https://docs.astral.sh/uv/) is a fast Python package manager. Install it first:

### Install uv

**macOS/Linux:**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**Windows (PowerShell):**
```powershell
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### Install and Run

1. Clone the repository and navigate to it
2. Copy the environment file and add your OpenAI API key:
   ```bash
   cp .env.example .env
   # Edit .env and add your OPENAI_API_KEY
   ```

3. Run the prompt optimizer:
   ```bash
   uv run prompt-optimizer
   ```

That's it! uv will automatically install all dependencies and run the tool.

## Alternative Installation (pip)

If you prefer using pip:

```bash
pip install -e .
```

For development:
```bash
pip install -e ".[dev]"
```

Then run:
```bash
python -m prompt_optimizer.main
```

## Configuration

Create a `.env` file with your OpenAI API key:
```
OPENAI_API_KEY=your-openai-api-key-here
```

Or copy the example file:
```bash
cp .env.example .env
```

## Usage

### Interactive Mode

Run the interactive prompt optimizer:
```bash
uv run prompt-optimizer
```

### Programmatic Usage

```python
from prompt_optimizer import prompt_optimizer

results = prompt_optimizer.run_prompt_optimizer("Your prompt here", "gpt-3.5-turbo")
print(f"Original: {results['task_type']}")
print(f"Clarified: {results['clarified_prompt']}")
print(f"Optimized: {results['crispo_prompt']}")
```

## Development

Run linting and type checking with uv:
```bash
uv run ruff check .
uv run mypy .
```

Or with traditional tools:
```bash
ruff check .
mypy .
```

## Author

Natasha Mayorga

## License

MIT License