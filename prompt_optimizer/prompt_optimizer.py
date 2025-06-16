"""
PROMPT OPTIMIZER - AI-Powered Prompt Engineering Assistant

Main entry point for the prompt optimizer.
"""

from . import ui
from .optimizer import run_optimization_flow


def run_prompt_optimizer(model: str) -> None:
    """Main function to run the prompt optimizer."""
    try:
        run_optimization_flow(model)
    except KeyboardInterrupt:
        ui.show_cancellation()
    except Exception as e:
        ui.show_error(str(e))
        raise