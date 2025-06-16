"""
PROMPT OPTIMIZER - AI-Powered Prompt Engineering Assistant

A tool that helps users create and optimize prompts through intelligent conversation.
Supports both optimizing existing prompts and creating new ones from scratch.
"""

import os
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from enum import Enum

from dotenv import load_dotenv
from openai import OpenAI
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich.rule import Rule

load_dotenv()


# ============================================================================
# Data Models
# ============================================================================

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


# ============================================================================
# UI Components
# ============================================================================

class UIManager:
    """Handles all user interface operations."""
    
    def __init__(self):
        self.console = Console()
    
    def clear_screen(self):
        """Clear the terminal screen."""
        self.console.clear()
    
    def show_welcome(self):
        """Display the welcome message."""
        self.console.print(Panel.fit(
            "[bold purple]🚀 PROMPT OPTIMIZER[/bold purple]\n\n"
            "[dim]Welcome to the AI Prompt Refinement Workshop!\n"
            "I'll help you transform your prompt into something amazing.[/dim]",
            border_style="purple"
        ))
    
    def get_user_input(self, prompt_text: str) -> str:
        """Get input from the user with styled prompt."""
        return Prompt.ask(prompt_text)
    
    def show_progress(self, message: str, style: str = "cyan"):
        """Display a progress spinner."""
        return Progress(
            SpinnerColumn(style=style),
            TextColumn(f"[{style}]{message}[/{style}]"),
            console=self.console,
            transient=True
        )
    
    def show_refinement_header(self):
        """Display the refinement workshop header."""
        self.console.print("\n", Rule("[bold green]🔧 Refinement Workshop[/bold green]", style="green"))
        self.console.print("[cyan]💭 Let's refine your prompt together. I'll ask targeted questions to understand your needs.[/cyan]")
        self.console.print("[dim]Type 'finalize' at any time when you're satisfied.[/dim]\n")
    
    def show_assistant_message(self, message: str):
        """Display a message from the assistant."""
        self.console.print(Panel(
            message,
            title="[bold blue]🤖 Assistant[/bold blue]",
            border_style="blue",
            padding=(1, 2)
        ))
    
    def show_ready_to_optimize(self, confidence: float):
        """Display the ready to optimize notification."""
        self.console.print(Panel.fit(
            f"[bold green]✨ READY TO OPTIMIZE ✨[/bold green]\n\n"
            f"💡 I have enough information to create an optimized prompt!\n"
            f"Type 'finalize' to see the result, or continue refining.\n\n"
            f"[dim]Confidence: [green]{'█' * int(confidence * 20)}{'░' * (20 - int(confidence * 20))}[/green] {confidence:.0%}[/dim]",
            border_style="green"
        ))
    
    def show_optimized_prompt(self, result: OptimizationResult):
        """Display the optimized prompt."""
        self.console.print("\n", Rule("[bold purple]🎯 Generating Optimized Prompt[/bold purple]", style="purple"))
        
        self.console.print("\n", Panel(
            f"[bold white]✨ OPTIMIZED PROMPT ✨[/bold white]\n\n"
            f"{result.optimized_prompt}",
            border_style="purple",
            padding=(2, 3)
        ))
        
        if result.improvements:
            improvements = result.improvements.strip().split('\n')
            self.console.print("\n[bold yellow]📊 Key Improvements:[/bold yellow]")
            for imp in improvements:
                if imp.strip():
                    self.console.print(f"  [green]✓[/green] {imp.strip()}")
    
    def show_menu(self, has_test_cases: bool) -> str:
        """Display the post-optimization menu and get user choice."""
        self.console.print("\n")
        choices_table = Table(show_header=False, box=None)
        choices_table.add_row("[cyan]1.[/cyan]", "Generate test cases for this prompt")
        choices_table.add_row("[cyan]2.[/cyan]", "Refine the prompt further")
        choices_table.add_row("[cyan]3.[/cyan]", "Start over with a new prompt")
        choices_table.add_row("[cyan]4.[/cyan]", "Exit")
        
        self.console.print(Panel(
            choices_table,
            title="[bold yellow]📝 What would you like to do?[/bold yellow]",
            border_style="yellow"
        ))
        
        choice = self.get_user_input("[bold yellow]Your choice (1-4)[/bold yellow]")
        if choice not in ["1", "2", "3", "4"]:
            self.console.print("[red]Invalid choice. Please enter 1-4.[/red]")
            return self.show_menu(has_test_cases)
        
        return choice
    
    def show_test_cases(self, test_cases: List[Tuple[str, str, str]]):
        """Display generated test cases."""
        self.console.print("\n", Rule("[bold cyan]🧪 Generating Test Cases[/bold cyan]", style="cyan"))
        self.console.print("\n[bold yellow]🧪 Test Cases:[/bold yellow]\n")
        
        for i, (scenario, test_input, expected) in enumerate(test_cases, 1):
            test_table = Table(
                title=f"[bold cyan]Test Case {i}[/bold cyan]",
                title_style="bold cyan",
                show_header=False,
                padding=(0, 1)
            )
            test_table.add_row("[yellow]Scenario:[/yellow]", scenario)
            test_table.add_row("[yellow]Input:[/yellow]", f"[dim]{test_input}[/dim]")
            test_table.add_row("[yellow]Expected:[/yellow]", f"[green]{expected}[/green]")
            
            self.console.print(test_table)
            self.console.print()
        
        self.console.print("[dim]💡 Try these test cases with your optimized prompt to ensure it works as expected![/dim]")


