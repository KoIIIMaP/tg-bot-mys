import logging
import random  # ← эта строка была пропущена
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

# Настройка логирования
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Список администраторов (замените на реальные ID)
ADMIN_IDS = [7089719051, 1621555803]  # ← замените на свои ID!

# Хранилище анонимных сообщений
anonymous_messages = []

# Мотивационные фразы по дням недели (0 = понедельник, 6 = воскресенье)
DAILY_MOTIVATION = [
    "☀️ Понедельник — время новых целей! Верьте в себя.",
    "☀️ Вторник — продолжай двигаться вперёд, даже если медленно.",
    "☀️ Среда — половина пути пройдена. Ты справляешься!",
    "☀️ Четверг — почти у цели. Не сдавайся!",
    "☀️ Пятница — ты заслужил отдых. Но сначала — ещё чуть-чуть!",
    "☀️ Суббота — пора расслабиться и насладиться результатами.",
    "☀️ Воскресенье — подумай, чего хочешь на следующей неделе."
]

# Коллекция интересных фактов (добавляйте свои)
FACTS = [
    "🔹 Человек за жизнь проходит около 160 000 км — это как 4 круга вокруг Земли.",
    "🔹 Мозг генерирует больше электрических импульсов, чем все телефоны в мире.",
    "🔹 Сердце бьётся примерно 100 000 раз в день.",
    "🔹 Ногти растут быстрее на доминирующей руке.",
    "🔹 Улыбка задействует 17 мышц, а хмурость — 43.",
    "🔹 У человека около 60 000 мыслей в день.",
    "🔹 Кожа — самый большой орган тела: её площадь ~2 м².",
    "🔹 За всю жизнь человек вырабатывает около 40 000 литров слюны.",
    "🔹 Кости прочнее стали того же веса.",
    "🔹 Глаза воспринимают около 36 000 визуальных сообщений в час."
]

# Словарь терминов (термин: определение + пример)
TERMS = {
    "Прокрастинация": (
        "Откладывание важных дел на потом, несмотря на осознание последствий.\n"
        "Пример: «Я знаю, что надо сдать отчёт сегодня, но сначала посмотрю сериал»."
    ),
    "Эмоциональный интеллект": (
        "Способность распознавать, понимать и управлять своими и чужими эмоциями.\n"
        "Пример: «Он заметил, что коллега расстроен, и тактично предложил помощь»."
    ),
    "Когнитивный диссонанс": (
        "Психологический дискомфорт от противоречия между убеждениями и действиями.\n"
        "Пример: «Курю, хотя знаю, что это вредно для здоровья»."
    ),
    "Ассертивность": (
        "Умение отстаивать свои интересы, не ущемляя права других.\n"
        "Пример: «Я понимаю вашу позицию, но мне важно, чтобы сроки соблюдались»."
    ),
    "Выгорание": (
        "Хроническое истощение из‑за длительного стресса и перегрузки.\n"
        "Пример: «После года без отпуска я перестал радоваться даже хобби»."
    ),
    "Грейс-период": (
        "Льготный срок, в течение которого можно выполнить обязательство без штрафов.\n"
        "Пример: «У кредитной карты есть грейс‑период — 55 дней без процентов»."
    ),
    "Фрод": (
        "Мошенничество в цифровой среде (например, кража данных).\n"
        "Пример: «Фрод‑мониторинг заблокировал подозрительный платёж»."
    ),
    "UX/UI": (
        "UX — удобство использования продукта; UI — визуальное оформление.\n"
        "Пример: «UX‑тестирование показало, что кнопка „Купить“ незаметна»."
    ),
    "Деплой": (
        "Размещение готовой версии программы на сервере.\n"
        "Пример: «После деплоя сайт стал работать быстрее»."
    ),
    "API": (
        "Интерфейс для взаимодействия программ между собой.\n"
        "Пример: «Мы подключили API платёжной системы для онлайн‑оплат»."
    )
}

# Главное меню (для всех)
def get_main_menu(user_id: int):
    keyboard = [
        [InlineKeyboardButton("💬 Анонимное сообщение", callback_data="anon_message")],
        [InlineKeyboardButton("📝 Советы по жизни", callback_data="life_tips")],
        [InlineKeyboardButton("📋 Интересные факты", callback_data="facts")],
        [InlineKeyboardButton("✨ Мотивация дня", callback_data="motivation")],
        [InlineKeyboardButton("📱 Словарик терминов", callback_data="terms")],        
    ]
    # Кнопка для админов
    if user_id in ADMIN_IDS:
        keyboard.append([InlineKeyboardButton("📬 Посмотреть сообщения", callback_data="show_messages")])
    return InlineKeyboardMarkup(keyboard)

# Кнопка «Назад»
def get_back_button():
    return InlineKeyboardMarkup([[InlineKeyboardButton("← Назад", callback_data="main_menu")]])
    
def get_return_menu_button():
    """Возвращает клавиатуру с кнопкой «Вернуться в меню»."""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("← Вернуться в меню", callback_data="main_menu")]
    ])
   
