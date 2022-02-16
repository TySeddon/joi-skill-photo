import random
from joiclient import JoiClient
import enviro

device_id = enviro.get_value("device_id")
client = JoiClient(device_id)
resident = client.get_Resident()
print(resident)

memoryboxes = client.list_MemoryBoxes()
print(len(memoryboxes))
memorybox = random.choice(memoryboxes)

mb_session = client.start_MemoryBoxSession(
                        memorybox_id=memorybox.memorybox_id, 
                        start_method="test")

session_media = client.start_MemoryBoxSessionMedia(
                        memorybox_session_id=mb_session.memorybox_session_id, 
                        media_url="some url",
                        media_name="some name",
                        media_artist="some artist",
                        media_tags="some tags",
                        media_classification="some classification")

media_interaction = client.add_MediaInteraction(
                        memorybox_session_media_id=session_media.memorybox_session_media_id, 
                        media_percent_completed=0,
                        event="prompt",
                        data="What a lovely garden")

media_interaction = client.add_MediaInteraction(
                        memorybox_session_media_id=session_media.memorybox_session_media_id, 
                        media_percent_completed=0,
                        event="utterance",
                        data="I miss working in my garden")

client.end_MemoryBoxSessionMedia(
                        memorybox_session_media_id=session_media.memorybox_session_media_id, 
                        media_percent_completed = 100,
                        resident_motion="23%", 
                        resident_utterances="fun", 
                        resident_self_reported_feeling="happy")

client.end_MemoryBoxSession(
                        memorybox_session_id=mb_session.memorybox_session_id, 
                        session_end_method="natural", 
                        resident_self_reported_feeling="happy")
