import uuid
import requests
import json
from munch import munchify
from datetime import datetime
from .enviro import get_setting

BASE_URL = get_setting("joi_server_url")
LOGIN_PATH = f"{BASE_URL}/joi/v1/users/login/"
DEVICE_PATH = f"{BASE_URL}/joi/v1/devices/"
RESIDENT_PATH = f"{BASE_URL}/joi/v1/residents/"
MEMORYBOX_PATH = f"{BASE_URL}/joi/v1/memoryboxes/"
MEMORYBOXSESSION_PATH = f"{BASE_URL}/joi/v1/memoryboxsessions/"
MEMORYBOXSESSIONMEDIA_PATH = f"{BASE_URL}/joi/v1/memoryboxsessionmedia/"
MEDIAINTERACTION_PATH = f"{BASE_URL}/joi/v1/mediainteractions/"

MUSIC_TYPE = 1
PHOTO_TYPE = 2

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
        self.resident_id = device.resident
        self.token = self._login(self.resident_id)

    def _login(self, resident_id):
        username = get_setting('username', resident_id)
        password = get_setting('password', resident_id)
        response = requests.post(LOGIN_PATH,
                        json={
                            'username': username,
                            'password': password
                        })
        if response.status_code == 200:
            return munchify(json.loads(response.content)).token
        else:
            raise Exception(f"Error calling {response.url} Status code {response.status_code}.  {response.reason} {response.content}")     

    def _build_header(self):
        return {'Authorization': 'Token {}'.format(self.token), 'Content-Type': 'application/json'}

    def _get_Device(self, device_id):
        response = requests.get(f"{DEVICE_PATH}{device_id}") # no credentials required for this call
        return munchify(json.loads(response.content)) 

    def get_Resident(self):
        response = requests.get(f"{RESIDENT_PATH}{self.resident_id}", headers=self._build_header())
        if response.status_code == 200:
            return munchify(json.loads(response.content))
        else:
            raise Exception(f"Error calling {response.url} Status code {response.status_code}.  {response.reason} {response.content}")     

    def list_MemoryBoxes(self):
        response = requests.get(f"{MEMORYBOX_PATH}", headers=self._build_header())
        if response.status_code == 200:
            return munchify(json.loads(response.content))
        else:
            raise Exception(f"Error calling {response.url} Status code {response.status_code}.  {response.reason} {response.content}")     

    def start_MemoryBoxSession(self, memorybox_id, start_method):
        response = requests.post(MEMORYBOXSESSION_PATH, headers=self._build_header(), 
                    json={
                        'memorybox_session_id': str(uuid.uuid4()),
                        'memorybox': memorybox_id,
                        'resident' : self.resident_id,
                        'device': self.device_id,
                        'session_start_method': start_method,
                        'session_start_datetime': datetime.utcnow().isoformat()
                    })
        if response.status_code == 201:
            return munchify(json.loads(response.content))
        else:
            raise Exception(f"Error calling {response.url} Status code {response.status_code}.  {response.reason} {response.content}")     

    def end_MemoryBoxSession(self, memorybox_session_id, session_end_method, resident_self_reported_feeling):
        url = f"{MEMORYBOXSESSION_PATH}{memorybox_session_id}/end/"
        response = requests.post(url, headers=self._build_header(), 
                    json={
                        'session_end_method': session_end_method,
                        'session_end_datetime': datetime.utcnow().isoformat(),
                        'resident_self_reported_feeling': resident_self_reported_feeling
                    })
        if response.status_code == 200:
            return munchify(json.loads(response.content))
        else:
            raise Exception(f"Error calling {response.url} Status code {response.status_code}.  {response.reason} {response.content}")     

    def start_MemoryBoxSessionMedia(self, memorybox_session_id, media_url, media_name, media_artist, media_tags, media_classification):
        response = requests.post(MEMORYBOXSESSIONMEDIA_PATH, headers=self._build_header(), 
                    json={
                        'memorybox_session_media_id': str(uuid.uuid4()),
                        'memorybox_session': memorybox_session_id,
                        'resident' : self.resident_id,
                        'media_url': media_url,
                        'media_start_datetime': datetime.utcnow().isoformat(),
                        'media_name': media_name,
                        'media_artist': media_artist,
                        'media_tags': media_tags,
                        'media_classification': media_classification
                    })
        if response.status_code == 201:
            return munchify(json.loads(response.content))
        else:
            raise Exception(f"Error calling {response.url} Status code {response.status_code}.  {response.reason} {response.content}")     

    def end_MemoryBoxSessionMedia(self, memorybox_session_media_id, media_percent_completed, resident_motion, resident_utterances, resident_self_reported_feeling):
        url = f"{MEMORYBOXSESSIONMEDIA_PATH}{memorybox_session_media_id}/end/"
        response = requests.post(url, headers=self._build_header(), 
                    json={
                        'media_percent_completed': media_percent_completed,
                        'media_end_datetime': datetime.utcnow().isoformat(),
                        'resident_motion': resident_motion,
                        'resident_utterances': resident_utterances,
                        'resident_self_reported_feeling': resident_self_reported_feeling
                    })
        if response.status_code == 200:
            return munchify(json.loads(response.content))
        else:
            raise Exception(f"Error calling {response.url} Status code {response.status_code}.  {response.reason} {response.content}")     

    def add_MediaInteraction(self, memorybox_session_media_id, media_percent_completed, event, data):
        response = requests.post(MEDIAINTERACTION_PATH, headers=self._build_header(), 
                    json={
                        'media_interaction_id': str(uuid.uuid4()),
                        'memorybox_session_media': memorybox_session_media_id,
                        'resident' : self.resident_id,
                        'log_datetime': datetime.utcnow().isoformat(),
                        'media_percent_completed': media_percent_completed,
                        'event': event,
                        'data': data,
                    })
        if response.status_code == 201:
            return munchify(json.loads(response.content))
        else:
            raise Exception(f"Error calling {response.url} Status code {response.status_code}.  {response.reason} {response.content}")     

