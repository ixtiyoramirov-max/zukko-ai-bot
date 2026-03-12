
import os
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from groq import Groq
from aiohttp import web


TOKEN = "8792863121:AAGDQ_HBjbpXfOkzTUicj6TtPub90IR54Yw"
GROQ_API_KEY = "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"


client = Groq(api_key=GROQ_API_KEY)
bot = Bot(token=TOKEN)
dp = Dispatcher()


async def handle(request):
return web.Response(text="Bot is live!")

@dp.message(Command("start"))
async def start_handler(message: types.Message):
await message.answer("Salom! Men Zukko AI repetitorman. Savolingizni bering! 🚀")

@dp.message()
async def ai_handler(message: types.Message):
try:
# Eng barqaror model nomi: llama3-8b-8192
response = client.chat.completions.create(
model="llama3-8b-8192",
messages=[
{"role": "system", "content": "Siz zukko AI repetitorsiz. O'zbek tilida javob bering."},
{"role": "user", "content": message.text}
]
)
await message.answer(response.choices[0].message.content)
except Exception as e:
print(f"Xato: {e}")
await message.answer("Hozircha javob bera olmayman, texnik xato.")

async def main():
# Veb-serverni Render portiga moslash
app = web.Application()
app.router.add_get('/', handle)
runner = web.AppRunner(app)
await runner.setup()
port = int(os.environ.get("PORT", 8080))
site = web.TCPSite(runner, '0.0.0.0', port)
await site.start()

if name == "main":
asyncio.run(main())



