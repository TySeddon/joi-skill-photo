from ast import Return
from operator import truediv
import random
from adapt.intent import IntentBuilder
from mycroft import MycroftSkill, intent_handler
from mycroft.skills.common_play_skill import CommonPlaySkill, CPSMatchLevel
from mycroft.messagebus import Message
import webbrowser
from time import sleep
import uuid
import urllib.parse
import os

from .google_photo import GooglePhoto
from .slideshow import Slideshow, JOI_SERVER_URL

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

    ###########################################

    @intent_handler(IntentBuilder('PlayPhotoIntent').require('Photo').optionally("Play"))
    def handle_play_photo_intent(self, message):
        """ This is an Adapt intent handler, it is triggered by a keyword."""
        self.log.info("handle_play_photo_intent")
        self.log.info(os.getcwd())
        self.stopped = False

        self.resident_name = "Ruth"

        # start the session
        self.speak_dialog(key="Session_Start", 
                          data={"resident_name": self.resident_name})

        # login to Google Photo
        self.google_photo = GooglePhoto()

        # setup slideshow
        self.slideshow = Slideshow()

        # get list of albums
        albums = self.google_photo.get_albums()

        # choose a playlist
        album = random.choice(albums)
        photos = self.google_photo.get_media_items(album.id)

        # create a random set of photos for this session
        self.session_photos = self.suffle_photos(photos)

        # launch photo player
        self.open_browser()

        self.start_next_photo(False)

    def open_browser(self):
        url = "%s/joi/slideshow?id=%s" % (JOI_SERVER_URL, self.slideshow.slideshow_id)
        webbrowser.open(url=url, autoraise=True)

    def close_browser(self):
        os.system("killall chromium-browser")

    def session_end(self):
        self.log.info("session_end")
        if self.stopped: return 
        self.speak_dialog(key="Session_End")
        sleep(5)
        self.close_browser()

    def photo_intro(self, photo):
        self.log.info("photo_intro")
        if self.stopped: return 
        self.speak_dialog(key="Photo_Intro",
                          data={},
                          wait=True)

    def photo_followup(self, photo):
        self.log.info("photo_followup")
        if self.stopped: return 
        self.speak_dialog(key="Photo_Followup",
                          data={},
                          wait=True)

    ###########################################

    def suffle_photos(self, photos):
         return random.sample(photos,10)

    def get_next_photo(self):
        if len(self.session_photos) > 0:
            track = self.session_photos.pop(0)
            return track
        else:
            return None

    def start_next_photo(self, pauseFirst):
        self.photo = self.get_next_photo()
        if self.photo:
            if self.stopped: return False
            #if pauseFirst:
            #    sleep(1)
            if self.stopped: return False
            self.log.info("Starting photo %s" % (self.photo.filename))
            self.photo_intro(self.photo)
            self.slideshow.show_photo(self.photo.id, self.photo.baseUrl)
            self.start_monitor()
            return True
        else:
            self.log.info("No more photos in queue")
            return False

    def is_photo_done(self):
        if self.play_state.tick_count > 5:
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
        self.schedule_repeating_event(
            self.monitor_play_state, None, 2, name="WaitSlideshow"
        )
        #self.add_event("recognizer_loop:record_begin", self.handle_listener_started)

    def stop_monitor(self):
        self.log.info("stop_monitor")
        self.cancel_scheduled_event("WaitSlideshow")
        self.not_playing_count = 0

    def monitor_play_state(self):
        self.slideshow.tick_photo() # increment counter
        self.play_state = self.slideshow.get_playback_state()
        #self.log.info('%.2f %% - Playing=%s - %s - Vol=%.0f %%' % (self.play_state.progress_pct * 100, self.play_state.is_playing, self.photo.name, self.play_state.volume_pct))
        self.log.info('Tick %i - Showing %s' % (self.play_state.tick_count, self.photo.name))

        if not self.play_state.is_playing:
            # if no longer playing, abandon polling after 60 seconds
            self.not_playing_count += 1
            if self.not_playing_count > 60:
                self.stop_monitor()

        if self.is_photo_done():
            # phot is done, so follow-up with user and start next photo
            self.play_state.is_playing = False
            self.stop_monitor()
            self.photo_followup(self.photo)

            started = self.start_next_photo(True)
            if not started:
                self.session_end()        

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
        self.play_state.is_playing = False

        self.stop_monitor()
        self.stop_idle_check()
        self.close_browser()
        return True

    def shutdown(self):
        """ The shutdown method is called during the Skill process termination. 
        It is used to perform any final actions to ensure all processes and operations 
        in execution are stopped safely. This might be particularly useful for Skills 
        that have scheduled future events, may be writing to a file or database, 
        or that have initiated new processes.
        """
        self.log.info("shutdown")
        self.stopped = True
        self.play_state.is_playing = False
        self.stop_monitor()
        self.stop_idle_check()


def create_skill():
    return JoiPhotoSkill()