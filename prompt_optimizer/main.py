from dotenv import load_dotenv

from . import prompt_optimizer

load_dotenv()


def main():
    # 3.5 for dev, switch to 4o later
    model = "gpt-3.5-turbo"

    try:
        user_prompt = input("Enter a prompt to optimize: ")
        results = prompt_optimizer.run_prompt_optimizer(user_prompt, model)
    except ValueError as e:
        print(f"Error: {e}")
        return

    print("\n--- Prompt Optimizer Results ---")
    print(f"Raw Prompt: {user_prompt}")
    print(f"Task Type: {results['task_type']}")
    print(f"\nClarified Prompt:\n{results['clarified_prompt']}")
    print(f"\nCRISPO Output:\n{results['crispo_prompt']}")


if __name__ == "__main__":
    main()
