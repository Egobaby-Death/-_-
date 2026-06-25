# Copyright (c) 2025 MalikX
# Licensed under the MIT License.
# This file is part of RoseX_Musicbot

import psutil
from pyrogram import filters, types
from anony import app, db, lang

@app.on_message(
    filters.command(["clearcache", "cache"])
    & (filters.user(app.owner) | filters.user(list(app.sudoers)))
)
@lang.language()
async def _clearcache(_, m: types.Message):
    sent = await m.reply_text("🔄 **Cache check kar raha hoon...**")
    before_ram = psutil.virtual_memory().percent
    in_memory_cleared = 0
    for cache in [db.admin_list, db.lang, db.auth, db.assistant]:
        if cache:
            cache.clear()
            in_memory_cleared += 1
    try:
        stats = await db.mongo.command("dbStats")
        db_info = (
            f"\n\n**📦 MongoDB Stats:**\n"
            f"• Database: `{db.db.name}`\n"
            f"• Data Size: `{round(stats.get('dataSize',0)/(1024*1024),2)} MB`\n"
            f"• Storage: `{round(stats.get('storageSize',0)/(1024*1024),2)} MB`\n"
            f"• Documents: `{stats.get('objects',0)}`"
        )
    except Exception:
        db_info = "\n\n⚠️ MongoDB stats nahi mili."
    after_ram = psutil.virtual_memory().percent
    freed = round(before_ram - after_ram, 1)
    await sent.edit_text(
        f"✅ **Cache Clear!**\n\n"
        f"🧠 RAM: `{before_ram}%` → `{after_ram}%` ({'freed '+str(freed)+'%' if freed>0 else 'already clean'})\n"
        f"🗂 Caches cleared: `{in_memory_cleared}/4`"
        f"{db_info}"
    )
