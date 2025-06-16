"""
Data models for the prompt optimizer.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
from enum import Enum


class UserIntent(Enum):
    """Represents the user's intent when using the prompt optimizer."""
    OPTIMIZE_EXISTING = "optimize_existing"
    CREATE_NEW = "create_new"
    UNCLEAR = "unclear"


@dataclass
class ContextUnderstanding:
    """Tracks what we understand about the user's prompt requirements."""
    context: str = "Not yet clear"
    goal: str = "Not yet clear"
    format: str = "Not yet clear"
    ai_role: str = "Not yet clear"
    additional_insights: str = ""


@dataclass
class OptimizationResult:
    """Contains the results of prompt optimization."""
    optimized_prompt: str
    improvements: str
    test_cases: Optional[str] = None


@dataclass
class ConversationState:
    """Maintains the state of the optimization conversation."""
    messages: List[Dict[str, str]] = field(default_factory=list)
    context_understanding: ContextUnderstanding = field(default_factory=ContextUnderstanding)
    original_input: str = ""
    user_intent: UserIntent = UserIntent.UNCLEAR