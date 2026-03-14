import os
import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from groq import Groq
from aiohttp import web  # Port ochish uchun kerak

# --- SOZLAMALAR ---
BOT_TOKEN = "8792863121:AAGDQ_HBjbpXfOkzTUicj6TtPub9OIR54Yw"
GROQ_API_KEY = "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"
CHANNELS = ["@zukko_ai_kanali"] 

# AI va Botni ishga tushirish
client = Groq(api_key=GROQ_API_KEY)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# --- SOXTA SERVER (Render uchun) ---
async def handle(request):
    return web.Response(text="Bot is running!")

app = web.Application()
app.router.add_get("/", handle)

# --- BOT FUNKSIYALARI ---
async def check_subscription(user_id):
    for channel in CHANNELS:
        try:
            member = await bot.get_chat_member(chat_id=channel, user_id=user_id)
            if member.status in ["left", "kicked"]:
                return False
        except Exception:
            return False
    return True

def get_sub_keyboard():
    builder = InlineKeyboardBuilder()
    for channel in CHANNELS:
        builder.row(types.InlineKeyboardButton(text="Kanalga a'zo bo'lish 📢", url=f"https://t.me/{channel.replace('@', '')}"))
    builder.row(types.InlineKeyboardButton(text="Tasdiqlash ✅", callback_data="check_subs"))
    return builder.as_markup()

@dp.message(Command("start"))
async def start_handler(message: types.Message):
    if await check_subscription(message.from_user.id):
        await message.answer(f"Assalomu alaykum! Zukko AI tayyor.")
    else:
        await message.answer("Botdan foydalanish uchun kanalga a'zo bo'ling:", reply_markup=get_sub_keyboard())

@dp.callback_query(F.data == "check_subs")
async def check_callback(callback: types.CallbackQuery):
    if await check_subscription(callback.from_user.id):
        await callback.message.edit_text("Rahmat! Endi savol yuboring.")
    else:
        await callback.answer("Siz hali a'zo bo'lmadingiz! ❌", show_alert=True)

@dp.message()
async def ai_message_handler(message: types.Message):
    if not await check_subscription(message.from_user.id):
        await message.answer("Kanalga a'zo bo'ling!", reply_markup=get_sub_keyboard())
        return
    try:
        completion = client.chat.completions.create(
            messages=[{"role": "user", "content": message.text}],
            model="mixtral-8x7b-32768",
        )
        await message.answer(completion.choices[0].message.content)
    except Exception:
        await message.answer("Xatolik yuz berdi.")

# --- ISHGA TUSHIRISH ---
async def main():
    # Render uchun portni ochish
    port = int(os.environ.get("PORT", 10000))
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    
    print(f"Server {port}-portda ishga tushdi")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
