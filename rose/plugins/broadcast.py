# Copyright (c) 2025 MalikX
# Licensed under the MIT License.
# This file is part of RoseX_Musicbot

import os
import asyncio
import time

from pyrogram import errors, filters, types
from anony import app, db, lang

broadcasting = asyncio.Lock()

@app.on_message(filters.command(["broadcast"]) & app.sudoers)
@lang.language()
async def _broadcast(_, message: types.Message):
    if not message.reply_to_message:
        return await message.reply_text(
            "**📢 Broadcast Usage:**\n\n"
            "Ek message ko reply karo aur `/broadcast` likhao.\n\n"
            "**Optional flags:**\n"
            "• `/broadcast -nochat` — groups skip\n"
            "• `/broadcast -nouser` — users DM skip\n"
            "• `/broadcast -nopin` — pin mat karo\n"
            "• `/broadcast -copy` — copy mode"
        )

    if broadcasting.locked():
        return await message.reply_text(message.lang["gcast_active"])

    msg = message.reply_to_message
    cmd = message.text or ""
    skip_chats = "-nochat" in cmd
    skip_users = "-nouser" in cmd
    skip_pin   = "-nopin" in cmd
    copy_msg   = "-copy" in cmd

    groups = set() if skip_chats else set(await db.get_chats())
    users  = set() if skip_users else set(await db.get_users())
    all_targets = list(groups | users)

    sent = await message.reply_text(
        f"📢 **Broadcast shuru ho raha hai...**\n\n"
        f"👥 Users: `{len(users)}`\n"
        f"💬 Groups: `{len(groups)}`\n"
        f"📌 Auto-pin: `{'OFF' if skip_pin else 'ON'}`"
    )

    g_count = 0
    u_count = 0
    pin_count = 0
    fail_count = 0
    failed_file = None
    start_time = time.time()

    async with broadcasting:
        for chat_id in all_targets:
            try:
                if copy_msg:
                    sent_msg = await msg.copy(chat_id, reply_markup=msg.reply_markup)
                else:
                    sent_msg = await msg.forward(chat_id)

                if chat_id in groups:
                    g_count += 1
                    if not skip_pin:
                        try:
                            await app.pin_chat_message(chat_id, sent_msg.id, disable_notification=False)
                            pin_count += 1
                        except Exception:
                            pass
                else:
                    u_count += 1

                await asyncio.sleep(0.3)

            except errors.FloodWait as fw:
                await asyncio.sleep(fw.value + 10)
            except errors.UserIsBlocked:
                fail_count += 1
                await db.rm_user(chat_id)
            except errors.ChatWriteForbidden:
                fail_count += 1
            except errors.PeerIdInvalid:
                fail_count += 1
            except Exception as ex:
                fail_count += 1
                if not failed_file:
                    failed_file = open("broadcast_errors.txt", "w")
                failed_file.write(f"{chat_id} — {ex}\n")

    elapsed = int(time.time() - start_time)
    mins, secs = divmod(elapsed, 60)
    time_taken = f"{mins}m {secs}s" if mins else f"{secs}s"

    summary = (
        f"✅ **Broadcast Complete!**\n\n"
        f"📊 **Results:**\n"
        f"💬 Groups mein bheja: `{g_count}`\n"
        f"👥 Users ke DM mein bheja: `{u_count}`\n"
        f"📌 Groups mein pin hua: `{pin_count}`\n"
        f"❌ Failed: `{fail_count}`\n\n"
        f"📦 Total: `{g_count + u_count}` / `{len(all_targets)}`\n"
        f"⏱ Time laga: `{time_taken}`"
    )

    if failed_file:
        failed_file.close()
        await message.reply_document(document="broadcast_errors.txt", caption=summary)
        try:
            os.remove("broadcast_errors.txt")
        except Exception:
            pass

    await sent.edit_text(summary)
