import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from groq import Groq

# ========================================================
# 1. SOZLAMALAR (BU YERGA O'ZINGNI KODLARINGNI QO'Y)
# ========================================================
GROQ_API_KEY = "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" 
TELEGRAM_TOKEN = "8792863121:AAGDQ_HBjbpXfOkzTUicj6TtPub9OIR54Yw"

# Xatolarni kuzatish uchun loglar
logging.basicConfig(level=logging.INFO)

# Obyektlarni yaratish
client = Groq(api_key=GROQ_API_KEY)
bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher()

# ========================================================
# 2. START BUYRUG'I (BOT ISHGA TUSHGANDA)
# ========================================================
@dp.message(Command("start"))
async def start_handler(message: types.Message):
    user_name = message.from_user.first_name
    await message.answer(
        f"Assalomu alaykum, {user_name}! 👋\n\n"
        "Men sening **Zukko AI** repetitoringman. "
        "Istalgan fan bo'yicha savolingni berishing mumkin. "
        "Men darslarni tushuntirishga harakat qilaman! 📚"
    )

# ========================================================
# 3. ASOSIY AI MANTIQ (SAVOL-JAVOB VA LIMITLAR)
# ========================================================
@dp.message()
async def ai_message_handler(message: types.Message):
    # Bot "yozmoqda..." holatida ko'rinadi
    await bot.send_chat_action(chat_id=message.chat.id, action="typing")
    
    try:
        # Groq AI'ga murojaat (Yangi va kuchli model)
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system", 
                    "content": (
                        "Sen professional o'zbek tili repetitorisan. "
                        "Faqat adabiy o'zbek tilida, imlo xatolarisiz javob ber. "
                        "H va X harflarini to'g'ri ishlat. Javoblaringni "
                        "emoji va qalin harflar bilan chiroyli formatla."
                    )
                },
                {"role": "user", "content": message.text},
            ],
            temperature=0.7,
            max_tokens=2048
        )
        
        # AI javobini olish
        ai_response = completion.choices[0].message.content
        
        # Javobni foydalanuvchiga yuborish
        await message.answer(ai_response, parse_mode="Markdown")

    except Exception as e:
        error_msg = str(e).lower()
        logging.error(f"Xatolik: {e}")

        # LIMIT TUGAGANDA OGOHLANTIRISH
        if "rate_limit_reached" in error_msg or "429" in error_msg:
            await message.answer(
                "⚠️ **DIQQAT: Limit tugadi!**\n\n"
                "Hozir savollar juda ko'p. Men biroz dam olishim kerak. "
                "Iltimos, **1-2 daqiqadan so'ng** qayta yozib ko'ring. 😊"
            )
        else:
            await message.answer("😔 Kechirasiz, ulanishda xato bo'ldi. Birozdan so'ng urinib ko'ring.")

# ========================================================
# 4. BOTNI YURGIZISH
# ========================================================
async def main():
    print("Zukko AI repetitoringiz ishga tushdi! ✅")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("Bot to'xtatildi! 🛑")
import os
from aiohttp import web

async def handle(request):
    return web.Response(text="Bot is running!")

app = web.Application()
app.router.add_get('/', handle)

if __name__ == "__main__":
    # Botni ishga tushirish bilan birga kichik veb-serverni ham yoqamiz
    import asyncio
    port = int(os.environ.get("PORT", 8080))
    runner = web.AppRunner(app)
    
    async def main():
        await runner.setup()
        site = web.TCPSite(runner, '0.0.0.0', port)
        await site.start()
        await dp.start_polling(bot)

    asyncio.run(main())
