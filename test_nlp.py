# Named Entity Recognition

# pip install azure-ai-textanalytics==5.1.0
# pip install azure-ai-textanalytics==5.2.0b1
# pip install azure-ai-language-questionanswering

from pprint import pprint
from azure.ai.textanalytics import TextAnalyticsClient, ExtractSummaryAction
from azure.core.credentials import AzureKeyCredential
from azure.ai.language.questionanswering import QuestionAnsweringClient
from azure.ai.language.questionanswering import models as qna
import re
from munch import munchify
import enviro

ta_key = enviro.get_value("ta_key")
ta_endpoint = enviro.get_value("ta_endpoint")
qna_key = enviro.get_value("qna_key")
qna_endpoint = enviro.get_value("qna_endpoint")
knowledge_base_project = enviro.get_value("knowledge_base_project")
knowledge_base_deployment = enviro.get_value("knowledge_base_deployment")


# Authenticate the client using your key and endpoint 
def authenticate_client():
    credential = AzureKeyCredential(ta_key)
    text_analytics_client = TextAnalyticsClient(
            endpoint=ta_endpoint, 
            credential=credential)
    return text_analytics_client

def print_entities(entities):
    print("Named Entities:\n")
    for entity in entities:
        print("\tText: \t", entity.text, "\tCategory: \t", entity.category, "\tSubCategory: \t", entity.subcategory,
                "\n\tConfidence Score: \t", round(entity.confidence_score, 2), "\tLength: \t", entity.length, "\tOffset: \t", entity.offset, "\n")

# Example function for recognizing entities from text
def recognize_entities(client, documents):
    try:
        result = client.recognize_entities(documents = documents)[0]
        return [entity for entity in result.entities]
    except Exception as err:
        print("Encountered exception. {}".format(err))

def print_key_phrases(key_phrases):
    print("\tKey Phrases:")
    for phrase in key_phrases:
        print("\t\t", phrase)

def extract_key_phrases(client, documents):
    try:
        response = client.extract_key_phrases(documents = documents)[0]
        if not response.is_error:
            return [phrase for phrase in response.key_phrases]                
        else:
            print(response.id, response.error)

    except Exception as err:
        print("Encountered exception. {}".format(err))


########################


# Example method for summarizing text
def sample_extractive_summarization(client, document):

    poller = client.begin_analyze_actions(
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

def replace_whole_word(search, replace, text):
    return re.sub(r"\b%s\b" % search , replace, text, flags =re.IGNORECASE)

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

###########################

def print_kb_response(original_question, kb_response):
    print("---------------------------------")
    print("Q: %s" % original_question)
    for answer in kb_response.answers:    
        print("Q: %s" % answer.questions[0])
        if answer.short_answer is not None:
            print("A (%.2f%%): %s" % (answer.short_answer.confidence * 100, answer.short_answer.text))    
        print("A (%.2f%%): %s" % (answer.confidence * 100, answer.answer))

def answer_question_kb(question):
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
    return [munchify({'question':o.questions[0],'short_answer':o.short_answer,'long_answer':o.answer,'confidence':o.confidence}) for o in output.answers]

def compose_prompt(object_text):
    entities = recognize_entities(client, [object_text])
    # entities_text = [o.text for o in entities]
    # phrases = key_phrase_extraction_example(client, object_text)
    #answer_question_kb(' '.join(phrases))
    #answer_question_kb(' '.join(entities_text))

    list = []
    responses = answer_question_kb(object_text)
    for response in responses:
        list.extend([
            "Is this %s?" % response.question,
            "Can you tell me more about %s %s?" % (response.question, response.long_answer),       
            "%s is %s" % (response.question, response.long_answer),
            "%s is %s" % (response.long_answer, response.question)
        ])
    return list        

    #Entity Category
    # "Person", "Location", "Organization", "Quantity", "DateTime", "personType", "Event", "Product", "Skill"

######################

# setup client
client = authenticate_client()

object_text = "garden, flower, daffodil, pretty"
prompts = compose_prompt(object_text)
for p in prompts:
    print(p)
quit()

answer_question_kb("My daughter?")
answer_question_kb("Lisa's daughter")
answer_question_kb("Who is Susanna?")
answer_question_kb("What is my daughter's name?")
answer_question_kb("How old is my daughter?")
answer_question_kb("sense of pride")
answer_question_kb("most proud")
quit()

entities = recognize_entities(client, object_text)
entities_text = [o.text for o in entities]
phrases = extract_key_phrases(client, object_text)
