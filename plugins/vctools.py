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

import asyncio
import os
from pathlib import Path
from typing import Tuple

import httpx
from pytgcalls import PyTgCalls
from pytgcalls.exceptions import AlreadyJoinedError, NoActiveGroupCall
from pytgcalls.types import AudioQuality, GroupCall, MediaStream
from telethon.tl.types import User

# Assuming these are defined elsewhere in your project
from . import get_string, ultroid_cmd, LOGS, call_client # Remove unused imports

@ultroid_cmd(
    pattern="startvc(?: |$)(.*)",
    admins_only=True,
    groups_only=True,
)
async def start_voice_chat(event):
    """Starts a voice chat in the group."""
    try:
        chat = await event.get_chat()
        
        audio_url = "https://t.me/vc-audio-test/2"  # Replace with the actual audio URL if needed
        file_path = Path("audio.mp3")
        
        
        async with httpx.AsyncClient() as client:
          try:
            response = await client.get(audio_url)
            response.raise_for_status() # Raise exception for bad status codes
          except httpx.HTTPError as e:
             await event.eor(f"Error downloading audio: {e}")
             return

        with open(file_path, "wb") as file:
            file.write(response.content)
            
        media_stream = MediaStream(
            str(file_path),
            audio_flags=MediaStream.Flags.NO_LATENCY
        )
        
        call = await call_client.create_group_call(chat.id)
        await call.start(media_stream)
        
        await event.eor(get_string("vct_1"))

         # Clean up file to keep storage clean
        await asyncio.sleep(20) # Clean up after 20 seconds to make sure file is loaded.
        os.remove(file_path)


    except NoActiveGroupCall:
        await event.eor(
            "No active group call found. You may need to start one in the Telegram client."
        )
    except AlreadyJoinedError:
          if call := await get_group_call(event):
                if call[0].initiator_id == event.sender_id:
                    await event.eor("You already started the group call.")
                else:
                    await event.eor("A different user already started the group call.")
          else:
             await event.eor("Already joined the group call.") # This code should not be reached
    except Exception as ex:
        LOGS.error(f"Error starting call: {ex}")
        await event.eor(f"`{ex}`")

async def get_group_call(event) -> Tuple[GroupCall, int] | Tuple[None, int]:
    """Retrieves the active group call object and chat ID.

    Returns:
      A tuple containing the GroupCall object and chat ID, or (None, chat ID) if no call is active.
    """
    chat = await event.get_chat()
    try:
        call = await call_client.get_active_call(chat.id)
    except NoActiveGroupCall:
        return None, chat.id
    return call, chat.id



@ultroid_cmd(
    pattern="stopvc$",
    admins_only=True,
    groups_only=True,
)
async def stop_voice_chat(event):
    """Stops the active group voice chat."""
    try:
        call, chat_id = await get_group_call(event)
        if call:
            await call.stop()
            await event.eor(get_string("vct_4"))
        else:
            await event.eor("No active group call to stop.")
    except Exception as ex:
        await event.eor(f"`{ex}`")



@ultroid_cmd(
    pattern="vcinvite$",
    groups_only=True,
)
async def invite_to_voice_chat(event):
    """Invites all non-bot users in a group to the voice chat."""
    ok = await event.eor(get_string("vct_3"))
    call, chat_id = await get_group_call(event)
    if not call:
        await ok.edit("No active group call found.")
        return
    users_invited_count = 0
    async for user in event.client.iter_participants(event.chat_id):
        if isinstance(user, User) and not user.bot:
          try:
            await call.invite(users=[user.id])
            users_invited_count += 1
          except Exception as e:
             LOGS.error(f"Error inviting user {user.id}: {e}")

    await ok.edit(get_string("vct_5").format(users_invited_count))




@ultroid_cmd(
    pattern="vctitle(?: |$)(.*)",
    admins_only=True,
    groups_only=True,
)
async def set_voice_chat_title(event):
    """Sets the title of the active group voice chat."""
    title = event.pattern_match.group(1).strip()
    if not title:
        return await event.eor(get_string("vct_6"), time=5)
    try:
        call, chat_id = await get_group_call(event)
        if call:
            await call.set_title(title)
            await event.eor(get_string("vct_2").format(title))
        else:
            await event.eor("No active group call found.")
    except Exception as ex:
        await event.eor(f"`{ex}`")
