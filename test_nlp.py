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


def compose_product_prompts(product_text, subcategory, confidence, custom_categories):
    list = []
    list.extend([
        f"That is a nice looking {product_text}"
    ])
    if custom_categories.food and product_text != "food":
        list.extend([
            f"How do you make {product_text}?",
            f"Do you like to eat {product_text}?",
            f"What does {product_text} taste like?",
        ])

    return [f"{s} ({confidence})" for s in list]

def compose_skill_prompts(skill_text, subcategory, confidence):
    list = []
    list.extend([
        f"{skill_text} looks enjoyable",
        f"How did you learn {skill_text}?",
        f"Who taught you {skill_text}?",
        f"Who do you like to {skill_text} with?",
        f"Is {skill_text} difficult to learn?"
    ])
    return [f"{s} ({confidence})" for s in list]

def compose_person_prompts(person_text, subcategory, confidence):
    list = []
    list.extend([
        f"What else do you like to do with {person_text}?",
        f"It must be fun to spend time with {person_text}"
    ])
    return [f"{s} ({confidence})" for s in list]
    
def compose_persontype_prompts(persontype_text, subcategory, confidence):
    list = []
    list.extend([
        f"What else do you like to do with your {persontype_text}?",
        f"It must be fun to spend time with your {persontype_text}"
    ])
    return [f"{s} ({confidence})" for s in list]

def compose_location_prompts(location_text, subcategory, confidence):
    list = []
    if subcategory == "GPE":
        list.extend([
            f"What is it like in {location_text}?",
            f"{location_text} looks like a nice place",
            f"Do you like to go to {location_text}?"
        ])
    else:        
        list.extend([
            f"What is it like at the {location_text}?",
            f"Do you like to go to the {location_text}?",
            f"What kinds of things do you see at the {location_text}?",
            f"What are your favorite things to do at the {location_text}?"
        ])
    return [f"{s} ({confidence})" for s in list]

def compose_entity_promts(entities, custom_categories):
    list = []
    for entity in entities:
        if entity.category=="Location":
            list.extend(compose_location_prompts(entity.text, entity.subcategory, entity.confidence_score))
        elif entity.category=="Person":
            list.extend(compose_person_prompts(entity.text, entity.subcategory, entity.confidence_score))
        elif entity.category=="PersonType":
            list.extend(compose_persontype_prompts(entity.text, entity.subcategory, entity.confidence_score))
        elif entity.category=="Product":
            list.extend(compose_product_prompts(entity.text, entity.subcategory, entity.confidence_score, custom_categories))
        elif entity.category=="Skill":
            list.extend(compose_skill_prompts(entity.text, entity.subcategory, entity.confidence_score))
        else:
            list.extend([f"Not sure what to say about {entity.category}"])
    return list

def compose_prompts(object_text):
    # entities_text = [o.text for o in entities]
    # phrases = key_phrase_extraction_example(client, object_text)
    #answer_question_kb(' '.join(phrases))
    #answer_question_kb(' '.join(entities_text))

    list = []
    responses = answer_question_kb(object_text)
    for response in responses:
        question = response.question
        long_answer = response.long_answer
        short_answer = response.short_answer
        list.extend([
            f"Is this {question}?",
            #f"Can you tell me more about {question} {long_answer}?",       
            #f"{question} is {long_answer}",
            #f"{long_answer} is {question}"
        ])

        question_entities = recognize_entities(client, [question])
        answer_entities = recognize_entities(client, [long_answer])
        custom_categories = munchify({
            "food": "food" in [e.text for e in question_entities] or "food" in [e.text for e in answer_entities]
        })

        list.extend(compose_entity_promts(question_entities, custom_categories))
        list.extend(compose_entity_promts(answer_entities, custom_categories))

    object_entities = recognize_entities(client, [object_text])
    custom_categories = munchify({
        "food": "food" in [e.text for e in object_entities]
    })
    list.extend(compose_entity_promts(object_entities, custom_categories))

    return list        

    #Entity Category
    # "Person", "Location", "Organization", "Quantity", "DateTime", "personType", "Event", "Product", "Skill"

######################

# setup client
client = authenticate_client()

#object_text = "garden, flower, daffodil, pretty"
object_text = "ice cream, Susanna, beach, walk, Clearwater"
#object_text = "pinnocle, Fred, Margaret"
#object_text = "crochet blanket for grandchildren"
object_text = "jello with fruit, party"
prompts = compose_prompts(object_text)
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
