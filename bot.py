import os
import uuid
import json
import zipfile
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    CallbackQueryHandler,
    ContextTypes,
)
from config import BOT_TOKEN, CHANNEL_ID

# Настройка логирования
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# Проверка подписки на канал
async def check_subscription(user_id, context):
    try:
        # Проверяем статус пользователя в канале
        chat_member = await context.bot.get_chat_member(CHANNEL_ID, user_id)
        is_subscribed = chat_member.status in ["member", "administrator", "creator"]
        logger.info(f"Пользователь {user_id} подписан на канал: {is_subscribed}")
        return is_subscribed
    except Exception as e:
        logger.error(f"Ошибка при проверке подписки: {e}")
        return False

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    logger.info(f"Пользователь {user_id} отправил команду /start")

    if not await check_subscription(user_id, context):
        # Если пользователь не подписан, отправляем кнопку для подписки
        keyboard = [[InlineKeyboardButton("Подписаться", url=f"https://t.me/{CHANNEL_ID[1:]}")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "Привет! Я телеграм-бот для создания скинов с руками зомби.\n"
            "Сначала необходимо подписаться на телеграм-канал, чтобы я работал.",
            reply_markup=reply_markup,
        )
    else:
        # Если пользователь подписан, предлагаем отправить скин
        await update.message.reply_text("Отлично! Отправьте мне ваш скин в формате .png.")

# Обработка сообщений с изображениями
async def handle_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if not await check_subscription(user_id, context):
        # Если пользователь не подписан, напоминаем подписаться
        await update.message.reply_text("Вы не подписаны на канал. Подпишитесь, чтобы продолжить.")
        return

    file = await update.message.photo[-1].get_file()
    file_extension = os.path.splitext(file.file_path)[-1].lower()

    if file_extension != ".png":
        # Если файл не в формате .png, отправляем сообщение об ошибке
        await update.message.reply_text(
            "Ошибка! Данный формат мною не поддерживается. Пожалуйста, отправьте скин в формате .png."
        )
        return

    # Создание папки для пользователя
    user_folder = f"lskinbot_{user_id}"
    os.makedirs(user_folder, exist_ok=True)

    # Сохранение изображения
    skin_path = os.path.join(user_folder, "zombie.png")
    logger.info(f"Сохранение файла: {skin_path}")
    await file.download_to_drive(custom_path=skin_path)

    # Генерация manifest.json
    manifest_data = {
        "format_version": 2,
        "header": {
            "name": "Create/Создано: @LSkinZombieBot",
            "description": "By Sent:y",
            "uuid": str(uuid.uuid4()),
            "version": [1, 0, 0],
        },
        "modules": [
            {
                "type": "skin_pack",
                "uuid": str(uuid.uuid4()),
                "version": [1, 0, 0],
            }
        ],
        "metadata": {
            "authors": ["Senty"],
        },
    }
    manifest_path = os.path.join(user_folder, "manifest.json")
    with open(manifest_path, "w") as f:
        json.dump(manifest_data, f, indent=4)

    # Генерация skins.json
    skins_data = {
        "skins": [
            {
                "localization_name": "skin1",
                "geometry": "geometry.humanoid.custom",
                "texture": "zombie.png",
                "animations": {
                    "move.arms": "animation.player.move.arms.zombie",
                    "attack.rotations": "animation.player.holding.zombie",
                    "holding": "animation.zombie.attack_bare_hand",
                },
                "type": "free",
            }
        ],
        "serialize_name": "Create/Создано: @LSkinZombieBot",
        "localization_name": "Create/Создано: @LSkinZombieBot",
    }
    skins_path = os.path.join(user_folder, "skins.json")
    with open(skins_path, "w") as f:
        json.dump(skins_data, f, indent=4)

    # Архивация в .zip
    zip_path = os.path.join(user_folder, "lskinbot.zip")
    with zipfile.ZipFile(zip_path, "w") as zipf:
        zipf.write(manifest_path, arcname="manifest.json")
        zipf.write(skins_path, arcname="skins.json")
        zipf.write(skin_path, arcname="zombie.png")

    # Переименование в .mcpack
    mcpack_path = os.path.join(user_folder, "lskinbot.mcpack")
    os.rename(zip_path, mcpack_path)

    # Отправка файла пользователю
    with open(mcpack_path, "rb") as f:
        await update.message.reply_document(
            document=f,
            caption="Ваш файл готов! Нажмите кнопку ниже, если хотите создать ещё.",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("Хотите создать ещё?", callback_data="create_another")]]
            ),
        )

# Обработка callback-запросов
async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "create_another":
        # Если пользователь хочет создать ещё один скин
        await query.message.reply_text("Отлично! Отправьте мне ваш скин в формате .png.")

# Основная функция
if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Регистрация обработчиков
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.PHOTO, handle_image))
    app.add_handler(CallbackQueryHandler(handle_callback))

    # Запуск бота
    app.run_polling()