"""
✘ Commands Available -

• `{i}startvc`
    Start Group Call in a group.

• `{i}stopvc`
    Stop Group Call in a group.

• `{i}vctitle <title>`
    Change the title Group call.

• `{i}vcinvite`
    Invite all members of group in Group Call.
    (You must be joined)
"""

from telethon.tl.functions.channels import GetFullChannelRequest as getchat
from telethon.tl.functions.phone import GetGroupCallRequest as getvc
from pytgcalls import PyTgCalls
from pytgcalls.types import AudioQuality, MediaStream
from pytgcalls.exceptions import NoActiveGroupCall, AlreadyJoinedError
from pytgcalls.types import Update, GroupCall
import httpx
import asyncio
import os
from pathlib import Path


from . import get_string, ultroid_cmd, LOGS, vc_connection, call_client



async def get_group_call(event) -> tuple[GroupCall, int]:
    """This function now returns a tuple of (GroupCall object, chat id)"""
    chat = await event.get_chat()
    try:
        call = await call_client.get_active_call(chat.id)
    except NoActiveGroupCall:
        return None, chat.id # Return None if no active call exists
    return call, chat.id # Return the call object, and chat id



@ultroid_cmd(
    pattern="stopvc$",
    admins_only=True,
    groups_only=True,
)
async def _(event):
    try:
        call, chat_id = await get_group_call(event)
        if call:
            await call.stop()  # Stop the call using the call object
            await event.eor(get_string("vct_4"))
        else:
            await event.eor("No active group call to stop.")
    except Exception as ex:
        await event.eor(f"`{ex}`")


@ultroid_cmd(
    pattern="vcinvite$",
    groups_only=True,
)
async def _(event):
    ok = await event.eor(get_string("vct_3"))
    call, chat_id = await get_group_call(event)
    if not call:
        await ok.edit("No active group call found.")
        return
    users = []
    z = 0
    async for x in event.client.iter_participants(event.chat_id):
        if not x.bot:
            users.append(x.id)

    for user_id in users:
        try:
            await call.invite(users=[user_id]) # Invite using the call object
            z += 1
        except Exception as e:
            LOGS.error(f"Error inviting user {user_id}: {e}")
    
    await ok.edit(get_string("vct_5").format(z))

@ultroid_cmd(
    pattern="startvc(?: |$)(.*)",
    admins_only=True,
    groups_only=True,
)
async def _(event):
    try:
      chat = await event.get_chat()

      audio_url = "https://t.me/vc-audio-test/2"  # Replace with the actual audio URL if needed

      # Download audio file locally
      async with httpx.AsyncClient() as client:
          response = await client.get(audio_url)
          response.raise_for_status() # Raise exception for bad status codes

      file_path = Path("audio.mp3")
      with open(file_path, "wb") as file:
          file.write(response.content)

      
      media_stream = MediaStream( # Create the media stream
          str(file_path),
        audio_flags=MediaStream.Flags.NO_LATENCY
          )

      
      call = await call_client.create_group_call(chat.id)  # Create the call
      await call.start(media_stream)    # Start the call with the media

      await event.eor(get_string("vct_1"))

      # Clean up file to keep storage clean
      await asyncio.sleep(20) # Clean up after 20 seconds to make sure file is loaded.
      os.remove(file_path)
    
    except NoActiveGroupCall:
        await event.eor("No active group call found. You may need to start one in the Telegram client.")
    except AlreadyJoinedError:
        await event.eor("Already joined the group call.")
    except Exception as ex:
        LOGS.error(f"Error Starting call: {ex}")
        await event.eor(f"`{ex}`")


@ultroid_cmd(
    pattern="vctitle(?: |$)(.*)",
    admins_only=True,
    groups_only=True,
)
async def _(event):
    title = event.pattern_match.group(1).strip()
    if not title:
        return await event.eor(get_string("vct_6"), time=5)
    try:
        call, chat_id = await get_group_call(event)
        if call:
            await call.set_title(title) # set title using call object
            await event.eor(get_string("vct_2").format(title))
        else:
            await event.eor("No active group call found.")
    except Exception as ex:
        await event.eor(f"`{ex}`")
