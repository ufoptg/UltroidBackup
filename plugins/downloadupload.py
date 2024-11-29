# Ultroid - UserBot
# Copyright (C) 2021-2023 TeamUltroid
#
# This file is a part of < https://github.com/TeamUltroid/Ultroid/ >
# PLease read the GNU Affero General Public License in
# <https://www.github.com/TeamUltroid/Ultroid/blob/main/LICENSE/>.

from . import get_help

__doc__ = get_help("help_downloadupload")

import asyncio
import glob
import os
import time
from datetime import datetime as dt

from aiohttp.client_exceptions import InvalidURL
from telethon.errors.rpcerrorlist import MessageNotModifiedError

from pyUltroid.fns.helper import time_formatter
from pyUltroid.fns.tools import get_chat_and_msgid, set_attributes
from telethon.tl.types import DocumentAttributeFilename, DocumentAttributeVideo
from pyUltroid.fns.tools import metadata

from . import (
    LOGS,
    ULTConfig,
    downloader,
    eor,
    fast_download,
    get_all_files,
    get_string,
    progress,
    ultroid_cmd,
)

async def extract_thumbnail(file_path, thumbnail_path):
    try:
        process = await asyncio.create_subprocess_exec(
            "ffmpeg",
            "-i",
            file_path,
            "-ss",
            "00:00:04",
            "-vframes",
            "1",
            thumbnail_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await process.communicate()
        if process.returncode != 0:
            raise Exception(stderr.decode())
    except Exception as e:
        print("Error extracting thumbnail:", e)
        # Consider logging the error or handling it appropriately

async def process_video(file_path, directory_path, caption_str, event):
    if file_path.lower().endswith((".mp4", ".avi", ".mov", ".mkv")):
        meta = await metadata(file_path)
        video_duration_in_seconds = meta.get("duration")
        if video_duration_in_seconds is not None:
            thumbnail_path = os.path.join(directory_path, "thumb.jpg")
            await extract_thumbnail(file_path, thumbnail_path)

            thumbnail_size = (
                int(meta.get("width", 0)),
                int(meta.get("height", 0))
            )
            attributes = [
                DocumentAttributeFilename(os.path.basename(file_path)),
                DocumentAttributeVideo(
                    duration=int(video_duration_in_seconds),
                    w=thumbnail_size[0],
                    h=thumbnail_size[1],
                    supports_streaming=True,
                ),
            ]

            file, _ = await event.client.fast_uploader(
                file_path, show_progress=True, event=event, to_delete=True
            )
            thumbnail, _ = await event.client.fast_uploader(
                thumbnail_path, show_progress=True, event=event, to_delete=True
            )
            await event.client.send_file(
                event.chat_id,
                file,
                caption=caption_str,
                attributes=attributes,
                thumb=thumbnail,
            )

@ultroid_cmd(
    pattern="download( (.*)|$)",
)
async def down(event):
    matched = event.pattern_match.group(1).strip()
    msg = await event.eor(get_string("udl_4"))
    if not matched:
        return await eor(msg, get_string("udl_5"), time=5)
    try:
        splited = matched.split(" | ")
        link = splited[0]
        filename = splited[1]
    except IndexError:
        filename = None
    s_time = time.time()
    try:
        filename, d = await fast_download(
            link,
            filename,
            progress_callback=lambda d, t: asyncio.get_event_loop().create_task(
                progress(
                    d,
                    t,
                    msg,
                    s_time,
                    f"Downloading from {link}",
                )
            ),
        )
    except InvalidURL:
        return await msg.eor("`Invalid URL provided :(`", time=5)
    await msg.eor(f"`{filename}` `downloaded in {time_formatter(d*1000)}.`")


@ultroid_cmd(
    pattern="dl( (.*)|$)",
)
async def download(event):
    match = event.pattern_match.group(1).strip()
    if match and "t.me/" in match:
        chat, msg = get_chat_and_msgid(match)
        if not (chat and msg):
            return await event.eor(get_string("gms_1"))
        match = ""
        ok = await event.client.get_messages(chat, ids=msg)
    elif event.reply_to_msg_id:
        ok = await event.get_reply_message()
    else:
        return await event.eor(get_string("cvt_3"), time=8)
    xx = await event.eor(get_string("com_1"))
    if not (ok and ok.media):
        return await xx.eor(get_string("udl_1"), time=5)
    s = dt.now()
    k = time.time()
    if hasattr(ok.media, "document"):
        file = ok.media.document
        mime_type = file.mime_type
        filename = match or ok.file.name
        if not filename:
            if "audio" in mime_type:
                filename = "audio_" + dt.now().isoformat("_", "seconds") + ".ogg"
            elif "video" in mime_type:
                filename = "video_" + dt.now().isoformat("_", "seconds") + ".mp4"
        try:
            result = await downloader(
                f"resources/downloads/{filename}",
                file,
                xx,
                k,
                f"Downloading {filename}...",
            )

        except MessageNotModifiedError as err:
            return await xx.edit(str(err))
        file_name = result.name
    else:
        d = "resources/downloads/"
        file_name = await event.client.download_media(
            ok,
            d,
            progress_callback=lambda d, t: asyncio.get_event_loop().create_task(
                progress(
                    d,
                    t,
                    xx,
                    k,
                    get_string("com_5"),
                ),
            ),
        )
    e = dt.now()
    t = time_formatter(((e - s).seconds) * 1000)
    await xx.eor(get_string("udl_2").format(file_name, t))


@ultroid_cmd(
    pattern="ul( (.*)|$)",
)
async def _(event):
    msg = await event.eor(get_string("com_1"))
    match = event.pattern_match.group(1)
    if match:
        match = match.strip()
    if not event.out and match == ".env":
        return await event.reply("`You can't do this...`")

    stream, force_doc, delete, thumb, is_video, custom_caption = (
        False,
        True,
        False,
        ULTConfig.thumb,
        False,
        None,
    )

    # Check for flags
    if "--stream" in match:
        stream = True
        force_doc = False
    if "--delete" in match:
        delete = True
    if "--no-thumb" in match:
        thumb = None
    if "--video" in match:
        is_video = True

    # Remove flags from match
    arguments = ["--stream", "--delete", "--no-thumb", "--video"]
    for item in arguments:
        match = match.replace(item, "").strip()

    # Split the match to extract custom caption if provided
    if "|" in match:
        match, custom_caption = map(str.strip, match.split("|", 1))

    if match.endswith("/"):
        match += "*"
    results = glob.glob(match)
    if not results and os.path.exists(match):
        results = [match]
    if not results:
        try:
            await event.reply(file=match)
            return await event.try_delete()
        except Exception as er:
            LOGS.exception(er)
        return await msg.eor(get_string("ls1"))

    for result in results:
        if os.path.isdir(result):
            return await msg.eor("`Uploading directories is not supported for videos.`")

        # Handle video files specifically
        if is_video and result.endswith((".mp4", ".avi", ".mov", ".mkv")):
            try:
                # Generate metadata
                meta = await metadata(result)
                duration = meta.get("duration")
                width = meta.get("width", 1280)
                height = meta.get("height", 720)

                # Generate thumbnail
                thumbnail_path = os.path.join(
                    os.path.dirname(result), "thumb.jpg"
                )
                await extract_thumbnail(result, thumbnail_path)

                # Prepare attributes
                attributes = [
                    DocumentAttributeFilename(os.path.basename(result)),
                    DocumentAttributeVideo(
                        duration=int(duration),
                        w=width,
                        h=height,
                        supports_streaming=True,
                    ),
                ]

                # Upload video with metadata
                file, _ = await event.client.fast_uploader(
                    result, show_progress=True, event=msg, to_delete=delete
                )
                await event.client.send_file(
                    event.chat_id,
                    file,
                    supports_streaming=True,
                    thumb=thumbnail_path if os.path.exists(thumbnail_path) else None,
                    attributes=attributes,
                    caption=custom_caption or f"`Uploaded: {os.path.basename(result)}`",
                    reply_to=event.reply_to_msg_id or event,
                )
                if delete and os.path.exists(thumbnail_path):
                    os.remove(thumbnail_path)
            except Exception as e:
                LOGS.exception(e)
                await msg.eor(f"Failed to upload `{result}`: {e}")
            continue

        # Handle non-video files
        attributes = None
        if stream:
            try:
                attributes = await set_attributes(result)
            except KeyError as er:
                LOGS.exception(er)

        file, _ = await event.client.fast_uploader(
            result, show_progress=True, event=msg, to_delete=delete
        )
        await event.client.send_file(
            event.chat_id,
            file,
            supports_streaming=stream,
            force_document=force_doc,
            thumb=thumb,
            attributes=attributes,
            caption=custom_caption or f"`Uploaded` `{os.path.basename(result)}`",
        )
    await msg.try_delete()
