import os
import re
from dotenv import load_dotenv
from groq import Groq
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, MessageHandler, CommandHandler, filters, ContextTypes
)

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

client = Groq(api_key=GROQ_API_KEY)

# ============================================================
# MESSAGES
# ============================================================

MESSAGES = {
    "uz": {
        "photo_received": (
            "✅ Mahsulot rasmi qabul qilindi!\n\n"
            "Buyurtmani rasmiylashtirish uchun quyidagi ma'lumotlarni ketma-ket kiriting:\n\n"
            "👤 Ismingizni to'liq kiriting (masalan: Akmal Jabborov):"
        ),
        "ask_phone": "📞 Telefon raqamingizni kiriting:\nMisol: +998901234567 yoki 901234567",
        "ask_location": "📍 Yetkazib berish manzilingizni kiriting (shahar, tuman, ko'cha):",
        "ask_username": "📱 Telegram username'ingizni kiriting (@ bilan) yoki 'yo'q' deb yozing:",

        "invalid_name": "❌ Ism noto'g'ri! Faqat harflar va bo'shliq bo'lishi kerak. Qayta kiriting:",
        "invalid_phone": "❌ Telefon raqam noto'g'ri!\nFaqat raqamlar yozing (masalan: +998901234567 yoki 901234567).\nQayta kiriting:",
        "invalid_username": "❌ Username noto'g'ri! @ bilan boshlanishi kerak yoki 'yo'q' deb yozing. Qayta kiriting:",

        "confirm": (
            "📋 Buyurtmangizni tekshiring:\n\n"
            "👤 Ism: {name}\n"
            "📞 Telefon: {phone}\n"
            "📍 Manzil: {location}\n"
            "📱 Username: {username}\n\n"
            "Hammasi to'g'rimi? **Ha** yoki **Yo'q** deb javob bering."
        ),
        "order_accepted": "✅ Buyurtma qabul qilindi!\nAdmin tez orada siz bilan bog'lanadi. Rahmat! 🌸",
        "order_cancelled": "❌ Buyurtma bekor qilindi.\nYangi buyurtma uchun mahsulot rasmini yuboring.",
        "already_in_order": "⚠️ Siz allaqachon buyurtma jarayonidasiz.\nBekor qilish uchun /start yoki 'cancel' deb yozing.",
        "restarted": "🔄 Barcha ma'lumotlar tozalandi.\nYangi buyurtma uchun mahsulot rasmini yuboring."
    }
}

def detect_language(text: str) -> str:
    if not text:
        return "uz"
    text_lower = text.lower()
    if any(c in "абвгдеёжзийклмнопрстуфхцчшщъыьэюя" for c in text_lower):
        return "ru"
    if any(w in text_lower for w in ["salom", "rahmat", "iltimos", "kerak", "yo'q", "ha"]):
        return "uz"
    return "en" if any(w in text_lower for w in ["hello", "hi", "order"]) else "uz"

# ====================== BETTER VALIDATION ======================
def is_valid_phone(phone: str) -> bool:
    """Accepts almost any Uzbek phone format, ignores letters"""
    # Remove everything except digits
    cleaned = re.sub(r'\D', '', phone)
    # Must have between 9 and 13 digits
    return 9 <= len(cleaned) <= 13

def is_valid_name(name: str) -> bool:
    cleaned = name.strip()
    return len(cleaned) >= 2 and all(c.isalpha() or c.isspace() for c in cleaned)

def is_valid_username(username: str) -> bool:
    u = username.strip().lower()
    if u in ["yo'q", "yoq", "нет", "none", "no", "yok"]:
        return True
    return username.strip().startswith("@") and len(username.strip()) >= 3

def get_ai_prompt(lang: str) -> str:
    return f"""You are a sales assistant for Madina Shop.

Rules:
- Always reply in {lang} language.
- Be short and polite.
- DO NOT say hello, hi, salom, assalomu alaykum in every message.
- Only greet ONCE if the user greets first.
- If the user asks a question, answer directly without greeting.
- If you don't know something, say:
  "Kechirasiz, bu haqida ma'lumotim yo'q. Iltimos admin bilan bog'laning: @M_Abdirashidovna"
- Channel: t.me/MADINA_CHIK_2025
- Your job is to help customers and help them order products.
- If user wants to order → tell them to send product photo.
- Be very short. Max 2 sentences.
"""

