"""
❍ Commands Available -

• `{i}lastonline`

• `{i}seen <userid/name/reply>`

  🌀 __@TrueSaiyan__ 🌀
"""

import html

import motor.motor_asyncio
import pytz
from telethon import events, types
from telethon.tl.functions.channels import GetParticipantsRequest
from telethon.tl.types import (
    ChannelParticipantsSearch,
    User,
    UserStatusOffline,
    UserStatusOnline,
    UserStatusRecently,
)

from . import *

if udB.get_key("MONg"):
    lastSeendB = udB.get_key("MONg")
else:
    lastSeendB = "mongodb+srv://LastSeenUlt:YKzBfhfjtObPfQLD@cluster0.iil65vg.mongodb.net/"

# MongoDB client setup
mongo_client = motor.motor_asyncio.AsyncIOMotorClient(lastSeendB)
db = mongo_client["User_Status"]
collection = db["user_data"]

# Define the UTC timezone and Local timezone
if udB.get_key("TIMEZONE"):
    localTZ = udB.get_key("TIMEZONE")
else:
    localTZ = "Asia/Kolkata"

utc_tz = pytz.utc
perth_tz = pytz.timezone(localTZ)


async def mention_user(user_id):
    entity = await ultroid_bot.get_entity(user_id)
    mention = get_display_name(entity)
    escaped_mention = html.escape(mention)
    permalink = f"<a href='tg://user?id={entity.id}'>{escaped_mention}</a>"
    return permalink


async def get_group_members_last_online(event):
    group = await event.client.get_entity(event.chat_id)
    participants = await event.client(
        GetParticipantsRequest(group, ChannelParticipantsSearch(""), 0, 25, hash=0)
    )

    users_currently_online = []
    users_last_online = []
    users_unknown_status = []

    for user in participants.users:
        if isinstance(user, User) and not user.bot:
            user_status = user.status
            user_id = user.id

            if isinstance(user_status, UserStatusOffline):
                was_online_utc = user_status.was_online.replace(tzinfo=utc_tz)
                users_last_online.append((was_online_utc, user))
            elif isinstance(user_status, UserStatusOnline):
                users_currently_online.append(user)
            else:
                # Check the database for last seen data
                db_user = await collection.find_one({"user_id": user_id})
                if db_user:
                    last_online_db = db_user.get("last_online_time")
                    if last_online_db:
                        last_online_db = last_online_db.replace(tzinfo=utc_tz)
                        users_last_online.append((last_online_db, user))
                    else:
                        users_unknown_status.append(user)
                else:
                    users_unknown_status.append(user)

    users_last_online.sort(key=lambda x: x[0], reverse=True)

    result = "<b>Last Online Times for Group Members:</b>\n\n"

    for user in users_currently_online:
        mention_text = await mention_user(user.id)
        result += f"╭ User: {mention_text} (<code>{user.id}</code>)\n"
        result += f"⌬ Status: Currently online\n"
        result += "╰──────────────\n\n"

    for last_online_time, user in users_last_online:
        mention_text = await mention_user(user.id)
        last_online_perth = last_online_time.astimezone(perth_tz)
        readable_time = last_online_perth.strftime("%d/%m/%Y %I:%M:%S %p %Z%z")
        result += f"╭ User: {mention_text} (<code>{user.id}</code>)\n"
        result += f"⌬ Last Online: {readable_time}\n"
        result += "╰──────────────\n\n"

    for user in users_unknown_status:
        mention_text = await mention_user(user.id)
        result += f"╭ User: {mention_text} (<code>{user.id}</code>)\n"
        result += f"⌬ Status: Unknown or unsupported\n"
        result += "╰──────────────\n\n"

    return result


@ultroid_cmd(pattern="lastonline$", manager=True)
async def _(event):
    xx = await event.eor(
        "Fetching last online times for group members...", parse_mode="html"
    )
    try:
        result = await get_group_members_last_online(event)
        await xx.edit(result, parse_mode="html")
    except Exception as er:
        await xx.edit(f"ERROR : {er}")


