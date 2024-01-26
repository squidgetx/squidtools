# squidtools

Collection of Python functions and libraries that I would like to be
generally available to many different projects that involve data wrangling

## gpt_utils

`basic_prompt` which takes a prompt and input as arguments
and returns a tuple of response and cost.

Includes retry logic with exponential backoff

## robust_task

`robust_task` takes an iterable of filenames and a task to process them
it writes output of the task to disk after each filename and skips previously
completed tasks. very useful for flaky BS processing.
