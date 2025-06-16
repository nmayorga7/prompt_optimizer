"""
XML parsing utilities.
"""

import re
from typing import Dict, List


def extract_xml_content(text: str, tag: str) -> str:
    """Extract content from XML tags, handling potential parsing errors."""
    pattern = f"<{tag}>(.*?)</{tag}>"
    match = re.search(pattern, text, re.DOTALL)
    return match.group(1).strip() if match else ""


def parse_xml_response(response: str, tags: List[str]) -> Dict[str, str]:
    """Parse multiple XML tags from a response."""
    return {tag: extract_xml_content(response, tag) for tag in tags}


# Common tag sets
ASSESSMENT_TAGS = ["intent", "reasoning", "initial_understanding"]

REFINEMENT_TAGS = [
    "thinking", "extracted_context", "extracted_goal", "extracted_format",
    "ai_role", "additional_insights", "score", "reasoning", 
    "ready_to_finalize", "user_message"
]

OPTIMIZATION_TAGS = ["thinking", "optimized_prompt", "improvement_summary"]