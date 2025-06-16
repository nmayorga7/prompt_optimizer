"""

PROMPT OPTIMIZER LOGIC (REVISED - v2):
1. initial user prompt --> high-level actionable feedback
2. enter iterative refinement mode
    goal: clarify (1) prompt context (2) user goals (3) desired response format/style
    after each turn: restate understanding & ask follow-up questions
3. user ends refinement → request final optimized prompt

"""

import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

_client = None

def get_client() -> OpenAI:
    global _client
    if _client is None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")
        _client = OpenAI(api_key=api_key)
    return _client

def crispo_review(user_input: str, model: str):

    client = get_client()

    crispo_review = """
    You are a prompt optimization assistant. Given a user prompt, critique it across up to five of the most relevant from the following aspects:
    number_of_words, precision, recall, conciseness, syntax, specificity, level_of_detail, style, grammatical_structure, etc. 
    Identify any weaknesses or points for improvement, especially where the prompt may be vague, overly broad, or hard for an AI model to interpret correctly.

    Format your response like this:
    Critiques:
    - [Aspect]: [Comment]
    - [Aspect]: [Comment]

    """

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": crispo_review},
            {"role": "user", "content": user_input},
        ],
    )
    return response.choices[0].message.content

def run_prompt_optimizer(model: str):
    client = get_client()
    user_input = input("Enter your initial prompt: ").strip()

    # initial Crispo review
    print("\nInitial Feedback (CriSPO-inspired):\n")
    print(crispo_review(user_input, model))

    # set up conversation state
    conversation_state = {
        "initial_prompt": user_input,
        "context": None,
        "goal": None,
        "expected_output_format": None,
        "history": [],
    }

    # start refinement loop
    print("\nLet’s workshop this together. I’ll ask questions to better understand your intent.\n")

    while True:
        user_input = input("\nProvide clarification (or type 'finalize' to finish): ").strip()
        if user_input.lower() == "finalize":
            print("\n✅ Final optimized prompt:\n")
            print(finalize_prompt(conversation_state, model))
            break

        conversation_state["history"].append(user_input)

        # build system prompt dynamically with updated state
        system_prompt = f"""
            You are assisting a user in refining an AI prompt.

            Here is the current version:
            "{conversation_state['initial_prompt']}"

            So far, here is what you know:
            - Context: {conversation_state['context']}
            - Goal: {conversation_state['goal']}
            - Desired Output Format: {conversation_state['expected_output_format']}

            Ask any follow-up clarifying questions that would help better understand the user's intent, especially around:
            - the situation or domain (who/what/why)
            - the specific goal or task the user wants solved
            - the structure, tone, or style of the desired output

            Then, update or correct your understanding of the prompt context, goal, and desired output based on the user response.
        """

        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_input},
            ],
        )

        print("\n🤖 Assistant:\n")
        print(response.choices[0].message.content)


def finalize_prompt(state: dict, model: str):
    client = get_client()

    optimization_prompt = f"""
        You are a prompt rewriting assistant. Based on the following understanding of the user's intent, rewrite the prompt to be as clear, specific, and optimized as possible:

        - Context: {state['context']}
        - Goal: {state['goal']}
        - Expected Output Format: {state['expected_output_format']}

        Original Prompt:
        "{state['initial_prompt']}"

        Return only the rewritten prompt, no explanation.
    """

    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "system", "content": optimization_prompt}],
    )

    return response.choices[0].message.content.strip()
