import os
import logging
import sys
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# ========== КОНФИГУРАЦИЯ ==========
BOT_TOKEN = "8355392266:AAHLDpU6Zn7TInLt1ULj8cgcATM0rk3NgUk"
ADMIN_USERNAME = "@Dmitry_Kh_87"  # username администратора

# ========== ДАННЫЕ ==========
PDF_LINK = "https://clck.ru/3RuZKG"  # ссылка на оферту/договор
QR_LINK = "https://clck.ru/3RuZZA"    # ссылка на QR-код для оплаты
REQUISITES_LINK = PDF_LINK  # используем ту же ссылку для реквизитов

# ========== ОБНОВЛЕННЫЕ ДАННЫЕ КЭМПОВ ==========
CAMPS = [
    {
        "name": "🏕️ Солнцево (городской)",
        "address": "Ул. Богданова д. 19",
        "id": "solntsevo",
        "legal_entity": "ООО ШМП",
        "type": "city",
        "offer_text": "футбольный дневной КЭМП в Солнцево"
    },
    {
        "name": "🏕️ Сочи (с ночёвкой)",
        "address": "Парк отель Сочи",
        "id": "sochi",
        "legal_entity": "ООО ШМП",
        "type": "overnight",
        "offer_text": "футбольный КЭМП в Сочи"
    },
    {
        "name": "🏕️ Тушино (городской)",
        "address": "Ул. Лодочная д. 15 стр. 1А",
        "id": "tushino",
        "legal_entity": "ИП Зубанова ШМП",
        "type": "city",
        "offer_text": "футбольный дневной КЭМП в Тушино"
    },
    {
        "name": "🏕️ Кузьминки (городской)",
        "address": "Ул. Академика Скрябина д. 23 стр. 2",
        "id": "kuzminki",
        "legal_entity": "ИП Зубанова ДХ",
        "type": "city",
        "offer_text": "футбольный дневной КЭМП в Кузьминках"
    },
    {
        "name": "🏕️ Хамовники (городской)",
        "address": "Ул. Плющиха 57а",
        "id": "khamovniki",
        "legal_entity": "ООО ШМП",
        "type": "city",
        "offer_text": "футбольный дневной КЭМП в Хамовниках"
    }
]

# ========== УСЛУГИ ==========
SERVICES = {
    "camp": {
        "name": "🏕️ КЭМП",
        "options": [
            {"name": "10 дней - смена 1", "price": "69 990р.", "id": "camp_10_days_1"},
            {"name": "10 дней - смена 7", "price": "69 990р.", "id": "camp_10_days_7"},
            {"name": "1 день", "price": "7 900р.", "id": "camp_1_day"}
        ]
    },
    "training": {
        "name": "⚽ ТРЕНИРОВКИ",
        "options": [
            {"name": "Тренировка - 1 занятие", "price": "1 890р.", "id": "training_1"},
            {"name": "Абонемент - 5 занятий", "price": "7 450р. (1 490р./занятие)", "id": "training_5"},
            {"name": "Абонемент - 10 занятий", "price": "12 900р. (1 290р./занятие)", "id": "training_10"}
        ]
    },
    "other": {
        "name": "📦 ПРОЧЕЕ",
        "options": [
            {"name": "Оплата после пробного дня", "price": "65 000р.", "id": "trial_day"},
            {"name": "Форма", "price": "4 500р.", "id": "uniform"}
        ]
    }
}