# ============================================================================
# AI Integration
# ============================================================================

class AIClient:
    """Handles all AI model interactions."""
    
    def __init__(self, model: str):
        self.model = model
        self._client = None
    
    @property
    def client(self) -> OpenAI:
        """Lazy initialization of OpenAI client."""
        if self._client is None:
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY not found in environment variables")
            self._client = OpenAI(api_key=api_key)
        return self._client
    
    def chat_completion(self, messages: List[Dict[str, str]], temperature: float = 0.7) -> str:
        """Make a chat completion request to the AI model."""
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature
        )
        return response.choices[0].message.content


# ============================================================================
# XML Parsing Utilities
# ============================================================================

def extract_xml_content(text: str, tag: str) -> str:
    """Extract content from XML tags, handling potential parsing errors."""
    pattern = f"<{tag}>(.*?)</{tag}>"
    match = re.search(pattern, text, re.DOTALL)
    return match.group(1).strip() if match else ""


def parse_xml_response(response: str) -> Dict[str, str]:
    """Parse multiple XML tags from a response."""
    tags = ["thinking", "extracted_context", "extracted_goal", "extracted_format", 
            "ai_role", "additional_insights", "score", "reasoning", "ready_to_finalize", 
            "user_message", "intent", "initial_understanding", "optimized_prompt", 
            "improvement_summary"]
    
    return {tag: extract_xml_content(response, tag) for tag in tags}


# ============================================================================
# Core Business Logic
# ============================================================================

