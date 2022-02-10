from datetime import datetime, timedelta
from time import sleep
from xmlrpc.client import DateTime
from amcrest import AmcrestCamera
from amcrest.exceptions import CommError
from munch import munchify
import sys
import asyncio
from asyncio import Event, AbstractEventLoop
from typing import Optional, AsyncIterator
import signal
from contextlib import suppress

PASSWORD = 'Smarthome#1'


def build_motion_event(event_name):
    return munchify({
        'Event':event_name,
        'DateTime':datetime.utcnow()
    })

def build_event_obj(event_str):
    if "Code=VideoMotion" in event_str:
        if "action=Start" in event_str:
            return build_motion_event('MotionStart')
        elif "action=Stop" in event_str:
            return build_motion_event('MotionStop')
        else:
            return None
    else:
        return None




# async def get_event_stream():
#     async for event_str in camera.async_event_stream("VideoMotion", timeout_cmd=float(seconds_length)):
#         current_event = build_event_obj(event_str)
#         await handle_tick(current_event.Event)

async def async_time_ticker(delay: float) -> AsyncIterator[datetime]:
    while True:
        await asyncio.sleep(delay)
        yield datetime.now()  

async def cancellable_aiter(async_iterator: AsyncIterator, cancellation_event: Event) -> AsyncIterator:
    cancellation_task = asyncio.create_task(cancellation_event.wait())
    result_iter = async_iterator.__aiter__()
    while not cancellation_event.is_set():
        next_result_task = asyncio.create_task(result_iter.__anext__())
        done, pending = await asyncio.wait(
            [cancellation_task, next_result_task],
            return_when=asyncio.FIRST_COMPLETED
        )
        for done_task in done:
            if done_task == cancellation_task:
                for pending_task in pending:
                    await pending_task

                    # clean up the async iterator
                    next_result_task.cancel()
                    await result_iter.aclose()
                    
                    break
            else:
                yield done_task.result()
           
def cancel(cancellation_event):
    print("Canceling")
    cancellation_event.set()

async def main_async(camera, timeout_secs):
    loop = asyncio.get_event_loop()
    cancellation_event = asyncio.Event()
    loop.call_later(timeout_secs, cancel, cancellation_event)
    #async_iter = async_time_ticker(1)
    async_iter = camera.async_event_stream("VideoMotion")
    async for event_str in cancellable_aiter(async_iter, cancellation_event):
        current_event = build_event_obj(event_str)
        print(current_event)
    print("Done")

seconds_length = 10
camera = AmcrestCamera('192.168.1.27', 80, 'admin', PASSWORD).camera

#Check software information
print(camera.software_information)

asyncio.run(main_async(camera, seconds_length))



