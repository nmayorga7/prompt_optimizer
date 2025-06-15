# fixed costs/rates for models
thous_tokens_rate = {
    "gpt-4o": {"input": 0.005, "output": 0.015},
    "gpt-3.5-turbo": {"input": 0.0005, "output": 0.0015},
}

total_tokens_used = 0
total_estimated_cost = 0.0


def log_api_usage(response, model):
    global total_tokens_used, total_estimated_cost

    # usage deets
    usage = response.usage
    prompt_tokens = usage.prompt_tokens
    completion_tokens = usage.completion_tokens
    total_tokens = usage.total_tokens

    # calculate cost
    pricing = thous_tokens_rate[model]
    cost = (
        prompt_tokens * pricing["input"] + completion_tokens * pricing["output"]
    ) / 1000

    # totals
    total_tokens_used += total_tokens
    total_estimated_cost += cost

    # display
    print("\n*call usage estimates*")
    # print(f"prompt tokens: {prompt_tokens}")
    # print(f"completion tokens: {completion_tokens}")
    # print(f"total tokens this call: {total_tokens}")
    print(f"estimated cost this call: ${cost:.4f}")
    # print(f"running total tokens: {total_tokens_used}")
    print(f"running total estimated cost: ${total_estimated_cost:.4f}")
