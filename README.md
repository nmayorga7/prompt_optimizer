# Prompt Optimizer

A tool to optimize user prompts through automated task identification and CRISPO-inspired single candidate optimization techniques (He et al., 2025).

## Overview

This tool helps improve prompt effectiveness by:
1. **Task Classification**: Automatically identifies the type of task (summarization, question-answering, code-generation, etc.)
2. **Prompt Clarification**: Enhances prompts based on their identified task type
3. **CRISPO Optimization**: Applies critique-based optimization to generate improved prompts

## Installation

```bash
pip install -e .
```

For development:
```bash
pip install -e ".[dev]"
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

Run the interactive prompt optimizer:
```bash
python -m prompt_optimizer.main
```

Or use programmatically:
```python
from prompt_optimizer import prompt_optimizer

results = prompt_optimizer.run_prompt_optimizer("Your prompt here", "gpt-3.5-turbo")
print(results['crispo_prompt'])
```

## Development

Run linting and type checking:
```bash
ruff check .
mypy .
```

## Author

Natasha Mayorga

## License

MIT License