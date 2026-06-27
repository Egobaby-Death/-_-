# Copyright (c) 2025 Riskyhater
# Licensed under the MIT License.
# This file is part of RoseXMusic


import os
import platform
import sys

import psutil
from pyrogram import __version__, filters, types
from pytgcalls import __version__ as pytgver

from anony import app, config, db, lang, userbot
from anony.plugins import all_modules


@app.on_message(filters.command(["stats"]) & filters.group & ~app.bl_users)
@lang.language()
async def _stats(_, m: types.Message):
    try:
        sent = await m.reply_photo(
            photo=config.PING_IMG,
            caption=m.lang["stats_fetching"],
        )
    except Exception:
        sent = await m.reply_text(m.lang["stats_fetching"])

    sudoers_list = await db.get_sudoers()
    bl_count = len(db.blacklisted)
    sudo_count = len(sudoers_list) + 1

    pid = os.getpid()
    _utext = m.lang["stats_user"].format(
        app.name,
        len(userbot.clients),
        config.AUTO_LEAVE,
        bl_count,
        bl_count,
        sudo_count,
        len(await db.get_chats()),
        len(await db.get_users()),
    )
    if m.from_user.id in app.sudoers:
        process = psutil.Process(pid)
        storage = psutil.disk_usage("/")
        _utext += m.lang["stats_sudo"].format(
            len(all_modules),
            platform.system(),
            f"{process.memory_info().rss / 1024**2:.2f}",
            round(psutil.virtual_memory().total / (1024.0**3)),
            process.cpu_percent(interval=1.0),
            psutil.cpu_count(),
            f"{storage.used / (1024.0**3):.2f}",
            f"{storage.total / (1024.0**3):.2f}",
            sys.version.split()[0],
            __version__,
            pytgver,
        )
    try:
        await sent.edit_caption(_utext)
    except Exception:
        await sent.edit_text(_utext)
