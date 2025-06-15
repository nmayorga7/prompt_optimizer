from openai import OpenAI
from config import OPENAI_API_KEY
import prompt_optimizer

client = OpenAI(api_key=OPENAI_API_KEY)

# 3.5 for dev, switch to 4o later
model = "gpt-3.5-turbo"

user_prompt = input("Enter a prompt to optimize: ")
results = prompt_optimizer.run_prompt_optimizer(user_prompt, model)

print("\n--- Prompt Optimizer Results ---")
print(f"Raw Prompt: {user_prompt}")
print(f"Task Type: {results['task_type']}")
print(f"\nClarified Prompt:\n{results['clarified_prompt']}")
print(f"\nCRISPO Output:\n{results['crispo_prompt']}")