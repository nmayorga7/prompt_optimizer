"""

PROMPT OPTIMIZER LOGIC - ITERATIVE SELF-EVALUATION WITH USER CLARIFICATION TOOL:

This tool takes an initial user prompt and performs a structured optimization process:
1. Accepts the user's raw prompt input.
2. Automatically generates challenging test cases designed to probe ambiguity, edge cases, and weaknesses.
3. Simulates responses to each test case using the current prompt.
4. Evaluates each response to identify shortcomings, misalignments with user intent, or lack of clarity.
5. Uses the ask_user tool when clarification is needed to resolve ambiguities.
6. Based on the evaluations and clarifications, generates a final, improved version of the prompt.

"""

import os
import json
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
    "clarifications": [],
    "final_prompt": None
}

# clarify ambiguities with user
def ask_user(question: str) -> str:

    print(f"\n***CLARIFICATION NEEDED***")
    print(f"Question: {question}\n")
    
    user_response = input("Your answer: ").strip()
    
    # store user clarification to conversation context
    conversation["clarifications"].append({
        "question": question,
        "answer": user_response
    })
    
    return user_response

# tool schema for tool function calling
ask_user_tool = {
    "type": "function",
    "function": {
        "name": "ask_user",
        "description": "Ask the user a clarifying question to resolve information gaps that cannot be inferred from context. Use when you encounter: personal references that need context, subjective terms that need definition, ambiguous goals that could be interpreted multiple ways, or missing specifications that would significantly impact the optimization.",
        "parameters": {
            "type": "object",
            "properties": {
                "question": {
                    "type": "string",
                    "description": "A clear, specific question to resolve an information gap that you cannot fill through reasoning alone"
                }
            },
            "required": ["question"]
        }
    }
}

# handle tool calls made by the model
def handle_tool_calls(tool_calls):
    #for tool_call in tool_calls:
        #if tool_call.function.name == "ask_user":
    tool_call = tool_calls[0]
    args = json.loads(tool_call.function.arguments)
    question = args["question"]
            
    response = ask_user(question)
            
    return {
        "tool_call_id": tool_call.id,
        "role": "tool",
        "name": "ask_user",
        "content": response
    }

def initialize_prompt():
    user_input = input("Enter the initial prompt: ").strip()
    conversation["initial_prompt"] = user_input
    conversation["messages"].append({"role": "user", "content": user_input})

# assess information gaps existing in the prompt
def assess_information_gaps(model):

    client = get_client()
    
    assessment_prompt = f"""
    Analyze this prompt for information gaps that would prevent effective optimization:
    
    PROMPT: "{conversation['initial_prompt']}"
    
    Identify gaps in these categories:
    1. Personal context (references to people, projects, situations you cannot know)
    2. Subjective definitions (terms like "good", "professional", "simple" that need user's definition)
    3. Ambiguous goals (multiple possible interpretations of what user wants to achieve)
    4. Missing specifications (context, audience, format, constraints that would change the approach)
    
    For each significant gap you identify, use the ask_user tool to get clarification.
    If no significant gaps exist that would impact optimization, respond with "NO_GAPS_IDENTIFIED".
    """
    
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": assessment_prompt}],
        tools=[ask_user_tool],
        tool_choice="auto"
    )
    
    # handle any tool calls
    current_messages = [{"role": "user", "content": assessment_prompt}]
    current_response = response
    
    while current_response.choices[0].message.tool_calls:
        current_messages.append(current_response.choices[0].message)
        
        # save user response to conversation history
        for tool_call in current_response.choices[0].message.tool_calls:
            tool_response = handle_tool_calls([tool_call])
            current_messages.append(tool_response)
        
        # call API again
        # may decide to call ask_user again 
        current_response = client.chat.completions.create(
            model=model,
            messages=current_messages,
            tools=[ask_user_tool],
            tool_choice="auto"
        )
    
    return current_response.choices[0].message.content.strip()

def generate_tests(model):
    client = get_client()
    
    # initial ambiguity assessment
    print("\nAssessing information gaps in the prompt...")
    gap_assessment = assess_information_gaps(model)
    
    if gap_assessment != "NO_GAPS_IDENTIFIED":
        print(f"Gap assessment: {gap_assessment}")
    
    # generate test cases with any clarifications incorporated
    clarification_context = ""
    if conversation["clarifications"]:
        clarification_context = "\n\nUser Clarifications:\n"
        for clarification in conversation["clarifications"]:
            clarification_context += f"Q: {clarification['question']}\nA: {clarification['answer']}\n"
    
    system_prompt = f"""
    Generate 5 challenging test cases for this prompt that probe for weaknesses, edge cases, and ambiguities.
    Focus on scenarios that would reveal whether the prompt achieves the user's actual intent.
    
    Original Prompt: {conversation['initial_prompt']}
    {clarification_context}
    
    Return the test cases in a numbered list.
    """

    response = client.chat.completions.create(
        model=model, 
        messages=[{"role": "system", "content": system_prompt}]
    )
    
    test_list = response.choices[0].message.content.strip()
    conversation["tests"] = test_list
    print("\nGenerated Test Cases:\n")
    print(test_list)

