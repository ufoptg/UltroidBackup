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
from pytgcalls.types import MediaStream
from pytgcalls.exceptions import NoActiveGroupCall, AlreadyJoinedError
from pytgcalls.types import Update
from pytgcalls import StreamType


from . import get_string, ultroid_cmd, LOGS, vc_connection, call_client


async def get_group_call(event):
    chat = await event.get_chat()
    call = await call_client.get_active_call(chat.id)
    return chat, call

@ultroid_cmd(
    pattern="stopvc$",
    admins_only=True,
    groups_only=True,
)
async def _(event):
    try:
        chat, call = await get_group_call(event)
        if call:
            await call_client.leave_group_call(chat.id)
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
    chat, call = await get_group_call(event)
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
            await call_client.invite_to_call(chat.id, [user_id])
            z += 1
        except Exception as e:
            LOGS.error(f"Error inviting user {user_id}: {e}")
    
    await ok.edit(get_string("vct_5").format(z))
@ultroid_cmd(
    pattern="startvc$",
    admins_only=True,
    groups_only=True,
)
async def _(event):
    try:
        chat = await event.get_chat()
        audio_url = "https://t.me/vc-audio-test/2"  # Replace with the actual audio URL if needed
        media_stream = MediaStream(
            audio_url,
            video_flags=MediaStream.Flags.IGNORE  # Assuming you only want audio
        )
        call = await call_client.join_group_call(
            chat.id,
            media_stream,
            stream_type=StreamType().pulse_stream,  # Assuming you want pulse stream type
        )
        
        await event.eor(get_string("vct_1"))
    
    except NoActiveGroupCall:
        await event.eor("No active group call found. You may need to start one in the Telegram client.")
    except AlreadyJoinedError:
        await event.eor("Already joined the group call.")
    except Exception as ex:
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
        chat, call = await get_group_call(event)
        if call:
            await call_client.change_title(chat.id, title)
            await event.eor(get_string("vct_2").format(title))
        else:
            await event.eor("No active group call found.")
    except Exception as ex:
        await event.eor(f"`{ex}`")
