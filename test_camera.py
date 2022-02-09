from datetime import datetime
from time import sleep
from amcrest import AmcrestCamera
from amcrest.exceptions import CommError

PASSWORD = 'Smarthome#1'

camera = AmcrestCamera('192.168.1.27', 80, 'admin', PASSWORD).camera

#Check software information
print(camera.software_information)

print(camera.is_motion_detector_on())

print(camera.is_record_on_motion_detection())

#print(camera.storage_device_info())
print(camera.event_channels_happened("VideoMotion"))

#camera.snapshot(channel=0, path_file="snapshot00.jpeg")
camera.ptz_control_command(action="start", code="PositionABS", arg1=180, arg2=0, arg3=0)
camera.ptz_control_command(action="start", code="PositionABS", arg1=180, arg2=30, arg3=0)
#camera.ptz_control_command(action="start", code="AutoScanOn", arg1=0, arg2=0, arg3=0)
#quit()


""" motion_observations = []
for i in range(30):
    is_hit = bool(camera.is_motion_detected)
    dt = datetime.utcnow()
    print(f"{is_hit}, {dt}")
    motion_observations.append((is_hit, dt))
    sleep(1)

motion_hits = list(filter(lambda o: o[0] == True, motion_observations))
motion_percent = len(motion_hits)/len(motion_observations)
print(motion_percent) """

# for i in range(10):
#     print(camera.event_stream("VideoMotion"))
#     sleep(1)

# for i in range(20):
#     e = next(camera.event_stream("VideoMotion"))
#     print(e)

max_count = 2
count = 0
motion_events = []
try:
    for e in camera.event_stream("VideoMotion", timeout_cmd=60.0):
        print(e)
        motion_events.append(e)
        count += 1
        if count > max_count:
            break
except CommError as error:
    pass     

print("==============")
print(motion_events)