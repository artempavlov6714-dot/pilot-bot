import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, CallbackContext

TOKEN = "8924554471:AAEhKhxHcee5X55DutFdffC-LeX0dHCXV1c"

logging.basicConfig(level=logging.INFO)

def start(update: Update, context: CallbackContext):
    keyboard = [
        [InlineKeyboardButton("✈️ Создать пост", callback_data="create")],
        [InlineKeyboardButton("📋 Мои посты", callback_data="posts")],
        [InlineKeyboardButton("💎 Подписка", callback_data="subscribe")],
        [InlineKeyboardButton("🆘 Поддержка", callback_data="support")]
    ]
    update.message.reply_text(
        "✈️ **PostPilot** — твой пилот в мире контента\n\n👇 Выбери действие:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

def button_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    
    if query.data == "create":
        query.edit_message_text("✈️ Функция создания поста скоро будет доступна!")
    elif query.data == "posts":
        query.edit_message_text("📋 У тебя пока нет постов.")
    elif query.data == "subscribe":
        query.edit_message_text("💎 Подписка: 29₽/неделя, 49₽/месяц")
    elif query.data == "support":
        query.edit_message_text("🆘 Напиши в поддержку: @support")

def main():
    if not TOKEN:
        print("❌ Ошибка: TOKEN не найден")
        return
    
    updater = Updater(token=TOKEN, use_context=True)
    dp = updater.dispatcher
    
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CallbackQueryHandler(button_handler))
    
    print("🚀 PostPilot запущен!")
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
