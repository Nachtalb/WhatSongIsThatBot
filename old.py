from asyncio import create_task
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from tempfile import NamedTemporaryFile

from ShazamAPI import Shazam
from aiohttp.client import ClientSession
from moviepy.editor import AudioFileClip
from telegram import File, InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)
from tqdm.asyncio import tqdm
from yarl import URL

DOWNLOAD_DIR = Path(__file__).with_name("downloads")
DOWNLOAD_DIR.mkdir(exist_ok=True)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        f"Hello {update.effective_user.full_name}, send me a piece of music and I'll try to find it's name :)"
    )


@dataclass
class Song:
    title: str
    artist: str
    cover: str
    shazam: str
    apple: str
    youtube: str | None
    current_pass: int


async def recognise_song(song_data: bytes, session: ClientSession, passes: int = 20):
    try:
        shazam = Shazam(song_data)
        recognition = shazam.recognizeSong()
        for index in range(1, passes + 1):
            print(index)
            data = next(recognition)  # type: ignore
            if track := data[1].get("track"):
                youtube_url = None
                for section in track["sections"]:
                    if yt_url := section.get("youtubeurl"):
                        async with session.get(yt_url) as response:
                            data = await response.json()
                            youtube_url = str(URL(data["actions"][0]["uri"]).with_query({}))

                song = Song(
                    title=track["title"],
                    artist=track["subtitle"],
                    cover=track["share"]["image"],
                    shazam=track["url"],
                    apple=f"https://music.apple.com/album/{track['albumadamid']}",
                    youtube=youtube_url,
                    current_pass=index,
                )

                yield song
    except:
        return


def get_song_markup(song: Song) -> tuple[str, InlineKeyboardMarkup]:
    info_text = f'{song.title} - {song.artist}\n<a href="{song.cover}">​</a>'
    buttons = [
        InlineKeyboardButton("Shazam", song.shazam),
        InlineKeyboardButton("Apple Music", song.apple),
    ]
    if song.youtube:
        buttons.append(InlineKeyboardButton("YouTube", song.youtube))

    button_array = InlineKeyboardMarkup(
        [[InlineKeyboardButton(f"{song.title} by {song.artist}", song.shazam)], buttons]
    )

    return info_text, button_array


async def what_song_is_that__audio(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    file = await (update.message.audio or update.message.voice).get_file()
    with BytesIO() as in_memory:
        await file.download_to_memory(out=in_memory)
        await what_song_is_that(update, context, in_memory)


async def what_song_is_that__video(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message.video:
        file = await update.message.video.get_file()
        file_name = update.message.video.file_name
    else:
        file = await update.message.video_note.get_file()
        file_name = Path(file.file_path).name
    file = await (update.message.video or update.message.video_note).get_file()
    with NamedTemporaryFile(suffix=file_name) as temp_video:
        await file.download_to_drive(temp_video.name)
        clip = AudioFileClip(temp_video.name)
        with NamedTemporaryFile(suffix=".ogg") as temp_audio:
            clip.write_audiofile(temp_audio.name)
            clip.write_audiofile(Path(__file__).with_name("test.ogg"))
            with BytesIO(Path(temp_audio.name).read_bytes()) as in_memory:
                await what_song_is_that(update, context, in_memory)


async def what_song_is_that(update: Update, context: ContextTypes.DEFAULT_TYPE, memory: BytesIO) -> None:
    message = await update.message.reply_text("Trying to find song info....")

    try:
        async with ClientSession() as session:
            last_guess = None
            task = None

            async for song in recognise_song(memory.getvalue(), session):
                if song == last_guess:
                    continue

                last_guess = song
                text, markup = get_song_markup(song)

                if task:
                    task.cancel()

                task = create_task(
                    message.edit_text(
                        f"<b>Analysing... Current Guess:</b>\n{text}", reply_markup=markup, parse_mode=ParseMode.HTML
                    )
                )

                if song.current_pass % 6 == 0:
                    # Try to stop every 6th pass if we got something there
                    # Max passes is defined by the recognise_song function
                    break

            if task:
                task.cancel()

            if last_guess:
                text, markup = get_song_markup(last_guess)
                await message.edit_text(f"<b>🎶 {text}</b>", reply_markup=markup, parse_mode=ParseMode.HTML)
            else:
                await message.edit_text(f"<b>Could not find any matches</b>", parse_mode=ParseMode.HTML)

    except:
        await message.edit_text("Something went wrong :(")
        raise


# cspell: disable-next-line
app = ApplicationBuilder().token("6134944280:AAGBeid_Hwp1yqwKGO6KizAjhCNcVl8CrfM").build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.AUDIO | filters.VOICE, what_song_is_that__audio))
app.add_handler(MessageHandler(filters.VIDEO | filters.VIDEO_NOTE, what_song_is_that__video))
app.run_polling()
