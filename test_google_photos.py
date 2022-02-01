import os 
import pickle
import json
from pprint import pprint
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
import requests
from munch import munchify

ALBUMS_URL = 'https://photoslibrary.googleapis.com/v1/albums'
MEDIAITEMS_URL = 'https://photoslibrary.googleapis.com/v1/mediaItems'

def login():
    # Setup the Photo v1 API
    SCOPES = ['https://www.googleapis.com/auth/photoslibrary.readonly', 'https://www.googleapis.com/auth/photoslibrary.appendonly']
    creds = None
    if(os.path.exists("token.pickle")):
        with open("token.pickle", "rb") as tokenFile:
            creds = pickle.load(tokenFile)
    if not creds or not creds.valid:
        if (creds and creds.expired and creds.refresh_token):
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('client_secret.json', SCOPES)
            creds = flow.run_local_server(port = 0)
        with open("token.pickle", "wb") as tokenFile:
            pickle.dump(creds, tokenFile)
    return creds            

def build_header(creds):
    return {'Authorization': 'Bearer {}'.format(creds.token), 'Content-Type': 'application/json'}

def create_album(creds, title):
    header = build_header(creds)
    response = requests.post(ALBUMS_URL, headers=header, data=str({"album": {'title': 'Joi'}}))

def get_albums(creds):
    header = build_header(creds)
    response = requests.get(ALBUMS_URL,headers=header,params={'pageSize':50})
    albums = munchify(json.loads(response.content)).albums
    return albums

def get_media_items(creds, album_id):
    header = build_header(creds)
    response = requests.post(MEDIAITEMS_URL+":search", headers=header, data=str({'albumId':album_id}))
    mediaItems = munchify(json.loads(response.content)).mediaItems
    return mediaItems

# test

creds = login()

albums = get_albums(creds)
album = list(filter(lambda o: o.title == "Joi", albums))[0]
pprint(album)
print(album.id)

mediaItems = get_media_items(creds, album_id=album.id)
print('===Getting Media Items=============')
print(len(mediaItems))
pprint(mediaItems[0])
