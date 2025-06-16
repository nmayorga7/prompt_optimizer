from dotenv import load_dotenv
import prompt_optimizer.prompt_optimizer as prompt_optimizer
import os

load_dotenv('../.env')

def main():

    model = "gpt-4.1"

    try:
        prompt_optimizer.run_prompt_optimizer(model)
    except ValueError as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
