from pprint import pprint
from time import sleep
import webbrowser
from google_photo import GooglePhoto
from slideshow import Slideshow, JOI_SERVER_URL

# get photos from Google
client = GooglePhoto()
albums = client.get_albums()
album = list(filter(lambda o: o.title == "Joi", albums))[0]
mediaItems = client.get_media_items(album_id=album.id)


# start slideshow on server (just writes record to database)
client = Slideshow()

# launch browser
url = "%s/joi/slideshow?id=%s" % (JOI_SERVER_URL, client.slideshow_id)
webbrowser.open(url=url)

#play_state = client.get_playback_state()
for photo in mediaItems:
    client.show_photo(photo.id, photo.baseUrl)
    for i in range(3):
        play_state = client.get_playback_state()
        print('Tick %i - Showing %s' % (play_state.tick_count, play_state.media_id))
        sleep(1)

client.end_slideshow()    
