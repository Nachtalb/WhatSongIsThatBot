# [WhatSongIsThatBot][tgbot]

[![WhatSongIsThatBot](https://img.shields.io/badge/-Telegram-0088CC?logo=telegram&logoColor=white)][tgbot]

Identify songs in seconds right from Telegram. Not only through audio files but
also via voice messages and videos!

## Setup

Install python dependencies:

```bash
git clone https://github.com/Nachtalb/WhatSongIsThatBot
cd WhatSongIsThatBot
pip install -r requirements.txt
```

Install additional dependency [songrec][songrec-repo] according to its
[instruction][songrec-installation].

Copy over the sample config and adjust it's contents.

```bash
cp config.sample.json config.json
```

| Name | Description |
| --- | --- |
| `token` | Telegram bot token acquired via [BotFather][botfather] |
| `songrec` | Path to songrec's binary |

### With webhook

To run in webhook mode, add these additional settings to your `config.json`.
`{token}` will be automatically filled in.

```json
{
    // ...

    "webhook": {
        "port": 9001,
        "host": "0.0.0.0",
        "path": "{token}",
        "url": "https://example.com"
    }
}
```

Like this the hook will be started on `0.0.0.0:9001/your_token` and Telegram
connects via `https://example.com/your_token`.

### As a service

You can copy the `wsit.service` over to `/etc/systemd/system/` or
`~/.config/systemd/user/` to run the bot as a service. Once you have copied
the file over, you have to adjust the paths inside it. Then:

```bash
# If it's inside ~/.config/systemd/user/ folder
systemctl --user daemon-reload               # load the service
systemctl --user enable --now wsit.service   # start the service on boot up and now

# Otherwise on system level
sudo systemctl daemon-reload
sudo systemctl enable --now wsit.service
```

## Usage

There are no fancy option or whatever needed, just run the main.py file.

```bash
python main.py
```

## `old.py`?

I first tried to implement the whole scheme with [ShazamAPI][shazamapi]. An
unofficial packaged that aims to do the same as songrec programmatically in python.
But after implementing and testing it, I dropped it. Compared with
songrec it's very very slow and much more inaccurate. But I left it in
here as reference material.

[tgbot]: https://t.me/WhatSongIsThatBot
[songrec-repo]: https://github.com/marin-m/SongRec
[songrec-installation]: https://github.com/marin-m/SongRec#installation
[botfather]: https://t.me/BotFather
[shazamapi]: https://github.com/Numenorean/ShazamAPI
