import os
import json
import time
from .util import print_err

from openai  import AsyncOpenAI
from openai import _exceptions as error

client = AsyncOpenAI(api_key=os.environ["OPENAI_KEY"])

MAX_ATTEMPTS = 5
DEFAULT_MODEL = 'gpt-3.5-turbo'

class SchemaValidationError(Exception):
    pass

# Main interface are these prompting strats

async def basic_prompt(prompt, input, model=DEFAULT_MODEL):
    messages = [{"role": "user", "content": f"{prompt}\n{input}"}]
    response = await generate_chat_response(messages, model)
    return get_message_text(response), get_total_cost([response])

async def system_prompt(prompt, input, model=DEFAULT_MODEL):
    messages = [
        {"role": "system", "content": prompt},
        {"role": "user", "content": input}
    ]
    response = await generate_chat_response(messages, model)
    return get_message_text(response), get_total_cost([response])

async def json_prompt(prompt_text, input, method=basic_prompt, model=DEFAULT_MODEL, schema=None, attempt=1, best=(0,None)):
    response_txt, cost = await method(prompt_text, input, model)
    response_txt = response_txt.replace('```json', '').replace('```', '').strip()
    try: 
        serialized = json.loads(response_txt)
    except json.decoder.JSONDecodeError as e:
        if attempt < MAX_ATTEMPTS:
            print_err(f"JSON decode error, retrying ({attempt})")
            return await json_prompt(prompt_text, input, method, model, schema, attempt + 1, best)
        else:
            raise e
    # Schema is a method that returns a value between 0 and 1
    # 1 indicates full compliance with the schema
    # 0 indicates non compliance with the schema
    # In between values indicate partial compliance
    # The code will retry until the schema check returns 1, saving the "best so far"
    # If MAX ATTEMPTS is reached, then we return the "best so far" 
    # If it's None then raise an exception
    # TBD if we should return None instead, could be useful either way 
    if schema:
        check = schema(serialized)
        if check != 1:
            if attempt < MAX_ATTEMPTS:
                print_err(f"Schema check failed, retrying ({attempt})")
                if check > best[0]:
                    best = (check, serialized)
                return await json_prompt(prompt_text, input, method, model, schema, attempt + 1, best)
            else:
                print_err(serialized)
                if best[1]:
                    return best[1]
                else:
                    raise SchemaValidationError
    return serialized, cost

async def json_prompt_system(prompt_text, input, model=DEFAULT_MODEL, schema=None):
    return await json_prompt(prompt_text, input, method=system_prompt, model=model, schema=schema)

async def generate_chat_response(messages, model=DEFAULT_MODEL, attempt=0):
    try:
        response = await client.chat.completions.create(model=model,
        temperature=0.5,
        messages=messages)
        return response
    except (error.InternalServerError, error.APITimeoutError, error.UnprocessableEntityError, error.RateLimitError) as e:
        attempt += 1
        if attempt > MAX_ATTEMPTS:
            raise e
        sleeptime = pow(2, attempt + 1)
        print_err("Service Unavailable.. sleeping for " + str(sleeptime))
        time.sleep(sleeptime)
        return await generate_chat_response(messages, model, attempt)
    except error.APIError as e:
        if "bad gateway" in str(e).lower():
            # bad gateway, we retry
            attempt += 1
            if attempt > MAX_ATTEMPTS:
                raise e
            sleeptime = pow(2, attempt + 1)
            print_err("Bad Gateway. Sleeping for {sleeptime}s.")
            time.sleep(sleeptime)
            return await generate_chat_response(messages, model, attempt)
        else:
            raise e


def get_message_text(response):
    return response.choices[0].message.content


def get_total_tokens(responses):
    return sum([r.usage.total_tokens for r in responses])


def get_total_cost(responses):
    input_costs = {
        "gpt-4-0613": 0.03 / 1000,
        "gpt-3.5-turbo-0613": 0.0015 / 1000,
        "gpt-3.5-turbo-0125": 0.0005 / 1000,
        "gpt-3.5-turbo-16k-0613": 0.003 / 1000,
    }
    output_costs = {
        "gpt-4-0613": 0.06 / 1000,
        "gpt-3.5-turbo-0613": 0.002 / 1000,
        "gpt-3.5-turbo-0125": 0.0015 / 1000,
        "gpt-3.5-turbo-16k-0613": 0.004 / 1000,
    }
    # check if models are present
    for r in responses:
        if r.model not in input_costs:
            print_err(f"{r.model} not found in input costs! update please")
            return -1

    return sum(
        [
            r.usage.prompt_tokens * input_costs[r.model]
            + r.usage.completion_tokens * output_costs[r.model]
            for r in responses
        ]
    )

