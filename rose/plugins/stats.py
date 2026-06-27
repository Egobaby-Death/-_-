# Copyright (c) 2025 Riskyhater
# Licensed under the MIT License.
# This file is part of RoseXMusic


import os
import platform
import sys

import psutil
from pyrogram import __version__, filters, types
from pytgcalls import __version__ as pytgver

from anony import app, config, db, lang, logger, userbot
from anony.plugins import all_modules


@app.on_message(filters.command(["stats"]) & ~app.bl_users)
@lang.language()
async def _stats(_, m: types.Message):
    sent = await m.reply_text(m.lang["stats_fetching"])
    try:
        chats_count = len(await db.get_chats())
        users_count = len(await db.get_users())
        bl_count    = len(db.blacklisted)
        sudo_count  = len(app.sudoers)

        _utext = m.lang["stats_user"].format(
            app.name,
            len(userbot.clients),
            config.AUTO_LEAVE,
            bl_count,
            bl_count,
            sudo_count,
            chats_count,
            users_count,
        )

        if m.from_user.id in app.sudoers:
            pid     = os.getpid()
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

        await sent.edit_text(_utext)

    except Exception as e:
        logger.warning(f"stats command error: {e}")
        await sent.edit_text(f"⚠️ Stats fetch error: <code>{e}</code>")
