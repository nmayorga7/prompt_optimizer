"""
Type definitions for the prompt optimizer.
"""

from typing import TypedDict, List, Dict, Optional, Literal
from enum import Enum


class UserIntent(Enum):
    """Represents the user's intent when using the prompt optimizer."""
    OPTIMIZE_EXISTING = "optimize_existing"
    CREATE_NEW = "create_new"
    UNCLEAR = "unclear"


class ContextUnderstanding(TypedDict):
    """Tracks what we understand about the user's prompt requirements."""
    context: str
    goal: str
    format: str
    ai_role: str
    additional_insights: str


class OptimizationResult(TypedDict):
    """Contains the results of prompt optimization."""
    optimized_prompt: str
    improvements: str
    test_cases: Optional[str]


class ConversationState(TypedDict):
    """Maintains the state of the optimization conversation."""
    messages: List[Dict[str, str]]
    context_understanding: ContextUnderstanding
    original_input: str
    user_intent: UserIntent


# Test case tuple: (scenario, input, expected)
TestCase = tuple[str, str, str]