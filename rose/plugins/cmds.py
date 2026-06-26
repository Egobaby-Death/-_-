from pyrogram import filters, types

from anony import app, lang


CMDS_TEXT = """
<blockquote expandable>
👥 <b>Group Members</b>

🎵 /play &lt;song / url&gt; — Play audio in voice chat
🎬 /vplay &lt;song / url&gt; — Play video in voice chat
⚡ /playforce — Force play (skips current)
⚡ /vplayforce — Force play video
📋 /queue — View current queue
🏓 /ping — Bot ping &amp; uptime
📊 /stats — Bot statistics
🌐 /lang — Change bot language
👑 /sudolist — View sudo users
</blockquote>

<blockquote expandable>
👮 <b>Group Admins</b>

⏸️ /pause — Pause current song
▶️ /resume — Resume playback
⏭️ /skip — Skip to next song
⏹️ /stop — Stop &amp; clear queue
⏩ /seek &lt;seconds&gt; — Seek forward
⏪ /seekback &lt;seconds&gt; — Seek backward
🔁 /loop &lt;count&gt; — Set loop count (0 to disable)
🔐 /auth &lt;user&gt; — Authorize a user
🔓 /unauth &lt;user&gt; — Remove user authorization
📋 /authlist — View authorized users
🔄 /reload — Reload admin cache
⚙️ /settings — Bot settings (play mode, etc.)
</blockquote>

<blockquote expandable>
👑 <b>Owner / Sudo Only</b>

📢 /broadcast — Broadcast message to all chats
📂 /logs — Get bot log file
🪵 /logger on/off — Toggle play logger
🔄 /restart — Restart the bot
🚫 /blacklist &lt;id&gt; — Blacklist a chat or user
✅ /unblacklist &lt;id&gt; — Remove from blacklist
📞 /activevc — List active voice chats
🔢 /ac — Count active voice chats
➕ /addsudo &lt;user&gt; — Add sudo user <i>(Owner only)</i>
➖ /rmsudo &lt;user&gt; — Remove sudo user <i>(Owner only)</i>
⚙️ /eval &lt;code&gt; — Execute Python code <i>(Owner only)</i>
</blockquote>
"""


@app.on_message(filters.command(["cmds", "commands", "cmdlist"]))
@lang.language()
async def _cmds(_, m: types.Message):
    await m.reply_text(
        text=f"🌹 <b>Rose X Music — Command List</b>\n{CMDS_TEXT}",
        quote=True,
    )
