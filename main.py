import asyncio
import json
import os
import time
import random

from dotenv import load_dotenv
from telethon import TelegramClient
from telethon.errors import FloodWaitError, UserAlreadyParticipantError
from telethon.tl.functions.channels import JoinChannelRequest
from telethon.tl.types import Channel


EXPORT_FILE = "channels.json"
BASE_DELAY = 20  # seconds


load_dotenv()

API_FROM_ID = int(os.getenv("API_FROM_ID"))
API_FROM_HASH = os.getenv("API_FROM_HASH")

API_TO_ID = int(os.getenv("API_TO_ID"))
API_TO_HASH = os.getenv("API_TO_HASH")


async def export_channels():
    client = TelegramClient("session_from", API_FROM_ID, API_FROM_HASH)
    await client.start()

    dialogs = await client.get_dialogs()
    channels = []

    for d in dialogs:
        if isinstance(d.entity, Channel) and d.entity.username:
            channels.append({
                "title": d.entity.title,
                "username": d.entity.username
            })

    with open(EXPORT_FILE, "w", encoding="utf-8") as f:
        json.dump(channels, f, ensure_ascii=False, indent=2)

    print(f"[EXPORT] Saved {len(channels)} channels to {EXPORT_FILE}")
    await client.disconnect()


async def import_channels():
    with open(EXPORT_FILE, "r", encoding="utf-8") as f:
        channels = json.load(f)

    client = TelegramClient("session_to", API_TO_ID, API_TO_HASH)
    await client.start()


    dialogs = await client.get_dialogs()
    old_channels = []

    for d in dialogs:
        if isinstance(d.entity, Channel) and d.entity.username:
            old_channels.append({
                "title": d.entity.title,
                "username": d.entity.username
            })

    joined = 0
    skipped = 0

    for ch in channels:
        if ch not in old_channels:
            try:
                await client(JoinChannelRequest(ch["username"]))
                print(f"[JOINED] @{ch['username']}")
                joined += 1
            except UserAlreadyParticipantError:
                skipped += 1
            except FloodWaitError as e:
                print(f"[FLOOD] Waiting {e.seconds}s")
                time.sleep(e.seconds + 1)
            except Exception as e:
                print(f"[ERROR] @{ch['username']} — {e}")

            time.sleep(BASE_DELAY * random.uniform(0, 0.8))

    print(f"[IMPORT] Joined: {joined}, Skipped: {skipped}")
    await client.disconnect()


async def main():
    await export_channels()
    await import_channels()


if __name__ == "__main__":
    asyncio.run(main())