import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from config import BOT_TOKEN, CHANNEL_ID

# Настройка логирования
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    logger.info(f"Пользователь {user_id} отправил команду /start")

    # Проверка подписки на канал
    try:
        chat_member = await context.bot.get_chat_member(CHANNEL_ID, user_id)
        if chat_member.status in ["member", "administrator", "creator"]:
            await update.message.reply_text("Привет! Я работаю!")
        else:
            await update.message.reply_text(
                "Сначала подпишитесь на канал, чтобы я работал!"
            )
    except Exception as e:
        logger.error(f"Ошибка при проверке подписки: {e}")
        await update.message.reply_text("Произошла ошибка при проверке подписки.")

# Основной блок
if __name__ == "__main__":
    # Логирование запуска бота
    logger.info("Запуск бота...")
    logger.info(f"BOT_TOKEN: {BOT_TOKEN}")
    logger.info(f"CHANNEL_ID: {CHANNEL_ID}")

    # Создание приложения
    try:
        app = ApplicationBuilder().token(BOT_TOKEN).build()
        logger.info("Бот успешно инициализирован.")
    except Exception as e:
        logger.error(f"Ошибка инициализации бота: {e}")
        exit(1)

    # Регистрация обработчиков
    app.add_handler(CommandHandler("start", start))

    # Запуск бота
    try:
        logger.info("Запуск polling...")
        app.run_polling()
    except Exception as e:
        logger.error(f"Ошибка при запуске polling: {e}")