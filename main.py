import os
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from groq import Groq
from aiohttp import web

# API KALITLAR
TOKEN = "8792863121:AAGDQ_HBjbpXfOkzTUicj6TtPub9OIR54Yw"
GROQ_API_KEY = "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"

client = Groq(api_key=GROQ_API_KEY)
bot = Bot(token=TOKEN)
dp = Dispatcher()

async def handle(request):
    return web.Response(text="Bot is live!")

@dp.message(Command("start"))
async def start_handler(message: types.Message):
    await message.answer("Salom! Men hozir ishga tushdim. Savol bering!")

@dp.message()
async def ai_handler(message: types.Message):
    try:
        # Model nomini soddaroq variantga o'zgartirdik
        response = client.chat.completions.create(
            model="llama3-8b-8192" 
            messages=[{"role": "user", "content": message.text}],
        )
        await message.answer(response.choices[0].message.content)
    except Exception as e:
        # Xatoni aniq ko'rsatish
        await message.answer(f"Xato: {str(e)[:50]}...")

async def main():
    app = web.Application()
    app.router.add_get('/', handle)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', int(os.environ.get("PORT", 8080)))
    await site.start()
    
    # Eski ulanishlarni tozalash
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())






