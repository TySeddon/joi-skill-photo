import re
import os
import random
import webbrowser
import asyncio
from time import sleep
from adapt.intent import IntentBuilder
from mycroft import MycroftSkill, intent_handler
from mycroft.skills.common_play_skill import CommonPlaySkill, CPSMatchLevel
from mycroft.messagebus import Message
from mycroft.audio import wait_while_speaking
from joi_skill_utils.nlp import NLP
from joi_skill_utils.dialog import Dialog
from joi_skill_utils.enviro import get_setting
from joi_skill_utils.joiclient import JoiClient, PHOTO_TYPE
from joi_skill_utils.google_photo import GooglePhoto
from joi_skill_utils.slideshow import Slideshow

class JoiPhotoSkill(MycroftSkill):
    def __init__(self):
        """ The __init__ method is called when the Skill is first constructed.
        It is often used to declare variables or perform setup actions, however
        it cannot utilise MycroftSkill methods as the class does not yet exist.
        """
        super().__init__()
        self.learning = True
        self.stopped = False
        self.play_state = None
        self.google_photo = None
        self.slideshow = None
        self.sentiments = []

    def initialize(self):
        """ Perform any final setup needed for the skill here.
        This function is invoked after the skill is fully constructed and
        registered with the system. Intents will be registered and Skill
        settings will be available."""
        my_setting = self.settings.get('my_setting')
        #self.add_event("mycroft.stop", self.stop)
        self.add_event("recognizer_loop:record_begin", self.handle_listener_started)
        self.add_event("skill.joi-skill-photo.stop", self.stop)
        self.add_event("skill.joi-skill-photo.start", self.handle_play_photo_intent)
        self.open_browser_home()

    ###########################################

    @intent_handler(IntentBuilder('PlayPhotoIntent').require('Photo').optionally("Play"))
    def handle_play_photo_intent(self, message):
        """ This is an Adapt intent handler, it is triggered by a keyword."""
        self.log.info("handle_play_photo_intent")
        self.start(start_method=f"User said: {message.data['utterance']}")

    def start(self, start_method):
        self.log.info("start")
        self.stopped = False
        if not start_method:
            start_method = "bus.event"

        # stop the music player (in case it is running)
        self.bus.emit(Message("skill.joi-skill-music.stop"))

        # establish connection to Joi server
        joi_device_id = get_setting("device_id")
        self.joi_client = JoiClient(joi_device_id)
        resident = self.joi_client.get_Resident()
        self.resident_name = resident.first_name
        self.sentiments = []

        self.speak_dialog(key="Session_Start", 
                          data={"resident_name": self.resident_name})

        self.activate_smarthome_scene()

        # setup natural language processing clients
        self.nlp = NLP(resident.knowledge_base_name)
        self.dialog = Dialog(self.nlp, self.resident_name)   

        # get memory boxes. Choose one at random
        memoryboxes = self.joi_client.list_MemoryBoxes()
        self.log.info(f"{len(memoryboxes)} memoryboxes found")
        photo_memoryboxes = list(filter(lambda o: o.memorybox_type == PHOTO_TYPE, memoryboxes))
        self.log.info(f"{len(photo_memoryboxes)} photo_memoryboxes found")
        photo_memorybox = random.choice(photo_memoryboxes)
        self.log.info(f"Selected memory box '{photo_memorybox.name}'")

        # start the session
        self.start_memorybox_session(photo_memorybox, start_method)

        # login to Google Photo
        self.google_photo = GooglePhoto()
        # setup slideshow
        self.slideshow = Slideshow()
        # get list of albums
        # albums = self.google_photo.get_albums()
        # album = random.choice(albums)
        # self.log.info(f"album.id = {album.id}")

        # choose a album
        album_id = photo_memorybox.url
        self.log.info(f"album_id = {album_id}")
        photos = self.google_photo.get_media_items(album_id)
        # create a random set of photos for this session
        self.session_photos = self.arrange_photos(photos, 10)

        # launch photo player
        self.open_browser_music()

        wait_while_speaking()

        self.start_next_photo(False)

    ################################

    def activate_smarthome_scene(self):
        self.log.info("activate_smarthome_scene")
        self.bus.emit(Message("skill.homeassistant.turn_action",  
                                data={
                                    "Entity": "light strip",  
                                    "Action" : "on"}))  

    def deactivate_smarthome_scene(self):
        self.log.info("deactivate_smarthome_scene")
        self.bus.emit(Message("skill.homeassistant.turn_action",  
                                data={
                                    "Entity": "light strip",  
                                    "Action" : "off"}))  

    ################################

    def open_browser_music(self):
        joi_server_url = get_setting("joi_server_url")
        url = f"{joi_server_url}/joi/slideshow?id={self.slideshow.slideshow_id}"

        retry_count = 0
        success = False
        while not success and retry_count < 3:
            success = webbrowser.open(url=url, autoraise=True)
            sleep(1)
            retry_count += 1

    def open_browser_home(self):
        joi_server_url = get_setting("joi_server_url")
        url = f"{joi_server_url}/joi/joi_home"

        retry_count = 0
        success = False
        while not success and retry_count < 3:
            success = webbrowser.open(url=url, autoraise=True)
            sleep(1)
            retry_count += 1

    def close_browser(self):
        try:
            os.system("killall chromium-browser")
        except:
            self.log.warn("Error closing web browser")

    def session_end(self):
        self.log.info("session_end")
        if self.stopped: return 
        self.speak_dialog(key="Session_End",
                          data={"resident_name": self.resident_name})
        self.deactivate_smarthome_scene()                          
        sleep(5)
        self.slideshow.end_slideshow()
        self.close_browser()
        self.open_browser_home()

    def photo_intro(self, photo):
        self.log.info("photo_intro")
        if self.stopped: return 

        self.log.info(f"Starting photo: {self.photo.filename}")
        object_text = photo.description
        self.log.info(f"Photo description: {object_text}")
        prompts_objs = self.dialog.compose_prompts(object_text)

        # give user a few seconds to look at photo before prompting
        sleep(3)

        if prompts_objs:
            prompt_obj = random.choice(prompts_objs)
            prompt = prompt_obj.prompt
            self.log.info(f"Selected prompt {prompt} from {len(prompts_objs)} possible prompts")
            self.speak(prompt)
            self.add_media_interaction(elapsed_seconds=0, event="Joi prompt", data=prompt)
        else:
            self.log.warn(f"No prompts found for {object_text}.  Falling back to dialog Photo_Intro")
            self.speak_dialog(key="Photo_Intro",
                            data={
                                "resident_name": self.resident_name
                                })

    def photo_followup(self, photo):
        self.log.info("photo_followup")
        if self.stopped: return 

        if self.is_latest_sentiment_negative(): 
            self.speak_dialog(key="Photo_Followup_Negative",
                          data={"resident_name": self.resident_name})
        else:
            self.speak_dialog(key="Photo_Followup",
                          data={"resident_name": self.resident_name})

    def is_latest_sentiment_negative(self):
        if self.sentiments and self.sentiments[-1] and self.sentiments[-1].negative > 0.8:
            return True
        else:
            return False

    ###########################################

    def _build_pyramid(self, sorted_list):
        """Take a sorted list and arrange it so the highest is in the middle
        This results in a ramp-up and ramp-down
        """
        even = sorted_list[::2]
        odd = sorted_list[1::2]
        even.extend(reversed(odd))
        return even

    def arrange_photos(self, photos, n):
        #return random.sample(photos,10)

        # get the stars (asterisks) in description
        # looking for *, **, ***, ****, etc
        for photo in photos:
            stars = re.findall(r'[\*]+',photo.description)
            photo.stars = len(stars[0]) if stars else 0

        sorted_photos = sorted(photos,key=lambda o: o.stars)
        # split list low and high rating
        # choose a few slow and fast songs
        low_photos = random.sample(sorted_photos[:len(sorted_photos)//2],n//2)
        high_photos = random.sample(sorted_photos[len(sorted_photos)//2:],n//2)
        sorted_photos_subset = sorted(low_photos + high_photos, key=lambda o: o.stars)

        # arrange in a ramp-up, ramp-down pyramid
        result = self._build_pyramid(sorted_photos_subset)
        for photo in result:
            self.log.info(f"{photo.stars}")
        return result

    def get_next_photo(self):
        if len(self.session_photos) > 0:
            track = self.session_photos.pop(0)
            return track
        else:
            return None

    def get_user_response(self):
        user_response = self.get_response() # listen to user
        self.log.info(f"User said: {user_response}")
        if user_response is not None:
            if user_response.lower() == "stop":
                self.stop()
                return

            last_sentiment_was_negative = self.is_latest_sentiment_negative()
            sentiment_response = self.nlp.get_sentiment(user_response)
            sentiment = sentiment_response.sentiment
            self.log.info(f"positive:{sentiment.positive}, neutral:{sentiment.neutral}, negative:{sentiment.negative}")
            self.sentiments.append(sentiment)

            # if this sentiment is negative and the last sentimend was negative
            # disabling this.  This will take a while to test
            if False and self.is_latest_sentiment_negative() and last_sentiment_was_negative:
                self.speak("Let's listen to some music instead.")
                wait_while_speaking()
                # stop showing photos and switch over to music
                self.stop()
                self.bus.emit(Message("skill.joi-skill-music.start"))
                return

            entities = self.nlp.recognize_entities([user_response])
            for e in entities:
                self.log.info(f"Extracted entity {e.text}")
            entity = random.choice(entities) if entities else None
            entity_text = entity.text if entity else 'that' # generic place holder in case we can't identify any entities

            if sentiment and sentiment.negative > 0.8:
                self.speak_dialog(key='Response_Followup_Negative',
                            data={
                                "resident_name": self.resident_name,
                                "entity_text": entity_text
                            })
            elif sentiment and sentiment.positive > 0.8:
                self.speak_dialog(key='Response_Followup_Positive',
                            data={
                                "resident_name": self.resident_name,
                                "entity_text": entity_text
                            })
            else:
                self.speak_dialog(key='Response_Followup',
                            data={
                                "resident_name": self.resident_name,
                                "entity_text": entity_text
                            })

            self.add_media_interaction(elapsed_seconds=0, event="Resident response", data=user_response, analysis=sentiment)                        
            wait_while_speaking()
        else:
            self.sentiments.append(None)
            self.add_media_interaction(elapsed_seconds=0, event="Resident response", data="None")

    def start_next_photo(self, pauseFirst):
        self.photo = self.get_next_photo()
        if self.photo:
            if self.stopped: return False
            #if pauseFirst:
            #    sleep(1)
            if self.stopped: return False
            self.log.info(f"Starting photo {self.photo.filename}")
            self.slideshow.show_photo(self.photo.id, self.photo.baseUrl)
            self.start_memorybox_session_media(self.photo)
            self.photo_intro(self.photo)
            wait_while_speaking()

            self.start_monitor()

            self.get_user_response()

            return True
        else:
            self.log.info("No more photos in queue")
            return False

    def is_photo_done(self):
        if self.is_latest_sentiment_negative() or self.play_state.tick_count >= 3:
            return True
        else:
            return False

    def pause_photo(self, message=None):
        self.log.info("pause_photo")
        self.slideshow.pause_playback()
        self.play_state.is_playing = False
        self.stop_monitor()        

    def resume_photo(self):
        self.log.info("resume_photo")
        self.slideshow.resume_playback()
        self.play_state.is_playing = True
        self.start_monitor()

    def start_monitor(self):
        # Clear any existing event
        self.stop_monitor()
        if self.stopped: return

        self.log.info("start_monitor")
        # Schedule a new one every second to monitor Slideshow play status
        self.schedule_event(self.monitor_play_state,when=5,name="WaitSlideshow")
        #self.schedule_repeating_event(self.monitor_play_state, None, 5, name="WaitSlideshow")
        #self.add_event("recognizer_loop:record_begin", self.handle_listener_started)

    def stop_monitor(self):
        self.log.info("stop_monitor")
        self.cancel_scheduled_event("WaitSlideshow")
        self.not_playing_count = 0

    def monitor_play_state(self):
        self.play_state = self.slideshow.get_playback_state()
        self.log.info(f"Tick {self.play_state.tick_count} - Showing {self.photo.filename}")

        if not self.play_state.is_playing:
            # if no longer playing, abandon polling after 60 seconds
            self.not_playing_count += 1
            if self.not_playing_count > 60:
                self.stop_monitor()
                return

        if self.is_photo_done():
            # phot is done, so follow-up with user and start next photo
            self.play_state.is_playing = False
            self.stop_monitor()
            self.photo_followup(self.photo)
            self.end_memorybox_session_media()
            wait_while_speaking()
            started = self.start_next_photo(True)
            if not started:
                self.end_memorybox_session("normal completion")
                self.session_end()
                return

        self.start_monitor()

    def handle_listener_started(self, message):
        self.log.info("handle_listener_started")
        if self.play_state and self.play_state.is_playing:
            self.pause_photo()
            self.start_idle_check()

    def start_idle_check(self):
        self.idle_count = 0
        self.stop_idle_check()
        self.schedule_repeating_event(
            self.check_for_idle, None, 1, name="IdleCheck"
        )       

    def stop_idle_check(self):
        self.cancel_scheduled_event("IdleCheck")

    def check_for_idle(self):
        self.log.info("check_for_idle")
        if self.play_state and self.play_state.is_playing:
            self.stop_idle_check()
            return
        self.idle_count += 1
        if self.idle_count >= 5:
            # Resume playback after 5 seconds of being idle
            self.stop_idle_check()
            if self.stopped: return
            self.resume_photo()


    ###########################################
    def start_memorybox_session(self, photo_memorybox, start_method):
        self.memorybox_session = self.joi_client.start_MemoryBoxSession(
                                    memorybox_id=photo_memorybox.memorybox_id, 
                                    start_method=start_method)

    def end_memorybox_session(self, end_method):
        if hasattr(self, 'memorybox_session') and self.memorybox_session:
            self.joi_client.end_MemoryBoxSession(
                            self.memorybox_session.memorybox_session_id,
                            session_end_method=end_method, 
                            resident_self_reported_feeling="NA")
            self.memorybox_session = None                        

    def start_memorybox_session_media(self, photo):
        if hasattr(self, 'memorybox_session') and self.memorybox_session:
            self.session_media = self.joi_client.start_MemoryBoxSessionMedia(
                            memorybox_session_id=self.memorybox_session.memorybox_session_id, 
                            media_url=photo.baseUrl,
                            media_name=photo.filename,
                            media_artist="NA",
                            media_tags=photo.description,
                            media_classification="NA",
                            media_features=None)

    def end_memorybox_session_media(self):
        if hasattr(self, 'session_media') and self.session_media:
            self.joi_client.end_MemoryBoxSessionMedia(
                            memorybox_session_media_id=self.session_media.memorybox_session_media_id, 
                            media_percent_completed = 1,
                            resident_motion="NA", 
                            resident_utterances="NA", 
                            resident_self_reported_feeling="NA")
            self.session_media = None                        

    def add_media_interaction(self, elapsed_seconds, event, data, analysis=None):
        if hasattr(self, 'session_media') and self.session_media:
            media_interaction = self.joi_client.add_MediaInteraction(
                            memorybox_session_media_id=self.session_media.memorybox_session_media_id, 
                            elapsed_seconds=elapsed_seconds,
                            media_percent_completed=0,
                            event=event,
                            data=data,
                            analysis=analysis)

    def stop_memorybox_session(self, end_method):
        self.end_memorybox_session_media()
        self.end_memorybox_session(end_method)

    ###########################################

    # def converse(self, utterances, lang):
    #     """ The converse method can be used to handle follow up utterances 
    #     prior to the normal intent handling process. It can be useful for handling 
    #     utterances from a User that do not make sense as a standalone intent.
    #     """
    #     if utterances and self.voc_match(utterances[0], 'understood'):
    #         self.speak_dialog('great')
    #         return True
    #     else:
    #         return False        

    def stop(self):
        """ The stop method is called anytime a User says "Stop" or a similar command. 
        It is useful for stopping any output or process that a User might want to end 
        without needing to issue a Skill specific utterance such as media playback 
        or an expired alarm notification.
        """
        self.log.info("mycroft.stop")
        self.stopped = True
        if self.slideshow:
            self.slideshow.end_slideshow()
        if self.play_state:
            self.play_state.is_playing = False

        loop = asyncio.new_event_loop()
        loop.call_later(5, self.deactivate_smarthome_scene())
        
        self.stop_monitor()
        self.stop_idle_check()
        self.close_browser()
        self.open_browser_home()
        self.stop_memorybox_session("stop")
        return True

    def shutdown(self):
        """ The shutdown method is called during the Skill process termination. 
        It is used to perform any final actions to ensure all processes and operations 
        in execution are stopped safely. This might be particularly useful for Skills 
        that have scheduled future events, may be writing to a file or database, 
        or that have initiated new processes.
        """
        self.log.info("shutdown")
        if self.slideshow:
            self.slideshow.end_slideshow()
        self.stopped = True
        if self.play_state:
            self.play_state.is_playing = False
        self.stop_monitor()
        self.stop_idle_check()
        self.stop_memorybox_session("shutdown")


def create_skill():
    return JoiPhotoSkill()