# Для Сочи свои цены
SOCHI_SERVICES = {
    "camp": {
        "name": "🏕️ КЭМП в Сочи",
        "options": [
            {"name": "Спортсмен (без сопровождения) - Май 02-08", "price": "89 990р.", "id": "sochi_sportsman_may"},
            {"name": "Спортсмен (без сопровождения) - Июнь 19-27", "price": "114 990р.", "id": "sochi_sportsman_june"},
            {"name": "Спортсмен (без сопровождения) - Июль 4-11", "price": "102 490р.", "id": "sochi_sportsman_july"},
            {"name": "Спортсмен (без сопровождения) - Август 1-8", "price": "102 490р.", "id": "sochi_sportsman_august"},
            {"name": "Спортсмен + родитель - Май 02-08", "price": "139 990р.", "id": "sochi_family_may"},
            {"name": "Спортсмен + родитель - Июнь 19-27", "price": "183 990р.", "id": "sochi_family_june"},
            {"name": "Спортсмен + родитель - Июль 4-11", "price": "161 990р.", "id": "sochi_family_july"},
            {"name": "Спортсмен + родитель - Август 1-8", "price": "161 990р.", "id": "sochi_family_august"},
            {"name": "Сопровождающий - Май 02-08", "price": "59 990р.", "id": "sochi_accompanist_may"},
            {"name": "Сопровождающий - Июнь 19-27", "price": "77 990р.", "id": "sochi_accompanist_june"},
            {"name": "Сопровождающий - Июль 4-11", "price": "68 990р.", "id": "sochi_accompanist_july"},
            {"name": "Сопровождающий - Август 1-8", "price": "68 990р.", "id": "sochi_accompanist_august"}
        ]
    }
}

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

