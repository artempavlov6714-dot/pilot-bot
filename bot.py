import os
import logging
import json
import asyncio
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
from dotenv import load_dotenv
import aiohttp

load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DATA_FILE = "data.json"

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_data(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

async def generate_post(topic: str, style: str, length: str) -> str:
    if not GROQ_API_KEY:
        return "⚠️ API ключ не настроен"
    
    styles = {
        "Деловой": "Напиши деловой пост. Факты, аргументы, структура.",
        "Дружеский": "Напиши дружеский пост. Тепло, просто, по-своему.",
        "Вдохновляющий": "Напиши вдохновляющий пост. Мотивация, драйв, эмоции."
    }
    
    lengths = {
        "Короткий": "3-4 предложения",
        "Средний": "5-7 предложений",
        "Длинный": "8-12 предложений"
    }
    
    prompt = f"""
{styles.get(style, styles["Деловой"])}
Тема: {topic}
Длина: {lengths.get(length, lengths["Средний"])}
Напиши пост для Telegram-канала. Используй эмодзи, где уместно.
"""
    
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "mixtral-8x7b-32768",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 500,
        "temperature": 0.7
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=data) as response:
                if response.status == 200:
                    result = await response.json()
                    return result["choices"][0]["message"]["content"]
                return f"❌ Ошибка API: {response.status}"
    except Exception as e:
        return f"❌ Ошибка: {str(e)}"

async def connect_channel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    chat_id = update.effective_chat.id
    chat = await context.bot.get_chat(chat_id)
    
    if chat.type == "channel":
        data = load_data()
        if user_id not in data:
            data[user_id] = {
                "posts": {},
                "stats": {"posts_used": 0, "images_used": 0},
                "channels": [],
                "subscription": None
            }
        
        if chat_id not in data[user_id]["channels"]:
            data[user_id]["channels"].append(chat_id)
            save_data(data)
            
            await update.message.reply_text(
                f"✅ **Канал подключен!**\n\n📌 Канал: **{chat.title}**\n\n🎉 Теперь ты можешь создавать посты!",
                parse_mode="Markdown"
            )
        else:
            await update.message.reply_text(f"ℹ️ Канал **{chat.title}** уже подключен!", parse_mode="Markdown")
    else:
        await update.message.reply_text(
            "⚠️ **Эта команда работает только в канале!**\n\n"
            "1️⃣ Создай канал\n"
            "2️⃣ Добавь бота в канал как администратора\n"
            "3️⃣ Напиши /connect в этом канале",
            parse_mode="Markdown"
        )

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    data = load_data()
    
    if user_id not in data:
        data[user_id] = {
            "posts": {},
            "stats": {"posts_used": 0, "images_used": 0},
            "channels": [],
            "subscription": None
        }
        save_data(data)
    
    stats = data[user_id]["stats"]
    channels = data[user_id].get("channels", [])
    channels_count = len(channels)
    
    header = f"""
✈️ **PostPilot** — твой пилот в мире контента

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 **Моя статистика**

• Посты: {stats.get('posts_used', 0)} / 3 использовано
• Картинки: {stats.get('images_used', 0)} / 2 использовано
• Тариф: 🔓 Бесплатный
• Каналов: {channels_count} / 1{' ✅' if channels_count > 0 else ''}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
    
    if channels_count == 0:
        text = header + """
⚠️ **Для работы бота необходимо подключить канал!**

[🔗 Подключить канал]   [💎 Подписка]
[🆘 Поддержка]
"""
        keyboard = [
            [InlineKeyboardButton("🔗 Подключить канал", callback_data="connect")],
            [InlineKeyboardButton("💎 Подписка", callback_data="subscription")],
            [InlineKeyboardButton("🆘 Поддержка", callback_data="support")]
        ]
    else:
        text = header + """
👇 **Выбери действие:**

[✈️ Создать пост]   [📋 Мои посты]
[💎 Подписка]       [🆘 Поддержка]
"""
        keyboard = [
            [InlineKeyboardButton("✈️ Создать пост", callback_data="create_post")],
            [InlineKeyboardButton("📋 Мои посты", callback_data="my_posts")],
            [InlineKeyboardButton("💎 Подписка", callback_data="subscription")],
            [InlineKeyboardButton("🆘 Поддержка", callback_data="support")]
        ]
    
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = str(update.effective_user.id)
    data = load_data()
    action = query.data
    
    if user_id not in data:
        data[user_id] = {
            "posts": {},
            "stats": {"posts_used": 0, "images_used": 0},
            "channels": [],
            "subscription": None
        }
        save_data(data)
    
    if action == "connect":
        text = """
🔗 **Подключение канала — ОБЯЗАТЕЛЬНЫЙ ШАГ**

