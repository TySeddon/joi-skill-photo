import os 
import pickle
import json
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
import requests
from munch import munchify

ALBUMS_URL = 'https://photoslibrary.googleapis.com/v1/albums'
MEDIAITEMS_URL = 'https://photoslibrary.googleapis.com/v1/mediaItems'
SCOPES = ['https://www.googleapis.com/auth/photoslibrary.readonly', 'https://www.googleapis.com/auth/photoslibrary.appendonly']

class GooglePhoto():

    def __init__(self):
        self.creds = self._login()

    def _login(self):
        creds = None
        if(os.path.exists("token.pickle")):
            with open("token.pickle", "rb") as tokenFile:
                creds = pickle.load(tokenFile)
        if not creds or not creds.valid:
            if (creds and creds.expired and creds.refresh_token):
                try:
                    creds.refresh(Request())
                except Exception as error:
                    creds = None                    
            if not creds:
                flow = InstalledAppFlow.from_client_secrets_file('client_secret.json', SCOPES)
                creds = flow.run_local_server(port = 0)
            with open("token.pickle", "wb") as tokenFile:
                pickle.dump(creds, tokenFile)
        return creds            

    def _build_header(self):
        return {'Authorization': 'Bearer {}'.format(self.creds.token), 'Content-Type': 'application/json'}

    def create_album(self, title):
        header = self._build_header()
        response = requests.post(ALBUMS_URL, headers=header, data=str({"album": {'title': 'Joi'}}))

    def get_albums(self):
        header = self._build_header()
        response = requests.get(ALBUMS_URL,headers=header,params={'pageSize':50})
        albums = munchify(json.loads(response.content)).albums
        return albums

    def get_media_items(self, album_id):
        header = self._build_header()
        response = requests.post(MEDIAITEMS_URL+":search", headers=header, data=str({'albumId':album_id,'pageSize':100}))
        mediaItems = munchify(json.loads(response.content)).mediaItems

        # clean up media items
        for o in mediaItems:
            if not hasattr(o, 'description'):
                o.description = None

        return mediaItems    