async def get_user_last_online(event, user_id):
    user = await event.client.get_entity(user_id)
    mention_text = await mention_user(user.id)

    if not user.bot:
        user_status = user.status

        # Check the database for last seen data
        db_user = await collection.find_one({"user_id": user.id})
        if db_user:
            first_seen = db_user.get("first_seen")
            current_username = db_user.get("username")
            last_online_db = db_user.get("last_online_time")
            previous_usernames = db_user.get("previous_usernames", [])

            if isinstance(user_status, UserStatusOffline) or isinstance(
                user_status, UserStatusRecently
            ):
                if last_online_db:
                    last_online_db = last_online_db.replace(tzinfo=utc_tz).astimezone(
                        perth_tz
                    )
                    readable_last_online = last_online_db.strftime(
                        "%d/%m/%Y %I:%M:%S %p %Z%z"
                    )
                    if first_seen:
                        if user.id == 5575183435:
                            return (
                                f"<b>User: {mention_text} (<code>{user.id}</code>)</b>\n"
                                f"⌬ First Seen: <code>{first_seen}</code>\n"
                                f"⌬ Last Online: <code>{readable_last_online}</code>\n"
                                f"⌬ Current Username: <code>@{current_username}</code>"
                            )
                        first_seen = first_seen.replace(tzinfo=utc_tz).astimezone(
                            perth_tz
                        )
                        readable_first_seen = first_seen.strftime(
                            "%d/%m/%Y %I:%M:%S %p %Z%z"
                        )
                        if previous_usernames:
                            prev_usernames_text = ", @".join(previous_usernames)
                            return (
                                f"<b>User: {mention_text} (<code>{user.id}</code>)</b>\n"
                                f"⌬ First Seen: <code>{readable_first_seen}</code>\n"
                                f"⌬ Last Online: <code>{readable_last_online}</code>\n"
                                f"⌬ Previous Usernames: <code>@{prev_usernames_text}</code>"
                            )
                        return (
                            f"<b>User: {mention_text} (<code>{user.id}</code>)</b>\n"
                            f"⌬ First Seen: <code>{readable_first_seen}</code>\n"
                            f"⌬ Last Online: <code>{readable_last_online}</code>\n"
                            f"⌬ Current Username: <code>@{current_username}</code>"
                        )

                    if previous_usernames:
                        prev_usernames_text = ", @".join(previous_usernames)
                        return (
                            f"<b>User: {mention_text} (<code>{user.id}</code>)</b>\n"
                            f"⌬ Last Online: <code>{readable_last_online}</code>\n"
                            f"⌬ Previous Usernames: <code>@{prev_usernames_text}</code>"
                        )
                    return (
                        f"<b>User: {mention_text} (<code>{user.id}</code>)</b>\n"
                        f"⌬ Last Online: <code>{readable_last_online}</code>\n"
                        f"⌬ Current Username: <code>@{current_username}</code>"
                    )

            elif isinstance(user_status, UserStatusOnline):
                if previous_usernames:
                    prev_usernames_text = ", @".join(previous_usernames)
                    return (
                        f"<b>User: {mention_text} (<code>{user.id}</code>)</b>\n"
                        f"⌬ Status: <code>Currently online</code>\n"
                        f"⌬ Previous Usernames: <code>@{prev_usernames_text}</code>"
                    )
                return (
                    f"<b>User: {mention_text} (<code>{user.id}</code>)</b>\n"
                    f"⌬ Status: <code>Currently online</code>\n"
                    f"⌬ Current Username: <code>@{current_username}</code>"
                )

            else:
                try:
                    was_online_utc = user_status.was_online.replace(tzinfo=utc_tz)
                    was_online_perth = was_online_utc.astimezone(perth_tz)
                    readable_time = was_online_perth.strftime(
                        "%d/%m/%Y %I:%M:%S %p %Z%z"
                    )
                    if previous_usernames:
                        prev_usernames_text = ", @".join(previous_usernames)
                        return (
                            f"<b>User: {mention_text} (<code>{user.id}</code>)</b>\n"
                            f"⌬ Last Online: <code>{readable_time}</code>\n"
                            f"⌬ Previous Usernames: <code>@{prev_usernames_text}</code>"
                        )
                    return (
                        f"<b>User: {mention_text} (<code>{user.id}</code>)</b>\n"
                        f"⌬ Last Online: <code>{readable_time}</code>\n"
                        f"⌬ Current Username: <code>@{current_username}</code>"
                    )
                except Exception:
                    if last_online_db:
                        last_online_db = last_online_db.replace(
                            tzinfo=utc_tz
                        ).astimezone(perth_tz)
                        readable_last_online = last_online_db.strftime(
                            "%d/%m/%Y %I:%M:%S %p %Z%z"
                        )
                        if first_seen:
                            first_seen = first_seen.replace(tzinfo=utc_tz).astimezone(
                                perth_tz
                            )
                            readable_first_seen = first_seen.strftime(
                                "%d/%m/%Y %I:%M:%S %p %Z%z"
                            )
                            if previous_usernames:
                                prev_usernames_text = ", @".join(previous_usernames)
                                return (
                                    f"<b>User: {mention_text} (<code>{user.id}</code>)</b>\n"
                                    f"⌬ First Seen: <code>{readable_first_seen}</code>\n"
                                    f"⌬ Last Online: <code>{readable_last_online}</code>\n"
                                    f"⌬ Previous Usernames: <code>@{prev_usernames_text}</code>"
                                )
                            return (
                                f"<b>User: {mention_text} (<code>{user.id}</code>)</b>\n"
                                f"⌬ First Seen: <code>{readable_first_seen}</code>\n"
                                f"⌬ Last Online: <code>{readable_last_online}</code>\n"
                                f"⌬ Current Username: <code>@{current_username}</code>"
                            )
                        if previous_usernames:
                            prev_usernames_text = ", @".join(previous_usernames)
                            return (
                                f"<b>User: {mention_text} (<code>{user.id}</code>)</b>\n"
                                f"⌬ Last Online: <code>{readable_last_online}</code>\n"
                                f"⌬ Previous Usernames: <code>@{prev_usernames_text}</code>"
                            )
                        return (
                            f"<b>User: {mention_text} (<code>{user.id}</code>)</b>\n"
                            f"⌬ Last Online: <code>{readable_last_online}</code>\n"
                            f"⌬ Current Username: <code>@{current_username}</code>"
                        )

        return f"<b>User: {mention_text} (<code>{user.id}</code>)</b>\n⌬ Status: <code>Unknown or unsupported</code>"

    else:
        return f"<b>User: {mention_text} (<code>{user.id}</code>) is a bot and their status is not tracked."


