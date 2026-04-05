import os
from dotenv import load_dotenv
from groq import Groq
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    ApplicationBuilder, MessageHandler, CommandHandler,
    CallbackQueryHandler, filters, ContextTypes
)

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
ADMIN_ID = int(os.getenv("ADMIN_ID"))  # ← Replace with your Telegram ID from @userinfobot

client = Groq(api_key=GROQ_API_KEY)

# ============================================================
# EXAMPLE PRODUCTS (replace with real ones later)
# ============================================================
PRODUCTS = {
    "dresses": [
        {"name": "Luna Dress", "price": "$45", "sizes": "S/M/L", "colors": "Black, White", "desc": "Beautiful summer dress"},
        {"name": "Rose Dress", "price": "$55", "sizes": "M/L/XL", "colors": "Red, Pink", "desc": "Elegant evening dress"},
    ],
    "tshirts": [
        {"name": "Basic Tee", "price": "$20", "sizes": "S/M/L/XL", "colors": "White, Black, Grey", "desc": "Comfortable everyday t-shirt"},
        {"name": "Floral Tee", "price": "$25", "sizes": "S/M/L", "colors": "Pink, Yellow", "desc": "Pretty floral print t-shirt"},
    ],
    "pants": [
        {"name": "Classic Pants", "price": "$40", "sizes": "S/M/L", "colors": "Black, Beige", "desc": "Stylish everyday pants"},
        {"name": "Jeans", "price": "$50", "sizes": "S/M/L/XL", "colors": "Blue, Dark Blue", "desc": "Comfortable slim jeans"},
    ],
    "skirts": [
        {"name": "Mini Skirt", "price": "$30", "sizes": "S/M/L", "colors": "Black, White", "desc": "Trendy mini skirt"},
        {"name": "Maxi Skirt", "price": "$38", "sizes": "S/M/L", "colors": "Floral", "desc": "Flowing maxi skirt"},
    ],
    "sale": [
        {"name": "Summer Dress SALE", "price": "~~$60~~ $35", "sizes": "S/M", "colors": "Yellow", "desc": "Last pieces! Hurry!"},
        {"name": "Jacket SALE", "price": "~~$80~~ $50", "sizes": "M/L", "colors": "Brown", "desc": "Winter jacket on sale"},
    ],
}