def get_service_categories_keyboard():
    keyboard = [
        [InlineKeyboardButton("🏕️ КЭМП", callback_data="service_category:camp")],
        [InlineKeyboardButton("⚽ ТРЕНИРОВКИ", callback_data="service_category:training")],
        [InlineKeyboardButton("📦 ПРОЧЕЕ", callback_data="service_category:other")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_services_keyboard(category, is_sochi=False):
    keyboard = []
    services = SOCHI_SERVICES if is_sochi else SERVICES
    if category in services:
        for option in services[category]["options"]:
            keyboard.append([InlineKeyboardButton(
                f"{option['name']} - {option['price']}", 
                callback_data=f"service:{option['id']}"
            )])
    keyboard.append([InlineKeyboardButton("🔙 Назад к категориям", callback_data="back_to_categories")])
    return InlineKeyboardMarkup(keyboard)

def get_agree_keyboard():
    keyboard = [[InlineKeyboardButton("✅ СОГЛАСЕН", callback_data="agree")]]
    return InlineKeyboardMarkup(keyboard)

def get_contract_keyboard():
    keyboard = [
        [InlineKeyboardButton("📄 Скачать договор", callback_data="download_contract")],
        [InlineKeyboardButton("✅ Отправить подписанный договор", callback_data="send_contract")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_payment_keyboard():
    keyboard = [
        [InlineKeyboardButton("💳 Реквизиты для оплаты", callback_data="show_requisites")],
        [InlineKeyboardButton("📤 Отправить чек об оплате", callback_data="send_receipt")]
    ]
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
    """Выбор кэмпа"""
    query = update.callback_query
    await query.answer()

    data = query.data
    if data.startswith("camp:"):
        camp_id = data.split(":")[1]
        camp = next((c for c in CAMPS if c["id"] == camp_id), None)
        
        if not camp:
            return
        
        context.user_data["selected_camp"] = camp
        context.user_data["is_sochi"] = (camp_id == "sochi")
        
        # Для Сочи показываем сразу выбор формата поездки
        if camp_id == "sochi":
            await show_sochi_services(update, context)
        else:
            # Для городских кэмпов показываем оферту
            text = (
                f"<b>Вы выбрали:</b>\n"
                f"🏕️ {camp['offer_text']}\n"
                f"📍 {camp['address']}\n\n"
                f"📄 <a href='{PDF_LINK}'>Оферта (PDF)</a> ({camp['legal_entity']})\n\n"
                f"Нажимая «Согласен», вы подтверждаете, что ознакомились и согласны с условиями оферты."
            )
            
            await query.edit_message_text(
                text=text,
                parse_mode='HTML',
                disable_web_page_preview=True,
                reply_markup=get_agree_keyboard()
            )

async def show_sochi_services(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать услуги для Сочи"""
    query = update.callback_query
    await query.edit_message_text(
        text="<b>Какой формат поездки вы выбираете?🌝</b>",
        parse_mode='HTML',
        reply_markup=get_services_keyboard("camp", is_sochi=True)
    )

async def handle_service_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Выбор категории услуг"""
    query = update.callback_query
    await query.answer()
    
    category = query.data.split(":")[1]
    is_sochi = context.user_data.get("is_sochi", False)
    
    # Для Сочи показываем только КЭМП
    if is_sochi and category != "camp":
        await query.answer("Для Сочи доступен только формат КЭМП", show_alert=True)
        return
    
    await query.edit_message_text(
        text=f"<b>Выберите услугу:</b>",
        parse_mode='HTML',
        reply_markup=get_services_keyboard(category, is_sochi)
    )

async def handle_service_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Выбор конкретной услуги"""
    query = update.callback_query
    await query.answer()
    
    service_id = query.data.split(":")[1]
    camp = context.user_data.get("selected_camp")
    
    # Находим выбранную услугу
    selected_service = None
    services_dict = SOCHI_SERVICES if camp and camp["id"] == "sochi" else SERVICES
    
    for category in services_dict.values():
        for option in category["options"]:
            if option["id"] == service_id:
                selected_service = option
                break
    
    if not selected_service:
        return
    
    context.user_data["selected_service"] = selected_service
    
    text = (
        f"<b>🏟 Вы выбрали УСЛУГУ:</b>\n"
        f"{selected_service['name']} - {selected_service['price']}\n\n"
        f"<b>📍 {camp['name']}</b>\n"
        f"{camp['address']}"
    )
    
    await query.edit_message_text(
        text=text,
        parse_mode='HTML',
        reply_markup=get_payment_keyboard()
    )

async def handle_agree(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Согласие с офертой → выбор услуг"""
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_reply_markup(reply_markup=None)
    
    await query.message.reply_text(
        text="<b>Какая услуга вас интересует?</b>",
        parse_mode='HTML',
        reply_markup=get_service_categories_keyboard()
    )

async def handle_sochi_contract(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка договора для Сочи"""
    query = update.callback_query
    await query.answer()
    
    if query.data == "download_contract":
        await query.message.reply_text(
            text=f"📄 <a href='{PDF_LINK}'>Скачать договор</a>\n\n"
                 "1. Скачайте договор\n"
                 "2. Заполните персональные данные (отмечены жёлтым)\n"
                 "3. Распечатайте и подпишите\n"
                 "4. Пришлите скан подписанного договора в этот чат",
            parse_mode='HTML'
        )
        context.user_data["awaiting_contract"] = True
        
    elif query.data == "send_contract":
        await query.message.reply_text(
            "📎 Пожалуйста, отправьте скан или фото подписанного договора"
        )
        context.user_data["awaiting_contract"] = True

async def handle_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка оплаты"""
    query = update.callback_query
    await query.answer()
    
    if query.data == "show_requisites":
        await query.message.reply_text(
            text=f"📄 <a href='{REQUISITES_LINK}'>Реквизиты \"Школа мяча\"</a>\n\n"
                 "⬇️ Для оплаты услуги нужно:\n"
                 "1️⃣ В назначении платежа указать ФИО участника + название услуги\n"
                 "2️⃣ Ввести верную сумму\n"
                 "3️⃣ Произвести оплату по реквизитам✅\n\n"
                 "Пожалуйста, не забудьте прислать нам скриншот - подтверждение оплаты в следующем сообщении🙌",
            parse_mode='HTML'
        )
        
    elif query.data == "send_receipt":
        # Запрашиваем данные для идентификации платежа
        await query.message.reply_text(
            "📝 Пожалуйста, отправьте чек об оплате и укажите данные:\n"
            "ФИО участника:\n"
            "ФИО плательщика:\n"
            "Телефон для связи:"
        )
        context.user_data["awaiting_receipt"] = True

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка сообщений (договоры, чеки)"""
    user_data = context.user_data
    user = update.effective_user
    
    # Если ожидаем договор
    if user_data.get("awaiting_contract"):
        if update.message.document or update.message.photo:
            # Пересылаем админу
            caption = (f"📄 Договор от пользователя\n"
                      f"ID: {user.id}\n"
                      f"Username: @{user.username or 'нет'}\n"
                      f"Кэмп: {user_data.get('selected_camp', {}).get('name', 'Не выбран')}\n"
                      f"Услуга: {user_data.get('selected_service', {}).get('name', 'Не выбрана')}")
            
            if update.message.document:
                await context.bot.send_document(
                    chat_id=ADMIN_USERNAME,
                    document=update.message.document.file_id,
                    caption=caption
                )
            else:
                await context.bot.send_photo(
                    chat_id=ADMIN_USERNAME,
                    photo=update.message.photo[-1].file_id,
                    caption=caption
                )
            
            await update.message.reply_text(
                "✅ Договор получен и отправлен администратору. Спасибо!"
            )
            user_data["awaiting_contract"] = False
        else:
            await update.message.reply_text(
                "Пожалуйста, отправьте файл или фото договора"
            )
    
    # Если ожидаем чек
    elif user_data.get("awaiting_receipt"):
        if update.message.photo or update.message.document:
            # Получаем текст сообщения для данных
            text = update.message.caption or update.message.text or ""
            
            # Пересылаем админу
            caption = (f"💰 Чек об оплате\n"
                      f"От пользователя: {user.full_name}\n"
                      f"ID: {user.id}\n"
                      f"Username: @{user.username or 'нет'}\n"
                      f"Кэмп: {user_data.get('selected_camp', {}).get('name', 'Не выбран')}\n"
                      f"Услуга: {user_data.get('selected_service', {}).get('name', 'Не выбрана')}\n"
                      f"Данные плательщика: {text}")
            
            if update.message.photo:
                await context.bot.send_photo(
                    chat_id=ADMIN_USERNAME,
                    photo=update.message.photo[-1].file_id,
                    caption=caption
                )
            else:
                await context.bot.send_document(
                    chat_id=ADMIN_USERNAME,
                    document=update.message.document.file_id,
                    caption=caption
                )
            
            await update.message.reply_text(
                "✅ Чек получен и отправлен администратору. Спасибо! 🌟\n"
                "Спасибо, что выбираете Школа мяча! 🌟"
            )
            user_data["awaiting_receipt"] = False
        else:
            # Если просто текст без файла
            await update.message.reply_text(
                "Пожалуйста, отправьте фото или скан чека об оплате"
            )

async def handle_back(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Возврат к выбору категорий"""
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        text="<b>Какая услуга вас интересует?</b>",
        parse_mode='HTML',
        reply_markup=get_service_categories_keyboard()
    )

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик ошибок - только логирование, без отправки админу"""
    logger.error(f"Ошибка: {context.error}")
    
    # Просто уведомляем пользователя, админу не отправляем
    try:
        if update and update.callback_query:
            await update.callback_query.answer("⚠️ Произошла ошибка. Попробуйте /start")
        elif update and update.message:
            await update.message.reply_text("⚠️ Ошибка. Нажмите /start")
    except:
        pass

# ========== ЗАПУСК ==========
def main():
    """Запуск бота"""
    logger.info("🚀 Запуск бота (обновленная версия)...")
    
    try:
        application = Application.builder().token(BOT_TOKEN).build()
        
        # Обработчики команд
        application.add_handler(CommandHandler('start', start))
        
        # Обработчики callback'ов
        application.add_handler(CallbackQueryHandler(handle_camp_selection, pattern='^camp:'))
        application.add_handler(CallbackQueryHandler(handle_service_category, pattern='^service_category:'))
        application.add_handler(CallbackQueryHandler(handle_service_selection, pattern='^service:'))
        application.add_handler(CallbackQueryHandler(handle_agree, pattern='^agree$'))
        application.add_handler(CallbackQueryHandler(handle_sochi_contract, pattern='^(download_contract|send_contract)$'))
        application.add_handler(CallbackQueryHandler(handle_payment, pattern='^(show_requisites|send_receipt)$'))
        application.add_handler(CallbackQueryHandler(handle_back, pattern='^back_to_categories$'))
        
        # Обработчик сообщений (фото и документы)
        application.add_handler(MessageHandler(filters.PHOTO | filters.Document.ALL, handle_message))
        
        # Обработчик ошибок
        application.add_error_handler(error_handler)
        
        logger.info("✅ Бот запущен в режиме polling!")
        logger.info("🤖 Бот готов к работе!")
        
        application.run_polling(drop_pending_updates=True)
        
    except Exception as e:
        logger.error(f"💥 Критическая ошибка: {e}")
        raise

if __name__ == '__main__':
    main()
