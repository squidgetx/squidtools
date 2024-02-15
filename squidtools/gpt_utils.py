import asyncio
from . import gpt_utils_async

DEFAULT_MODEL = 'gpt-3.5-turbo'


# utility functions for handling open AI responses
def basic_prompt(prompt, input, model=DEFAULT_MODEL):
    return asyncio.run(gpt_utils_async.basic_prompt(prompt, input, model))

def system_prompt(prompt, input, model=DEFAULT_MODEL):
    return asyncio.run(gpt_utils_async.system_prompt(prompt, input, model))

def json_prompt(prompt_text, input, method=basic_prompt, model=DEFAULT_MODEL, schema=None):
    return asyncio.run(gpt_utils_async.json_prompt(prompt_text, input, method, model, schema))


