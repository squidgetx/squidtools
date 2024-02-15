import csv
import sys

def write_csv(records, filename, delimiter):
    fieldnames = set()
    for r in records:
        fieldnames.update(r.keys())
    with open(filename, 'wt') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=delimiter)
        writer.writeheader()
        writer.writerows(records)

def write_tsv(records, filename):
    write_csv(records, filename, delimiter='\t')

def print_err(msg):
    sys.stderr.write(str(msg) + "\n")
    sys.stderr.flush()

# batch generator
def gen_batches(iterable, max_batch_size: int):
    """ Batches an iterable into lists of given maximum size, yielding them one by one. """
    batch = []
    for element in iterable:
        batch.append(element)
        if len(batch) >= max_batch_size:
            yield batch
            batch = []
    if len(batch) > 0:
        yield batch