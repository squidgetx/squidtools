from QualtricsAPI.Setup import Credentials
from QualtricsAPI.Survey import Responses
import os
import wordfreq

Credentials().qualtrics_api_credentials(token=os.environ['QUALTRICS_TOKEN'],data_center=os.environ['QUALTRICS_DC'])


def download_survey(sid, dest):
    if os.path.isdir(dest):
        dest = f"{dest}/{sid}"
    responses = Responses().get_survey_responses(survey=sid)
    questions = Responses().get_survey_questions(survey=sid).to_dict('Questions')
    # Automatically create better labels
    for qid, text in questions:
        cmps = text.split('-')



    responses.iloc[2:].to_csv(f"{dest}-responses.tsv", sep='\t')
    questions.to_csv(f"{dest}-questions.tsv", sep='\t')

