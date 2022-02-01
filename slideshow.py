import datetime
import uuid
from datetime import datetime
import requests
from munch import munchify
import json

JOI_SERVER_URL = 'http://127.0.0.1:8000'
#JOI_SERVER_URL = 'https://joi-test-site.azurewebsites.net'

SLIDESHOW_API_PATH = '/joi/v1/slideshows/'

class Slideshow():

    def __init__(self):
        self.slideshow_id = uuid.uuid4()
        self.url = JOI_SERVER_URL + SLIDESHOW_API_PATH
        self.start()

    def start(self):
        response = requests.post(self.url, json={
            'slideshow_id': str(self.slideshow_id),
            'media_id' : 'x',
            'media_url' : 'x',
            'tick_count' : 0,
            'ping_datetime': datetime.utcnow().isoformat()
        })
        print(response.status_code)

    def show_photo(self, media_id, media_url):
        url = "%s%s/" % (self.url, self.slideshow_id)
        requests.put(url, json={
            'slideshow_id': str(self.slideshow_id),
            'media_id' : media_id,
            'media_url' : media_url,
            'tick_count' : 0,
            'ping_datetime': datetime.utcnow().isoformat()
        })

    def tick_photo(self):
        play_state = self.get_playback_state()
        url = "%s%s/" % (self.url, self.slideshow_id)
        requests.patch(url, json={
            'tick_count' : play_state.tick_count + 1,
        })

    def get_playback_state(self):
        url = "%s%s/" % (self.url, self.slideshow_id)
        response = requests.get(url)
        obj = munchify(json.loads(response.content))
        return obj
