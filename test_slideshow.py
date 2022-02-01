from pprint import pprint
from slideshow import Slideshow


## HTTP Logging #####################
import logging
import http.client as http_client
http_client.HTTPConnection.debuglevel = 1
logging.basicConfig()
logging.getLogger().setLevel(logging.DEBUG)
requests_log = logging.getLogger("requests.packages.urllib3")
requests_log.setLevel(logging.DEBUG)
requests_log.propagate = True
#####################


client = Slideshow()

play_state = client.get_playback_state()
pprint(play_state)

client.show_photo('y','y')
play_state = client.get_playback_state()
pprint(play_state)


client.tick_photo()
play_state = client.get_playback_state()
pprint(play_state)
