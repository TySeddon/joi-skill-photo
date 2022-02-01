from pprint import pprint
from google_photo import GooglePhoto

# test
client = GooglePhoto()

albums = client.get_albums()
album = list(filter(lambda o: o.title == "Joi", albums))[0]
pprint(album)
print(album.id)

mediaItems = client.get_media_items(album_id=album.id)
print('===Getting Media Items=============')
print(len(mediaItems))
pprint(mediaItems[0])
