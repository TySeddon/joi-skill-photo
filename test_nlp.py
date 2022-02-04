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

client = authenticate_client()

# Example function for recognizing entities from text
def entity_recognition_example(client, documents):
    try:
        result = client.recognize_entities(documents = documents)[0]
        print("Named Entities:\n")
        for entity in result.entities:
            print("\tText: \t", entity.text, "\tCategory: \t", entity.category, "\tSubCategory: \t", entity.subcategory,
                    "\n\tConfidence Score: \t", round(entity.confidence_score, 2), "\tLength: \t", entity.length, "\tOffset: \t", entity.offset, "\n")
        return [entity for entity in result.entities]
    except Exception as err:
        print("Encountered exception. {}".format(err))


def key_phrase_extraction_example(client, documents):
    try:
        response = client.extract_key_phrases(documents = documents)[0]

        if not response.is_error:
            print("\tKey Phrases:")
            for phrase in response.key_phrases:
                print("\t\t", phrase)
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

def answer_question(question, kb_documents):
    credential = AzureKeyCredential(qna_key)
    client = QuestionAnsweringClient(qna_endpoint, credential)
    with client:
        input = qna.AnswersFromTextOptions(
            question=clean_question(question),
            text_documents=kb_documents
        )

        output = client.get_answers_from_text(input)

    answers = sorted([a for a in output.answers], key=lambda o: o.confidence, reverse=True)
    # for answer in answers:
    #     print(u"Q: {}".format(input.question))
    #     print(u"A: {}".format(answer.answer))
    #     print("Confidence Score: {}".format(answer.confidence))

    best_answer = answers[0]
    print(u"Q: {}".format(question))
    #print(u"Q: {}".format(input.question))
    #print(u"A: {}".format(best_answer.answer))
    print(u"A: {}".format(clean_answer(best_answer.answer)))
    print("Confidence Score: {}".format(best_answer.confidence))



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
    print("---------------------------------")
    print("Q: %s" % question)
    for answer in output.answers:    
        print("Q: %s" % answer.questions[0])
        if answer.short_answer is not None:
            print("A (%.2f%%): %s" % (answer.short_answer.confidence * 100, answer.short_answer.text))    
        print("A (%.2f%%): %s" % (answer.confidence * 100, answer.answer))
    return [munchify({'question':o.questions[0],'short_answer':o.short_answer,'long_answer':o.answer,'confidence':o.confidence}) for o in output.answers]

def compose_prompt(object_text):
    entities = entity_recognition_example(client, object_text)
    # entities_text = [o.text for o in entities]
    # phrases = key_phrase_extraction_example(client, object_text)
    #answer_question_kb(' '.join(phrases))
    #answer_question_kb(' '.join(entities_text))

    response = answer_question_kb(object_text[0])
    print("Is this %s?" % response[0].question)
    print("Can you tell me more about %s %s?" % (response[0].question, response[0].long_answer))
    print("%s is %s" % (response[0].question, response[0].long_answer))
    print("%s is %s" % (response[0].long_answer, response[0].question))

    #Entity Category
    # "Person", "Location", "Organization", "Quantity", "DateTime", "personType", "Event", "Product", "Skill"



object_text = ["garden, flower, daffodil, pretty"]
compose_prompt(object_text)
quit()

answer_question_kb("My daughter?")
answer_question_kb("Lisa's daughter")
answer_question_kb("Who is Susanna?")
answer_question_kb("What is my daughter's name?")
answer_question_kb("How old is my daughter?")
answer_question_kb("sense of pride")
answer_question_kb("most proud")
quit()

documents = [
    "Ruth grew sunflowers in the summer in her garden in North Carolina. They are some of Ruth's favorite flowers to grow. She won several awards for her sunflowers."
    ]






documents = [
    "Ruth has 3 children and 5 grandchildren.",
    "Ruth once lived in North Carolina",
    "Ruth currently lives in Indiana",
    "Ruth's daughter is Lisa",
    "Lisa's daughter is Susanna",
] 

documents2 = [
    "You have 3 children and 5 grandchildren.",
    "Your once lived in North Carolina",
    "You currently live in Indiana",
    "Your daughter is Lisa",
    "Lisa's daughter is Susanna",
] 

persona = [
    "Ruth is a 78 year old female who is an avid gardener. Always an active community member and volunteer, Ruth enjoys seeing her neighbors and friends. She has known these people her whole life as the wife of a judge and business man as well as her stints into selling Avon, leading the DAR, playing the piano in her church, and growing her beautiful flowers and vegetables. Ruth had 6 children over the span of 16 years and is now Gram to her 29 grandchildren. Her home base is in upper NY state with her oldest son. However, in the winter, she travels to Florida to stay with her oldest daughter. She and her granddaughter love to go on afternoon walks at the beach, get ice cream or a Wendy's frosty, and play pinochle in the evenings. Ruth played pinochle for years with her brother, Fred, and his wife Margaret. Her favorite saying when something tickles her is goody, goody. Ruth is also known to keep Cadbury chocolate bars in her top dresser drawer that she shares a snitch with her granddaughter. Of course, her Jello with fruit is always a hit (orange with carrots, lime with celery, and mixed fruit with cherry). In addition, Ruth makes beautiful crocheted blankets. In fact, she has made one for each of her grandchildren and her great-grandchildren. Although she accepts life as it comes, she sorely misses her home in Somerville, NJ and her beautiful flower beds. Ruth loves music! She comes from a musical family and is known to play hymns and popular tunes on the piano. She plays at church and for the old people at the home. She also is an avid fan of Lawrence Welk"
]

entity_recognition_example(client, persona)
key_phrase_extraction_example(client, persona)
quit()


#entity_recognition_example(client, documents)
#key_phrase_extraction_example(client, documents)
#sample_extractive_summarization(client, documents)
#answer_question("How long does it takes to charge a surface?", text_documents)
#answer_question("Who is Ruth's daughter?", documents)
answer_question("Who is my daughter?", documents)
answer_question("Where do I live?", documents)
answer_question("Where did I live?", documents)
answer_question("Where am I?", documents)


documents = [
    "Ruth had a garden in North Carolina",
    "Ruth's favorite flower is daffodil",
    "Ruth's favorite hobby is gardening",
    "Ruth loves to paint"
]

answer_question("What is my favorite flower?", documents)
answer_question("What is my favorite hobby?", documents)
answer_question("What do I love doing?", documents)
answer_question("Where is my garden?", documents)