# ============================================================
# HANDLERS
# ============================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    lang = detect_language(update.message.text or "")
    context.user_data["lang"] = lang
    await update.message.reply_text(
        "👋 Assalomu alaykum!\n\n"
        "Buyurtma berish uchun kanaldan mahsulot rasmini va tavsifini yuboring."
    )

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """New photo always starts fresh order"""
    lang = detect_language(update.message.caption or "")
    context.user_data.clear()
    context.user_data["lang"] = lang
    context.user_data["state"] = "name"
    context.user_data["photo_id"] = update.message.photo[-1].file_id
    context.user_data["caption"] = update.message.caption or "Tavsif yo'q"

    await update.message.reply_text(MESSAGES["uz"]["photo_received"])

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    state = context.user_data.get("state")
    lang = context.user_data.get("lang", "uz")
    msgs = MESSAGES.get(lang, MESSAGES["uz"])

    # Restart / Cancel
    if text.lower() in ["/start", "restart", "cancel", "bekor", "отмена", "tozalash"]:
        context.user_data.clear()
        context.user_data["lang"] = lang
        await update.message.reply_text(msgs["restarted"])
        return

    # ==================== ORDER FLOW ====================
    if state == "name":
        if not is_valid_name(text):
            await update.message.reply_text(msgs["invalid_name"])
            return
        context.user_data["order_name"] = text
        context.user_data["state"] = "phone"
        await update.message.reply_text(msgs["ask_phone"])
        return

    if state == "phone":
        if not is_valid_phone(text):
            await update.message.reply_text(msgs["invalid_phone"])
            return
        context.user_data["order_phone"] = text
        context.user_data["state"] = "location"
        await update.message.reply_text(msgs["ask_location"])
        return

    if state == "location":
        if len(text.strip()) < 5:
            await update.message.reply_text("❌ Manzil juda qisqa. Aniqroq yozing:")
            return
        context.user_data["order_location"] = text
        context.user_data["state"] = "username"
        await update.message.reply_text(msgs["ask_username"])
        return

    if state == "username":
        if not is_valid_username(text):
            await update.message.reply_text(msgs["invalid_username"])
            return
        context.user_data["order_username"] = text
        context.user_data["state"] = "confirm"

        confirm_text = msgs["confirm"].format(
            name=context.user_data.get("order_name", ""),
            phone=context.user_data.get("order_phone", ""),
            location=context.user_data.get("order_location", ""),
            username=text
        )
        await update.message.reply_text(confirm_text)
        return

    if state == "confirm":
        if text.lower() in ["ha", "да", "yes", "ok", "tasdiqlash"]:
            await send_order_to_admin(update, context)
            context.user_data.clear()
        else:
            context.user_data.clear()
            await update.message.reply_text(msgs["order_cancelled"])
        return

    # If still in order flow but no matching state
    if state is not None:
        await update.message.reply_text(msgs["already_in_order"])
        return

    # General questions - AI
    await context.bot.send_chat_action(update.effective_chat.id, "typing")
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": get_ai_prompt(lang)},
                {"role": "user", "content": text}
            ],
            max_tokens=250,
            temperature=0.5
        )
        await update.message.reply_text(response.choices[0].message.content)
    except Exception:
        await update.message.reply_text("Iltimos, @M_Abdirashidovna ga murojaat qiling.")

async def send_order_to_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(MESSAGES["uz"]["order_accepted"])

    admin_text = (
        f"🛍 *YANGI BUYURTMA!*\n\n"
        f"👤 Ism: {context.user_data.get('order_name', '—')}\n"
        f"📞 Telefon: {context.user_data.get('order_phone', '—')}\n"
        f"📍 Manzil: {context.user_data.get('order_location', '—')}\n"
        f"📱 Username: {context.user_data.get('order_username', '—')}\n\n"
        f"📦 Mahsulot tavsifi:\n{context.user_data.get('caption', '—')}"
    )

    if context.user_data.get("photo_id"):
        await context.bot.send_photo(
            chat_id=ADMIN_ID,
            photo=context.user_data["photo_id"],
            caption=admin_text,
            parse_mode="Markdown"
        )

# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("✅ Madina Shop Bot is running!")
    app.run_polling()