import os
import logging
import sys
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# ========== КОНФИГУРАЦИЯ ==========
BOT_TOKEN = os.environ.get("BOT_TOKEN")
if not BOT_TOKEN:
    BOT_TOKEN = "ВАШ_ТОКЕН_ЗДЕСЬ"  # Замени на свой от @BotFather

PORT = int(os.environ.get("PORT", 8080))
WEBHOOK_URL = os.environ.get("WEBHOOK_URL", "https://web-production-bd8b.up.railway.app")

# ========== ДАННЫЕ (ВСТАВЬ СВОИ) ==========
# Ссылка на PDF с офертой (прямая ссылка на файл или короткая)
PDF_LINK = "https://github.com/твой-логин/название-репозитория/raw/main/oferta.pdf"

# Ссылка на картинку с QR-кодом (прямая ссылка)
QR_LINK = "https://github.com/твой-логин/название-репозитория/raw/main/qr.png"

# Текст инструкции после оплаты
INSTRUCTION = "Оплатите по QR‑коду и отправьте скриншот менеджеру.\nСпасибо за выбор нашего кэмпа! 🌟"

# Названия 5 кэмпов (можно менять)
CAMPS = [
    {"name": "🏕️ КЭМП 1 — Название", "id": "camp1"},
    {"name": "🏕️ КЭМП 2 — Название", "id": "camp2"},
    {"name": "🏕️ КЭМП 3 — Название", "id": "camp3"},
    {"name": "🏕️ КЭМП 4 — Название", "id": "camp4"},
    {"name": "🏕️ КЭМП 5 — Название", "id": "camp5"}
]

# ========== ЛОГИРОВАНИЕ ==========
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# ========== КЛАВИАТУРЫ ==========
def get_camps_keyboard():
    """Кнопки для выбора кэмпа"""
    keyboard = []
    for camp in CAMPS:
        keyboard.append([InlineKeyboardButton(camp["name"], callback_data=f"camp:{camp['id']}")])
    return InlineKeyboardMarkup(keyboard)

def get_agree_keyboard():
    """Кнопка 'Согласен'"""
    keyboard = [[InlineKeyboardButton("✅ СОГЛАСЕН", callback_data="agree")]]
    return InlineKeyboardMarkup(keyboard)

# ========== ОБРАБОТЧИКИ ==========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /start — показывает кнопки с кэмпами"""
    await update.message.reply_text(
        "🏕️ <b>Выберите КЭМП, который вас интересует:</b>",
        parse_mode='HTML',
        reply_markup=get_camps_keyboard()
    )

async def handle_camp_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка выбора кэмпа — показывает оферту и кнопку 'Согласен'"""
    query = update.callback_query
    await query.answer()

    data = query.data
    if data.startswith("camp:"):
        camp_id = data.split(":")[1]
        camp_name = next((c["name"] for c in CAMPS if c["id"] == camp_id), "Выбранный кэмп")
        
        # Сохраняем выбранный кэмп в данных пользователя (на всякий случай)
        context.user_data["selected_camp"] = camp_name
        
        # Текст с офертой
        text = (
            f"<b>Вы выбрали:</b> {camp_name}\n\n"
            f"📄 <a href='{PDF_LINK}'>Оферта (PDF)</a>\n\n"
            f"Нажимая «Согласен», вы подтверждаете, что ознакомились и согласны с условиями оферты."
        )
        
        await query.edit_message_text(
            text=text,
            parse_mode='HTML',
            disable_web_page_preview=True,
            reply_markup=get_agree_keyboard()
        )

async def handle_agree(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка нажатия 'Согласен' — отправляет QR и инструкцию"""
    query = update.callback_query
    await query.answer()
    
    # Убираем кнопки под предыдущим сообщением
    await query.edit_message_reply_markup(reply_markup=None)
    
    # Отправляем QR-код
    await query.message.reply_photo(
        photo=QR_LINK,
        caption=f"<b>🗳️ QR‑код для оплаты</b>\n\n{INSTRUCTION}",
        parse_mode='HTML'
    )
    
    # Дополнительное сообщение
    await query.message.reply_text(
        "✅ Спасибо! Если остались вопросы — напишите нам.",
        parse_mode='HTML'
    )

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик ошибок"""
    logger.error(f"Ошибка: {context.error}")
    try:
        if update and update.callback_query:
            await update.callback_query.answer("⚠️ Произошла ошибка. Попробуйте /start")
        elif update and update.message:
            await update.message.reply_text("⚠️ Ошибка. Нажмите /start")
    except:
        pass

# ========== ОСНОВНАЯ ФУНКЦИЯ ==========
def main():
    """Запуск бота на Railway"""
    logger.info("🚀 Запуск бота (кэмпы)...")
    
    try:
        application = Application.builder().token(BOT_TOKEN).build()
        
        # Регистрируем обработчики
        application.add_handler(CommandHandler('start', start))
        application.add_handler(CallbackQueryHandler(handle_camp_selection, pattern='^camp:'))
        application.add_handler(CallbackQueryHandler(handle_agree, pattern='^agree$'))
        application.add_error_handler(error_handler)
        
        logger.info("✅ Приложение создано")
        
        # Настройка webhook
        webhook_url = f"{WEBHOOK_URL.rstrip('/')}/{BOT_TOKEN}"
        logger.info(f"🌐 Webhook: {webhook_url}")
        
        application.run_webhook(
            listen="0.0.0.0",
            port=PORT,
            url_path=BOT_TOKEN,
            webhook_url=webhook_url,
            drop_pending_updates=True
        )
        
    except Exception as e:
        logger.error(f"💥 Критическая ошибка: {e}")
        raise

if __name__ == '__main__':
    main()