1️⃣ **Создай канал** в Telegram
2️⃣ **Добавь бота в канал** как администратора
3️⃣ **Напиши /connect в канале**
4️⃣ **Вернись сюда** и нажми "Проверить"
"""
        keyboard = [
            [InlineKeyboardButton("🔄 Проверить подключение", callback_data="check_connect")],
            [InlineKeyboardButton("🔙 Назад", callback_data="menu")]
        ]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
        return
    
    if action == "check_connect":
        channels = data[user_id].get("channels", [])
        if channels:
            text = "✅ **Канал подключен!**\n\n🎉 Теперь ты можешь создавать посты!"
            keyboard = [
                [InlineKeyboardButton("✈️ Создать пост", callback_data="create_post")],
                [InlineKeyboardButton("🔙 В меню", callback_data="menu")]
            ]
        else:
            text = "⚠️ **Канал не подключен!**\n\nДобавь бота в канал и напиши /connect"
            keyboard = [
                [InlineKeyboardButton("🔄 Проверить снова", callback_data="check_connect")],
                [InlineKeyboardButton("🔙 Назад", callback_data="menu")]
            ]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
        return
    
    if action == "create_post":
        channels = data[user_id].get("channels", [])
        if not channels:
            text = "⛔ **Доступ запрещён!**\n\nДля создания постов необходимо подключить канал."
            keyboard = [
                [InlineKeyboardButton("🔗 Подключить канал", callback_data="connect")],
                [InlineKeyboardButton("🔙 Назад", callback_data="menu")]
            ]
            await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
            return
        
        context.user_data["step"] = "style"
        text = """
✈️ **Новый пост** — Шаг 1 из 2

🎨 **Выбери стиль текста:**

[💼 Деловой]   [🤝 Дружеский]   [✨ Вдохновляющий]

📝 **Теперь напиши тему поста:**
"""
        keyboard = [
            [InlineKeyboardButton("💼 Деловой", callback_data="style_Деловой")],
            [InlineKeyboardButton("🤝 Дружеский", callback_data="style_Дружеский")],
            [InlineKeyboardButton("✨ Вдохновляющий", callback_data="style_Вдохновляющий")],
            [InlineKeyboardButton("🔙 Отмена", callback_data="menu")]
        ]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
        return
    
    if action.startswith("style_"):
        style = action.replace("style_", "")
        context.user_data["style"] = style
        context.user_data["step"] = "topic"
        
        text = f"""
✈️ **Новый пост** — Шаг 1 из 2

✅ Стиль выбран: **{style}**

📝 **Напиши тему поста:**
"""
        keyboard = [[InlineKeyboardButton("🔙 Отмена", callback_data="menu")]]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
        return
    
    if action == "my_posts":
        posts = data[user_id].get("posts", {})
        if not posts:
            text = "📭 У тебя пока нет постов."
            keyboard = [[InlineKeyboardButton("✈️ Создать пост", callback_data="create_post")]]
            await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
            return
        
        text = "📋 **Твои посты:**\n\n"
        for i, (post_id, post) in enumerate(posts.items(), 1):
            status = "✅ Активен" if post.get("active", True) else "⏸️ Приостановлен"
            text += f"{i}. {post.get('topic', 'Без темы')[:30]} | {post.get('time', '12:00')} | {status}\n"
        
        keyboard = [
            [InlineKeyboardButton("✈️ Новый пост", callback_data="create_post")],
            [InlineKeyboardButton("🔙 Назад", callback_data="menu")]
        ]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
        return
    
    if action == "subscription":
        text = """
💎 **Подписка**

Твой тариф: 🔓 **Бесплатный**

💰 **Выбери период:**

[🟢 Неделя 29 ₽]   [🔵 Месяц 49 ₽]
[🟣 3 месяца 119 ₽]   [🟡 Год 399 ₽]
"""
        keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="menu")]]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
        return
    
    if action == "support":
        text = """
🆘 **Поддержка**

Не нашли ответ?

[📝 Написать в поддержку]
"""
        keyboard = [
            [InlineKeyboardButton("📝 Написать в поддержку", callback_data="write_support")],
            [InlineKeyboardButton("🔙 Назад", callback_data="menu")]
        ]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
        return
    
    if action == "write_support":
        context.user_data["step"] = "support_message"
        text = "📩 Введи текст сообщения:"
        keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="support")]]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
        return
    
    if action == "menu":
        await start(update, context)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    text = update.message.text
    step = context.user_data.get("step")
    data = load_data()
    
    if step == "topic":
        context.user_data["topic"] = text
        context.user_data["step"] = "image"
        
        keyboard = [
            [InlineKeyboardButton("✅ Да, добавить — 1/2", callback_data="image_yes")],
            [InlineKeyboardButton("❌ Нет, только текст — 0/2", callback_data="image_no")]
        ]
        
        await update.message.reply_text(
            f"""
✈️ **Новый пост** — Шаг 2 из 2

📝 Тема: "{text}"
🎨 Стиль: {context.user_data.get('style', 'Деловой')}

🖼️ **Добавить картинку?**

[✅ Да, добавить — 1/2]
[❌ Нет, только текст — 0/2]
""",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        return
    
    if step == "support_message":
        if "support_messages" not in data:
            data["support_messages"] = []
        data["support_messages"].append({
            "user_id": user_id,
            "message": text,
            "date": datetime.now().isoformat()
        })
        save_data(data)
        context.user_data["step"] = None
        
        await update.message.reply_text(
            "✅ **Сообщение отправлено!**\n\nСвяжемся с тобой в ближайшее время! 🤝",
            parse_mode="Markdown"
        )
        return
    
    await update.message.reply_text("⚠️ Сначала нажми кнопку в меню!")

def main():
    if not TOKEN:
        print("❌ Ошибка: TELEGRAM_BOT_TOKEN не найден в .env")
        return
    
    application = Application.builder().token(TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("connect", connect_channel))
    application.add_handler(CallbackQueryHandler(button_callback))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("🚀 PostPilot запущен!")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
