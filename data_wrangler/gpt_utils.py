import openai
from openai import error
import os
import time
import sys

openai.api_key = os.environ["OPENAI_KEY"]

MAX_ATTEMPTS = 5

# utility functions for handling open AI responses
def basic_prompt(prompt, input, big_context=False):
    messages = [{"role": "user", "content": f"{prompt}\n{input}"}]
    response = generate_chat_response(messages, big_context)
    return get_message_text(response), get_total_cost([response])


def generate_chat_response(messages, big_context=False, attempt=0):
    if big_context:
        model = "gpt-3.5-turbo-16k"
    else:
        model = "gpt-3.5-turbo"
    try:
        response = openai.ChatCompletion.create(
            model=model,
            temperature=0.5,
            messages=messages,
        )
        return response
    except error.ServiceUnavailableError as e:
        attempt += 1
        if attempt > MAX_ATTEMPTS:
            raise e

        sleeptime = pow(2, attempt + 1)
        sys.stderr.write("Service Unavailable.. sleeping for " + str(sleeptime) + "\n")
        sys.stderr.flush()
        time.sleep(sleeptime)
        return generate_chat_response(messages, big_context, attempt)
    except error.APIError as e:
        if "bad gateway" in str(e).lower():
            # bad gateway, we retry
            attempt += 1
            if attempt > MAX_ATTEMPTS:
                raise e
            sleeptime = pow(2, attempt + 1)
            print(f"Bad Gateway. Sleeping for {sleeptime}s.")
            time.sleep(sleeptime)
            return generate_chat_response(messages, big_context, attempt)
        else:
            raise e


def get_message_text(response):
    return response.choices[0].message.content


def get_total_tokens(responses):
    return sum([r.usage.total_tokens for r in responses])


def get_total_cost(responses):
    input_costs = {
        "gpt-3.5-turbo-0613": 0.0015 / 1000,
        "gpt-3.5-turbo-16k-0613": 0.003 / 1000,
    }
    output_costs = {
        "gpt-3.5-turbo-0613": 0.002 / 1000,
        "gpt-3.5-turbo-16k-0613": 0.004 / 1000,
    }
    # check if models are present
    for r in responses:
        if r["model"] not in input_costs:
            sys.stderr.write(f"{r['model']} not found in input costs! update please")
            return -1

    return sum(
        [
            r.usage.prompt_tokens * input_costs[r["model"]]
            + r.usage.completion_tokens * output_costs[r["model"]]
            for r in responses
        ]
    )

