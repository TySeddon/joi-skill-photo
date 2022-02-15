from imp import source_from_cache
from re import sub
from munch import munchify
from .nlp import NLP

class Dialog():

    GENERIC_FOOD_NAMES = ['food', 'fruit', 'meat', 'vegetable']

    def __init__(self, nlp, resident_name) -> None:
        self.nlp = nlp
        self.resident_name = resident_name

    def wrap_entity_prompt(self, prompt, entity):
        return munchify({
                'prompt' : prompt,
                'entity_text' : entity.text,
                'category' : entity.category,
                'subcategory' : entity.subcategory,
                'confidence' : entity.confidence_score,
                'source': entity.source
            })

    def wrap_nonentity_prompt(self, prompt, text, confidence, source):
        return munchify({
                'prompt' : prompt,
                'entity_text' : text,
                'category' : None,
                'subcategory' : None,
                'confidence' : confidence,
                'source': source
            })

    def compose_product_prompts(self, entity):
        product_text = entity.text
        subcategory = entity.subcategory
        
        list = []
        if subcategory=="food" and product_text not in Dialog.GENERIC_FOOD_NAMES:
            list.extend([
                f"That is a delicious looking {product_text}?",
                f"That is a yummy looking {product_text}?",
                f"How do you make {product_text}?",
                f"Who taught you to make {product_text}?",
                f"When do you typicallly eat {product_text}?",
            ])
        else:
            list.extend([
                f"That is a nice looking {product_text}",
                f"What a lovely {product_text}",
                f"This is a beautiful {product_text}",
            ])
        return [self.wrap_entity_prompt(s,entity) for s in list]

    def compose_skill_prompts(self, entity):
        skill_text = entity.text
        subcategory = entity.subcategory

        list = []
        list.extend([
            f"{skill_text} looks like an enjoyable activity",
            f"How did you learn {skill_text}?",
            f"Who taught you {skill_text}?",
            f"Who do you like to {skill_text} with?",
            f"Do you like to {skill_text} with other people?",
            f"Is {skill_text} something you have done for a long time?",
            f"Is {skill_text} hard to learn?",
        ])
        return [self.wrap_entity_prompt(s,entity) for s in list]

    def compose_person_prompts(self,entity):
        person_text = entity.text
        subcategory = entity.subcategory
        
        list = []
        list.extend([
            f"What else do you like to do with {person_text}?",
            f"It must be fun to spend time with {person_text}",
            f"It must be nice to spend time with {person_text}",
            f"It must be an adventure to spend time with {person_text}",
        ])
        return [self.wrap_entity_prompt(s,entity) for s in list]
        
    def compose_persontype_prompts(self, entity):
        persontype_text = entity.text
        subcategory = entity.subcategory
        list = []
        list.extend([
            f"What else do you like to do with your {persontype_text}?",
            f"It must be fun to spend time with your {persontype_text}",
        ])
        return [self.wrap_entity_prompt(s,entity) for s in list]

    def compose_event_prompts(self, entity):
        event_text = entity.text
        subcategory = entity.subcategory
        list = []
        if subcategory=="DateRange":
            event_text = event_text.replace('the ', '')
            list.extend([
                f"What does your family do in {event_text}?",
                f"Do you like to visit your family in {event_text}?",
                f"Tell me a story about {event_text}?",
            ])
        else:
            list.extend([
                f"What does your family do at {event_text}?",
                f"Tell me a story about {event_text}?",
                f"Do your friends come to {event_text}?",
            ])
        return [self.wrap_entity_prompt(s,entity) for s in list]

    def compose_location_prompts(self, entity):
        location_text = entity.text
        subcategory = entity.subcategory

        list = []
        if subcategory=="GPE" or subcategory=="Geographical":
            list.extend([
                f"Is {location_text} a pleasant place?",
                f"{location_text} looks like a beautiful place",
                f"{location_text} looks like a lovely place",
                f"Is {location_text} a friendly place?",
                f"Is it pretty in {location_text}?",
                f"Looks like there is a lot to do in {location_text}",
                f"Do you like to visit friends in {location_text}?",
                f"Do you like to go to {location_text}?",
            ])
        elif subcategory=="Structural":
            list.extend([
                f"Is {location_text} comfortable?",
                f"Can you tell me more about this {location_text}?",
                f"What a nice looking {location_text}",
                f"Do you like to go to {location_text}?",
                f"What kinds of things do you see at {location_text}?",
                f"What are your favorite things to do at {location_text}?",
            ])
        else:        
            list.extend([
                f"Do you like to go to the {location_text}?",
                f"What kinds of things do you see at the {location_text}?",
                f"What are your favorite things to do at the {location_text}?",
            ])
        return [self.wrap_entity_prompt(s,entity) for s in list]

    def compose_unknown_prompts(self, entity):
        text = entity.text
        category = entity.category

        list = []
        list.extend([
                f"Not sure what to say about {category} {text}"
            ])
        return [self.wrap_entity_prompt(s,entity) for s in list]

    def compose_pride_prompts(self, entity):
        pride_text = entity.text
        list = []
        list.extend([
            f"This must make you feel proud",
            f"{pride_text} must make you feel proud",
            f"Does {pride_text} make you happy?",
        ])
        return [self.wrap_entity_prompt(s,entity) for s in list]

    def compose_entity_prompts(self, entities):
        #Entity Category
        # "Person", "Location", "Organization", "Quantity", "DateTime", "personType", "Event", "Product", "Skill"
        list = []
        for entity in entities:
            # custom prompts
            if hasattr(entity, 'sense_of_pride') and entity.sense_of_pride:
                list.extend(self.compose_pride_prompts(entity))

            # category prompts    
            if entity.category=="Location":
                list.extend(self.compose_location_prompts(entity))
            elif entity.category=="Person":
                list.extend(self.compose_person_prompts(entity))
            elif entity.category=="PersonType":
                list.extend(self.compose_persontype_prompts(entity))
            elif entity.category=="Product":
                list.extend(self.compose_product_prompts(entity))
            elif entity.category=="Skill":
                list.extend(self.compose_skill_prompts(entity))
            elif entity.category=="Event":
                list.extend(self.compose_event_prompts(entity))
            elif entity.category=="DateTime":
                list.extend(self.compose_event_prompts(entity))
            else:
                list.extend(self.compose_unknown_prompts(entity))
        return list

    def compose_quoted_prompts(self, quoted, confidence):
        list = []
        list.extend([
            f"{quoted}"
        ])
        return [self.wrap_nonentity_prompt(s,quoted, confidence, "object_quote") for s in list]

    def compose_kb_prompts(self, response):
        question = response.question
        long_answer = response.long_answer
        short_answer = response.short_answer.text if response.short_answer else None

        list = []
        list.extend([
            f"Is this {question}?",
            #f"This looks like {question}",
            #f"Can you tell me more about {question} {long_answer}?",       
            #f"{question} is {long_answer}",
            #f"Is {long_answer} {question}?"
        ])
        return [self.wrap_nonentity_prompt(s,question, response.confidence, "kb_response") for s in list]

    def set_source(self, entities, source):
        for o in entities:
            o.source = source

    def identify_custom_attributes_kb(self, kb_response):
        for o in kb_response.answer_entities:
            o.sense_of_pride=NLP.contains_whole_word("pride", kb_response.question)

        if "food" in [o.text for o in kb_response.question_entities]:
            for o in kb_response.answer_entities:
                if o.category=="Product":
                    o.subcategory="food"

    def identify_custom_attributes_entities(self, object_entities):
        if "food" in [o.text for o in object_entities]:
            for o in object_entities:
                if o.category=="Product" and o.text != "food":
                    o.subcategory="food"

    def compose_prompts(self, object_text):
        # phrases = key_phrase_extraction_example(client, object_text)
        list = []
        entities = []

        # get text between quotes
        quotes = NLP.get_quoted(object_text)
        for q in quotes:
            list.extend(self.compose_quoted_prompts(q,1.0))
            # remove quoted text from object_text
            object_text = object_text.replace(f'"{q}"', '')

        if object_text:
            # query the Knowledge Base
            responses = self.nlp.answer_question_kb(object_text)
            #NLP.print_kb_responses(responses)
            for response in responses:
                question = response.question
                long_answer = response.long_answer
                short_answer = response.short_answer.text if response.short_answer else None

                if question:
                    list.extend(self.compose_kb_prompts(response))
                    response.question_entities = self.nlp.recognize_entities([question])
                else:
                    response.question_entities = []

                self.set_source(response.question_entities, "kb_question")
                entities.extend(response.question_entities)

                response.answer_entities = self.nlp.recognize_entities([long_answer])
                self.set_source(response.answer_entities, "kb_answer")
                entities.extend(response.answer_entities)

                self.identify_custom_attributes_kb(response)

            object_entities = self.nlp.recognize_entities([object_text])
            self.set_source(object_entities, "object")
            self.identify_custom_attributes_entities(object_entities)
            entities.extend(object_entities)

            ue = NLP.unique_entities(entities)
            list.extend(self.compose_entity_prompts(ue))

            #NLP.print_entities(entities)

        return list        




# active listening phrases
# tell me more about…
# What is it like in… <place>
# Wow, you must feel really proud about <pride>
# That must have felt good to <hobby> or <pride>
# What was it like to grow up in <place>
# <place> looks really nice
# It must have been fun to play <game> with <who>
# Do you like <treat>
# Who else in your family likes <treat>
# Who would you share <treat> with
# How did you learn how to make <food>
# Is it hard to make <food>
# What does <food> taste like?
