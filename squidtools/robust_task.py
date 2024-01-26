import os
import io
import json
import csv
import sys

"""
Library / helper functions to manage idempotent execution of flaky tasks.

Supply robust_task with a list of files that need to be processed and a processing function 
that returns a dict (or other JSON serializable) result

Results are stored on disk in the progress capture filename given (or progress.json as default)
"""

DEFAULT_FILENAME = 'progress.json'

PKEY = '_pkey'

# Progress capture is implemented as lines of json in a file
# Each line of json is a dict/object that contains a primary key indexed by '_pkey'
# This design allows us to easily append new records to the file 
# Note if multiple records use the same pkey, later entries overwrite the older ones
# This is useful when intentionally overwriting records
def load_progress(pname):
    progress = {}
    if os.path.exists(pname):
        with open(pname, 'rt') as f:
            for line in f:
                p = json.loads(line)
                # Legacy code, some progress files index by filename 
                pk = p.get(PKEY, p.get('filename'))
                if pk:
                    progress[pk] = p
    return progress


# Save the result to disk
def save_progress(pname, name: str, result: dict):
    result[PKEY] = name
    with open(pname, 'at') as f:
        f.write(json.dumps(result) + '\n')


"""
objs: array or dict of strings to process. 
    if dict, progress is tracked by the dict keys and the task operates on the dict values
task: function that processes a string
progress_name: file that stores progress 
skip_existing: don't re-process already processed files
"""
def robust_task(objs: dict[str, str]|list[str], task, progress_name=DEFAULT_FILENAME, skip_existing=True, show_progress=True):
    progress = load_progress(progress_name)
    if isinstance(objs, list):
        objs = {k:k for k in objs}

    n_objs = len(objs.keys())

    for i, (name, value) in enumerate(objs.items()):
        if skip_existing and name in progress:
            continue
        try:
            results = task(value) 
            save_progress(progress_name, name, results)
        except Exception as e:
            sys.stderr.write(f"robust_task: processing {name} raised {e.__class__.__name__}: {e}, skipping this item\n")
            sys.stderr.flush()
            continue
        if (show_progress):
            pct = int(i / n_objs * 100)
            sys.stderr.write(f"{i}/{n_objs} - {pct}%\r")
        progress[name] = results
    return progress


def naive_dict_to_tsv(data):
    if len(data) > 0:
        outs = io.StringIO()
        column_headers = list(data.values())[0].keys()
        writer = csv.DictWriter(outs, delimiter='\t', fieldnames=column_headers)
        writer.writeheader()
        writer.writerows(data.values())
        return outs.getvalue()
    else:
        return ""
