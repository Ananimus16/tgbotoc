import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

QUIZ_DATA = [
    {
        "question": "Вопрос №1: Какой город является столицей Италии?",
        "options": ["Рим", "Москва", "Берлин", "Лондон"],
        "correct_option_id": 0
    },
    {
        "question": "Вопрос №2: Кто изобрел лампочку?",
        "options": ["Томас Эдисон", "Альберт Эйнштейн", "Никола Тесла", "Илон Маск"],
        "correct_option_id": 0
    },
    {
        "question": "Вопрос №3: Самый глубокий океан Земли называется...",
        "options": ["Атлантический", "Северный Ледовитый", "Тихий", "Индийский"],
        "correct_option_id": 2
    },
]


SELECTING_ACTION, ANSWERING_QUIZ = range(2)



async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Начало разговора."""
    reply_markup = InlineKeyboardMarkup([
        [InlineKeyboardButton(text="Начать викторину", callback_data="start_quiz")]
    ])
    await update.message.reply_text("Добро пожаловать в нашу викторину!\n\n"
                                    "Хотите проверить свои знания?\n"
                                    "Нажмите 'Начать викторину'.", reply_markup=reply_markup)
    return SELECTING_ACTION



async def handle_start_quiz(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Начинаем викторину."""
    # Инициализируем состояние викторины
    context.user_data['current_question'] = 0
    context.user_data['score'] = 0

    return await show_question(update, context)



async def show_question(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Показать вопрос с вариантами ответов."""
    current_question_index = context.user_data['current_question']
    question_data = QUIZ_DATA[current_question_index]

    buttons = []
    for i, option in enumerate(question_data["options"]):
        button = InlineKeyboardButton(option, callback_data=f"answer_{i}")
        buttons.append([button])

    reply_markup = InlineKeyboardMarkup(buttons)

    if update.callback_query:
        await update.callback_query.edit_message_text(question_data["question"], reply_markup=reply_markup)
    else:
        await update.message.reply_text(question_data["question"], reply_markup=reply_markup)

    return ANSWERING_QUIZ



async def handle_answer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int | None:
    """Обработка ответа пользователя."""
    data = update.callback_query.data
    selected_option_id = int(data.split("_")[1])  # Получаем выбранный индекс варианта

    current_question_index = context.user_data['current_question']
    question_data = QUIZ_DATA[current_question_index]

    # Проверяем правильность ответа
    is_correct = question_data['correct_option_id'] == selected_option_id

    if is_correct:
        context.user_data['score'] += 1
        message = "Правильно!"
    else:
        correct_answer = question_data["options"][question_data["correct_option_id"]]
        message = f"Неправильно! Правильный ответ: {correct_answer}"

    await update.callback_query.answer(message)

    # Переходим к следующему вопросу или завершаем викторину
    context.user_data['current_question'] += 1

    if context.user_data['current_question'] < len(QUIZ_DATA):
        # Показываем следующий вопрос
        return await show_question(update, context)
    else:
        # Завершаем викторину
        score = context.user_data['score']
        total = len(QUIZ_DATA)

        # Предлагаем начать заново
        reply_markup = InlineKeyboardMarkup([
            [InlineKeyboardButton(text="Начать заново", callback_data="start_quiz")]
        ])

        await update.callback_query.edit_message_text(
            f"Викторина закончена!\n"
            f"Ваш результат: {score}/{total}\n\n"
            f"Спасибо за участие!",
            reply_markup=reply_markup
        )

        # Очищаем данные пользователя
        context.user_data.clear()
        return SELECTING_ACTION



async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Завершаем разговор."""
    context.user_data.clear()
    await update.message.reply_text("До свидания! Возвращайтесь снова.")
    return ConversationHandler.END


def main() -> None:
    application = ApplicationBuilder().token("Your Token").build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            SELECTING_ACTION: [
                CallbackQueryHandler(handle_start_quiz, pattern=r'^start_quiz$'),
            ],
            ANSWERING_QUIZ: [
                CallbackQueryHandler(handle_answer, pattern=r'^answer_\d+$'),
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        allow_reentry=True  # Разрешаем перезапуск
    )

    application.add_handler(conv_handler)
    application.run_polling()


if __name__ == "__main__":

    main()
