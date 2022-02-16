import datetime
import uuid
from datetime import datetime
import requests
from munch import munchify
import json
from .enviro import get_setting

JOI_SERVER_URL = get_setting("joi_server_url")

SLIDESHOW_API_PATH = '/joi/v1/slideshows/'

class Slideshow():

    def __init__(self):
        self.slideshow_id = uuid.uuid4()
        self.url = JOI_SERVER_URL + SLIDESHOW_API_PATH
        self.tick_count = 0
        self.start()

    def start(self):
        response = requests.post(self.url, json={
            'slideshow_id': str(self.slideshow_id),
            'media_id' : 'x',
            'media_url' : 'x',
            'tick_count' : self.tick_count,
            'ping_datetime': datetime.utcnow().isoformat()
        })

    def show_photo(self, media_id, media_url):
        self.tick_count = 0
        url = "%s%s/" % (self.url, self.slideshow_id)
        requests.put(url, json={
            'slideshow_id': str(self.slideshow_id),
            'media_id' : media_id,
            'media_url' : media_url,
            'tick_count' : self.tick_count,
            'ping_datetime': datetime.utcnow().isoformat()
        })

    def _tick_photo(self):
        self.tick_count += 1
        url = "%s%s/" % (self.url, self.slideshow_id)
        response = requests.patch(url, json={
                        'ping_datetime': datetime.utcnow().isoformat(),
                        'tick_count' : self.tick_count,
                    })
        obj = munchify(json.loads(response.content))
        return obj

    def get_playback_state(self):
        # url = "%s%s/" % (self.url, self.slideshow_id)
        # response = requests.get(url)
        # obj = munchify(json.loads(response.content))
        obj = self._tick_photo()
        obj.is_playing = True
        self.tick_count = obj.tick_count
        return obj

    def end_slideshow(self):
        url = "%s%s/" % (self.url, self.slideshow_id)
        response = requests.delete(url)

    def pause_playback(self):
        pass

    def resume_playback(self):
        pass