def get_inline_keyboard_with_return():
    """
    Возвращает клавиатуру с двумя кнопками:
    - «Другой термин 🔄» (для нового термина)
    - «← Вернуться в меню» (в главное меню)
    """
    keyboard = [
        [InlineKeyboardButton("Другой термин 🔄", callback_data="terms_next")],
        [InlineKeyboardButton("← Вернуться в меню", callback_data="main_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)
    
# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    await update.message.reply_text(
        "🤗 Добро пожаловать, в бота канала Sun Days! Выберите действие:",
        reply_markup=get_main_menu(user_id)
    )

# Обработчик кнопок
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    if query.data == "main_menu":
        context.user_data.pop("last_term", None)
        await query.edit_message_text(
            text="🌍 Главное меню:",
            reply_markup=get_main_menu(user_id)
        )
    elif query.data == "anon_message":
        await query.edit_message_text(
            text="📝 Напишите ваше анонимное пожелание или вопрос:",
            reply_markup=get_back_button()
        )
        context.user_data["awaiting_anon"] = True
    elif query.data == "life_tips":
        tips = (
            "1. Начинайте день с плана.\n"
            "2. Высыпайтесь (7–9 часов).\n"
            "3. Пейте воду.\n"
            "4. Уделяйте время хобби.\n"
            "5. Общайтесь с близкими."
        )
        await query.edit_message_text(
            text=f"*🔥 Советы по жизни:*\n\n{tips}",
            parse_mode="Markdown",
            reply_markup=get_back_button()
        )
    elif query.data == "facts":
        # Выбираем случайный факт из списка
        fact = random.choice(FACTS)
        await query.edit_message_text(
            text=f"*📜 Интересный факт:*\n\n{fact}",
            parse_mode="Markdown",
            reply_markup=get_back_button()
        )
    elif query.data == "motivation":
        # Берём мотивацию по дню недели
        day_index = datetime.now().weekday()  # 0-6
        motivation = DAILY_MOTIVATION[day_index]
        await query.edit_message_text(
            text=f"*🌟 Мотивация дня:*\n\n{motivation}",
            parse_mode="Markdown",
            reply_markup=get_back_button()
        )
        await query.edit_message_text(
            text=f"⚠️ Мотивация дня:\n\n{motivation}",
            reply_markup=get_back_button()
        )
    elif query.data == "show_messages":
        if user_id not in ADMIN_IDS:
            await query.answer("Доступ запрещён!", show_alert=True)
            return
        if anonymous_messages:
            msg = "\n".join([f"• {m}" for m in anonymous_messages])
        else:
            msg = "📜Пока нет анонимных сообщений."
        await query.edit_message_text(
            text=f"[❗] Анонимные сообщения:\n\n{msg}",
            reply_markup=get_back_button()
        )
    elif query.data == "terms":
        if not TERMS:
            await query.edit_message_text(
                text="*Ошибка:* словарь терминов пуст.",
                parse_mode="Markdown",
                reply_markup=get_return_menu_button()
            )
            return
    
        term, definition = random.choice(list(TERMS.items()))
        message_text = f"*Термин:* {term}\n\n{definition}"
    
        await query.edit_message_text(
            text=message_text,
            parse_mode="Markdown",
            reply_markup=get_inline_keyboard_with_return()  # ← две кнопки
        )
    
    elif query.data == "terms_next":
        if not TERMS:
            await query.edit_message_text(
                text="*Ошибка:* словарь терминов пуст.",
                parse_mode="Markdown",
                reply_markup=get_return_menu_button()
            )
            return
    
        all_terms = list(TERMS.items())
        current_term = context.user_data.get("last_term")
    
        available_terms = [
            item for item in all_terms
            if item[0] != current_term
        ]
    
        if available_terms:
            term, definition = random.choice(available_terms)
        else:
            term, definition = random.choice(all_terms)
    
        context.user_data["last_term"] = term
    
        # Комбинирование: текст + timestamp
        import time
        timestamp = int(time.time() * 1000)
        message_text = f"*Термин:* {term}\n\n{definition}\n\n🕒"
    
        await query.edit_message_text(
            text=message_text,
            parse_mode="Markdown",
            reply_markup=get_inline_keyboard_with_return()
        )



# Обработка текстовых сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if context.user_data.get("awaiting_anon"):
        text = update.message.text
        anonymous_messages.append(text)
        context.user_data["awaiting_anon"] = False
        logger.info(f"[Аноним] от {user_id}: {text}")

        await update.message.reply_text(
            "✔️ ~ Спасибо! Ваше сообщение получено анонимно.",
            reply_markup=get_main_menu(user_id)
        )
    else:
        await update.message.reply_text(
            "👉 Используйте кнопки меню.",
            reply_markup=get_main_menu(user_id)
        )

def main():
    TOKEN = "7992646305:AAGzYvli1lqJl2VFbwLk6Bbu-jlQEEJF108"  # ← замените на токен вашего бота

    application = Application.builder().token(TOKEN).build()

    # Команды
    application.add_handler(CommandHandler("start", start))

    # Обработчики
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    application.run_polling()

if __name__ == "__main__":
    main()