class PromptOptimizer:
    """Main class that orchestrates the prompt optimization process."""
    
    def __init__(self, model: str):
        self.ui = UIManager()
        self.ai = AIClient(model)
        self.state = ConversationState()
    
    def run(self):
        """Main entry point for the prompt optimizer."""
        self.ui.clear_screen()
        self.ui.show_welcome()
        
        # Get initial user input
        user_input = self.ui.get_user_input("\n[bold yellow]🎯 Enter your prompt or describe what you need help with[/bold yellow]")
        self.state.original_input = user_input
        
        # Assess user intent
        self._assess_user_intent(user_input)
        
        # Initialize conversation based on intent
        self._initialize_conversation()
        
        # Run refinement loop
        self._refinement_loop()
    
    def _assess_user_intent(self, user_input: str):
        """Determine what the user wants to do."""
        assessment_prompt = """You are an expert prompt engineering assistant. Analyze the user's input to determine their intent.

The user might be:
1. Providing an existing prompt they want optimized
2. Describing a task/goal and need help creating a prompt from scratch
3. Something else that needs clarification

Analyze their input and respond with this XML format:
<assessment>
<intent>[optimize_existing/create_new/unclear]</intent>
<reasoning>[Brief explanation of why you categorized it this way]</reasoning>
<initial_understanding>[What you understand about their needs so far]</initial_understanding>
</assessment>"""
        
        with self.ui.show_progress("Understanding your request..."):
            response = self.ai.chat_completion(
                [
                    {"role": "system", "content": assessment_prompt},
                    {"role": "user", "content": user_input}
                ],
                temperature=0.3
            )
        
        parsed = parse_xml_response(response)
        intent_str = parsed.get("intent", "unclear")
        
        # Map string to enum
        intent_map = {
            "optimize_existing": UserIntent.OPTIMIZE_EXISTING,
            "create_new": UserIntent.CREATE_NEW,
            "unclear": UserIntent.UNCLEAR
        }
        
        self.state.user_intent = intent_map.get(intent_str, UserIntent.UNCLEAR)
        self.state.context_understanding.additional_insights = parsed.get("initial_understanding", "")
    
    def _initialize_conversation(self):
        """Set up the conversation based on user intent."""
        if self.state.user_intent == UserIntent.CREATE_NEW:
            system_prompt = self._get_creation_system_prompt()
            start_message = f"""User's request: '{self.state.original_input}'

I understand you want to create a new prompt. {self.state.context_understanding.additional_insights}

Please begin helping them create an effective prompt."""
        else:
            system_prompt = self._get_optimization_system_prompt()
            start_message = f"""Initial prompt: '{self.state.original_input}'

Please begin the refinement process."""
        
        self.state.messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": start_message}
        ]
    
    def _get_creation_system_prompt(self) -> str:
        """Get the system prompt for creating new prompts."""
        return """You are an expert prompt engineering assistant helping users CREATE optimal prompts from scratch.

The user has described what they want to achieve but hasn't provided a prompt yet. Your task is to:
1. Understand their goals and requirements
2. Ask clarifying questions to gather necessary details
3. Guide them toward creating an effective prompt

""" + self._get_common_prompt_instructions()
    
    def _get_optimization_system_prompt(self) -> str:
        """Get the system prompt for optimizing existing prompts."""
        return """You are an expert prompt engineering assistant helping users create optimal prompts through iterative refinement.

Your task is to guide a conversation that extracts key information needed to transform a vague/incomplete prompt into a clear, specific, and effective one.

""" + self._get_common_prompt_instructions()
    
    def _get_common_prompt_instructions(self) -> str:
        """Get common instructions for all system prompts."""
        return """# Your Process:
For each turn, you will:
1. THINK through what you know and what you need to learn
2. ANALYZE the user's response for extractable information
3. DECIDE on the best questions to ask next
4. CHECK if you have enough information to create an optimal prompt

# Response Format:
Structure ALL your responses using this XML format:

<response>
<thinking>
- What do I know so far?
- What key information am I still missing?
- What can I infer from the user's response?
- How should I adapt my approach based on their communication style?
- Is this for roleplay/character simulation? If so, I need to understand who will be playing which role.
</thinking>

<analysis>
<extracted_context>[What you've learned about the domain/situation or "Not yet clear"]</extracted_context>
<extracted_goal>[What you've learned about their objective or "Not yet clear"]</extracted_goal>
<extracted_format>[What you've learned about desired output style or "Not yet clear"]</extracted_format>
<ai_role>[What role the AI will play - e.g. "Playing character X", "Task executor", "Classifier", etc. or "Not yet clear"]</ai_role>
<additional_insights>[Other important details you've gathered]</additional_insights>
</analysis>

<confidence_assessment>
<score>[0.0-1.0]</score>
<reasoning>[Why you gave this confidence score]</reasoning>
<ready_to_finalize>[yes/no]</ready_to_finalize>
</confidence_assessment>

<user_message>
[Your conversational response with 1-3 targeted questions. Be friendly but efficient.]
</user_message>
</response>

# Important Guidelines:
- Extract information from EVERY user response, even minimal ones
- If user says "do what you think is best", make reasonable assumptions and confirm them
- If user seems impatient (short responses, multiple "finalize"), offer to wrap up
- When confidence >= 0.8, suggest finalizing
- Focus on quality over quantity - often 2-3 good clarifications suffice
- Adapt your questioning style to the user's communication style
- CRITICAL: Always clarify what role the AI will be playing (character in roleplay, task executor, classifier, etc.)
- For roleplay/character scenarios, understand: who plays which character, the setting, interaction style

# When Test Cases are Provided:
If test cases are included in the refinement request:
- Analyze each test case to identify potential issues or edge cases the current prompt might not handle well
- Suggest specific improvements based on the test scenarios
- Focus on making the prompt more robust to handle the various test inputs
- Pay special attention to edge cases and failure modes revealed by the tests"""
    
    def _refinement_loop(self):
        """Main conversation loop for refining the prompt."""
        self.ui.show_refinement_header()
        
        while True:
            # Get AI response
            with self.ui.show_progress("Assistant is thinking..."):
                response = self.ai.chat_completion(self.state.messages)
            
            self.state.messages.append({"role": "assistant", "content": response})
            
            # Parse and process response
            parsed = parse_xml_response(response)
            self._update_context_understanding(parsed)
            
            # Display assistant message
            user_message = parsed.get("user_message", "")
            if user_message:
                self.ui.show_assistant_message(user_message)
            
            # Check if ready to finalize
            if parsed.get("ready_to_finalize") == "yes":
                try:
                    confidence = float(parsed.get("score", "0.8"))
                    self.ui.show_ready_to_optimize(confidence)
                except ValueError:
                    pass
            
            # Get user input
            user_input = self.ui.get_user_input(
                "\n[bold yellow]👤 Your response[/bold yellow] [dim](or 'finalize' to finish)[/dim]"
            )
            
            if user_input.lower() in ["finalize", "done", "finish", "end", "f"]:
                self._finalize_and_show_menu()
                break
            
            self.state.messages.append({"role": "user", "content": user_input})
    
    def _update_context_understanding(self, parsed: Dict[str, str]):
        """Update our understanding based on the AI's analysis."""
        updates = {
            "context": parsed.get("extracted_context"),
            "goal": parsed.get("extracted_goal"),
            "format": parsed.get("extracted_format"),
            "ai_role": parsed.get("ai_role"),
            "additional_insights": parsed.get("additional_insights")
        }
        
        for field, value in updates.items():
            if value and value != "Not yet clear":
                setattr(self.state.context_understanding, field, value)
    
    def _finalize_and_show_menu(self):
        """Generate the optimized prompt and show the menu."""
        result = self._generate_optimized_prompt()
        self.ui.show_optimized_prompt(result)
        
        # Menu loop
        while True:
            choice = self.ui.show_menu(result.test_cases is not None)
            
            if choice == "1":
                # Generate test cases
                test_cases = self._generate_test_cases(result.optimized_prompt)
                result.test_cases = self._format_test_cases_for_context(test_cases)
                self.ui.show_test_cases(test_cases)
                
            elif choice == "2":
                # Refine further
                feedback = self.ui.get_user_input("\n[cyan]What would you like to change about the optimized prompt?[/cyan]")
                
                if result.test_cases:
                    self.ui.console.print("\n[dim]Note: Test cases will be included in the refinement context.[/dim]")
                
                self._add_refinement_to_conversation(result, feedback)
                self._refinement_loop()
                break
                
            elif choice == "3":
                # Start over
                self.run()
                return
                
            elif choice == "4":
                # Exit
                self.ui.console.print("\n[bold green]Thank you for using Prompt Optimizer! 🎉[/bold green]")
                return
    
    def _generate_optimized_prompt(self) -> OptimizationResult:
        """Generate the final optimized prompt."""
        optimization_prompt = """You are a master prompt engineer creating the optimal version of a prompt based on a refinement conversation.

# Your Task:
Create a single, optimized prompt that incorporates everything learned during the refinement process.

# Process:
1. THINK through all the information gathered
2. IDENTIFY the key elements that must be included
3. CRAFT a prompt that is clear, specific, and effective
4. ENSURE it addresses all discovered requirements

# Response Format:
<optimization_response>
<thinking>
- Key context elements to include:
- Core objective to achieve:
- Format/style requirements:
- AI's role in this scenario:
- Potential edge cases to handle:
- Best structure for this prompt:
</thinking>

<optimized_prompt>
[The final, polished prompt that incorporates all learnings. This should be ready to copy and paste.]
</optimized_prompt>

<improvement_summary>
[Brief explanation of key improvements made from the original]
</improvement_summary>
</optimization_response>

# Guidelines:
- Make the prompt self-contained (no external context needed)
- Use clear, specific language appropriate for the domain
- Include any necessary examples or format specifications
- Anticipate and prevent common misunderstandings
- Keep it as concise as possible while being complete
- For roleplay: Clearly specify that the AI will play the character, include personality/behavioral guidelines
- For tasks: Include clear success criteria and expected output format
- Always clarify the AI's role explicitly"""
        
        context_summary = f"""
Original Prompt: "{self.state.original_input}"

Understanding Gained:
- Context: {self.state.context_understanding.context}
- Goal: {self.state.context_understanding.goal}
- Format: {self.state.context_understanding.format}
- AI's Role: {self.state.context_understanding.ai_role}
- Additional Insights: {self.state.context_understanding.additional_insights}
"""
        
        with self.ui.show_progress("Analyzing conversation and crafting the perfect prompt...", style="purple"):
            response = self.ai.chat_completion(
                [
                    {"role": "system", "content": optimization_prompt},
                    {"role": "user", "content": context_summary}
                ],
                temperature=0.3
            )
        
        parsed = parse_xml_response(response)
        
        return OptimizationResult(
            optimized_prompt=parsed.get("optimized_prompt", ""),
            improvements=parsed.get("improvement_summary", "")
        )
    
    def _generate_test_cases(self, optimized_prompt: str) -> List[Tuple[str, str, str]]:
        """Generate test cases for the optimized prompt."""
        test_generation_prompt = """You are creating test cases for a refined prompt to ensure it works as intended.

Based on the prompt and understanding below, generate 3-5 diverse test cases that:
1. Cover typical use cases
2. Test edge cases or challenging scenarios
3. Verify the prompt handles different inputs appropriately

# Response Format:
<test_cases>
<test number="1">
<scenario>[Brief description of the test scenario]</scenario>
<input>[Example input or user message]</input>
<expected_behavior>[What the AI should do/how it should respond]</expected_behavior>
</test>
[Additional test cases...]
</test_cases>

For roleplay prompts, test different conversation styles and situations.
For task prompts, test various input formats and edge cases.
"""
        
        context_summary = f"""
Optimized Prompt:
{optimized_prompt}

Context Understanding:
- AI's Role: {self.state.context_understanding.ai_role}
- Goal: {self.state.context_understanding.goal}
- Format: {self.state.context_understanding.format}
"""
        
        with self.ui.show_progress("Creating diverse test scenarios...", style="cyan"):
            response = self.ai.chat_completion(
                [
                    {"role": "system", "content": test_generation_prompt},
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
    
    def _format_test_cases_for_context(self, test_cases: List[Tuple[str, str, str]]) -> str:
        """Format test cases as a string for inclusion in refinement context."""
        formatted = []
        for i, (scenario, test_input, expected) in enumerate(test_cases, 1):
            formatted.append(f"""Test Case {i}:
Scenario: {scenario}
Input: {test_input}
Expected: {expected}""")
        
        return "\n\n".join(formatted)
    
    def _add_refinement_to_conversation(self, result: OptimizationResult, feedback: str):
        """Add refinement feedback to the conversation."""
        refinement_context = f"""The user wants to refine the optimized prompt further.
                        
Current optimized prompt:
{result.optimized_prompt}
"""
        
        if result.test_cases:
            refinement_context += f"""
Test cases that were generated:
{result.test_cases}
"""
        
        refinement_context += f"""
User's feedback: {feedback}"""
        
        self.state.messages.append({"role": "user", "content": refinement_context})


# ============================================================================
# Main Entry Point
# ============================================================================

def run_prompt_optimizer(model: str):
    """Main function to run the prompt optimizer."""
    try:
        optimizer = PromptOptimizer(model)
        optimizer.run()
    except KeyboardInterrupt:
        Console().print("\n[yellow]Optimization cancelled by user.[/yellow]")
    except Exception as e:
        Console().print(f"\n[red]Error: {e}[/red]")
        raise