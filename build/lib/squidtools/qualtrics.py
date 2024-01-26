"""
Get responses from qualtrics JSON in tsv format
"""
def get_records(qualtrics_responses: dict, replaceWithText=False):
    assert 'responses' in qualtrics_responses 
    responses = qualtrics_responses ['responses']
    records = []
    for r in responses:
        record = {
            'responseId': r['responseId']
        }
        record.update(r['values'])
        records.append(record)
    return records

