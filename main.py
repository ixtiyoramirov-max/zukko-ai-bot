import os
import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from groq import Groq

# --- SOZLAMALAR ---
BOT_TOKEN = "8792863121:AAGDQ_HBjbpXfOkzTUicj6TtPub9OIR54Yw"
GROQ_API_KEY = "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"
CHANNELS = ["@zukko_ai_channel"]  # Kanalingiz username'ini @ bilan yozing

# AI va Botni ishga tushirish
client = Groq(api_key=GROQ_API_KEY)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# --- FUNKSIYALAR ---

# Obunani tekshirish funksiyasi
async def check_subscription(user_id):
    for channel in CHANNELS:
        try:
            member = await bot.get_chat_member(chat_id=channel, user_id=user_id)
            if member.status in ["left", "kicked"]:
                return False
        except Exception as e:
            print(f"Xatolik yuz berdi: {e}")
            return False
    return True

# Obuna tugmalarini yasash
def get_sub_keyboard():
    builder = InlineKeyboardBuilder()
    for channel in CHANNELS:
        builder.row(types.InlineKeyboardButton(
            text="Kanalga a'zo bo'lish 📢", 
            url=f"https://t.me/{channel.replace('@', '')}")
        )
    builder.row(types.InlineKeyboardButton(
        text="Tasdiqlash ✅", 
        callback_data="check_subs")
    )
    return builder.as_markup()

# --- HANDLERLAR ---

# /start komandasi
@dp.message(Command("start"))
async def start_handler(message: types.Message):
    is_sub = await check_subscription(message.from_user.id)
    if is_sub:
        await message.answer(f"Assalomu alaykum {message.from_user.full_name}! Zukko AI yordamga tayyor. Savolingizni yozishingiz mumkin.")
    else:
        await message.answer(
            "Botdan foydalanish uchun quyidagi kanalimizga obuna bo'ling:",
            reply_markup=get_sub_keyboard()
        )

# Tasdiqlash tugmasi bosilganda
@dp.callback_query(F.data == "check_subs")
async def check_callback(callback: types.CallbackQuery):
    is_sub = await check_subscription(callback.from_user.id)
    if is_sub:
        await callback.message.edit_text("Rahmat! Endi savolingizni yuborishingiz mumkin.")
    else:
        await callback.answer("Siz hali a'zo bo'lmadingiz! ❌", show_alert=True)

# AI bilan muloqot qismi
@dp.message()
async def ai_message_handler(message: types.Message):
    # Avval obunani tekshiramiz
    is_sub = await check_subscription(message.from_user.id)
    if not is_sub:
        await message.answer("Botdan foydalanish uchun kanalga a'zo bo'ling!", reply_markup=get_sub_keyboard())
        return

    # Agar obuna bo'lgan bo'lsa, AI ga yuboramiz
    try:
        chat_completion = client.chat.completions.create(
            messages=[{"role": "user", "content": message.text}],
            model="mixtral-8x7b-32768", # Yoki boshqa model
        )
        await message.answer(chat_completion.choices[0].message.content)
    except Exception as e:
        await message.answer("Kechirasiz, AI bilan bog'lanishda xatolik yuz berdi.")
        print(e)

# --- ASOSIY ISHGA TUSHIRISH ---
async def main():
    print("Bot ishga tushdi...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