# ============================================================
# MAIN MENU
# ============================================================
def main_menu_keyboard():
    keyboard = [
        ["🛍 New Collection", "👗 Categories"],
        ["🔥 Sale", "🛒 My Cart"],
        ["📦 My Orders", "📞 Contact Admin"],
        ["⭐ Reviews", "🎁 Discounts"]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def categories_keyboard():
    keyboard = [
        [InlineKeyboardButton("👗 Dresses", callback_data="cat_dresses"),
         InlineKeyboardButton("👕 T-Shirts", callback_data="cat_tshirts")],
        [InlineKeyboardButton("👖 Pants", callback_data="cat_pants"),
         InlineKeyboardButton("🩱 Skirts", callback_data="cat_skirts")],
        [InlineKeyboardButton("🔙 Back", callback_data="back_main")]
    ]
    return InlineKeyboardMarkup(keyboard)

def product_keyboard(category, index):
    total = len(PRODUCTS[category])
    buttons = []

    nav = []
    if index > 0:
        nav.append(InlineKeyboardButton("⬅️ Prev", callback_data=f"prod_{category}_{index-1}"))
    if index < total - 1:
        nav.append(InlineKeyboardButton("Next ➡️", callback_data=f"prod_{category}_{index+1}"))
    if nav:
        buttons.append(nav)

    buttons.append([
        InlineKeyboardButton("🛒 Add to Cart", callback_data="add_cart"),
        InlineKeyboardButton("📞 Ask Admin", callback_data="ask_admin")
    ])
    buttons.append([InlineKeyboardButton("🔙 Back to Categories", callback_data="back_categories")])

    return InlineKeyboardMarkup(buttons)

# ============================================================
# HANDLERS
# ============================================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.effective_user.first_name
    await update.message.reply_text(
        f"👋 Assalomu alaykum, {name}!\n\n"
        f"🌸 *Madina Shop* ga xush kelibsiz!\n\n"
        f"Biz ayollar kiyimlari bo'yicha eng yaxshi tanlovni taqdim etamiz.\n"
        f"Quyidagi menyudan tanlang 👇",
        parse_mode="Markdown",
        reply_markup=main_menu_keyboard()
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if text == "👗 Categories":
        await update.message.reply_text(
            "👗 *Kategoriyalardan birini tanlang:*",
            parse_mode="Markdown",
            reply_markup=categories_keyboard()
        )

    elif text == "🛍 New Collection":
        await update.message.reply_text(
            "✨ *Yangi kolleksiya!*\n\n"
            "Eng yangi kiyimlarimiz bilan tanishing!\n"
            "Kategoriyalar bo'limiga o'ting 👇",
            parse_mode="Markdown",
            reply_markup=categories_keyboard()
        )

    elif text == "🔥 Sale":
        products = PRODUCTS["sale"]
        for p in products:
            await update.message.reply_text(
                f"🔥 *{p['name']}*\n\n"
                f"💰 Narx: {p['price']}\n"
                f"📏 O'lchamlar: {p['sizes']}\n"
                f"🎨 Ranglar: {p['colors']}\n\n"
                f"📝 {p['desc']}\n\n"
                f"Buyurtma uchun: @M_Abdirashidovna",
                parse_mode="Markdown"
            )

    elif text == "🛒 My Cart":
        await update.message.reply_text(
            "🛒 *Savatingiz*\n\n"
            "Hozircha savatcha bo'sh.\n"
            "Mahsulot qo'shish uchun kategoriyalarga o'ting!",
            parse_mode="Markdown"
        )

    elif text == "📦 My Orders":
        await update.message.reply_text(
            "📦 *Mening buyurtmalarim*\n\n"
            "Hozircha buyurtmalar yo'q.\n"
            "Buyurtma berish uchun mahsulot tanlang!",
            parse_mode="Markdown"
        )

    elif text == "📞 Contact Admin":
        await update.message.reply_text(
            "📞 *Admin bilan bog'laning*\n\n"
            "👤 Admin: @M_Abdirashidovna\n\n"
            "Ish vaqti: 09:00 - 21:00\n"
            "Savollar, buyurtmalar va takliflar uchun yozing!",
            parse_mode="Markdown"
        )

    elif text == "⭐ Reviews":
        await update.message.reply_text(
            "⭐ *Mijozlar fikrlari*\n\n"
            "❤️ Dilnoza: 'Juda chiroyli ko'ylak, tez yetkazildi!'\n"
            "❤️ Malika: 'Sifat zo'r, narx ham qulay!'\n"
            "❤️ Zulfiya: 'Har doim bu do'kondan xarid qilaman!'\n\n"
            "Siz ham fikr qoldiring: @M_Abdirashidovna",
            parse_mode="Markdown"
        )

    elif text == "🎁 Discounts":
        await update.message.reply_text(
            "🎁 *Chegirmalar va aksiyalar*\n\n"
            "🔥 Hozirgi aksiya:\n"
            "2 ta mahsulot olsangiz — 10% chegirma!\n\n"
            "🎀 Promo kod: *MADINA10*\n\n"
            "Buyurtma berishda admin ga yuboring: @M_Abdirashidovna",
            parse_mode="Markdown"
        )

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "back_main":
        await query.message.reply_text(
            "🏠 Asosiy menyu:",
            reply_markup=main_menu_keyboard()
        )

    elif data == "back_categories":
        await query.message.reply_text(
            "👗 Kategoriyalardan birini tanlang:",
            reply_markup=categories_keyboard()
        )

    elif data.startswith("cat_"):
        category = data.replace("cat_", "")
        await show_product(query, category, 0)

    elif data.startswith("prod_"):
        _, category, index = data.split("_")
        await show_product(query, category, int(index))

    elif data == "add_cart":
        await query.message.reply_text(
            "🛒 Mahsulot savatchaga qo'shildi!\n\n"
            "Buyurtma berish uchun: @M_Abdirashidovna"
        )

    elif data == "ask_admin":
        await query.message.reply_text(
            "📞 Admin: @M_Abdirashidovna\n"
            "Savol yoki buyurtma uchun yozing!"
        )

async def show_product(query, category, index):
    products = PRODUCTS[category]
    p = products[index]
    total = len(products)

    cat_names = {
        "dresses": "👗 Ko'ylaklar",
        "tshirts": "👕 Futbolkalar",
        "pants": "👖 Shimlar",
        "skirts": "🩱 Yubkalar",
        "sale": "🔥 Sale"
    }

    text = (
        f"{cat_names.get(category, category)} — {index+1}/{total}\n\n"
        f"👗 *{p['name']}*\n\n"
        f"💰 Narx: {p['price']}\n"
        f"📏 O'lchamlar: {p['sizes']}\n"
        f"🎨 Ranglar: {p['colors']}\n\n"
        f"📝 {p['desc']}"
    )

    await query.message.reply_text(
        text,
        parse_mode="Markdown",
        reply_markup=product_keyboard(category, index)
    )

# ============================================================
# ADMIN COMMANDS
# ============================================================
async def admin_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    await update.message.reply_text(f"📊 Bot ishlayapti!\n👥 Foydalanuvchilar: faol")

async def admin_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    message = " ".join(context.args)
    if not message:
        await update.message.reply_text("Usage: /broadcast Your message")
        return
    await update.message.reply_text(f"✅ Xabar yuborildi: {message}")

# ============================================================
# MAIN
# ============================================================
if __name__ == "__main__":
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stats", admin_stats))
    app.add_handler(CommandHandler("broadcast", admin_broadcast))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("✅ Madina Shop Bot is running!")
    app.run_polling()