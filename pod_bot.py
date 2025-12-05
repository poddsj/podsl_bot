import logging
import time
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
from telegram.error import NetworkError
from collections import defaultdict

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Конфигурация
BOT_TOKEN = "your_token"
CHANNEL_ID = "your_tgc"
ADMIN_IDS = [id_admins]  # Замени на реальные ID администраторов

user_last_message_time = {}  # Для ограничения частоты отправки
private_conversations = {}  # Для хранения приватных диалогов {user_id: message_id}
user_message_history = defaultdict(list)  # История сообщений пользователя админу


async def start(update: Update, _: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    user = update.effective_user
    welcome_text = f"""
👋 Привет, {user.first_name}!

🤫 Этот бот предназначен для:
1. Анонимной отправки сообщений в канал (раз в 30 секунд)
2. Приватной переписки с администраторами

📨 Отправь любое сообщение (текст, фото, видео, документ) - и оно будет переслано в канал анонимно.

💬 Или используй команду /message для приватного обращения к администраторам.
    """
    await update.message.reply_text(welcome_text)


async def help_command(update: Update, _: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /help"""
    help_text = """
📖 Справка по использованию бота:

🕐 **Анонимные сообщения в канал:**
• Просто отправь текстовое сообщение или медиафайл
• Ограничение: 1 сообщение в 30 секунд
• Все сообщения отправляются анонимно

💬 **Приватная переписка с администраторами:**
• Используй команду /message
• Напиши сообщение после команды
• Администраторы смогут ответить тебе лично

❓ Если возникли проблемы - свяжись с администратором.
    """
    await update.message.reply_text(help_text)


async def message_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /message для приватных сообщений админам"""
    user = update.effective_user
    user_id = user.id

    if not context.args:
        await update.message.reply_text(
            "💬 Напиши сообщение для администраторов после команды:\n"
            "Пример: /message Привет, у меня вопрос по работе бота"
        )
        return

    message_text = ' '.join(context.args)

    # Формируем информацию об отправителе
    user_info = f"""
👤 Новое приватное сообщение от пользователя:
ID: {user_id}
Имя: {user.first_name or 'Не указано'}
Фамилия: {user.last_name or 'Не указана'}
Username: @{user.username if user.username else 'Не указан'}
    """

    # Создаем клавиатуру для ответа
    keyboard = [
        [InlineKeyboardButton("📨 Ответить", callback_data=f"reply_{user_id}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Отправляем всем администраторам
    message_sent = False
    for admin_id in ADMIN_IDS:
        try:
            sent_message = await context.bot.send_message(
                chat_id=admin_id,
                text=f"{user_info}\n\n📩 Сообщение: {message_text}",
                reply_markup=reply_markup
            )

            # Сохраняем связь для ответа
            private_conversations[f"{admin_id}_{sent_message.message_id}"] = {
                "user_id": user_id,
                "message_text": message_text
            }

            message_sent = True
        except Exception as e:
            logger.error(f"Не удалось отправить сообщение администратору {admin_id}: {e}")

    if message_sent:
        # Сохраняем в историю только если отправка удалась
        user_message_history[user_id].append({
            "to_admin": True,
            "text": message_text,
            "time": time.time()
        })
        await update.message.reply_text("✅ Ваше сообщение отправлено администраторам. Они ответят вам лично.")
    else:
        await update.message.reply_text("❌ Не удалось отправить сообщение. Попробуйте позже.")


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик нажатий на кнопки"""
    query = update.callback_query
    await query.answer()

    user_id = update.effective_user.id

    # Проверяем, что нажал администратор
    if user_id not in ADMIN_IDS:
        await query.edit_message_text("❌ Эта функция только для администраторов.")
        return

    callback_data = query.data

    if callback_data.startswith("reply_"):
        target_user_id = int(callback_data.split("_")[1])

        # Сохраняем ID пользователя для ответа в контексте
        context.user_data["replying_to"] = target_user_id

        await query.edit_message_text(
            f"✍️ Теперь отправьте текст ответа для пользователя {target_user_id}.\n"
            f"Любое ваше следующее текстовое сообщение будет отправлено ему."
        )


async def admin_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик ответов администраторов"""
    user_id = update.effective_user.id

    # Проверяем, что сообщение от администратора
    if user_id not in ADMIN_IDS:
        return

    # Проверяем, отвечает ли администратор кому-то
    if "replying_to" not in context.user_data:
        return

    target_user_id = context.user_data["replying_to"]
    admin_message = update.message.text

    try:
        # Отправляем сообщение пользователю
        await context.bot.send_message(
            chat_id=target_user_id,
            text=f"📨 Ответ от администратора:\n\n{admin_message}\n\n"
                 f"Вы можете продолжить диалог снова использовав команду /message"
        )

        # Сохраняем в историю
        user_message_history[target_user_id].append({
            "to_admin": False,
            "text": admin_message,
            "time": time.time(),
            "admin_id": user_id
        })

        await update.message.reply_text(f"✅ Ответ отправлен пользователю {target_user_id}")

        # Очищаем контекст
        del context.user_data["replying_to"]

    except Exception as e:
        logger.error(f"Не удалось отправить ответ пользователю {target_user_id}: {e}")
        await update.message.reply_text(f"❌ Не удалось отправить ответ: {e}")


async def notify_admins_about_message(context: ContextTypes.DEFAULT_TYPE, user_info: str, message_type: str,
                                      content: str = None, file_id: str = None, caption: str = None):
    """Уведомление администраторов о полученном сообщении"""

    if message_type == "text":
        admin_message = f"""
💬 Получено новое анонимное сообщение в канал:

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
📸 Получено новое фото в канал:

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
🎥 Получено новое видео в канал:

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
📎 Получен новый документ в канал:

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
🎵 Получено новое аудио в канал:

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
🎤 Получено новое голосовое сообщение в канал:

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

    # Пропускаем команды
    if message.text and message.text.startswith('/'):
        return

    # Проверяем лимит времени (30 секунд) - только для анонимных сообщений
    current_time = time.time()
    if user_id in user_last_message_time:
        time_diff = current_time - user_last_message_time[user_id]
        if time_diff < 30:
            remaining = int(30 - time_diff)
            await message.reply_text(
                f"⏳ Вы можете отправлять следующее анонимное сообщение через {remaining} секунд.\n"
                f"Используйте /message для срочного обращения к администраторам."
            )
            return

    # Обновляем время последнего сообщения
    user_last_message_time[user_id] = current_time

    # Формируем информацию об отправителе
    user_info = f"""
👤 ID: {user_id}
📛 Имя: {user.first_name or 'Не указано'}
🔖 Фамилия: {user.last_name or 'Не указана'}
🔗 Username: @{user.username if user.username else 'Не указан'}
⏰ Время: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(current_time))}
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


async def admin_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда для администраторов чтобы проверить работу бота"""
    user_id = update.effective_user.id

    if user_id not in ADMIN_IDS:
        await update.message.reply_text("❌ Эта команда только для администраторов.")
        return

    # Статистика
    active_users = len(user_last_message_time)
    total_private_messages = sum(len(messages) for messages in user_message_history.values())

    stats_text = f"""
👑 Панель администратора

📊 Статистика:
• Активных пользователей: {active_users}
• Приватных сообщений: {total_private_messages}
• Администраторов: {len(ADMIN_IDS)}
• ID администраторов: {', '.join(map(str, ADMIN_IDS))}

💬 Последние приватные сообщения:
"""

    # Добавляем последние 5 приватных сообщений
    recent_messages = []
    for uid, messages in user_message_history.items():
        for msg in messages[-3:]:  # Последние 3 сообщения от каждого пользователя
            if msg["to_admin"]:
                recent_messages.append({
                    "user_id": uid,
                    "text": msg["text"][:100] + "..." if len(msg["text"]) > 100 else msg["text"],
                    "time": time.strftime('%H:%M', time.localtime(msg["time"]))
                })

    recent_messages.sort(key=lambda x: x["time"], reverse=True)

    for i, msg in enumerate(recent_messages[:5], 1):
        stats_text += f"\n{i}. Пользователь {msg['user_id']} ({msg['time']}):\n   {msg['text']}"

    await update.message.reply_text(stats_text)


async def clear_limit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда для сброса лимита (только для админов)"""
    user_id = update.effective_user.id

    if user_id not in ADMIN_IDS:
        await update.message.reply_text("❌ Эта команда только для администраторов.")
        return

    if context.args:
        target_user_id = int(context.args[0])
        if target_user_id in user_last_message_time:
            del user_last_message_time[target_user_id]
            await update.message.reply_text(f"✅ Лимит для пользователя {target_user_id} сброшен.")
        else:
            await update.message.reply_text(f"❌ Пользователь {target_user_id} не найден.")
    else:
        user_last_message_time.clear()
        await update.message.reply_text("✅ Лимиты всех пользователей сброшены.")


def main():
    """Основная функция запуска бота"""
    application = Application.builder().token(BOT_TOKEN).build()

    # Добавляем обработчики команд
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("admin", admin_stats))
    application.add_handler(CommandHandler("message", message_command))
    application.add_handler(CommandHandler("clear_limit", clear_limit))

    # Обработчик нажатий на кнопки
    application.add_handler(CallbackQueryHandler(button_callback))

    # Обработчик ответов администраторов
    application.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND & filters.User(ADMIN_IDS),
        admin_reply
    ))

    # Общий обработчик сообщений (анонимные сообщения в канал)
    application.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, handle_message))

    # Запускаем бота
    print("🤖 Бот запущен...")
    print(f"👥 Администраторы: {ADMIN_IDS}")
    print(f"📢 Канал: {CHANNEL_ID}")
    print(f"⏱️ Лимит: 1 анонимное сообщение в 30 секунд")
    application.run_polling()


if __name__ == "__main__":
    main()
