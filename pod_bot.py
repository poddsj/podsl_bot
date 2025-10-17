import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.error import NetworkError

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Конфигурация
BOT_TOKEN = "7830781446:AAFWfIU1dt5_LIgqEWT6JWuYvr0RZmCH4A8"
CHANNEL_ID = "@podolsk14"
ADMIN_IDS = [6428177555, 6059441879, 2094730348]  # Замени на реальные ID администраторов


async def start(update: Update, _: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    user = update.effective_user
    welcome_text = f"""
👋 Привет, {user.first_name}!

🤫 Этот бот предназначен для анонимной отправки сообщений в канал.

📨 Просто отправь сюда любое сообщение (текст, фото, видео, документ), и оно будет переслано в канал анонимно.
    """
    await update.message.reply_text(welcome_text)


async def help_command(update: Update, _: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /help"""
    help_text = """
📖 Справка по использованию бота:

• Отправь текстовое сообщение - оно будет переслано в канал
• Отправь фото/видео/документ - медиафайл будет переслан в канал
• Все сообщения отправляются анонимно

❓ Если возникли проблемы - свяжись с администратором.
    """
    await update.message.reply_text(help_text)


async def notify_admins_about_message(context: ContextTypes.DEFAULT_TYPE, user_info: str, message_type: str,
                                      content: str = None, file_id: str = None, caption: str = None):
    """Уведомление администраторов о полученном сообщении"""

    if message_type == "text":
        admin_message = f"""
💬 Получено новое сообщение от пользователя:

{user_info}

📄 Текст: {content}
        """
        for admin_id in ADMIN_IDS:
            try:
                await context.bot.send_message(
                    chat_id=admin_id,
                    text=admin_message
                )
            except Exception as e:
                logger.error(f"Не удалось отправить уведомление администратору {admin_id}: {e}")

    elif message_type == "photo":
        admin_message = f"""
📸 Получено новое фото от пользователя:

{user_info}

📝 Подпись: {caption if caption else "нет подписи"}
        """
        for admin_id in ADMIN_IDS:
            try:
                if caption:
                    await context.bot.send_photo(
                        chat_id=admin_id,
                        photo=file_id,
                        caption=admin_message
                    )
                else:
                    await context.bot.send_photo(
                        chat_id=admin_id,
                        photo=file_id
                    )
                    await context.bot.send_message(
                        chat_id=admin_id,
                        text=admin_message
                    )
            except Exception as e:
                logger.error(f"Не удалось отправить уведомление администратору {admin_id}: {e}")

    elif message_type == "video":
        admin_message = f"""
🎥 Получено новое видео от пользователя:

{user_info}

📝 Подпись: {caption if caption else "нет подписи"}
        """
        for admin_id in ADMIN_IDS:
            try:
                if caption:
                    await context.bot.send_video(
                        chat_id=admin_id,
                        video=file_id,
                        caption=admin_message
                    )
                else:
                    await context.bot.send_video(
                        chat_id=admin_id,
                        video=file_id
                    )
                    await context.bot.send_message(
                        chat_id=admin_id,
                        text=admin_message
                    )
            except Exception as e:
                logger.error(f"Не удалось отправить уведомление администратору {admin_id}: {e}")

    elif message_type == "document":
        admin_message = f"""
📎 Получен новый документ от пользователя:

{user_info}

📝 Подпись: {caption if caption else "нет подписи"}
📄 Имя файла: {content}
        """
        for admin_id in ADMIN_IDS:
            try:
                if caption:
                    await context.bot.send_document(
                        chat_id=admin_id,
                        document=file_id,
                        caption=admin_message
                    )
                else:
                    await context.bot.send_document(
                        chat_id=admin_id,
                        document=file_id
                    )
                    await context.bot.send_message(
                        chat_id=admin_id,
                        text=admin_message
                    )
            except Exception as e:
                logger.error(f"Не удалось отправить уведомление администратору {admin_id}: {e}")

    elif message_type == "audio":
        admin_message = f"""
🎵 Получено новое аудио от пользователя:

{user_info}

📝 Подпись: {caption if caption else "нет подписи"}
        """
        for admin_id in ADMIN_IDS:
            try:
                if caption:
                    await context.bot.send_audio(
                        chat_id=admin_id,
                        audio=file_id,
                        caption=admin_message
                    )
                else:
                    await context.bot.send_audio(
                        chat_id=admin_id,
                        audio=file_id
                    )
                    await context.bot.send_message(
                        chat_id=admin_id,
                        text=admin_message
                    )
            except Exception as e:
                logger.error(f"Не удалось отправить уведомление администратору {admin_id}: {e}")

    elif message_type == "voice":
        admin_message = f"""
🎤 Получено новое голосовое сообщение от пользователя:

{user_info}
        """
        for admin_id in ADMIN_IDS:
            try:
                await context.bot.send_voice(
                    chat_id=admin_id,
                    voice=file_id
                )
                await context.bot.send_message(
                    chat_id=admin_id,
                    text=admin_message
                )
            except Exception as e:
                logger.error(f"Не удалось отправить уведомление администратору {admin_id}: {e}")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик всех входящих сообщений"""
    user_id = update.effective_user.id
    message = update.message
    user = update.effective_user

    # Формируем информацию об отправителе
    user_info = f"""
👤 ID: {user_id}
📛 Имя: {user.first_name or 'Не указано'}
🔖 Фамилия: {user.last_name or 'Не указана'}
🔗 Username: @{user.username if user.username else 'Не указан'}
    """

    try:
        # Обработка текстовых сообщений
        if message.text:
            # Анонимно в канал
            await context.bot.send_message(
                chat_id=CHANNEL_ID,
                text=message.text
            )

            # Уведомление администраторов
            await notify_admins_about_message(
                context=context,
                user_info=user_info,
                message_type="text",
                content=message.text
            )

        # Обработка фото
        elif message.photo:
            # Анонимно в канал
            await context.bot.send_photo(
                chat_id=CHANNEL_ID,
                photo=message.photo[-1].file_id,
                caption=message.caption
            )

            # Уведомление администраторов
            await notify_admins_about_message(
                context=context,
                user_info=user_info,
                message_type="photo",
                file_id=message.photo[-1].file_id,
                caption=message.caption
            )

        # Обработка видео
        elif message.video:
            await context.bot.send_video(
                chat_id=CHANNEL_ID,
                video=message.video.file_id,
                caption=message.caption
            )

            # Уведомление администраторов
            await notify_admins_about_message(
                context=context,
                user_info=user_info,
                message_type="video",
                file_id=message.video.file_id,
                caption=message.caption
            )

        # Обработка документов
        elif message.document:
            await context.bot.send_document(
                chat_id=CHANNEL_ID,
                document=message.document.file_id,
                caption=message.caption
            )

            # Уведомление администраторов
            await notify_admins_about_message(
                context=context,
                user_info=user_info,
                message_type="document",
                content=message.document.file_name,
                file_id=message.document.file_id,
                caption=message.caption
            )

        # Обработка аудио
        elif message.audio:
            await context.bot.send_audio(
                chat_id=CHANNEL_ID,
                audio=message.audio.file_id,
                caption=message.caption
            )

            # Уведомление администраторов
            await notify_admins_about_message(
                context=context,
                user_info=user_info,
                message_type="audio",
                file_id=message.audio.file_id,
                caption=message.caption
            )

        # Обработка голосовых сообщений
        elif message.voice:
            await context.bot.send_voice(
                chat_id=CHANNEL_ID,
                voice=message.voice.file_id
            )

            # Уведомление администраторов
            await notify_admins_about_message(
                context=context,
                user_info=user_info,
                message_type="voice",
                file_id=message.voice.file_id
            )

        else:
            await message.reply_text("❌ Этот тип сообщения не поддерживается.")
            return

        # Подтверждение пользователю
        await message.reply_text("✅ Сообщение успешно отправлено анонимно!")

    except NetworkError as e:
        logger.error(f"Ошибка сети: {e}")
        await message.reply_text("❌ Проблемы с интернет-соединением. Попробуйте позже.")
    except Exception as e:
        logger.error(f"Ошибка при пересылке сообщения: {e}")
        await message.reply_text("❌ Произошла ошибка при отправке сообщения.")


async def admin_stats(update: Update, _: ContextTypes.DEFAULT_TYPE):
    """Команда для администраторов чтобы проверить работу бота"""
    user_id = update.effective_user.id

    if user_id not in ADMIN_IDS:
        await update.message.reply_text("❌ Эта команда только для администраторов.")
        return

    stats_text = f"""
👑 Панель администратора

🤖 Бот работает корректно
👥 Администраторов: {len(ADMIN_IDS)}
📊 ID администраторов: {', '.join(map(str, ADMIN_IDS))}
    """

    await update.message.reply_text(stats_text)


def main():
    """Основная функция запуска бота"""
    application = Application.builder().token(BOT_TOKEN).build()

    # Добавляем обработчики
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("admin", admin_stats))
    application.add_handler(MessageHandler(filters.ALL, handle_message))

    # Запускаем бота
    print("🤖 Бот запущен...")
    print(f"👥 Администраторы: {ADMIN_IDS}")
    print(f"📢 Канал: {CHANNEL_ID}")
    application.run_polling()


if __name__ == "__main__":
    main()