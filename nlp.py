from logging import exception
from azure.ai.textanalytics import TextAnalyticsClient, ExtractSummaryAction
from azure.core.credentials import AzureKeyCredential
from azure.ai.language.questionanswering import QuestionAnsweringClient
from azure.ai.language.questionanswering import models as qna
import re
from munch import munchify
from .enviro import get_setting
from itertools import groupby

class NLP():

    def __init__(self, knowledge_base_project) -> None:
        self.ta_client = self.create_ta_client()
        self.knowledge_base_project = knowledge_base_project

    # Authenticate the client using your key and endpoint 
    def create_ta_client(self):
        ta_key = get_setting("ta_key")
        ta_endpoint = get_setting("ta_endpoint")
        credential = AzureKeyCredential(ta_key)
        text_analytics_client = TextAnalyticsClient(
                endpoint=ta_endpoint, 
                credential=credential)
        return text_analytics_client

    def print_entities(entities):
        for o in entities:
            print('------------------------------------------')
            for o in entities:
                print(f"{o.source}, {o.text}, {o.category}, {o.subcategory}, {o.confidence_score}")
            print('------------------------------------------')

    # function for recognizing entities from text
    def recognize_entities(self, documents):
        try:
            result = self.ta_client.recognize_entities(documents = documents)[0]
            return [entity for entity in result.entities]
        except Exception as err:
            raise err
            print("Encountered exception. {}".format(err))
            return []

    def print_key_phrases(key_phrases):
        for phrase in key_phrases:
            print(f"{phrase}")

    def extract_key_phrases(self, documents):
        try:
            response = self.ta_client.extract_key_phrases(documents = documents)[0]
            if not response.is_error:
                return [phrase for phrase in response.key_phrases]                
            else:
                raise Exception(response.error)
                print(response.id, response.error)

        except Exception as err:
            raise err
            print("Encountered exception. {}".format(err))


    ########################


    def extract_summary(self, document):

        poller = self.ta_client.begin_analyze_actions(
            document,
            actions=[
                ExtractSummaryAction(MaxSentenceCount=4)
            ],
        )

        document_results = poller.result()
        for result in document_results:
            extract_summary_result = result[0]  # first document, first result
            if extract_summary_result.is_error:
                print("...Is an error with code '{}' and message '{}'".format(
                    extract_summary_result.code, extract_summary_result.message
                ))
            else:
                print("Summary extracted: \n{}".format(
                    " ".join([sentence.text for sentence in extract_summary_result.sentences]))
                )


    ###################

    def contains_whole_word(search, text):
        return bool(re.findall(r"\b%s\b" % search, text, flags =re.IGNORECASE))

    def replace_whole_word(search, replace, text):
        return re.sub(r"\b%s\b" % search , replace, text, flags =re.IGNORECASE)

    """ 
    resident_name = "Ruth"
    resident_name_possessive = resident_name + "'s"
    resident_name_mapping = [
            ("my", "your", resident_name_possessive),
            ("mine", "your", resident_name_possessive),
            ("I", "you", resident_name),
            ("me", "you", resident_name),
            ("myself", "you", resident_name),
        ]

    def clean_question(question):
        result = question
        for m in resident_name_mapping:
            result = replace_whole_word(m[0], m[2], result)
        return result

    def clean_answer(question):
        result = question
        for m in resident_name_mapping:
            result = replace_whole_word(m[2], m[1], result)
        return result 

    """

    def unique_entities(entities):
        """Given a list of entities that contains duplicates, 
        return the entity for each 'text' attribute of the highest confidence_score """
        result = []
        sorted_entities = sorted(entities, key=lambda o: o.text)
        for key,items in groupby(sorted_entities, key=lambda o: o.text):
            first_obj = next(iter(sorted(items,key=lambda o: o.confidence_score, reverse=True)),None)
            result.append(first_obj)
        return result

    def get_quoted(text):
        return re.findall('"([^"]*)"', text)

    ###########################

    def print_kb_responses(responses):
        print("---------------------------------")
        for r in responses:
            print(f"{r.question}, {r.long_answer}, {r.short_answer.text if r.short_answer else None}, {r.confidence}")

    def answer_question_kb(self, question):
        qna_key = get_setting("qna_key")
        qna_endpoint = get_setting("qna_endpoint")
        knowledge_base_project = self.knowledge_base_project
        knowledge_base_deployment = get_setting("knowledge_base_deployment")

        credential = AzureKeyCredential(qna_key)
        client = QuestionAnsweringClient(qna_endpoint, credential)
        with client:
            output = client.get_answers(
                question = question,
                project_name=knowledge_base_project,
                deployment_name=knowledge_base_deployment,
                top=3,
                confidence_threshold=0.3,
                short_answer_options  = qna.ShortAnswerOptions(enable = True,confidence_threshold=0.3,top=3)
            )
        return [munchify(
            {'question':(o.questions[0] if o.questions else ''),
                'short_answer':o.short_answer,
                'long_answer':o.answer,
                'confidence':o.confidence
            }) for o in output.answers]


# Language Studio
# https://language.cognitive.azure.com/home