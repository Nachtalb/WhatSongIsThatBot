from asyncio.subprocess import PIPE, create_subprocess_exec
from dataclasses import dataclass
import json
from pathlib import Path
from tempfile import NamedTemporaryFile

from aiohttp.client import ClientSession
from moviepy.editor import AudioFileClip
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Message, Update
from telegram.constants import ParseMode
from telegram.error import BadRequest
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)
from yarl import URL

DOWNLOAD_DIR = Path(__file__).with_name("downloads")
DOWNLOAD_DIR.mkdir(exist_ok=True)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user:
        name = " " + update.effective_user.full_name
    elif update.effective_chat:
        name = " " + update.effective_chat.title
    else:
        name = ""

    await update.message.reply_text(
        f"Hello{name}, send me some music in audio or video form and I'll try and identify the songname :)\n\nI was"
        " built by @Nachtalb and you can find my source code <a"
        " href='https://github.com/Nachtalb/WhatSongIsThatBot'>here</a>",
        parse_mode=ParseMode.HTML,
    )


@dataclass
class Song:
    title: str
    artist: str
    cover: str
    providers: list[tuple[str, str, int]]


async def recognise_song(path: Path, session: ClientSession):
    proc = await create_subprocess_exec(CONFIG["songrec"], "audio-file-to-recognized-song", path, stdout=PIPE)
    raw = (await proc.communicate())[0].strip()

    track: dict = json.loads(raw).get("track")  # type: ignore
    if not track:
        return

    providers: list[tuple[str, str, int]] = [
        (f"{track['title']} by {track['subtitle']}", track["url"], 0),
    ]

    if "albumadamid" in track:
        providers.append(("Apple Music", f"https://music.apple.com/album/{track['albumadamid']}", 2))

    for section in track["sections"]:
        if yt_url := section.get("youtubeurl"):
            async with session.get(yt_url) as response:
                response_data = await response.json()
                providers.append(("YouTube", str(URL(response_data["actions"][0]["uri"]).with_query({})), 3))

    for provider in track["hub"]["providers"]:
        match provider["type"]:
            case "SPOTIFY":
                providers.append(
                    (
                        "Spotify",
                        provider["actions"][0]["uri"].replace("spotify:search:", "https://open.spotify.com/search/"),
                        1,
                    )
                )
            case "YOUTUBEMUSIC":
                providers.append(("YouTube Music", provider["actions"][0]["uri"], 4))
            case "DEEZER":
                providers.append(
                    (
                        "Deezer",
                        provider["actions"][0]["uri"].replace(
                            "deezer-query://www.deezer.com/play?query=", "https://deezer.com/search/"
                        ),
                        5,
                    )
                )

    song = Song(
        title=track["title"],
        artist=track["subtitle"],
        cover=track["share"]["image"],
        providers=providers,
    )

    return song


def chunks(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i : i + n]


def get_song_markup(song: Song) -> tuple[str, InlineKeyboardMarkup]:
    info_text = f'{song.title} - {song.artist}\n<a href="{song.cover}">​</a>'

    buttons = [InlineKeyboardButton(item[0], url=item[1]) for item in sorted(song.providers, key=lambda i: i[2])]
    button_array = InlineKeyboardMarkup(
        [
            [buttons[0]],  # Shazam button
            *list(chunks(buttons[1:], 2)),
        ]
    )

    return info_text, button_array


async def what_song_is_that__audio(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = await update.message.reply_text("Trying to find song info....")

    try:
        file = await (update.message.audio or update.message.voice).get_file()
    except BadRequest as error:
        if "too big" in error.message:
            await message.edit_text("The provided file is too big :(\nTelegram bots are limited to 20MB")
            return
        raise

    name = Path(file.file_path).name
    with NamedTemporaryFile(suffix=name) as temp_file:
        path = Path(temp_file.name)
        await file.download_to_drive(path)
        await what_song_is_that(update, context, path, message)


async def what_song_is_that__video(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = await update.message.reply_text("Trying to find song info....")

    try:
        if update.message.video:
            file = await update.message.video.get_file()
            file_name = update.message.video.file_name
        else:
            file = await update.message.video_note.get_file()
            file_name = Path(file.file_path).name
    except BadRequest as error:
        if "too big" in error.message:
            await message.edit_text("The provided file is too big :(\nTelegram bots are limited to 20MB")
            return
        raise

    with NamedTemporaryFile(suffix=file_name) as temp_video:
        await file.download_to_drive(temp_video.name)
        clip = AudioFileClip(temp_video.name)
        with NamedTemporaryFile(suffix=".ogg") as temp_audio:
            path = Path(temp_audio.name)
            clip.write_audiofile(temp_audio.name)
            await what_song_is_that(update, context, path, message)


async def what_song_is_that(
    update: Update, context: ContextTypes.DEFAULT_TYPE, path: Path, initial_msg: Message
) -> None:
    try:
        async with ClientSession() as session:
            if song := await recognise_song(path, session):
                text, markup = get_song_markup(song)
                await initial_msg.edit_text(f"<b>🎶 {text}</b>", reply_markup=markup, parse_mode=ParseMode.HTML)
            else:
                await initial_msg.edit_text(f"<b>Could not find any matches</b>", parse_mode=ParseMode.HTML)

    except:
        await initial_msg.edit_text("Something went wrong :(")
        raise


CONFIG = json.loads(Path(__file__).with_name("config.json").read_text())

app = ApplicationBuilder().token(CONFIG["token"]).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.AUDIO | filters.VOICE, what_song_is_that__audio))
app.add_handler(MessageHandler(filters.VIDEO | filters.VIDEO_NOTE, what_song_is_that__video))

if hook := CONFIG.get("webhook"):
    app.run_webhook(
        listen=hook["host"],
        port=hook["port"],
        url_path=hook["path"].format(**CONFIG),
        webhook_url=f"{hook['url']}/{hook['path'].format(**CONFIG)}",
    )
else:
    app.run_polling()