def simulate_tests(model):
    client = get_client()
    print("\nTesting Prompt...")
    test_cases = conversation["tests"].split("\n")
    
    for case in test_cases:
        if not case.strip() or not any(char.isalnum() for char in case):
            continue
            
        print(f"\nTest Case: {case}")

        # aggregate clarifications
        clarification_context = ""
        if conversation["clarifications"]:
            clarification_context = "\n\nAdditional Context from User:\n"
            for clarification in conversation["clarifications"]:
                clarification_context += f"Q: {clarification['question']}\nA: {clarification['answer']}\n"

        messages = [
            {"role": "system", "content": f"Execute this test case as if the original prompt were given. Return only the assistant's response.{clarification_context}"},
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
        
        # include clarifications in evaluation context
        clarification_context = ""
        if conversation["clarifications"]:
            clarification_context = "\n\nUser Clarifications:\n"
            for clarification in conversation["clarifications"]:
                clarification_context += f"Q: {clarification['question']}\nA: {clarification['answer']}\n"
        
        evaluation_prompt = f"""
        Evaluate this test case and response pair. Assess whether the response aligns with what the user likely intended.
        
        If you cannot determine user intent due to information gaps (personal context you don't know, subjective terms needing definition, ambiguous goals), use the ask_user tool to clarify.
        
        Test: {case}
        Response: {reply}
        Original Prompt: {conversation['initial_prompt']}
        {clarification_context}
        
        Provide your evaluation focusing on alignment with user intent and areas for improvement.
        """
        
        response = client.chat.completions.create(
            model=model, 
            messages=[{"role": "user", "content": evaluation_prompt}],
            tools=[ask_user_tool],
            tool_choice="auto"
        )

        # handle tool calls during evaluation
        current_messages = [{"role": "user", "content": evaluation_prompt}]
        current_response = response
        
        while current_response.choices[0].message.tool_calls:
            current_messages.append(current_response.choices[0].message)
            
            for tool_call in current_response.choices[0].message.tool_calls:
                tool_response = handle_tool_calls([tool_call])
                current_messages.append(tool_response)
            
            current_response = client.chat.completions.create(
                model=model,
                messages=current_messages,
                tools=[ask_user_tool],
                tool_choice="auto"
            )
        
        evaluation = current_response.choices[0].message.content.strip()
        conversation["evaluations"].append({"test": case, "evaluation": evaluation})
        print(f"\nEvaluation for '{case}':\n{evaluation}")

def generate_final_prompt(model):
    client = get_client()
    print("\nGenerating final optimized prompt...\n")

    prompt_summary = "\n".join(
        [f"Test: {e['test']}\nEvaluation: {e['evaluation']}" for e in conversation["evaluations"]]
    )
    
    # include clarifications in final prompt generation
    clarification_summary = ""
    if conversation["clarifications"]:
        clarification_summary = "\n\nUser Clarifications:\n"
        for clarification in conversation["clarifications"]:
            clarification_summary += f"Q: {clarification['question']}\nA: {clarification['answer']}\n"

    system_prompt = f"""
    You are a prompt optimization assistant. Based on the following information, create an improved version of the original prompt.
    
    Original Prompt: {conversation['initial_prompt']}
    
    Test Evaluations:
    {prompt_summary}
    {clarification_summary}
    
    Before finalizing the optimized prompt, assess if you need any additional clarification about the user's goals, preferences, or context that would significantly improve the optimization. If so, use the ask_user tool.
    
    Then provide the final optimized prompt that addresses identified weaknesses and incorporates user clarifications.
    """

    response = client.chat.completions.create(
        model=model, 
        messages=[{"role": "user", "content": system_prompt}],
        tools=[ask_user_tool],
        tool_choice="auto"
    )

    # handle any final tool calls
    current_messages = [{"role": "user", "content": system_prompt}]
    current_response = response
    
    while current_response.choices[0].message.tool_calls:
        current_messages.append(current_response.choices[0].message)
        
        for tool_call in current_response.choices[0].message.tool_calls:
            tool_response = handle_tool_calls([tool_call])
            current_messages.append(tool_response)
        
        current_response = client.chat.completions.create(
            model=model,
            messages=current_messages,
            tools=[ask_user_tool],
            tool_choice="auto"
        )
    
    final = current_response.choices[0].message.content.strip()
    conversation["final_prompt"] = final
    print(f"\nFinal Optimized Prompt:\n{final}")
    
"""    

Show summary of clarifications if any were made

    if conversation["clarifications"]:
        print(f"\nCLARIFICATIONS USED IN OPTIMIZATION:")
        for i, clarification in enumerate(conversation["clarifications"], 1):
            print(f"{i}. Q: {clarification['question']}")
            print(f"   A: {clarification['answer']}")

"""

def run_full_optimizer(model="gpt-4o"):

    print("Starting Interactive Prompt Optimizer")
    print("Note: The user may be called on to fill information gaps as needed.\n")
    
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
    except KeyboardInterrupt:
        print("\n\nProcess interrupted by user.")
    except Exception as e:
        print(f"Unexpected error: {e}")