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

Install additional dependency [songrec][songrec-repo] according to its instruction.

Copy over the sample config and adjust it's contents.

```bash
cp config.sample.json config.json
```

| Name | Description |
| --- | --- |
| `token` | Telegram bot token acquired via [BotFather][botfather] |
| `songrec` | Path to songrec's binary |

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
[botfather]: https://t.me/BotFather
[shazamapi]: https://github.com/Numenorean/ShazamAPI
