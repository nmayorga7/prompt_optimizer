"""
User interface functions for the prompt optimizer.
"""

from typing import List, Optional, Any
from contextlib import contextmanager

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich.rule import Rule

from .types import OptimizationResult, TestCase


# Global console instance
console = Console()


def clear_screen() -> None:
    """Clear the terminal screen."""
    console.clear()


def show_welcome() -> None:
    """Display the welcome message."""
    console.print(Panel.fit(
        "[bold purple]🚀 PROMPT OPTIMIZER[/bold purple]\n\n"
        "[dim]Welcome to the AI Prompt Refinement Workshop!\n"
        "I'll help you transform your prompt into something amazing.[/dim]",
        border_style="purple"
    ))


def get_user_input(prompt_text: str) -> str:
    """Get input from the user with styled prompt."""
    return Prompt.ask(prompt_text)


@contextmanager
def show_progress(message: str, style: str = "cyan"):
    """Context manager for displaying a progress spinner."""
    with Progress(
        SpinnerColumn(style=style),
        TextColumn(f"[{style}]{message}[/{style}]"),
        console=console,
        transient=True
    ) as progress:
        task = progress.add_task("working", total=None)
        yield progress
        progress.update(task, completed=True)


def show_refinement_header() -> None:
    """Display the refinement workshop header."""
    console.print("\n", Rule("[bold green]🔧 Refinement Workshop[/bold green]", style="green"))
    console.print("[cyan]💭 Let's refine your prompt together. I'll ask targeted questions to understand your needs.[/cyan]")
    console.print("[dim]Type 'finalize' at any time when you're satisfied.[/dim]\n")


def show_assistant_message(message: str) -> None:
    """Display a message from the assistant."""
    console.print(Panel(
        message,
        title="[bold blue]🤖 Assistant[/bold blue]",
        border_style="blue",
        padding=(1, 2)
    ))


def show_ready_to_optimize(confidence: float) -> None:
    """Display the ready to optimize notification."""
    console.print(Panel.fit(
        f"[bold green]✨ READY TO OPTIMIZE ✨[/bold green]\n\n"
        f"💡 I have enough information to create an optimized prompt!\n"
        f"Type 'finalize' to see the result, or continue refining.\n\n"
        f"[dim]Confidence: [green]{'█' * int(confidence * 20)}{'░' * (20 - int(confidence * 20))}[/green] {confidence:.0%}[/dim]",
        border_style="green"
    ))


def show_optimized_prompt(result: OptimizationResult) -> None:
    """Display the optimized prompt."""
    console.print("\n", Rule("[bold purple]🎯 Generating Optimized Prompt[/bold purple]", style="purple"))
    
    console.print("\n", Panel(
        f"[bold white]✨ OPTIMIZED PROMPT ✨[/bold white]\n\n"
        f"{result['optimized_prompt']}",
        border_style="purple",
        padding=(2, 3)
    ))
    
    if result['improvements']:
        improvements = result['improvements'].strip().split('\n')
        console.print("\n[bold yellow]📊 Key Improvements:[/bold yellow]")
        for imp in improvements:
            if imp.strip():
                console.print(f"  [green]✓[/green] {imp.strip()}")


def show_menu(has_test_cases: bool) -> str:
    """Display the post-optimization menu and get user choice."""
    console.print("\n")
    choices_table = Table(show_header=False, box=None)
    choices_table.add_row("[cyan]1.[/cyan]", "Generate test cases for this prompt")
    choices_table.add_row("[cyan]2.[/cyan]", "Refine the prompt further")
    choices_table.add_row("[cyan]3.[/cyan]", "Start over with a new prompt")
    choices_table.add_row("[cyan]4.[/cyan]", "Exit")
    
    console.print(Panel(
        choices_table,
        title="[bold yellow]📝 What would you like to do?[/bold yellow]",
        border_style="yellow"
    ))
    
    choice = get_user_input("[bold yellow]Your choice (1-4)[/bold yellow]")
    if choice not in ["1", "2", "3", "4"]:
        console.print("[red]Invalid choice. Please enter 1-4.[/red]")
        return show_menu(has_test_cases)
    
    return choice


def show_test_cases(test_cases: List[TestCase]) -> None:
    """Display generated test cases."""
    console.print("\n", Rule("[bold cyan]🧪 Generating Test Cases[/bold cyan]", style="cyan"))
    console.print("\n[bold yellow]🧪 Test Cases:[/bold yellow]\n")
    
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
        
        console.print(test_table)
        console.print()
    
    console.print("[dim]💡 Try these test cases with your optimized prompt to ensure it works as expected![/dim]")


def show_error(message: str) -> None:
    """Display an error message."""
    console.print(f"\n[red]Error: {message}[/red]")


def show_cancellation() -> None:
    """Display cancellation message."""
    console.print("\n[yellow]Optimization cancelled by user.[/yellow]")