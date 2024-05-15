from telegram import Update, Bot
from telegram.ext import Updater, CommandHandler, CallbackContext

TELEGRAM_TOKEN = '6997037540:AAE1EjkRY7VZ4h4DTJdyy6kjaUxX-0XS4-8'

def start(update: Update, context: CallbackContext) -> None:
    chat_id = update.message.chat_id
    update.message.reply_text(f'Your chat ID is: {chat_id}')

def main():
    # Создаем объект бота
    updater = Updater(TELEGRAM_TOKEN)

    # Получаем диспетчера для регистрации обработчиков
    dispatcher = updater.dispatcher

    # Регистрируем обработчик команды /start
    dispatcher.add_handler(CommandHandler("start", start))

    # Запуск бота
    updater.start_polling()

    # Бот будет работать до тех пор, пока не получит сигнал завершения
    updater.idle()

#if name == 'main':
    #main()