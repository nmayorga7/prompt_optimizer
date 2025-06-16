"""
Core optimization logic for the prompt optimizer.
"""

import re
from typing import List, Dict, Optional

from . import ui
from . import ai_client
from . import prompts
from .xml_utils import parse_xml_response, extract_xml_content, ASSESSMENT_TAGS, REFINEMENT_TAGS, OPTIMIZATION_TAGS
from .types import (
    UserIntent, ContextUnderstanding, OptimizationResult, 
    ConversationState, TestCase
)


def create_initial_state() -> ConversationState:
    """Create an initial conversation state."""
    return {
        'messages': [],
        'context_understanding': {
            'context': "Not yet clear",
            'goal': "Not yet clear",
            'format': "Not yet clear",
            'ai_role': "Not yet clear",
            'additional_insights': ""
        },
        'original_input': "",
        'user_intent': UserIntent.UNCLEAR
    }


def assess_user_intent(model: str, user_input: str) -> tuple[UserIntent, str]:
    """Determine what the user wants to do."""
    with ui.show_progress("Understanding your request..."):
        response = ai_client.chat_completion(
            model=model,
            messages=[
                {"role": "system", "content": prompts.ASSESSMENT_PROMPT},
                {"role": "user", "content": user_input}
            ],
            temperature=0.3
        )
    
    parsed = parse_xml_response(response, ASSESSMENT_TAGS)
    intent_str = parsed.get("intent", "unclear")
    initial_understanding = parsed.get("initial_understanding", "")
    
    # Map string to enum
    intent_map = {
        "optimize_existing": UserIntent.OPTIMIZE_EXISTING,
        "create_new": UserIntent.CREATE_NEW,
        "unclear": UserIntent.UNCLEAR
    }
    
    return intent_map.get(intent_str, UserIntent.UNCLEAR), initial_understanding


def initialize_conversation(state: ConversationState) -> None:
    """Set up the conversation based on user intent."""
    if state['user_intent'] == UserIntent.CREATE_NEW:
        system_prompt = prompts.get_creation_prompt()
        start_message = f"""User's request: '{state['original_input']}'

I understand you want to create a new prompt. {state['context_understanding']['additional_insights']}

Please begin helping them create an effective prompt."""
    else:
        system_prompt = prompts.get_optimization_prompt()
        start_message = f"""Initial prompt: '{state['original_input']}'

Please begin the refinement process."""
    
    state['messages'] = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": start_message}
    ]


def update_context_understanding(state: ConversationState, parsed: Dict[str, str]) -> None:
    """Update our understanding based on the AI's analysis."""
    fields = ["context", "goal", "format", "ai_role", "additional_insights"]
    field_map = {
        "extracted_context": "context",
        "extracted_goal": "goal",
        "extracted_format": "format",
        "ai_role": "ai_role",
        "additional_insights": "additional_insights"
    }
    
    for parsed_key, state_key in field_map.items():
        value = parsed.get(parsed_key)
        if value and value != "Not yet clear":
            state['context_understanding'][state_key] = value


def refinement_loop(model: str, state: ConversationState) -> None:
    """Main conversation loop for refining the prompt."""
    ui.show_refinement_header()
    
    while True:
        # Get AI response
        with ui.show_progress("Assistant is thinking..."):
            response = ai_client.chat_completion(model, state['messages'])
        
        state['messages'].append({"role": "assistant", "content": response})
        
        # Parse and process response
        parsed = parse_xml_response(response, REFINEMENT_TAGS)
        update_context_understanding(state, parsed)
        
        # Display assistant message
        user_message = parsed.get("user_message", "")
        if user_message:
            ui.show_assistant_message(user_message)
        
        # Check if ready to finalize
        if parsed.get("ready_to_finalize") == "yes":
            try:
                confidence = float(parsed.get("score", "0.8"))
                ui.show_ready_to_optimize(confidence)
            except ValueError:
                pass
        
        # Get user input
        user_input = ui.get_user_input(
            "\n[bold yellow]👤 Your response[/bold yellow] [dim](or 'finalize' to finish)[/dim]"
        )
        
        if user_input.lower() in ["finalize", "done", "finish", "end", "f"]:
            break
        
        state['messages'].append({"role": "user", "content": user_input})


