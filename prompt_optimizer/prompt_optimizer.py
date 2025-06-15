'''

PROMPT OPTIMIZER LOGIC:
1. classify the prompt objective (task)
2. based on task, feed raw prompt + corresponding clarification prompt
3. feed clarified prompt into CRISPO-inspired single candidate optimizer (He et al., 2025)
4. evaluate efficacy of optimized prompt

Note: helper token cost estimator function used to montor api usage

'''

import os
from dotenv import load_dotenv
from openai import OpenAI
from . import helper

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


def classify_task(prompt: str, model: str):
    client = get_client()
    response = client.chat.completions.create(
        model = model,
        messages= [{"role": "system", "content": "Classify the following prompt as on of the following tasks: summarization, question-answering, code-generation, creative-writing, translation, other"},
                   {"role": "user", "content": f"User Prompt: {prompt}"}]
    )
    helper.log_api_usage(response, model)
    return response.choices[0].message.content.strip().lower()

def clarify_prompt(prompt: str, task_type: str, model: str):
    client = get_client()
    
    clarify_templates = {
        "summarization": "Summarize the following text in 3 bullet points:\n\n" + prompt,
        "question-answering": "Answer the following question clearly and concisely:\n\n" + prompt,
        "code-generation": "Write a clean, well-documented Python function for the following task:\n\n" + prompt,
        "translation": "Translate this text to Spanish (formal tone):\n\n" + prompt,
        "creative-writing": "Rewrite this to sound more professional and structured:\n\n" + prompt,
        "other": "Make the following prompt clearer and more effective for an AI model:\n\n" + prompt
    }
    clarify_instruction = clarify_templates.get(task_type, clarify_templates["other"])

    response = client.chat.completions.create(
        model = model,
        messages=[{"role": "user", "content": clarify_instruction}]
    )
    helper.log_api_usage(response, model)
    return response.choices[0].message.content.strip()


def crispo_prompt(clarified_prompt: str, model: str):
    client = get_client()
    
    crispo_prompt = """
    You are a prompt optimization assistant. Given a user prompt, critique it across up to five of the most relevant from the following aspects: 
    number_of_words, precision, recall, conciseness, syntax, specificity, level_of_detail, style, grammatical_structure, etc.
    
    Then suggest one concrete rewrite of the prompt that would likely improve its effectiveness for an AI model.
    
    Format your response like this:
    Critiques:
    - [Aspect]: [Comment]
    - [Aspect]: [Comment]
    
    Final Optimized Suggestion:
    [Rewritten prompt]
    """

    response = client.chat.completions.create(
        model = model,
        messages=[{"role": "system", "content": crispo_prompt},
                  {"role": "user", "content": clarified_prompt}]
    )
    helper.log_api_usage(response, model)
    return response.choices[0].message.content


def run_prompt_optimizer(prompt: str, model: str):
    task = classify_task(prompt, model)
    clarified = clarify_prompt(prompt, task, model)
    crispo = crispo_prompt(clarified, model)

    return {
        "task_type": task,
        "clarified_prompt": clarified,
        "crispo_prompt": crispo
    }
