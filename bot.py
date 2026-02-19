import os
import logging
import sys
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# ========== КОНФИГУРАЦИЯ ==========
BOT_TOKEN = "8355392266:AAHLDpU6Zn7TInLt1ULj8cgcATM0rk3NgUk"

# ========== ДАННЫЕ ==========
PDF_LINK = "https://clck.ru/3RuVTQ"
QR_LINK = "https://github.com/твой-логин/название-репозитория/raw/main/qr.png"  # ЗАМЕНИ

INSTRUCTION = "Оплатите по QR‑коду и отправьте скриншот менеджеру.\nСпасибо за выбор нашего кэмпа! 🌟"

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
    keyboard = []
    for camp in CAMPS:
        keyboard.append([InlineKeyboardButton(camp["name"], callback_data=f"camp:{camp['id']}")])
    return InlineKeyboardMarkup(keyboard)

def get_agree_keyboard():
    keyboard = [[InlineKeyboardButton("✅ СОГЛАСЕН", callback_data="agree")]]
    return InlineKeyboardMarkup(keyboard)

# ========== ОБРАБОТЧИКИ ==========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /start"""
    await update.message.reply_text(
        "🏕️ <b>Выберите КЭМП, который вас интересует:</b>",
        parse_mode='HTML',
        reply_markup=get_camps_keyboard()
    )

async def handle_camp_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Выбор кэмпа → оферта + кнопка согласия"""
    query = update.callback_query
    await query.answer()

    data = query.data
    if data.startswith("camp:"):
        camp_id = data.split(":")[1]
        camp_name = next((c["name"] for c in CAMPS if c["id"] == camp_id), "Выбранный кэмп")
        
        context.user_data["selected_camp"] = camp_name
        
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
    """Согласие → QR + инструкция"""
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_reply_markup(reply_markup=None)
    
    await query.message.reply_photo(
        photo=QR_LINK,
        caption=f"<b>🗳️ QR‑код для оплаты</b>\n\n{INSTRUCTION}",
        parse_mode='HTML'
    )
    
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

# ========== ЗАПУСК ==========
def main():
    """Запуск бота с polling (как в рабочем боте)"""
    logger.info("🚀 Запуск бота (кэмпы)...")
    
    try:
        application = Application.builder().token(BOT_TOKEN).build()
        
        application.add_handler(CommandHandler('start', start))
        application.add_handler(CallbackQueryHandler(handle_camp_selection, pattern='^camp:'))
        application.add_handler(CallbackQueryHandler(handle_agree, pattern='^agree$'))
        application.add_error_handler(error_handler)
        
        logger.info("✅ Бот запущен в режиме polling!")
        logger.info("🤖 Бот готов к работе!")
        
        # ✅ ВАЖНО: используем polling, а не webhook!
        application.run_polling(drop_pending_updates=True)
        
    except Exception as e:
        logger.error(f"💥 Критическая ошибка: {e}")
        raise

if __name__ == '__main__':
    main()
