
def next_step_filename(file, step, delimiter='.'):
    # for a filename separated by '.'
    # insert "step" almost at the end
    # eg, a.b.txt => a.b.c.txt
    parts = file.split('.')
    parts.insert(-1, step)
    return '.'.join(parts)
