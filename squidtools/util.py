import csv

def write_csv(records, filename, delimiter):
    fieldnames = set()
    for r in records:
        fieldnames.update(r.keys())
    with open(filename, 'wt') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=delimiter)
        writer.writeheader()
        writer.writerows(records)