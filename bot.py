import os
from dotenv import load_dotenv
from groq import Groq
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, filters, ContextTypes

load_dotenv()


TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not TELEGRAM_TOKEN:
    raise ValueError("TELEGRAM_TOKEN not found in .env")

if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY not found in .env")

SYSTEM_PROMPT = """
Sen "Madina Shop" do'konining do'stona savdo yordamchisissan.

Hozircha mahsulotlar ro'yxati yangilanmoqda.

Vazifang:
- Har qanday savol uchun mijozni @M_Abdirashidovna ga yo'nalt
- Kanal: t.me/MADINA_CHIK_2025 (agar kanal bo'lsa)
- Har doim do'stona va qisqa javob ber
- Mijozga tez orada to'liq katalog chiqishini ayt
- Avia kargo naxri 10$
- Avia kargo yetib kelish muddati 7 yoki 10 kun ichida
- Avto kargo 6$ 
- Avto kargo yetib kelish mettadi 15 yoki 20 kun ichida
- Dastafka Toshken shari ichida yandex orqali yetkaziladi 
- Barcha Viloyatlarga BTS bochta orqali junatiladi


Misol javob:
"Hurmatli mijoz Mahsulotlarimiz haqida to'liq ma'lumot uchun @M_Abdirashidovna ga murojaat qiling. Tez orada to'liq katalogimiz ham chiqadi! 😊"
"""

client = Groq(api_key=GROQ_API_KEY)
conversations = {}

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_message = update.message.text

    if user_id not in conversations:
        conversations[user_id] = [{"role": "system", "content": SYSTEM_PROMPT}]

    conversations[user_id].append({"role": "user", "content": user_message})

    if len(conversations[user_id]) > 12:
        conversations[user_id] = [conversations[user_id][0]] + conversations[user_id][-10:]

    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=conversations[user_id],
        max_tokens=500
    )

    assistant_reply = response.choices[0].message.content
    conversations[user_id].append({"role": "assistant", "content": assistant_reply})

    await update.message.reply_text(assistant_reply)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    conversations[user_id] = [{"role": "system", "content": SYSTEM_PROMPT}]

    await update.message.reply_text(
        "👋 Assalomu alaykum! Madina Shop ga xush kelibsiz!\n\n"
        "Men sizning 24/7 savdo yordamchingizman. "
        "Mahsulotlar, narxlar yoki buyurtma haqida "
        "har qanday savolingizni bering! 🛍️"
    )

if __name__ == "__main__":
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("✅ Bot is running with Groq AI (FREE)!")
    app.run_polling()