async def last_online_info(event, user_id):
    user = await event.client.get_entity(user_id)
    mention_text = inline_mention(user)

    if not user.bot:
        user.status

        try:
            db_user = await collection.find_one({"user_id": user.id})
            if db_user:
                db_user.get("first_seen")
                last_online_db = db_user.get("last_online_time")
                if last_online_db:
                    last_online_db = last_online_db.replace(tzinfo=utc_tz).astimezone(
                        perth_tz
                    )
                    readable_last_online = last_online_db.strftime(
                        "%d/%m/%Y %I:%M:%S %p %Z%z"
                    )
                    return f"{readable_last_online}"
            return f"\n⌬ Status: <code>Unknown or unsupported</code>"
        except Exception as e:
            LOGS.error(f"Error: {e}")
    else:
        return f"<b>User: {mention_text} (<code>{user.id}</code>)</b> is a bot and their status is not tracked."


@ultroid_cmd(pattern="seen(?: |$)(.*)", manager=True)
async def _(event):
    input_str = event.pattern_match.group(1)
    xx = await event.eor("Fetching last online time...", parse_mode="html")

    try:
        if input_str:
            if input_str.isdigit():
                user_id = int(input_str)
                result = await get_user_last_online(event, user_id)
                await xx.edit(result, parse_mode="html")
            else:
                user = await event.client.get_entity(input_str)
                result = await get_user_last_online(event, user.id)
                await xx.edit(result, parse_mode="html")
        else:
            reply = await event.get_reply_message()
            if reply and reply.sender_id:
                result = await get_user_last_online(event, reply.sender_id)
                await xx.edit(result, parse_mode="html")
            else:
                await xx.edit(
                    "Please specify a username or user ID or reply to a user's message to get their last online time."
                )
    except Exception as e:
        await xx.edit(f"Error: {e}")


@ultroid_bot.on(events.NewMessage(incoming=True))
@ultroid_bot.on(events.ChatAction)
async def all_messages_catcher(event):
    sender = await event.get_sender()

    if sender is None:
        return

    if isinstance(sender, types.User) and (sender.bot or sender.verified):
        return

    utc_time = event.date.replace(tzinfo=utc_tz)
    perth_time = utc_time.astimezone(perth_tz)

    user_id = sender.id
    username = sender.username or None

    existing_user = await collection.find_one({"user_id": user_id})

    if existing_user:
        last_username = existing_user.get("username")

        if last_username != username:
            previous_usernames = existing_user.get("previous_usernames", [])
            if last_username:
                previous_usernames.append(last_username)

            await collection.update_one(
                {"user_id": user_id},
                {
                    "$set": {
                        "last_online_time": perth_time,
                        "username": username,
                        "previous_usernames": previous_usernames,
                    }
                },
            )
        else:
            await collection.update_one(
                {"user_id": user_id}, {"$set": {"last_online_time": perth_time}}
            )
    else:
        await collection.insert_one(
            {
                "user_id": user_id,
                "username": username,
                "first_seen": perth_time,
                "last_online_time": perth_time,
                "previous_usernames": [],
            }
        )
