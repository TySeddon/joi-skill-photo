import requests
import json
from munch import munchify
import datetime
import enviro

BASE_URL = enviro.get_value("joiserver_url")
LOGIN_URL = f"{BASE_URL}/joi/v1/users/login/"
DEVICE_URL = ""
RESIDENT_URL = ""
MEMORYBOX_URL = ""
MEMORYBOXSESSION_URL = ""
MEMORYBOXSESSIONMEDIA_URL = ""
MEDIAINTERACTION_URL = ""

class JoiClient():
    """
    
    General authentication flow:
        device = get_Device().  This allows the server to control which user to use.  Makes it easier for admin's to control.
        use device.resident_id to lookup the local yaml file for that resident that will contain username and password
        use that username and password to login the resident
        token = _login()
        with that token make all other REST calls
    """

    def __init__(self, device_id) -> None:
        """ Create a JoiClient for the given device_id.  Get the device_id from enviro.yaml"""
        self.device_id = device_id
        device = self._get_Device(self.device_id)
        self.resident_id = device.resident_id
        self.token = self._login(self.resident_id)

    def _login(self, resident_id):
        response = requests.post(LOGIN_URL, 
                        data=str({
                            'username': enviro.get_value('username', resident_id),
                            'password': enviro.get_value('password', resident_id),
                        }))
        return munchify(json.loads(response.content)).token

    def _build_header(self):
        return {'Authorization': 'Bearer {}'.format(self.token), 'Content-Type': 'application/json'}

    def _get_Device(self, device_id):
        response = requests.get(f"{DEVICE_URL}/{device_id}") # no credentials required for this call
        return munchify(json.loads(response.content)) 

    def get_Resident(self):
        response = requests.get(f"{RESIDENT_URL}/{self.resident_id}", header=self._build_header())
        return munchify(json.loads(response.content))

    def list_MemoryBoxes(self):
        response = requests.get(f"{MEMORYBOX_URL}", header=self._build_header())
        return munchify(json.loads(response.content))

    def add_MemoryBoxSession(self, memorybox_id, start_method):
        response = requests.post(MEMORYBOXSESSION_URL, headers=self._build_header(), 
                    data=str({
                        'memorybox_id': memorybox_id,
                        'resident_id' : self.resident_id,
                        'device_id': self.device_id,
                        'session_start_method': start_method,
                        'session_start_datetime': datetime.utcnow(),
                    }))
        return munchify(json.loads(response.content)) 

    # todo: update memoryboxsession

    def add_MemoryBoxSessionMedia(self, memorybox_session_id, media_url, media_name, media_artist, media_tags):
        response = requests.post(MEMORYBOXSESSIONMEDIA_URL, headers=self._build_header(), 
                    data=str({
                        'memorybox_session_id': memorybox_session_id,
                        'resident_id' : self.resident_id,
                        'media_url': media_url,
                        'media_start_datetime': datetime.utcnow(),
                        'media_name': media_name,
                        'media_artist': media_artist,
                        'media_tags': media_tags
                    }))
        return munchify(json.loads(response.content)) 

    # todo: update memoryboxsessionmedia

    def add_MediaInteraction(self, memorybox_session_media, media_percent_completed, event):
        response = requests.post(MEDIAINTERACTION_URL, headers=self._build_header(), 
                    data=str({
                        'memorybox_session_media': memorybox_session_media,
                        'resident_id' : self.resident_id,
                        'log_datetime': datetime.utcnow(),
                        'media_percent_completed': media_percent_completed,
                        'event': event,
                    }))
        return munchify(json.loads(response.content)) 


