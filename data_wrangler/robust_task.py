import os
import json

"""
Library / helper functions to manage idempotent execution of flaky tasks.

Supply robust_task with a list of files that need to be processed and a processing function 
that returns a dict (or other JSON serializable) result

Results are stored on disk in the progress capture filename given (or progress.json as default)
"""

DEFAULT_FILENAME = 'progress.json'

# Progress capture is implemented as lines of json in a file
# This way we can append easily to the file without thrashing the disk
def load_progress(pname):
    progress = {}
    if os.path.exists(pname):
        with open(pname, 'rt') as f:
            for line in f:
                p = json.loads(line)
                progress[p['filename']] = p
    return progress


# Save the result to disk
def save_progress(pname, result):
    with open(pname, 'at') as f:
        f.write(json.dumps(result) + '\n')


"""
files: array of filenames to process
task: function that processes a filename
progress_name: file that stores progress
skip_existing: don't re-process already processed files
"""
def robust_task(files, task, progress_name=DEFAULT_FILENAME, skip_existing=True):
    progress = load_progress(progress_name)
    for filename in files:
        if skip_existing and filename in progress:
            continue
        results = task(filename) 
        save_progress(progress_name, results)
        progress[filename] = results
    return progress


