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
from py_tgcalls import PyTgCalls
from py_tgcalls.exceptions import NoActiveGroupCall, AlreadyJoinedError
from py_tgcalls.types.input_stream import AudioPiped
from py_tgcalls.types import Update
from pytgcalls import StreamType
from pytgcalls.types import (
    JoinedGroupCallPayload,
    LeftGroupCallPayload,
    MediaStreamErrorPayload,
)

from . import get_string, ultroid_cmd, LOGS, vc_connection, Var, udB

VC_SESSION = Var.VC_SESSION or udB.get_key("VC_SESSION")

# Initialize call_client (assuming you have this in your main bot logic)
_, call_client = vc_connection(VC_SESSION, ultroid_bot) # Pass your UDB_STRING variable

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
        call = await call_client.join_group_call(
            chat.id,
            AudioPiped("https://t.me/vc-audio-test/2"), # Use a dummy audio file, we only want to start the call
            stream_type=StreamType().pulse_stream,
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
