import os
import random
import webbrowser
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
from joi_skill_utils.slideshow import Slideshow, JOI_SERVER_URL

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

    def initialize(self):
        """ Perform any final setup needed for the skill here.
        This function is invoked after the skill is fully constructed and
        registered with the system. Intents will be registered and Skill
        settings will be available."""
        my_setting = self.settings.get('my_setting')
        #self.add_event("mycroft.stop", self.stop)
        self.add_event("recognizer_loop:record_begin", self.handle_listener_started)
        self.add_event("skill.joi-skill-photo.stop", self.stop)

    ###########################################

    @intent_handler(IntentBuilder('PlayPhotoIntent').require('Photo').optionally("Play"))
    def handle_play_photo_intent(self, message):
        """ This is an Adapt intent handler, it is triggered by a keyword."""
        self.log.info("handle_play_photo_intent")
        self.start(start_method=f"User said: {message.data['utterance']}")

    def start(self, start_method):
        """ This is an Adapt intent handler, it is triggered by a keyword."""
        self.log.info("start")
        self.stopped = False

        # stop the music player (in case it is running)
        self.bus.emit(Message("skill.joi-skill-music.stop"))


        # establish connection to Joi server
        joi_device_id = get_setting("device_id")
        self.joi_client = JoiClient(joi_device_id)
        resident = self.joi_client.get_Resident()
        self.resident_name = resident.first_name

        self.speak_dialog(key="Session_Start", 
                          data={"resident_name": self.resident_name})

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
        self.session_photos = self.suffle_photos(photos)

        # launch photo player
        self.open_browser()

        wait_while_speaking()

        self.start_next_photo(False)

    def open_browser(self):
        url = f"{JOI_SERVER_URL}/joi/slideshow?id={self.slideshow.slideshow_id}"
        webbrowser.open(url=url, autoraise=True)

    def close_browser(self):
        os.system("killall chromium-browser")

    def session_end(self):
        self.log.info("session_end")
        if self.stopped: return 
        self.speak_dialog(key="Session_End",
                          data={"resident_name": self.resident_name})
        sleep(5)
        self.slideshow.end_slideshow()
        self.close_browser()

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
            self.add_media_interaction(event="Joi prompt", data=prompt)
        else:
            self.log.warn(f"No prompts found for {object_text}.  Falling back to dialog Photo_Intro")
            self.speak_dialog(key="Photo_Intro",
                            data={
                                "resident_name": self.resident_name
                                })

    def photo_followup(self, photo):
        self.log.info("photo_followup")
        if self.stopped: return 
        self.speak_dialog(key="Photo_Followup",
                          data={"resident_name": self.resident_name})

    ###########################################

    def suffle_photos(self, photos):
         return random.sample(photos,10)

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

            entities = self.nlp.recognize_entities([user_response])
            for e in entities:
                self.log.info(f"Extracted entity {e.text}")
            entity = random.choice(entities) if entities else None
            entity_text = entity.text if entity else 'that' # generic place holder in case we can't identify any entities
            self.speak_dialog(key='Response_Followup',
                        data={
                            "resident_name": self.resident_name,
                            "entity_text": entity_text
                        })
            self.add_media_interaction(event="Resident response", data=user_response)                        
            wait_while_speaking()
        else:
            self.add_media_interaction(event="Resident response", data="None")

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
        if self.play_state.tick_count >= 3:
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
                            media_classification="NA")

    def end_memorybox_session_media(self):
        if hasattr(self, 'session_media') and self.session_media:
            self.joi_client.end_MemoryBoxSessionMedia(
                            memorybox_session_media_id=self.session_media.memorybox_session_media_id, 
                            media_percent_completed = 100,
                            resident_motion="NA", 
                            resident_utterances="NA", 
                            resident_self_reported_feeling="NA")
            self.session_media = None                        

    def add_media_interaction(self, event, data):
        if hasattr(self, 'session_media') and self.session_media:
            media_interaction = self.joi_client.add_MediaInteraction(
                            memorybox_session_media_id=self.session_media.memorybox_session_media_id, 
                            media_percent_completed=0,
                            event=event,
                            data=data)

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
        if self.slideshow:
            self.slideshow.end_slideshow()
        self.stopped = True
        if self.play_state:
            self.play_state.is_playing = False

        self.stop_monitor()
        self.stop_idle_check()
        self.close_browser()
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