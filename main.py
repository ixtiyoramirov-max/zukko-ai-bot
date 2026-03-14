import os
import asyncio
import aiohttp
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from groq import Groq
from aiohttp import web

# --- SOZLAMALAR (Environment Variables) ---
BOT_TOKEN = os.environ.get("BOT_TOKEN")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
CHANNELS = ["@zukko_ai_channel"] # Kanalingiz nomini tekshiring

# AI va Botni ishga tushirish
client = Groq(api_key=GROQ_API_KEY)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Foydalanuvchilar xotirasi (Suhbat tarixini saqlash uchun)
user_history = {}

# --- SOXTA SERVER (Render uyg'oq turishi uchun) ---
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
        await message.answer(f"Assalomu alaykum {message.from_user.first_name}! Men Zukko AI botiman. Menga istalgan savolingizni bering.")
    else:
        await message.answer("Botdan foydalanish uchun kanalga a'zo bo'ling:", reply_markup=get_sub_keyboard())

@dp.callback_query(F.data == "check_subs")
async def check_callback(callback: types.CallbackQuery):
    if await check_subscription(callback.from_user.id):
        await callback.message.edit_text("Rahmat! Endi savol yuborishingiz mumkin.")
    else:
        await callback.answer("Siz hali a'zo bo'lmadingiz! ❌", show_alert=True)

# --- AI XABAR ISHLOVCHISI (Xotira bilan) ---
@dp.message()
async def ai_message_handler(message: types.Message):
    # Obunani tekshirish
    if not await check_subscription(message.from_user.id):
        await message.answer("Kanalga a'zo bo'ling!", reply_markup=get_sub_keyboard())
        return

    user_id = message.from_user.id
    
    # Xotirani tayyorlash
    if user_id not in user_history:
        user_history[user_id] = [
            {"role": "system", "content": "Siz aqlli va yordam beruvchi Zukko AI yordamchisisiz. O'zbek tilida javob berasiz."}
        ]

    # Foydalanuvchi xabarini xotiraga qo'shish
    user_history[user_id].append({"role": "user", "content": message.text})

    # Xotirani limitlash (Oxirgi 12 ta xabar: 6 ta savol-javob juftligi)
    if len(user_history[user_id]) > 12:
        user_history[user_id] = [user_history[user_id][0]] + user_history[user_id][-11:]

    # "Yozmoqda..." statusini yuborish
    await bot.send_chat_action(chat_id=message.chat.id, action="typing")

    try:
        completion = client.chat.completions.create(
            messages=user_history[user_id],
            model="llama-3.3-70b-versatile",
        )
        
        ai_response = completion.choices[0].message.content
        
        # AI javobini xotiraga qo'shish
        user_history[user_id].append({"role": "assistant", "content": ai_response})
        
        await message.answer(ai_response, parse_mode="Markdown")
        
    except Exception as e:
        print(f"Xatolik: {e}")
        await message.answer("Kechirasiz, hozirda javob bera olmayman. Birozdan so'ng urinib ko'ring.")

# --- ISHGA TUSHIRISH ---
async def main():
    # Portni ochish
    port = int(os.environ.get("PORT", 10000))
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    
    print(f"Server {port}-portda ishga tushdi")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
