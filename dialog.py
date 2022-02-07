from nlp import NLP

class Dialog():

    GENERIC_FOOD_NAMES = ['food', 'fruit', 'meat', 'vegetable']

    def __init__(self, nlp, resident_name) -> None:
        self.nlp = nlp
        self.resident_name = resident_name

    def compose_product_prompts(self, product_text, subcategory, confidence):
        list = []
        list.extend([
            f"That is a nice looking {product_text}"
        ])
        if subcategory=="food" and product_text not in Dialog.GENERIC_FOOD_NAMES:
            list.extend([
                f"How do you make {product_text}?",
                f"Who taught you to make {product_text}?",
                f"When do you typicallly eat {product_text}?",
            ])

        return [f"{s} ({confidence})" for s in list]

    def compose_skill_prompts(self, skill_text, subcategory, confidence):
        list = []
        list.extend([
            f"{skill_text} looks enjoyable",
            f"How did you learn {skill_text}?",
            f"Who taught you {skill_text}?",
            f"Who do you like to {skill_text} with?",
            f"Is {skill_text} difficult to learn?"
        ])
        return [f"{s} ({confidence})" for s in list]

    def compose_person_prompts(self, person_text, subcategory, confidence):
        list = []
        list.extend([
            f"What else do you like to do with {person_text}?",
            f"It must be fun to spend time with {person_text}"
        ])
        return [f"{s} ({confidence})" for s in list]
        
    def compose_persontype_prompts(self, persontype_text, subcategory, confidence):
        list = []
        list.extend([
            f"What else do you like to do with your {persontype_text}?",
            f"It must be fun to spend time with your {persontype_text}"
        ])
        return [f"{s} ({confidence})" for s in list]

    def compose_event_prompts(self, event_text, subcategory, confidence):
        list = []
        list.extend([
            f"What does your family do at a {event_text}?",
            f"Can you tell me a story about one memorable {event_text}?"
        ])
        return [f"{s} ({confidence})" for s in list]

    def compose_location_prompts(self, location_text, subcategory, confidence):
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

    def compose_entity_promts(self, entities):
        list = []
        for entity in entities:
            if entity.category=="Location":
                list.extend(self.compose_location_prompts(entity.text, entity.subcategory, entity.confidence_score))
            elif entity.category=="Person":
                list.extend(self.compose_person_prompts(entity.text, entity.subcategory, entity.confidence_score))
            elif entity.category=="PersonType":
                list.extend(self.compose_persontype_prompts(entity.text, entity.subcategory, entity.confidence_score))
            elif entity.category=="Product":
                list.extend(self.compose_product_prompts(entity.text, entity.subcategory, entity.confidence_score))
            elif entity.category=="Skill":
                list.extend(self.compose_skill_prompts(entity.text, entity.subcategory, entity.confidence_score))
            elif entity.category=="Event":
                list.extend(self.compose_event_prompts(entity.text, entity.subcategory, entity.confidence_score))
            else:
                list.extend([f"Not sure what to say about {entity.category}"])
        return list

    def set_source(self, entities, source):
        for o in entities:
            o.source = source

    def compose_prompts(self, object_text):
        # phrases = key_phrase_extraction_example(client, object_text)
        list = []
        entities = []

        # get text between quotes
        quotes = NLP.get_quoted(object_text)
        for q in quotes:
            list.extend([
                f"{q}"
            ])
            # remove quoted text from object_text
            object_text = object_text.replace(f'"{q}"', '')

        if object_text:
            # query the Knowledge Base
            responses = self.nlp.answer_question_kb(object_text)
            NLP.print_kb_responses(responses)
            for response in responses:
                question = response.question
                long_answer = response.long_answer
                short_answer = response.short_answer.text if response.short_answer else None

                if question:
                    list.extend([
                        f"Is this {question}?",
                        #f"This looks like {question}",
                        #f"Can you tell me more about {question} {long_answer}?",       
                        #f"{question} is {long_answer}",
                        #f"Is {long_answer} {question}?"
                    ])
                    response.question_entities = self.nlp.recognize_entities([question])
                else:
                    response.question_entities = []

                self.set_source(response.question_entities, "question")
                entities.extend(response.question_entities)

                response.answer_entities = self.nlp.recognize_entities([long_answer])
                self.set_source(response.answer_entities, "answer")
                entities.extend(response.answer_entities)

                if "food" in [o.text for o in response.question_entities]:
                    for o in response.answer_entities:
                        if o.category=="Product":
                            o.subcategory="food"

            object_entities = self.nlp.recognize_entities([object_text])
            self.set_source(object_entities, "object")
            entities.extend(object_entities)
            ue = NLP.unique_entities(entities)
            list.extend(self.compose_entity_promts(ue))

            NLP.print_entities(entities)

        return list        

        #Entity Category
        # "Person", "Location", "Organization", "Quantity", "DateTime", "personType", "Event", "Product", "Skill"
