# Archive Commands

Too many channels in your server? Need to delete some? Save the contents with the archive channel command!

Use `~help Archive` on the bot to know the commands in this module.

Archives are Discord-style HTML pages (with threads, forum posts and attachments), made with
[DiscordChatExporter](https://github.com/Tyrrrz/DiscordChatExporter). If the zip is too big to send,
the bot leaves out the biggest media files until it fits and lists them in its reply. If even the HTML
on its own is too big, it sends nothing.

## Setup for developers

Run `python scripts/install_dce.py` once. It downloads a pinned DiscordChatExporter release into `tools/dce/`
and checks its hash. On Linux, DiscordChatExporter also needs ICU (`sudo apt install libicu72` on Debian 12).
To use a copy somewhere else, set `DCE_PATH` in `.env`.

## Credits

Archives are made with [DiscordChatExporter](https://github.com/Tyrrrz/DiscordChatExporter)
by [Oleksii Holub (Tyrrrz)](https://github.com/Tyrrrz), © 2017–2026, under the
[MIT License](https://github.com/Tyrrrz/DiscordChatExporter/blob/master/License.txt).
BBN doesn't include DiscordChatExporter's code, but downloads a pinned release from GitHub. See `scripts/install_dce.py` for details.