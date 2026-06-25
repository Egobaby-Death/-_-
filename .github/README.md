<div align="center">

<h2>⏤͟͟͞͞ Ꭱ𝛐𝛔𝛆 ꭙ ❰ 𝐌 𝐔 𝐒 𝐈 𝐂 ❱ • !! ˹🌹🎶˼</h2>

<b>Telegram Group Calls Streaming Bot</b><br>
Supports YouTube, Spotify, Resso, Apple Music, SoundCloud and M3U8 links.

<a href="https://github.com/Techspider-alt/RoseX_Musicbot/stargazers">
    <img src="https://img.shields.io/github/stars/Techspider-alt/RoseX_Musicbot?color=blueviolet&logo=github&logoColor=black&style=for-the-badge" alt="Stars"/>
</a>
<a href="https://github.com/Techspider-alt/RoseX_Musicbot/network/members">
    <img src="https://img.shields.io/github/forks/Techspider-alt/RoseX_Musicbot?color=blueviolet&logo=github&logoColor=black&style=for-the-badge" alt="Forks"/>
</a>
<a href="https://github.com/Techspider-alt/RoseX_Musicbot/blob/master/LICENSE">
    <img src="https://img.shields.io/badge/License-MIT-blue?style=for-the-badge" alt="License"/>
</a>
<a href="https://www.python.org/">
    <img src="https://img.shields.io/badge/Written%20in-Python-blue?style=for-the-badge&logo=python" alt="Python"/>
</a>
<br>

<img src="https://files.catbox.moe/9q73nt.jpg" width="720" height="auto">

⏤͟͟͞͞ Ꭱ𝛐𝛔𝛆 ꭙ ❰ 𝐌 𝐔 𝐒 𝐈 𝐂 ❱ • !! ˹🌹🎶˼ lets you stream high-quality and low-latency audio and video playback into telegram group video chats.<br>
Built with Python, Pyrogram, and Py-TgCalls, it’s optimized for reliability and easy deployment on Heroku, VPS, or Docker.
</div>

<hr>

<h2>🔥 Features</h2>

- 🎧 Stream low-latency audio in real time to <b>Telegram group video chats</b>
- 🌐 Supports multiple platforms like <b>YouTube, Spotify, Apple Music, SoundCloud</b>
- ⚡ Advanced queue management with auto-play
- ⚙️ Easy deployment — works on Local, VPS, or Heroku
- ❤️ Built with Python
<hr>

<h2>☁️ Manual Deployment</h2>

<h3>✔️ Prerequisites</h3>

- <a href="https://www.python.org">Python 3.10+</a> installed  
- <a href="https://deno.com/">deno</a> & <a href="https://ffmpeg.org/">ffmpeg</a> installed on your system  
- Required variables mentioned in <a href="https://github.com/Techspider-alt/RoseX_Musicbot/blob/master/sample.env">sample.env</a>

<details>
    <summary>
        <h3>Local / VPS Setup</h3>
    </summary>

<h4>🐧 Linux/macOS</h4>

```bash
git clone https://github.com/Techspider-alt/RoseX_Musicbot && cd RoseX_Musicbot

# Install uv
curl -Ls https://astral.sh/uv/install.sh | sh
export PATH="$HOME/.local/bin:$PATH"

# Install dependencies
uv sync --frozen

# Rename and configure environment variables
mv sample.env .env
# Edit .env with your credentials

# Start the bot
bash start
'''

<h4>🪟 Windows (PowerShell)</h4>

git clone https://github.com/Techspider-alt/RoseX_Musicbot && cd RoseX_Musicbot

# Install uv
irm https://astral.sh/uv/install.ps1 | iex

# Install dependencies
uv sync --frozen

# Rename and configure environment variables
mv sample.env .env
# Edit .env with your credentials

# Start the bot
uv run python3 -m anony

> ⭐ or use Git Bash or WSL to run `bash start`.
'''

</details>

<details>
    <summary>
        <h3>Deploy to Heroku</h3>
    </summary>

Click on the button below to deploy on Heroku

<a href="https://dashboard.heroku.com/new?template=https://github.com/Techspider-alt/RoseX_Musicbot">
<img src="https://img.shields.io/badge/Deploy%20On%20Heroku-black?style=for-the-badge&logo=heroku"/>
</a>

</details>

<hr>

<h2>⚙️ Configuration</h2>

Edit <code>.env</code> (or set variables in your hosting environment):

<details>
    <summary>Here's an example of the .env file</summary>

```env
API_ID=123456
API_HASH=abcdef1234567890
BOT_TOKEN=123456:ABC-DEF
OWNER_ID=123456789
LOGGER_ID=-1001234567890
MONGO_URL=mongodb+srv://
SESSION=BQgfh...AA
```

📝 Check <a href="https://github.com/Techspider-alt/RoseX_Musicbot/blob/master/config.py">config.py</a> for all available options.

</details>

<hr>

<h2>🧐 Usage</h2>

1. Add the bot to your Telegram group.
2. Promote it to <b>admin</b> with invite users permission.
3. Use commands in the chat to control playback:

<details>
    <summary>Commands overview</summary>
    <pre>
/play [song name or link] -> Play audio in the videochat
/vplay [song name or link] -> Play video in the videochat
/pause -> Pause playback
/resume -> Resume playback
/skip -> Skip to next track
/stop -> Stop playback
/seek -> Seeks the stream
/queue -> Show queue
    </pre>
</details>

<hr>

<h2>❤️ Contributing</h2>

Contributions are welcome!

1. Fork the repository.
2. Create your branch: <code>git checkout -b feature/new</code>.
3. Commit changes: <code>git commit -m 'New feature'</code>.
4. Push: <code>git push origin feature/new</code>
5. Open a Pull Request.

<hr>

<h2>🗒️ License</h2>

This project is licensed under the <b>MIT License</b> — see <a href="https://github.com/Techspider-alt/RoseX_Musicbot/blob/master/LICENSE">LICENSE</a> for details.

<hr>

<h2>🤞 Updates and support</h2>

· <a href="https://t.me/+7Ykn9Hpn2MRhZjE0">Updates channel</a>
· <a href="https://t.me/+-g8ILICIFgsyMzQ0">Support group</a>
· <a href="https://t.me/Riskyhater">Owner</a>

<hr>

<h2>👀 Acknowledgements</h2>

· Inspired by other open-source Telegram music bots.
· Thanks to all the <a href="https://github.com/Techspider-alt/RoseX_Musicbot/graphs/contributors">contributors</a>.

<hr>

<div align="center">

⭐ Enjoying the tunes? <b>Star the repo</b> — feedback keeps the rhythm going!

</div>
```
