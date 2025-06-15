from openai import OpenAI
from config import OPENAI_API_KEY
import helper

#print('\n'.join(sorted([x.id for x in openai.models.list()])))

client = OpenAI(api_key=OPENAI_API_KEY)

# 3.5 for dev, switch to 4o later
model = "gpt-3.5-turbo"

# Basic Prompt
prompt = "What is the capital of Pakistan?"

# call chat completion
response = client.chat.completions.create(model=model, messages=[{"role": "user", "content": prompt}])
print(response.choices[0].message.content)

helper.log_api_usage(response, model)



    