def generate_optimized_prompt(model: str, state: ConversationState) -> OptimizationResult:
    """Generate the final optimized prompt."""
    context_summary = f"""
Original Prompt: "{state['original_input']}"

Understanding Gained:
- Context: {state['context_understanding']['context']}
- Goal: {state['context_understanding']['goal']}
- Format: {state['context_understanding']['format']}
- AI's Role: {state['context_understanding']['ai_role']}
- Additional Insights: {state['context_understanding']['additional_insights']}
"""
    
    with ui.show_progress("Analyzing conversation and crafting the perfect prompt...", style="purple"):
        response = ai_client.chat_completion(
            model=model,
            messages=[
                {"role": "system", "content": prompts.OPTIMIZATION_GENERATION_PROMPT},
                {"role": "user", "content": context_summary}
            ],
            temperature=0.3
        )
    
    parsed = parse_xml_response(response, OPTIMIZATION_TAGS)
    
    return {
        'optimized_prompt': parsed.get("optimized_prompt", ""),
        'improvements': parsed.get("improvement_summary", ""),
        'test_cases': None
    }


def generate_test_cases(model: str, optimized_prompt: str, context_understanding: ContextUnderstanding) -> List[TestCase]:
    """Generate test cases for the optimized prompt."""
    context_summary = f"""
Optimized Prompt:
{optimized_prompt}

Context Understanding:
- AI's Role: {context_understanding['ai_role']}
- Goal: {context_understanding['goal']}
- Format: {context_understanding['format']}
"""
    
    with ui.show_progress("Creating diverse test scenarios...", style="cyan"):
        response = ai_client.chat_completion(
            model=model,
            messages=[
                {"role": "system", "content": prompts.TEST_GENERATION_PROMPT},
                {"role": "user", "content": context_summary}
            ],
            temperature=0.5
        )
    
    # Parse test cases
    test_pattern = r'<test number="(\d+)">(.*?)</test>'
    tests = re.findall(test_pattern, response, re.DOTALL)
    
    test_cases = []
    for _, test_content in tests:
        scenario = extract_xml_content(test_content, "scenario")
        test_input = extract_xml_content(test_content, "input")
        expected = extract_xml_content(test_content, "expected_behavior")
        test_cases.append((scenario, test_input, expected))
    
    return test_cases


def format_test_cases_for_context(test_cases: List[TestCase]) -> str:
    """Format test cases as a string for inclusion in refinement context."""
    formatted = []
    for i, (scenario, test_input, expected) in enumerate(test_cases, 1):
        formatted.append(f"""Test Case {i}:
Scenario: {scenario}
Input: {test_input}
Expected: {expected}""")
    
    return "\n\n".join(formatted)


def add_refinement_to_conversation(state: ConversationState, result: OptimizationResult, feedback: str) -> None:
    """Add refinement feedback to the conversation."""
    refinement_context = f"""The user wants to refine the optimized prompt further.
                    
Current optimized prompt:
{result['optimized_prompt']}
"""
    
    if result['test_cases']:
        refinement_context += f"""
Test cases that were generated:
{result['test_cases']}
"""
    
    refinement_context += f"""
User's feedback: {feedback}"""
    
    state['messages'].append({"role": "user", "content": refinement_context})


def run_optimization_flow(model: str) -> None:
    """Main optimization flow."""
    ui.clear_screen()
    ui.show_welcome()
    
    # Get initial user input
    user_input = ui.get_user_input("\n[bold yellow]🎯 Enter your prompt or describe what you need help with[/bold yellow]")
    
    # Create initial state
    state = create_initial_state()
    state['original_input'] = user_input
    
    # Assess user intent
    intent, initial_understanding = assess_user_intent(model, user_input)
    state['user_intent'] = intent
    state['context_understanding']['additional_insights'] = initial_understanding
    
    # Initialize conversation
    initialize_conversation(state)
    
    # Run refinement loop
    refinement_loop(model, state)
    
    # Generate and show optimized prompt
    result = generate_optimized_prompt(model, state)
    ui.show_optimized_prompt(result)
    
    # Menu loop
    while True:
        choice = ui.show_menu(result['test_cases'] is not None)
        
        if choice == "1":
            # Generate test cases
            test_cases = generate_test_cases(
                model, 
                result['optimized_prompt'], 
                state['context_understanding']
            )
            result['test_cases'] = format_test_cases_for_context(test_cases)
            ui.show_test_cases(test_cases)
            
        elif choice == "2":
            # Refine further
            feedback = ui.get_user_input("\n[cyan]What would you like to change about the optimized prompt?[/cyan]")
            
            if result['test_cases']:
                ui.console.print("\n[dim]Note: Test cases will be included in the refinement context.[/dim]")
            
            add_refinement_to_conversation(state, result, feedback)
            refinement_loop(model, state)
            
            # Generate new optimized prompt
            result = generate_optimized_prompt(model, state)
            ui.show_optimized_prompt(result)
            
        elif choice == "3":
            # Start over
            run_optimization_flow(model)
            return
            
        elif choice == "4":
            # Exit
            ui.console.print("\n[bold green]Thank you for using Prompt Optimizer! 🎉[/bold green]")
            return