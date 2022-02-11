import requests
import json
from munch import munchify
import datetime
import enviro

BASE_URL = enviro.get_value("joi_server_url")
LOGIN_PATH = f"{BASE_URL}/joi/v1/users/login/"
DEVICE_PATH = f"{BASE_URL}/joi/v1/devices/"
RESIDENT_PATH = f"{BASE_URL}/joi/v1/residents/"
MEMORYBOX_PATH = f"{BASE_URL}/joi/v1/memoryboxes/"
MEMORYBOXSESSION_PATH = f"{BASE_URL}/joi/v1/memoryboxsessions/"
MEMORYBOXSESSIONMEDIA_PATH = f"{BASE_URL}/joi/v1/memoryboxsessionmedia/"
MEDIAINTERACTION_PATH = f"{BASE_URL}/joi/v1/mediainteractions/"

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
        response = requests.post(LOGIN_PATH, 
                        data=str({
                            'username': enviro.get_value('username', resident_id),
                            'password': enviro.get_value('password', resident_id),
                        }))
        return munchify(json.loads(response.content)).token

    def _build_header(self):
        return {'Authorization': 'Bearer {}'.format(self.token), 'Content-Type': 'application/json'}

    def _get_Device(self, device_id):
        response = requests.get(f"{DEVICE_PATH}{device_id}") # no credentials required for this call
        return munchify(json.loads(response.content)) 

    def get_Resident(self):
        response = requests.get(f"{RESIDENT_PATH}{self.resident_id}", header=self._build_header())
        return munchify(json.loads(response.content))

    def list_MemoryBoxes(self):
        response = requests.get(f"{MEMORYBOX_PATH}", header=self._build_header())
        return munchify(json.loads(response.content))

    def start_MemoryBoxSession(self, memorybox_id, start_method):
        response = requests.post(MEMORYBOXSESSION_PATH, headers=self._build_header(), 
                    data=str({
                        'memorybox_id': memorybox_id,
                        'resident_id' : self.resident_id,
                        'device_id': self.device_id,
                        'session_start_method': start_method,
                        'session_start_datetime': datetime.utcnow(),
                    }))
        return munchify(json.loads(response.content)) 

    def end_MemoryBoxSession(self, memorybox_session_id, session_end_method, resident_self_reported_feeling):
        response = requests.post(MEMORYBOXSESSION_PATH, headers=self._build_header(), 
                    data=str({
                        'memorybox_session_id': memorybox_session_id,
                        'session_end_method': session_end_method,
                        'session_end_datetime': datetime.utcnow(),
                        'resident_self_reported_feeling': resident_self_reported_feeling,
                    }))
        return munchify(json.loads(response.content)) 

    def start_MemoryBoxSessionMedia(self, memorybox_session_id, media_url, media_name, media_artist, media_tags, media_classification):
        response = requests.post(MEMORYBOXSESSIONMEDIA_PATH, headers=self._build_header(), 
                    data=str({
                        'memorybox_session_id': memorybox_session_id,
                        'resident_id' : self.resident_id,
                        'media_url': media_url,
                        'media_start_datetime': datetime.utcnow(),
                        'media_name': media_name,
                        'media_artist': media_artist,
                        'media_tags': media_tags,
                        'media_classification': media_classification
                    }))
        return munchify(json.loads(response.content)) 

    def end_MemoryBoxSessionMedia(self, memorbybox_session_media_id, resident_motion, resident_utterances, resident_self_reported_feeling):
        response = requests.patch(MEMORYBOXSESSIONMEDIA_PATH, headers=self._build_header(), 
                    data=str({
                        'memorbybox_session_media_id': memorbybox_session_media_id,
                        'media_end_datetime': datetime.utcnow(),
                        'resident_motion': resident_motion,
                        'resident_utterances': resident_utterances,
                        'resident_self_reported_feeling': resident_self_reported_feeling
                    }))
        return munchify(json.loads(response.content)) 

    def add_MediaInteraction(self, memorybox_session_media, media_percent_completed, event, data):
        response = requests.post(MEDIAINTERACTION_PATH, headers=self._build_header(), 
                    data=str({
                        'memorybox_session_media': memorybox_session_media,
                        'resident_id' : self.resident_id,
                        'log_datetime': datetime.utcnow(),
                        'media_percent_completed': media_percent_completed,
                        'event': event,
                        'data': data,
                    }))
        return munchify(json.loads(response.content)) 

