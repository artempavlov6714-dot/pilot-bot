import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("8924554471:AAEhKhxHcee5X55DutFdffC-LeXOdHCXV1c")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("✈️ Создать пост", callback_data="create")],
        [InlineKeyboardButton("📋 Мои посты", callback_data="posts")],
        [InlineKeyboardButton("💎 Подписка", callback_data="subscribe")],
        [InlineKeyboardButton("🆘 Поддержка", callback_data="support")]
    ]
    await update.message.reply_text(
        "✈️ **PostPilot** — твой пилот в мире контента\n\n"
        "Выбери действие:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == "create":
        await query.edit_message_text("✈️ Функция создания поста скоро будет доступна!")
    elif query.data == "posts":
        await query.edit_message_text("📋 У тебя пока нет постов.")
    elif query.data == "subscribe":
        await query.edit_message_text("💎 Подписка: 29₽/неделя, 49₽/месяц")
    elif query.data == "support":
        await query.edit_message_text("🆘 Напиши в поддержку: @support")

def main():
    if not TOKEN:
        print("❌ Ошибка: TELEGRAM_BOT_TOKEN не найден")
        return
    
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    
    print("🚀 PostPilot запущен!")
    app.run_polling()

if __name__ == "__main__":
    main()
