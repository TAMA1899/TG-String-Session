import asyncio

from bot import bot, HU_APP
from pyromod import listen
from asyncio.exceptions import TimeoutError

from pyrogram import filters, Client
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import (
    SessionPasswordNeeded, FloodWait,
    PhoneNumberInvalid, ApiIdInvalid,
    PhoneCodeInvalid, PhoneCodeExpired
)

API_TEXT = """Hello Friends, {}
Ini adalah Bot untuk mendapat **String Session** dari Telegram. 
By @justthetech 

Kirim `APP_ID` untuk Start Generating Session ambil dari my.telegram.org atau @scrapidhash_bot """
HASH_TEXT = "Kirim `API_HASH` dari my.telegram.org atau ambil dari @scrapidhash_bot."
PHONE_NUMBER_TEXT = (
    "Sekarang Kirim Nomer HP Telegrammu dengan Format . \n"
    "Contoh : **+6288800009999**\n\n"
    "Press /cancel untuk membatalkan."
)

@bot.on_message(filters.private & filters.command("start"))
async def genStr(_, msg: Message):
    chat = msg.chat
    api = await bot.ask(
        chat.id, API_TEXT.format(msg.from_user.mention)
    )
    if await is_cancel(msg, api.text):
        return
    try:
        check_api = int(api.text)
    except Exception:
        await msg.reply("`API_ID` tidak valid.\nKetik /start untuk memulai ulang.")
        return
    api_id = api.text
    hash = await bot.ask(chat.id, HASH_TEXT)
    if await is_cancel(msg, hash.text):
        return
    if not len(hash.text) >= 30:
        await msg.reply("`API_HASH` tidak valid.\nKetik /start untuk memulai ulang.")
        return
    api_hash = hash.text
    while True:
        number = await bot.ask(chat.id, PHONE_NUMBER_TEXT)
        if not number.text:
            continue
        if await is_cancel(msg, number.text):
            return
        phone = number.text
        confirm = await bot.ask(chat.id, f'`apakah "{phone}" sudah benar? (y/n):` \n\nKetik : `y` (jika sudah benar)\nSend: `n` (jika salah)')
        if await is_cancel(msg, confirm.text):
            return
        if "y" in confirm.text:
            break
    try:
        client = Client("my_account", api_id=api_id, api_hash=api_hash)
    except Exception as e:
        await bot.send_message(chat.id ,f"**ERROR:** `{str(e)}`\nKetik /start untuk memulai ulang.")
        return
    try:
        await client.connect()
    except ConnectionError:
        await client.disconnect()
        await client.connect()
    try:
        code = await client.send_code(phone)
        await asyncio.sleep(1)
    except FloodWait as e:
        await msg.reply(f"Terlalu banyak permintaan tunggu {e.x} detik")
        return
    except ApiIdInvalid:
        await msg.reply("API ID and API Hash tidak valid.\n\nKetik /start untuk memulai ulang.")
        return
    except PhoneNumberInvalid:
        await msg.reply("Nomer HP tidak valid.\n\nKetik /start untuk memulai ulang.")
        return
    try:
        otp = await bot.ask(
            chat.id, ("OTP sudah terkirim. Cek pesan!"
                      "Masukkan kode OTP Contoh : `1 2 3 4 5` format. __(setiap nomer kasih spasi!)__ \n\n"
                      "Jika OTP belum masuk ketik /restart dan mulai ulang ketik /start .\n"
                      "Ketik /cancel untuk membatalkan."), timeout=300)

    except TimeoutError:
        await msg.reply("Waktu telah habis lebih dari 5 min.\nKetik /start untuk memulai ulang.")
        return
    if await is_cancel(msg, otp.text):
        return
    otp_code = otp.text
    try:
        await client.sign_in(phone, code.phone_code_hash, phone_code=' '.join(str(otp_code)))
    except PhoneCodeInvalid:
        await msg.reply("Kode tidak valid.\n\nKetik /start untuk memulai ulang.")
        return
    except PhoneCodeExpired:
        await msg.reply("Code is Expired.\n\nKetik /start untuk memulai ulang.")
        return
    except SessionPasswordNeeded:
        try:
            two_step_code = await bot.ask(
                chat.id, 
                "Your account have Two-Step Verification.\nPlease enter your Password.\n\nPress /cancel untuk membatalkan.",
                timeout=300
            )
        except TimeoutError:
            await msg.reply("`Time limit reached of 5 min.\n\nKetik /start untuk memulai ulang.`")
            return
        if await is_cancel(msg, two_step_code.text):
            return
        new_code = two_step_code.text
        try:
            await client.check_password(new_code)
        except Exception as e:
            await msg.reply(f"**ERROR:** `{str(e)}`")
            return
    except Exception as e:
        await bot.send_message(chat.id ,f"**ERROR:** `{str(e)}`")
        return
    try:
        session_string = await client.export_session_string()
        await client.send_message("me", f"#PYROGRAM #STRING_SESSION\n\n```{session_string}``` \n\nOwner : @justthetech \nBy : @stringsessions_bot \nUpdate : @robotmusicupdate")
        await client.disconnect()
        text = "String Session is Successfully Generated.\nKlik Tombol dibawah."
        reply_markup = InlineKeyboardMarkup(
            [[InlineKeyboardButton(text="Show String Session", url=f"tg://openmessage?user_id={chat.id}")]]
        )
        await bot.send_message(chat.id, text, reply_markup=reply_markup)
    except Exception as e:
        await bot.send_message(chat.id ,f"**ERROR:** `{str(e)}`")
        return


@bot.on_message(filters.private & filters.command("restart"))
async def restart(_, msg: Message):
    await msg.reply("Restarted Bot!")
    HU_APP.restart()


@bot.on_message(filters.private & filters.command("help"))
async def restart(_, msg: Message):
    out = f"""
Hi, {msg.from_user.mention}. 
Saya adalah **Bot Generat Session**. Saya akan membantumu mendapat **String Session** dari Telegram. 

Ambil `API_ID` & `API_HASH` dari @scrapidhash_bot \
"""
    reply_markup = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton('ᴜᴘᴅᴀᴛᴇ', url='https://t.me/robotmusicupdate'),
                InlineKeyboardButton('ᴏᴡɴᴇʀ ', url='https://t.me/justthetech')
            ]
        ]
    )
    await msg.reply(out, reply_markup=reply_markup)


async def is_cancel(msg: Message, text: str):
    if text.startswith("/cancel"):
        await msg.reply("Process Cancelled.")
        return True
    return False

if __name__ == "__main__":
    bot.run()
