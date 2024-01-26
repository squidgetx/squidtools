from openai import OpenAI

import os
import time
import sys

client = OpenAI(api_key=os.environ["OPENAI_KEY"])
MAX_ATTEMPTS = 5

# utility functions for handling open AI responses
def basic_prompt(prompt, input, model="gpt-3.5-turbo", temperature=0.5):
    messages = [{"role": "user", "content": f"{prompt}\n{input}"}]
    response = generate_chat_response(messages, model)
    return get_message_text(response), get_total_cost([response])

def system_prompt(prompt, input, model="gpt-3.5-turbo", temperature=0.5):
    messages = [
        {"role": "system", "content": prompt},
        {"role": "user", "content": input}
    ]
    response = generate_chat_response(messages, model)
    return get_message_text(response), get_total_cost([response])

def generate_chat_response(messages, model="gpt-3.5-turbo", attempt=0, smart_context_setting=True, temperature=0.5):
    try:
        response = client.chat.completions.create(model=model,
        temperature=temperature,
        messages=messages)
        return response
    except (openai.APIConnectionError, openai.APITimeoutError, openai.RateLimitError) as e:
        attempt += 1
        if attempt > MAX_ATTEMPTS:
            raise e

        sleeptime = pow(2, attempt + 1)
        sys.stderr.write("Service Unavailable.. sleeping for " + str(sleeptime) + "\n")
        sys.stderr.flush()
        time.sleep(sleeptime)
        return generate_chat_response(messages, model, attempt)
    except openai.APIError as e:
        if "bad gateway" in str(e).lower():
            # bad gateway, we retry
            attempt += 1
            if attempt > MAX_ATTEMPTS:
                raise e
            sleeptime = pow(2, attempt + 1)
            print(f"Bad Gateway. Sleeping for {sleeptime}s.")
            time.sleep(sleeptime)
            return generate_chat_response(messages, model, attempt)
        else:
            raise e
    except openai.BadRequestError as e:
        if smart_context_setting and "maximum context length" in str(e).lower() and model == 'gpt-3.5-turbo':
            sys.stderr.write(
                "Input too large, automatically retrying with 16k context window.Pass smart_context_setting=False to disable this behavior\n"
            )
            return generate_chat_response(messages, 'gpt-3.5-turbo-16k', attempt)
        else:
            raise e


def get_message_text(response):
    return response.choices[0].message.content


def get_total_tokens(responses):
    return sum([r.usage.total_tokens for r in responses])


def get_total_cost(responses):
    input_costs = {
        "gpt-4-1106-preview": 0.01 / 1000,
        "gpt-4-0613": 0.03 / 1000,
        "gpt-3.5-turbo-0613": 0.0015 / 1000,
        "gpt-3.5-turbo-16k-0613": 0.003 / 1000,
    }
    output_costs = {
        "gpt-4-1106-preview": 0.02 / 1000,
        "gpt-4-0613": 0.06 / 1000,
        "gpt-3.5-turbo-0613": 0.002 / 1000,
        "gpt-3.5-turbo-16k-0613": 0.004 / 1000,
    }
    # check if models are present
    for r in responses:
        if r.model not in input_costs:
            sys.stderr.write(f"{r.model} not found in input costs! update please\n")
            return -1

    return sum(
        [
            r.usage.prompt_tokens * input_costs[r.model]
            + r.usage.completion_tokens * output_costs[r.model]
            for r in responses
        ]
    )

