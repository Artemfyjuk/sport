import os
import logging
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Токены берутся из переменных окружения (зададим позже на Render)
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
DEEPSEEK_API_KEY = os.environ.get('DEEPSEEK_API_KEY')
DEEPSEEK_API_URL = 'https://api.deepseek.com/v1/chat/completions'

# Настройка логирования
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# Системный промпт для фитнес-тренера
SYSTEM_PROMPT = """Ты - персональный фитнес-тренер и диетолог.
Помогаешь с планами питания, тренировками и здоровым образом жизни.
Отвечай кратко и по делу, используй дружелюбный тон."""

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        '👋 Привет! Я твой персональный фитнес-помощник на базе DeepSeek.\n\n'
        'Я помогу тебе с:\n'
        '• Планами питания и подсчетом калорий\n'
        '• Программами тренировок\n'
        '• Советами по здоровому образу жизни\n\n'
        'Просто напиши, что тебя интересует!'
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    await update.message.chat.send_action(action='typing')
    
    try:
        response = requests.post(
            DEEPSEEK_API_URL,
            headers={'Authorization': f'Bearer {DEEPSEEK_API_KEY}', 'Content-Type': 'application/json'},
            json={
                'model': 'deepseek-chat',
                'messages': [
                    {'role': 'system', 'content': SYSTEM_PROMPT},
                    {'role': 'user', 'content': user_message}
                ],
                'temperature': 0.7,
                'max_tokens': 1000
            },
            timeout=30
        )
        
        if response.status_code == 200:
            ai_response = response.json()['choices'][0]['message']['content']
            await update.message.reply_text(ai_response)
        else:
            await update.message.reply_text('❌ Ошибка DeepSeek API. Проверьте баланс.')
    except Exception as e:
        logging.error(f'Ошибка: {e}')
        await update.message.reply_text('❌ Произошла ошибка. Попробуйте позже.')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        '📚 Доступные команды:\n/start - Начать\n/help - Помощь\n/balance - Баланс DeepSeek'
    )

async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        response = requests.get(
            'https://api.deepseek.com/user/balance',
            headers={'Authorization': f'Bearer {DEEPSEEK_API_KEY}'}
        )
        if response.status_code == 200:
            bal = response.json().get('balance', 'Неизвестно')
            await update.message.reply_text(f'💰 Баланс API: {bal} юаней')
        else:
            await update.message.reply_text('❌ Не удалось получить баланс')
    except Exception as e:
        await update.message.reply_text('❌ Ошибка при проверке баланса')

def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler('start', start))
    app.add_handler(CommandHandler('help', help_command))
    app.add_handler(CommandHandler('balance', balance))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()

if __name__ == '__main__':
    main()
