import os
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from groq import Groq
from aiohttp import web

# API KALITLAR (O'zgaruvchilardan oladi)
TOKEN = "8792863121:AAGDQ_HBjbpXfOkzTUicj6TtPub90IR54Yw"
GROQ_API_KEY = "gsk_4Jr2tIFODIMX8z8ZSYoVW Gdyb3FYmccbei8cgbx0i8CR3L7iCLLn"

client = Groq(api_key=GROQ_API_KEY)
bot = Bot(token=TOKEN)
dp = Dispatcher()

# RENDER UCHUN ODDIY VEB-SERVER (BOTNI "LIVE" SAQLASH UCHUN)
async def handle(request):
    return web.Response(text="Bot is live and running!")

async def start_web_server():
    app = web.Application()
    app.router.add_get('/', handle)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 8080))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()

@dp.message(Command("start"))
async def start_handler(message: types.Message):
    await message.answer("Salom! Men Zukko AI repetitorman. Qanday yordam bera olaman?")

@dp.message()
async def ai_handler(message: types.Message):
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": "Siz zukko AI repetitorsiz. O'zbek tilida javob bering."},
            {"role": "user", "content": message.text},
        ],
    )
    await message.answer(response.choices[0].message.content)

async def main():
    # Veb-serverni va botni bir vaqtda ishga tushiramiz
    await start_web_server()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

