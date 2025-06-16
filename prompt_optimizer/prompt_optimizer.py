"""

PROMPT OPTIMIZER LOGIC - ITERATIVE SELF-EVALUATION:

This tool takes an initial user prompt and performs a structured optimization process:
1. Accepts the user's raw prompt input.
2. Automatically generates challenging test cases designed to probe ambiguity, edge cases, and weaknesses.
3. Simulates responses to each test case using the current prompt.
4. Evaluates each response to identify shortcomings, misalignments with user intent, or lack of clarity.
5. Based on the evaluations, generates a final, improved version of the prompt optimized for specificity, clarity, and robustness.

"""

import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv('../.env')

_client = None

def get_client() -> OpenAI:
    global _client
    if _client is None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")
        _client = OpenAI(api_key=api_key)
    return _client

conversation = {
    "initial_prompt": None,
    "messages": [],
    "tests": [],
    "responses": [],
    "evaluations": [],
    "final_prompt": None
}

def initialize_prompt():
    user_input = input("Enter the initial prompt: ").strip()
    conversation["initial_prompt"] = user_input
    conversation["messages"].append({"role": "user", "content": user_input})

def generate_tests(model):
    client = get_client()
    system_prompt = (
        "You are a prompt testing assistant. Generate 5 relelvant exploratory questions that could challenge or expose weaknesses in the following prompt."
        "Think of edge cases, ambiguity, assumptions, and varying goals. Return them to the user in a numbered list."
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": conversation["initial_prompt"]}
    ]

    response = client.chat.completions.create(model=model, messages=messages)
    test_list = response.choices[0].message.content.strip()
    conversation["tests"] = test_list
    print("\nGenerated Test Cases:\n")
    print(test_list)

def simulate_tests(model):
    client = get_client()
    print("\nTesting Prompt...")
    test_cases = conversation["tests"].split("\n")
    for case in test_cases:
        if not case.strip():
            continue
        print(f"\nTest Case: {case}")

        messages = [
            {"role": "system", "content": "Execute this test case as if the original prompt were given. Return only the assistant's response."},
            {"role": "user", "content": f"Prompt: {conversation['initial_prompt']}\n\nTest Case: {case}"}
        ]

        response = client.chat.completions.create(model=model, messages=messages)
        reply = response.choices[0].message.content.strip()
        conversation["responses"].append({"test": case, "response": reply})
        print(f"Response: {reply}")

def evaluate_tests(model):
    client = get_client()
    print("\nEvaluating responses...")

    for pair in conversation["responses"]:
        case = pair["test"]
        reply = pair["response"]
        messages = [
            {"role": "system", "content": "Evaluate the following test case and assistant response. Identify whether it satisfies the user's intent, what is missing, and any improvements that could be made."},
            {"role": "user", "content": f"Test: {case}\nResponse: {reply}"}
        ]

        response = client.chat.completions.create(model=model, messages=messages)
        evaluation = response.choices[0].message.content.strip()
        conversation["evaluations"].append({"test": case, "evaluation": evaluation})
        print(f"\nEvaluation for '{case}':\n{evaluation}")

def generate_final_prompt(model):
    client = get_client()
    print("\nGenerating final optimized prompt...\n")

    prompt_summary = "\n".join(
        [f"Test: {e['test']}\nEvaluation: {e['evaluation']}" for e in conversation["evaluations"]]
    )

    system_prompt = f"""
    You are a prompt optimization assistant. Based on the following:
    - Original Prompt: {conversation['initial_prompt']}
    - Evaluations of various test cases:
    {prompt_summary}

    Rewrite the original prompt to address weaknesses found in the evaluations. Make it more specific, robust, and tailored to the user's goals.
    Return only the final prompt.
    """

    response = client.chat.completions.create(model=model, messages=[{"role": "system", "content": system_prompt}])
    final = response.choices[0].message.content.strip()
    conversation["final_prompt"] = final
    print(f"\nFinal Optimized Prompt:\n{final}")

def run_full_optimizer(model="gpt-4o"):
    initialize_prompt()
    generate_tests(model)
    simulate_tests(model)
    evaluate_tests(model)
    generate_final_prompt(model)

if __name__ == "__main__":
    model = "gpt-4o"

    try:
        run_full_optimizer(model)
    except ValueError as e:
        print(f"Error: {e}")