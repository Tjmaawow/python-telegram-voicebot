import google.generativeai as genai
import asyncio
import uuid
import os
import mimetypes
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters.command import Command

genai.configure(api_key="ВАШ GEMINI ТОКЕН. ПОЛУЧИТЬ ЕГО МОЖНО В AI STUDIO")  # API ключ gemini
model = genai.GenerativeModel("gemini-2.5-pro")  # Задаем модель

TG_TOK = "TELEGRAM TOKEN ВАШЕГО БОТА. ПОЛУЧИТЬ ЕГО МОЖНО У @BotFather"  # API токен тг бота

bot = Bot(token=TG_TOK)
dp = Dispatcher()


@dp.message(Command("start"))  # команда /start
async def start_handler(msg: types.Message):
    await msg.reply("""
Привет! Я бесплатный бот для расшифровки на основе ИИ модели "Gemini 2.5 Pro".
Для расшифровки просто отравьте свое видео-сообщение или голосовое.
Для проверки буду ли я работать можно ввести /setup@googlespeech_bot.
""")


@dp.message(
    Command("setup"), F.chat.type.in_({"group", "supergroup"})
)  # Команда /setup в группе и супер-группе
async def setup_handler(msg: types.Message):
    chat_id = msg.chat.id  # Айди чата
    try:  # Пробуем получить пользователя бота как участника чата
        member = await bot.get_chat_member(chat_id, user_id=bot.id)
    except Exception as e:  # если не вышло
        return await msg.reply("Не смог проверить свою работу. Ошибка: \n {}".format(e))
    if isinstance(
        member, (types.ChatMemberOwner, types.ChatMemberAdministrator)
    ):  # если полученный пользователь является или владельцем или администратором
        await msg.reply(
            "Да. Я должен работать здесь.\nДля получения расшифровки просто отправьте голосовое или видео-сообщение."
        )
    else:  # иначе
        await msg.reply(
            "Нет, я не смогу здесь работать.\nДля того чтобы это исправить, выдайте мне права администратора. Это нужно только для того, чтобы я мог видеть сообщения кроме команд."
        )


@dp.message(Command("setup"))  # Если команда не в группе или в супер-группе
async def setupnogroup_handler(msg: types.Message):
    await msg.reply(
        "Это команда для групп и супергрупп. А это личные сообщения.\nВ личных сообщениях будет в любом случае работать, но не забывайте, что бот акцентируется на группах."
    )


# @dp.message(F.reply_to_message, F.text.lower() == "расшифровку", F.reply_to_message.content_type.in_({'voice', 'video_note'}))
@dp.message(F.content_type.in_({"voice", "video_note"}))  # Только гс и видеозаметка
async def transcribe_handler(msg: types.Message):
    try:
        await msg.react(
            [types.ReactionTypeEmoji(emoji="👍")]
        )  # если получится ставим эмодзи
    except:
        await msg.reply(
            "Секундочку...\nP.S. Выдайте мне право ставить реакции. С ним я не буду засорять чат этим сообщением."
        )  # если не получилось упоминаем
    try:
        if msg.voice:  # если сообщение - голосовое
            file_id = msg.voice.file_id  # айди для скачивания
            file_ext = ".mp3"  # на будущее задаем формат файла
        else:  # если сообщение какой либо другой тип(в любом случае кружок)
            file_id = msg.video_note.file_id  # айди
            file_ext = ".mp4"  # формат
        file = await bot.get_file(file_id)  # получает файл
        path = file.file_path  # получает путь файла
        filpath = (
            str(msg.message_id) + file_ext
        )  # собирается путь куда этот файл сохранится на пк
        await bot.download_file(path, filpath)  # скачивание

        # Все что далее - взято с форума
        mime_type, _ = mimetypes.guess_type(filpath)
        if mime_type is None:
            mime_type = "application/octet-stream"

        with open(filpath, "rb") as f:
            audio_bytes = f.read()

        audio_file_part = {"mime_type": mime_type, "data": audio_bytes}
        # кончается
        # определение промптов в зависимости от расширения файла
        prompt = {
            ".mp3": "Напиши расшифровку этого аудиофайла, без лишних слов. Также можешь описывать эмоции, звуки на фоне и т.д. Таймкоды писать не надо. Также, не используй форматирование текста",
            ".mp4": "Сначала напиши расшифровку того что говорится в этом видео, потом пропустив строку опиши что в нем происходит, но кратко. По поводу речи - так же можешь описывать эмоции, звуки на фоне и т.д. Таймкоды писать не надо. Также, не используй форматирование текста. Видео круглое потому что это скачанный кружок из телеграмма, не упоминай это.",
        }
        description = await model.generate_content_async(
            [prompt[file_ext], audio_file_part]
        )  # Ожидание ответа нейронки
        await msg.reply(description.text)  # Отправка сообщения
        os.remove(filpath)  # удаление файла
    except Exception as e:  # провал в какой то части кода
        await msg.reply("Что то не вышло.\n{}".format(e))  # Сообщаем об ошибке


async def boot():
    await dp.start_polling(bot)  # асинхронно запускается бот


if __name__ == "__main__":
    asyncio.run(boot())  # с помощью asyncio синхронно запускаем асинхронное
