import os
import asyncio
import aiohttp
import asyncpg
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from groq import Groq
from aiohttp import web
import json

# --- SOZLAMALAR ---
BOT_TOKEN = os.environ.get("BOT_TOKEN")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
DATABASE_URL = os.environ.get("DATABASE_URL")
CHANNELS = ["@zukko_ai_channel"] # Kanal manzilingizni tekshiring

# AI va Botni ishga tushirish
client = Groq(api_key=GROQ_API_KEY)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
db_pool = None # Bazaga ulanish hovuzi

# --- MA'LUMOTLAR BAZASI BILAN ISHLASH ---
async def init_db():
    global db_pool
    db_pool = await asyncpg.create_pool(DATABASE_URL)
    async with db_pool.acquire() as conn:
        # Foydalanuvchilar va ularning suhbat tarixini saqlash uchun jadval yaratish
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id BIGINT PRIMARY KEY,
                first_name TEXT,
                history JSONB DEFAULT '[]'
            )
        ''')
        print("Ma'lumotlar bazasi tayyor.")

async def get_user_data(user_id):
    async with db_pool.acquire() as conn:
        row = await conn.fetchrow('SELECT first_name, history FROM users WHERE user_id = $1', user_id)
        if row:
            return row['first_name'], json.loads(row['history'])
        return None, []

async def set_user_data(user_id, first_name, history):
    async with db_pool.acquire() as conn:
        history_json = json.dumps(history)
        await conn.execute('''
            INSERT INTO users (user_id, first_name, history)
            VALUES ($1, $2, $3)
            ON CONFLICT (user_id) DO UPDATE
            SET first_name = $2, history = $3
        ''', user_id, first_name, history_json)

# --- RENDER UCHUN PORT VA SERVER ---
async def handle(request):
    return web.Response(text="Bot is running!")

app = web.Application()
app.router.add_get("/", handle)

# --- OBUNANI TEKSHIRISH ---
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

# --- COMMAND HANDLERS ---
@dp.message(Command("start"))
async def start_handler(message: types.Message):
    if await check_subscription(message.from_user.id):
        # Bazadan foydalanuvchini tekshirish
        first_name, _ = await get_user_data(message.from_user.id)
        if not first_name:
            # Yangi foydalanuvchini bazaga qo'shish
            await set_user_data(message.from_user.id, message.from_user.first_name, [])
            await message.answer(f"Xush kelibsiz {message.from_user.first_name}! Men Zukko AI botiman. Rasm chizish uchun '/rasm [mavzu]' deb yozing yoki istalgan savolingizni bering.")
        else:
            await message.answer(f"Qayta xush kelibsiz {first_name}! Savolingizni bering.")
    else:
        await message.answer("Botdan foydalanish uchun kanalga a'zo bo'ling:", reply_markup=get_sub_keyboard())

@dp.callback_query(F.data == "check_subs")
async def check_callback(callback: types.CallbackQuery):
    if await check_subscription(callback.from_user.id):
        await callback.message.edit_text("Rahmat! Endi savol yuborishingiz mumkin.")
    else:
        await callback.answer("Siz hali a'zo bo'lmadingiz! ❌", show_alert=True)

# --- RASM CHIZISH FUNKSIYASI ---
@dp.message(Command("rasm"))
async def draw_image_handler(message: types.Message):
    # Obunani tekshirish
    if not await check_subscription(message.from_user.id):
        await message.answer("Botdan foydalanish uchun kanalga a'zo bo'ling!", reply_markup=get_sub_keyboard())
        return

    # Promptni olish
    prompt = message.text.replace("/rasm ", "").strip()
    if not prompt:
        await message.answer("Rasm chizish uchun mavzu bering. Masalan: '/rasm kosmosda uchayotgan mushuk'.")
        return

    # "Rasm chizilmoqda..." statusini yuborish
    await bot.send_chat_action(chat_id=message.chat.id, action="upload_photo")

    try:
        # Promptni ingliz tiliga yaqinlashtirish va xavfsiz formatga keltirish
        import urllib.parse
        safe_prompt = urllib.parse.quote(prompt)
        
        # Yangilangan ishonchli URL format
        image_url = f"https://image.pollinations.ai/prompt/{safe_prompt}?width=1024&height=1024&nologo=true"
        
        await message.answer_photo(photo=image_url, caption=f"Siz so'ragan rasm: '{prompt}'")
        
        
        
        await message.answer_photo(photo=image_url, caption=f"Siz so'ragan rasm: '{prompt}'")
        
    except Exception as e:
        print(f"Rasm chizishda xatolik: {e}")
        await message.answer(f"⚠️ Xato: Rasm chizib bo'lmadi. (Tafsilot: {e})")

# --- ASOSIY AI MANTIQI (Xotira va Baza bilan) ---
@dp.message()
async def ai_message_handler(message: types.Message):
    # 1. Obunani tekshirish
    if not await check_subscription(message.from_user.id):
        await message.answer("Botdan foydalanish uchun kanalga a'zo bo'ling!", reply_markup=get_sub_keyboard())
        return

    user_id = message.from_user.id
    
    # 2. Bazadan foydalanuvchi ma'lumotlarini olish
    first_name, user_history_list = await get_user_data(user_id)
    if not first_name:
        first_name = message.from_user.first_name
        user_history_list = []

    # 3. Xotirani shakllantirish (Doimiy xotira)
    if not user_history_list:
        user_history_list = [
            {"role": "system", "content": f"Siz Zukko AI yordamchisisiz. Foydalanuvchining ismi {first_name}. O'zbek tilida aniq va aqlli javob berasiz."}
        ]

    # Foydalanuvchi xabarini qo'shish
    user_history_list.append({"role": "user", "content": message.text})

    # 4. Xotirani limitlash (12 ta xabar)
    if len(user_history_list) > 12:
        user_history_list = [user_history_list[0]] + user_history_list[-11:]

    # 5. Typing status yuborish
    await bot.send_chat_action(chat_id=message.chat.id, action="typing")

    # 6. Groq AI ga so'rov yuborish
    try:
        completion = client.chat.completions.create(
            messages=user_history_list,
            model="llama-3.3-70b-versatile",
        )
        
        ai_response = completion.choices[0].message.content
        
        # Javobni xotiraga saqlash
        user_history_list.append({"role": "assistant", "content": ai_response})
        
        # 7. Yangilangan xotirani bazaga saqlash
        await set_user_data(user_id, first_name, user_history_list)
        
        # Javobni yuborish
        await message.answer(ai_response, parse_mode="Markdown")
        
    except Exception as e:
        print(f"Xatolik yuz berdi: {e}")
        await message.answer(f"⚠️ Xato: AI bilan bog'lanib bo'lmadi. (Tafsilot: {e})")

# --- ISHGA TUSHIRISH ---
async def main():
    # 1. Ma'lumotlar bazasini ishga tushirish
    await init_db()

    # 2. Render porti
    port = int(os.environ.get("PORT", 10000))
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    
    print(f"Server {port}-portda ishlamoqda...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
