# Copyright (c) 2025 MalikX
# Licensed under the MIT License.
# This file is part of RoseX_Musicbot

import gc
import os
import shutil

import psutil
from pyrogram import filters, types
from anony import app, db, lang


@app.on_message(
    filters.command(["clearcache", "cache", "clearall"])
    & app.sudoers
)
@lang.language()
async def _clearcache(_, m: types.Message):
    sent = await m.reply_text("🔄 **Cache aur memory clear kar raha hoon...**")

    before_ram = psutil.virtual_memory().percent
    before_disk = psutil.disk_usage("/").used / (1024 ** 3)

    in_memory_cleared = 0
    for cache in [db.admin_list, db.lang, db.auth, db.assistant]:
        if cache:
            cache.clear()
            in_memory_cleared += 1

    gc.collect()

    dirs_cleared = 0
    files_cleared = 0
    for directory in ["downloads", "cache"]:
        if os.path.exists(directory):
            for fname in os.listdir(directory):
                fpath = os.path.join(directory, fname)
                try:
                    if os.path.isfile(fpath):
                        os.remove(fpath)
                        files_cleared += 1
                    elif os.path.isdir(fpath):
                        shutil.rmtree(fpath, ignore_errors=True)
                        dirs_cleared += 1
                except Exception:
                    pass

    try:
        log_size = os.path.getsize("log.txt") / (1024 ** 2) if os.path.exists("log.txt") else 0
    except Exception:
        log_size = 0

    try:
        stats = await db.mongo.command("dbStats")
        db_info = (
            f"\n\n**📦 MongoDB Stats:**\n"
            f"• Database: `{db.db.name}`\n"
            f"• Data Size: `{round(stats.get('dataSize', 0) / (1024 * 1024), 2)} MB`\n"
            f"• Storage: `{round(stats.get('storageSize', 0) / (1024 * 1024), 2)} MB`\n"
            f"• Documents: `{stats.get('objects', 0)}`"
        )
    except Exception:
        db_info = "\n\n⚠️ MongoDB stats nahi mili."

    after_ram = psutil.virtual_memory().percent
    after_disk = psutil.disk_usage("/").used / (1024 ** 3)
    freed_ram = round(before_ram - after_ram, 1)
    freed_disk = round(before_disk - after_disk, 2)

    await sent.edit_text(
        f"✅ **Cache & Memory Clear!**\n\n"
        f"🧠 RAM: `{before_ram}%` → `{after_ram}%` "
        f"({'freed ' + str(freed_ram) + '%' if freed_ram > 0 else 'already clean'})\n"
        f"💾 Disk freed: `{freed_disk:.2f} GB`\n"
        f"📂 Files removed: `{files_cleared}`\n"
        f"🗂 In-memory caches cleared: `{in_memory_cleared}/4`\n"
        f"📋 Log size: `{log_size:.2f} MB`"
        f"{db_info}"
    )
