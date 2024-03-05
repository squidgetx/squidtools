import asyncio
import os
import io
import json
import csv
import sys
import time

from .util import gen_batches, print_err

"""
Library / helper functions to manage idempotent execution of flaky tasks.

Supply robust_task with a list of files that need to be processed and a processing function 
that returns a dict (or other JSON serializable) result

Results are stored on disk in the progress capture filename given (or progress.json as default)
"""

DEFAULT_FILENAME = "progress.json"

PKEY = "_pkey"


# Progress capture is implemented as lines of json in a file
# Each line of json is a dict/object that contains a primary key indexed by '_pkey'
# This design allows us to easily append new records to the file
# Note if multiple records use the same pkey, later entries overwrite the older ones
# This is useful when intentionally overwriting records
def load_progress(pname):
    progress = {}
    if os.path.exists(pname):
        with open(pname, "rt") as f:
            for line in f:
                p = json.loads(line)
                # Legacy code, some progress files index by filename
                pk = p.get(PKEY, p.get("filename"))
                if pk:
                    progress[pk] = p
    return progress


# Save the result to disk
def save_progress(pname, name: str, result: dict):
    result[PKEY] = name
    with open(pname, "at") as f:
        f.write(json.dumps(result) + "\n")


"""
objs: array or dict of strings to process. 
    if dict, progress is tracked by the dict keys and the task operates on the dict values
task: function that processes a string
progress_name: file that stores progress 
skip_existing: don't re-process already processed files
"""


def robust_task(
    objs: dict[str, str] | list[str],
    task,
    progress_name=DEFAULT_FILENAME,
    skip_existing=True,
    show_progress=True,
):
    progress = load_progress(progress_name)
    if isinstance(objs, list):
        objs = {k: k for k in objs}

    n_objs = len(objs.keys())
    names = (
        (k for k in objs.keys() if k not in progress) if skip_existing else objs.keys()
    )

    for i, name in enumerate(names):
        if skip_existing and name in progress:
            continue
        try:
            results = task(objs[name])
            save_progress(progress_name, name, results)
        except Exception as e:
            sys.stderr.write(
                f"robust_task: processing {name} raised {e.__class__.__name__}: {e}, skipping this item\n"
            )
            sys.stderr.flush()
            continue
        if show_progress:
            pct = int(i / n_objs * 100)
            sys.stderr.write(f"{i}/{n_objs} - {pct}%\r")
        progress[name] = results
    return progress


"""
Run an async task over the given objects, 
    saving progress as JSON to disk
Sleeps for (delay) seconds after each batch (default 0)
Each task has a timeout window of 8 seconds.
Automatically retries to process all timed out items 
    at the end with a doubled timeout window
    (control with retry_timeouts=False
"""


def async_robust_task(
    objs: dict[str, str] | list[str],
    task,
    progress_name=DEFAULT_FILENAME,
    skip_existing=True,
    show_progress=True,
    batch_size=100,
    delay=0,
    timeout=8,
    retry_errs=True,
):
    progress = load_progress(progress_name)
    if isinstance(objs, list):
        objs = {k: k for k in objs}
    n_objs = len(objs.keys())
    processed = len(progress)

    bi = 0
    errs = {}

    names = (
        (k for k in objs.keys() if k not in progress) if skip_existing else objs.keys()
    )

    for batch in gen_batches(names, batch_size):
        bi += 1

        async def process(name):
            try:
                value = objs[name]
                results = await asyncio.wait_for(task(value), timeout=timeout)
                return name, results
            except asyncio.TimeoutError as e:
                # Don't print an error message
                print_err(f"robust_task: processing {name} timed out")
                return name, None
            except Exception as e:
                print_err(
                    f"robust_task: processing {name} raised {e.__class__.__name__}: {e}, skipping this item"
                )
                return name, None

        tasks = []
        for name in batch:
            tasks.append(process(name))

        async def execute_all(tasks):
            results = await asyncio.gather(*tasks)
            for result in results:
                name, value = result
                if value is not None:
                    save_progress(progress_name, name, value)
                    progress[name] = value
                else:
                    errs[name] = objs[name]

        asyncio.run(execute_all(tasks))
        processed += len(tasks)
        if show_progress:
            pct = int(processed / n_objs * 100)
            sys.stderr.write(f"{bi}: {processed}/{n_objs} - {pct}%\r")
        if delay and len(tasks) > 0:
            time.sleep(delay)

    if len(errs) > 0:
        print_err(f"{len(errs)} items failed")
        if retry_errs:
            print_err(f"Auto-retrying with doubled timeout ({timeout*2}s)")
            async_robust_task(
                errs,
                task,
                progress_name,
                skip_existing,
                show_progress,
                batch_size,
                delay,
                timeout * 2,
                retry_errs=False,
            )
            progress = load_progress(progress_name)

    return progress


def naive_dict_to_tsv(data):
    if len(data) > 0:
        outs = io.StringIO()
        column_headers = list(data.values())[0].keys()
        writer = csv.DictWriter(outs, delimiter="\t", fieldnames=column_headers)
        writer.writeheader()
        writer.writerows(data.values())
        return outs.getvalue()
    else:
        return ""
