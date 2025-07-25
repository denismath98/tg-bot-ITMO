import json
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    ConversationHandler,
)

# === СТАДИИ ===
SELECT_PROGRAM, ASK_BACKGROUND = range(2)

# === Загрузка данных из JSON ===
with open("data.json", "r", encoding="utf-8") as f:
    program_data = json.load(f)

# === Доступные программы ===
available_programs = {
    "ai": program_data  # пока только одна программа
}

# === Состояние пользователя ===
user_state = {}

# === Команды ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [["AI"]]  # пока только одна программа
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text(
        "Привет! Я помогу тебе выбрать подходящую магистратуру в ИТМО.\n\nВыбери направление:",
        reply_markup=reply_markup
    )
    return SELECT_PROGRAM

async def select_program(update: Update, context: ContextTypes.DEFAULT_TYPE):
    choice = update.message.text.strip().lower()
    if "ai" in choice:
        program_key = "ai"
    else:
        await update.message.reply_text("Пожалуйста, выбери одну из программ: AI.")
        return SELECT_PROGRAM

    user_state[update.effective_user.id] = {"program": program_key}
    await update.message.reply_text("Отлично! А теперь опиши, пожалуйста, свой бэкграунд или интересы:")
    return ASK_BACKGROUND

async def ask_background(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text.lower()

    # Ограничение: не отвечать на нерелевантные вопросы
    if any(word in text for word in ["время", "погода", "новости"]):
        await update.message.reply_text("Я могу ответить только на вопросы, связанные с обучением в магистратуре ИТМО.")
        return ASK_BACKGROUND

    program_key = user_state[user_id]["program"]
    program = available_programs[program_key]
    title = program["name"]

    # Собираем все выборные дисциплины из учебного плана
    electives = []
    for key, value in program["учебный план"].items():
        if "выборных" in key.lower():
            electives.extend(value)

    # Убираем лишние пробелы
    electives = [course.strip() for course in electives if course.strip()]

    # Простая фильтрация по ключевым словам
    keywords_ml = ["ml", "машин", "data", "данн", "обучен", "deep", "врем"]
    keywords_nlp = ["язык", "текст", "nlp", "lingu"]
    keywords_cv = ["vision", "зрен", "изображен", "cv"]
    keywords_dev = ["backend", "dev", "разраб", "python", "инж", "с++", "програм", "проект"]
    keywords_biz = ["продукт", "бизнес", "ux", "pm", "product", "менедж"]

    recommended = []

    def match_keywords(keywords):
        return [course for course in electives if any(k in course.lower() for k in keywords)]

    recommended.extend(match_keywords(keywords_ml))
    recommended.extend(match_keywords(keywords_nlp))
    recommended.extend(match_keywords(keywords_cv))
    recommended.extend(match_keywords(keywords_dev))
    recommended.extend(match_keywords(keywords_biz))

    # Если ничего не подошло — выводим случайные дисциплины
    if not recommended:
        recommended = electives[:10]

    # Убираем дубликаты
    recommended = list(dict.fromkeys(recommended))

    await update.message.reply_text(
        f"На основе твоих интересов в программе *{title}* рекомендуем изучить выборные дисциплины:\n"
        + "\n".join(f"• {course}" for course in recommended[:15]),
        parse_mode='Markdown'
    )
    await update.message.reply_text("Если хочешь попробовать снова — напиши /start.")
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Диалог завершён. Напиши /start, чтобы начать заново.")
    return ConversationHandler.END

# === Запуск бота ===
def main():
    app = ApplicationBuilder().token("8019370531:AAHYnHQbEj3GXZoln7EwEoiTn4CPBH_T41g").build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            SELECT_PROGRAM: [MessageHandler(filters.TEXT & ~filters.COMMAND, select_program)],
            ASK_BACKGROUND: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_background)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(conv_handler)
    print("Бот запущен. Ожидает пользователей...")
    app.run_polling()

if __name__ == "__main__":
    main()

