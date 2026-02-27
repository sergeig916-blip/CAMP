import os
import logging
import sys
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes, ConversationHandler

# ========== КОНФИГУРАЦИЯ ==========
BOT_TOKEN = "8355392266:AAHLDpU6Zn7TInLt1ULj8cgcATM0rk3NgUk"

# 🛡️ ВАШ ID
ADMIN_CHAT_ID = 42038232
ADMIN_USERNAME = "Dmitry_Kh_87"  # без @
ADMIN_PHONE = "89855796779"

# Состояния для ConversationHandler
(FIO_PARTICIPANT, FIO_PAYER, PHONE, RECEIPT_PHOTO) = range(4)
# Состояния для Сочи
(SOCHI_WAIT_CONTRACT, SOCHI_FIO, SOCHI_PHONE) = range(4, 7)

# ========== ДАННЫЕ ==========
PDF_LINK = "https://clck.ru/3RuZKG"  # базовая ссылка
REQUISITES_LINK = PDF_LINK

# ========== ОБНОВЛЕННЫЕ ДАННЫЕ КЭМПОВ (версия 27.02) ==========
CAMPS = [
    {
        "name": "🏕️ Солнцево (городской)",
        "address": "Ул. Богданова д. 19",
        "id": "solntsevo",
        "legal_entity": "ООО ШМП",
        "type": "city",
        "offer_text": "Школа мяча. Футбольный дневной КЭМП в Солнцево"
    },
    {
        "name": "🏕️ Сочи (с ночёвкой)",
        "address": "Парк отель Сочи",
        "id": "sochi",
        "legal_entity": "ООО ШМП",
        "type": "overnight",
        "offer_text": "Школа мяча. Футбольный КЭМП в Сочи"
    },
    {
        "name": "🏕️ Тушино (городской)",
        "address": "Ул. Лодочная д. 15 стр. 1А",
        "id": "tushino",
        "legal_entity": "ИП Зубанова / счет ШМП",
        "type": "city",
        "offer_text": "Школа мяча. Футбольный дневной КЭМП в Тушино"
    },
    {
        "name": "🏕️ Кузьминки (городской)",
        "address": "Ул. Академика Скрябина д. 23 стр. 2",
        "id": "kuzminki",
        "legal_entity": "ИП Зубанова / счёт ДХ",
        "type": "city",
        "offer_text": "Школа мяча. Футбольный дневной КЭМП в Кузьминках"
    },
    {
        "name": "🏕️ Хамовники (городской)",
        "address": "Ул. Плющиха 57а",
        "id": "khamovniki",
        "legal_entity": "ООО ШМП",
        "type": "city",
        "offer_text": "Школа мяча. Футбольный дневной КЭМП в Хамовниках"
    }
]

# ========== УСЛУГИ С ДАТАМИ ==========
SERVICES = {
    "camp": {
        "name": "🏕️ КЭМП",
        "options": [
            {"name": "10 дней - смена 1 (01-12 июнь)", "price": "69 990р.", "id": "camp_10_days_1", 
             "short": "Смена 1 (01-12 июнь)"},
            {"name": "10 дней - смена 2 (15-26 июнь)", "price": "69 990р.", "id": "camp_10_days_2", 
             "short": "Смена 2 (15-26 июнь)"},
            {"name": "10 дней - смена 3 (29.06-10.07)", "price": "69 990р.", "id": "camp_10_days_3", 
             "short": "Смена 3 (29.06-10.07)"},
            {"name": "10 дней - смена 4 (13-24 июль)", "price": "69 990р.", "id": "camp_10_days_4", 
             "short": "Смена 4 (13-24 июль)"},
            {"name": "10 дней - смена 5 (27.07-07.08)", "price": "69 990р.", "id": "camp_10_days_5", 
             "short": "Смена 5 (27.07-07.08)"},
            {"name": "10 дней - смена 6 (10-21 авг)", "price": "69 990р.", "id": "camp_10_days_6", 
             "short": "Смена 6 (10-21 авг)"},
            {"name": "10 дней - смена 7 (24-27 авг)", "price": "69 990р.", "id": "camp_10_days_7", 
             "short": "Смена 7 (24-27 авг)"},
            {"name": "1 день", "price": "7 900р.", "id": "camp_1_day", 
             "short": "1 день"}
        ]
    },
    "training": {
        "name": "⚽ ТРЕНИРОВКИ",
        "options": [
            {"name": "Тренировка - 1 занятие", "price": "1 890р.", "id": "training_1", 
             "short": "1 тренировка"},
            {"name": "Абонемент - 5 занятий", "price": "7 450р. (1 490р./занятие)", "id": "training_5", 
             "short": "Абонемент 5 занятий"},
            {"name": "Абонемент - 10 занятий", "price": "12 900р. (1 290р./занятие)", "id": "training_10", 
             "short": "Абонемент 10 занятий"}
        ]
    },
    "other": {
        "name": "📦 ПРОЧЕЕ",
        "options": [
            {"name": "Оплата после пробного дня", "price": "65 000р.", "id": "trial_day", 
             "short": "Пробный день"},
            {"name": "Форма", "price": "4 500р.", "id": "uniform", 
             "short": "Форма"}
        ]
    }
}

# Для Сочи свои цены (с датами)
SOCHI_SERVICES = {
    "camp": {
        "name": "🏕️ КЭМП в Сочи",
        "options": [
            {"name": "Спортсмен (без сопровождения) - Май 02-08", "price": "89 990р.", 
             "id": "sochi_sportsman_may", "short": "Спортсмен (Май 02-08)"},
            {"name": "Спортсмен (без сопровождения) - Июнь 19-27", "price": "114 990р.", 
             "id": "sochi_sportsman_june", "short": "Спортсмен (Июнь 19-27)"},
            {"name": "Спортсмен (без сопровождения) - Июль 4-11", "price": "102 490р.", 
             "id": "sochi_sportsman_july", "short": "Спортсмен (Июль 4-11)"},
            {"name": "Спортсмен (без сопровождения) - Август 1-8", "price": "102 490р.", 
             "id": "sochi_sportsman_august", "short": "Спортсмен (Август 1-8)"},
            {"name": "Спортсмен + родитель - Май 02-08", "price": "139 990р.", 
             "id": "sochi_family_may", "short": "Спортсмен+род. (Май)"},
            {"name": "Спортсмен + родитель - Июнь 19-27", "price": "183 990р.", 
             "id": "sochi_family_june", "short": "Спортсмен+род. (Июнь)"},
            {"name": "Спортсмен + родитель - Июль 4-11", "price": "161 990р.", 
             "id": "sochi_family_july", "short": "Спортсмен+род. (Июль)"},
            {"name": "Спортсмен + родитель - Август 1-8", "price": "161 990р.", 
             "id": "sochi_family_august", "short": "Спортсмен+род. (Август)"},
            {"name": "Сопровождающий - Май 02-08", "price": "59 990р.", 
             "id": "sochi_accompanist_may", "short": "Сопровожд. (Май)"},
            {"name": "Сопровождающий - Июнь 19-27", "price": "77 990р.", 
             "id": "sochi_accompanist_june", "short": "Сопровожд. (Июнь)"},
            {"name": "Сопровождающий - Июль 4-11", "price": "68 990р.", 
             "id": "sochi_accompanist_july", "short": "Сопровожд. (Июль)"},
            {"name": "Сопровождающий - Август 1-8", "price": "68 990р.", 
             "id": "sochi_accompanist_august", "short": "Сопровожд. (Август)"}
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
            button_text = option.get("short", option["name"])
            keyboard.append([InlineKeyboardButton(
                f"{button_text} - {option['price']}", 
                callback_data=f"service:{option['id']}"
            )])
    
    keyboard.append([InlineKeyboardButton("🔙 Назад к категориям", callback_data="back_to_categories")])
    return InlineKeyboardMarkup(keyboard)

def get_agree_keyboard():
    keyboard = [[InlineKeyboardButton("✅ СОГЛАСЕН", callback_data="agree")]]
    return InlineKeyboardMarkup(keyboard)

def get_sochi_contract_keyboard():
    keyboard = [
        [InlineKeyboardButton("📄 Скачать договор (PDF)", callback_data="sochi_download_contract")],
        [InlineKeyboardButton("✅ Я подписал договор", callback_data="sochi_contract_signed")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_payment_keyboard():
    keyboard = [
        [InlineKeyboardButton("💳 Реквизиты для оплаты", callback_data="show_requisites")],
        [InlineKeyboardButton("📞 Связаться с администратором", callback_data="contact_admin")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_receipt_keyboard():
    keyboard = [
        [InlineKeyboardButton("📤 Отправить чек об оплате", callback_data="send_receipt")],
        [InlineKeyboardButton("📞 Связаться с администратором", callback_data="contact_admin")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_contact_admin_keyboard():
    """Кнопка перехода в чат с админом (через username)"""
    keyboard = [
        [InlineKeyboardButton("📞 Написать администратору", url=f"https://t.me/{ADMIN_USERNAME}")],
        [InlineKeyboardButton("🔙 Назад к услугам", callback_data="back_to_services")]
    ]
    return InlineKeyboardMarkup(keyboard)

# ========== ОБРАБОТЧИКИ ==========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text(
        "🏕️ <b>Выберите КЭМП, который вас интересует:</b>",
        parse_mode='HTML',
        reply_markup=get_camps_keyboard()
    )

async def handle_camp_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
        
        if camp_id == "sochi":
            text = (
                f"<b>Вы выбрали:</b>\n"
                f"🏕️ {camp['offer_text']}\n"
                f"📍 {camp['address']}\n\n"
                f"📄 <a href='{PDF_LINK}'>Договор: PDF ({camp['legal_entity']})</a>\n\n"
                f"<b>Необходимо:</b>\n"
                f"1. Скачать договор себе на устройство\n"
                f"2. Заполнить персональные данные в документе (отмечены жёлтым)\n"
                f"3. Распечатать договор\n"
                f"4. Подписать его\n"
                f"5. Прислать скан или фото ВСЕХ СТРАНИЦ подписанного договора в данный чат"
            )
            
            await query.edit_message_text(
                text=text,
                parse_mode='HTML',
                disable_web_page_preview=True,
                reply_markup=get_sochi_contract_keyboard()
            )
        else:
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

async def handle_sochi_contract(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == "sochi_download_contract":
        await query.message.reply_text(
            text=f"📄 <a href='{PDF_LINK}'>Скачать договор (PDF)</a>",
            parse_mode='HTML'
        )
        
    elif query.data == "sochi_contract_signed":
        await query.message.reply_text(
            "📎 Пожалуйста, отправьте скан или фото ВСЕХ СТРАНИЦ подписанного договора"
        )
        return SOCHI_WAIT_CONTRACT

async def sochi_wait_contract(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    
    if not (update.message.document or update.message.photo):
        await update.message.reply_text(
            "Пожалуйста, отправьте файл или фото ВСЕХ СТРАНИЦ подписанного договора"
        )
        return SOCHI_WAIT_CONTRACT
    
    camp = context.user_data.get("selected_camp", {}).get("name", "Не выбран")
    
    caption = (f"📄 Подписанный договор\n"
              f"━━━━━━━━━━━━━━━\n"
              f"👤 Пользователь: {user.full_name}\n"
              f"🆔 ID: {user.id}\n"
              f"📱 Username: @{user.username or 'нет'}\n"
              f"━━━━━━━━━━━━━━━\n"
              f"🏕️ Кэмп: {camp}\n"
              f"━━━━━━━━━━━━━━━")
    
    try:
        if update.message.document:
            await context.bot.send_document(
                chat_id=ADMIN_CHAT_ID,
                document=update.message.document.file_id,
                caption=caption
            )
        else:
            await context.bot.send_photo(
                chat_id=ADMIN_CHAT_ID,
                photo=update.message.photo[-1].file_id,
                caption=caption
            )
        
        await update.message.reply_text(
            "✅ Спасибо! Договор получен.\n\n"
            "📝 Шаг 1 из 4\n\n"
            "Введите <b>ФИО участника</b>:",
            parse_mode='HTML'
        )
        return SOCHI_FIO
        
    except Exception as e:
        logger.error(f"Ошибка при отправке договора: {e}")
        await update.message.reply_text(
            "✅ Спасибо! Договор получен.\n\n"
            "📝 Шаг 1 из 4\n\n"
            "Введите <b>ФИО участника</b>:",
            parse_mode='HTML'
        )
        return SOCHI_FIO

async def sochi_fio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["sochi_fio"] = update.message.text
    await update.message.reply_text(
        "📝 Шаг 2 из 4\n\n"
        "Введите <b>ФИО плательщика</b>:",
        parse_mode='HTML'
    )
    return SOCHI_PHONE

async def sochi_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["sochi_phone"] = update.message.text
    
    user = update.effective_user
    camp = context.user_data.get("selected_camp", {}).get("name", "Не выбран")
    fio = context.user_data.get("sochi_fio", "Не указано")
    phone = context.user_data.get("sochi_phone", "Не указано")
    
    info_caption = (f"📋 Регистрация на Сочи\n"
                   f"━━━━━━━━━━━━━━━\n"
                   f"👤 Пользователь: {user.full_name}\n"
                   f"🆔 ID: {user.id}\n"
                   f"📱 Username: @{user.username or 'нет'}\n"
                   f"━━━━━━━━━━━━━━━\n"
                   f"🏕️ Кэмп: {camp}\n"
                   f"👶 ФИО участника: {fio}\n"
                   f"📞 Телефон: {phone}\n"
                   f"━━━━━━━━━━━━━━━")
    
    try:
        await context.bot.send_message(
            chat_id=ADMIN_CHAT_ID,
            text=info_caption
        )
    except Exception as e:
        logger.error(f"Ошибка при отправке данных: {e}")
    
    await update.message.reply_text(
        "✅ Спасибо! Данные сохранены.\n\n"
        "<b>Какой формат поездки вы выбираете?🌝</b>",
        parse_mode='HTML',
        reply_markup=get_services_keyboard("camp", is_sochi=True)
    )
    
    return ConversationHandler.END

async def handle_service_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    category = query.data.split(":")[1]
    is_sochi = context.user_data.get("is_sochi", False)
    
    if is_sochi and category != "camp":
        await query.answer("Для Сочи доступен только формат КЭМП", show_alert=True)
        return
    
    await query.edit_message_text(
        text=f"<b>Выберите услугу:</b>",
        parse_mode='HTML',
        reply_markup=get_services_keyboard(category, is_sochi)
    )

async def handle_service_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    service_id = query.data.split(":")[1]
    camp = context.user_data.get("selected_camp")
    
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
    
    service_full_name = selected_service.get("name", selected_service.get("short", ""))
    
    text = (
        f"<b>🏟 Вы выбрали УСЛУГУ:</b>\n"
        f"{service_full_name}\n\n"
        f"<b>📍 {camp['name']}</b>\n"
        f"{camp['address']}"
    )
    
    await query.edit_message_text(
        text=text,
        parse_mode='HTML',
        reply_markup=get_payment_keyboard()
    )

async def handle_agree(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_reply_markup(reply_markup=None)
    
    await query.message.reply_text(
        text="<b>Какая услуга вас интересует?</b>",
        parse_mode='HTML',
        reply_markup=get_service_categories_keyboard()
    )

async def handle_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == "show_requisites":
        camp = context.user_data.get("selected_camp", {})
        legal = camp.get("legal_entity", "Школа мяча")
        
        await query.message.reply_text(
            text=f"📄 <a href='{REQUISITES_LINK}'>Реквизиты \"{legal}\"</a>\n\n"
                 "⬇️ Для оплаты услуги нужно:\n"
                 "1️⃣ В назначении платежа указать ФИО участника + название услуги\n"
                 "2️⃣ Ввести верную сумму\n"
                 "3️⃣ Произвести оплату по реквизитам✅\n\n"
                 "Пожалуйста, не забудьте прислать нам скриншот - подтверждение оплаты в следующем сообщении🙌",
            parse_mode='HTML',
            reply_markup=get_receipt_keyboard()
        )
        
    elif query.data == "send_receipt":
        await query.message.reply_text(
            "📝 Шаг 1 из 4\n\n"
            "Введите <b>ФИО участника</b>:",
            parse_mode='HTML'
        )
        return FIO_PARTICIPANT
        
    elif query.data == "contact_admin":
        await handle_contact_admin(update, context)

async def handle_contact_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = update.effective_user
    camp = context.user_data.get("selected_camp", {}).get("name", "Не выбран")
    service = context.user_data.get("selected_service", {}).get("name", "Не выбрана")
    
    notification = (f"📞 ЗАПРОС СВЯЗИ\n"
                   f"━━━━━━━━━━━━━━━\n"
                   f"👤 Пользователь: {user.full_name}\n"
                   f"🆔 ID: {user.id}\n"
                   f"📱 Username: @{user.username or 'нет'}\n"
                   f"━━━━━━━━━━━━━━━\n"
                   f"🏕️ Кэмп: {camp}\n"
                   f"📋 Услуга: {service}\n"
                   f"━━━━━━━━━━━━━━━")
    
    try:
        await context.bot.send_message(
            chat_id=ADMIN_CHAT_ID,
            text=notification
        )
    except Exception as e:
        logger.error(f"Ошибка при уведомлении админа: {e}")
    
    await query.message.reply_text(
        text=f"📞 <b>Связь с администратором</b>\n\n"
             f"Нажмите кнопку ниже, чтобы написать администратору в Telegram:",
        parse_mode='HTML',
        reply_markup=get_contact_admin_keyboard()
    )

async def handle_back_to_services(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    is_sochi = context.user_data.get("is_sochi", False)
    
    if is_sochi:
        await query.message.reply_text(
            text="<b>Какой формат поездки вы выбираете?🌝</b>",
            parse_mode='HTML',
            reply_markup=get_services_keyboard("camp", is_sochi=True)
        )
    else:
        await query.message.reply_text(
            text="<b>Какая услуга вас интересует?</b>",
            parse_mode='HTML',
            reply_markup=get_service_categories_keyboard()
        )

# ========== ОБРАБОТЧИКИ ДЛЯ ПОШАГОВОГО СБОРА ДАННЫХ (ОПЛАТА) ==========
async def fio_participant(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"Получено ФИО участника: {update.message.text}")
    context.user_data["fio_participant"] = update.message.text
    await update.message.reply_text(
        "📝 Шаг 2 из 4\n\n"
        "Введите <b>ФИО плательщика</b>:",
        parse_mode='HTML'
    )
    return FIO_PAYER

async def fio_payer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"Получено ФИО плательщика: {update.message.text}")
    context.user_data["fio_payer"] = update.message.text
    await update.message.reply_text(
        "📝 Шаг 3 из 4\n\n"
        "Введите <b>телефон для связи</b>:",
        parse_mode='HTML'
    )
    return PHONE

async def phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"Получен телефон: {update.message.text}")
    context.user_data["phone"] = update.message.text
    await update.message.reply_text(
        "📝 Шаг 4 из 4\n\n"
        "Теперь отправьте <b>фото или скан чека об оплате</b>:",
        parse_mode='HTML'
    )
    return RECEIPT_PHOTO

async def receipt_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    logger.info(f"Получен чек от пользователя {user.id}")
    
    if not (update.message.photo or update.message.document):
        await update.message.reply_text(
            "Пожалуйста, отправьте фото или скан чека об оплате"
        )
        return RECEIPT_PHOTO
    
    fio_participant = context.user_data.get("fio_participant", "Не указано")
    fio_payer = context.user_data.get("fio_payer", "Не указано")
    phone = context.user_data.get("phone", "Не указано")
    camp = context.user_data.get("selected_camp", {}).get("name", "Не выбран")
    service_data = context.user_data.get("selected_service", {})
    service_name = service_data.get("name", service_data.get("short", "Не выбрана"))
    
    caption = (
        f"💰 НОВАЯ ОПЛАТА\n"
        f"━━━━━━━━━━━━━━━\n"
        f"👤 Пользователь: {user.full_name}\n"
        f"🆔 ID: {user.id}\n"
        f"📱 Username: @{user.username or 'нет'}\n"
        f"━━━━━━━━━━━━━━━\n"
        f"🏕️ Кэмп: {camp}\n"
        f"📋 Услуга: {service_name}\n"
        f"━━━━━━━━━━━━━━━\n"
        f"👶 ФИО участника: {fio_participant}\n"
        f"👨 ФИО плательщика: {fio_payer}\n"
        f"📞 Телефон: {phone}\n"
        f"━━━━━━━━━━━━━━━"
    )
    
    try:
        if update.message.photo:
            await context.bot.send_photo(
                chat_id=ADMIN_CHAT_ID,
                photo=update.message.photo[-1].file_id,
                caption=caption
            )
        else:
            await context.bot.send_document(
                chat_id=ADMIN_CHAT_ID,
                document=update.message.document.file_id,
                caption=caption
            )
        
        await update.message.reply_text(
            "✅ Спасибо! Чек получен и отправлен администратору.\n"
            "🌟 Спасибо, что выбираете Школа мяча 🌟"
        )
    except Exception as e:
        logger.error(f"Ошибка при отправке админу: {e}")
        await update.message.reply_text(
            "✅ Спасибо! Ваш чек получен.\n"
            "🌟 Спасибо, что выбираете Школа мяча 🌟"
        )
    
    context.user_data.clear()
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Операция отменена. Нажмите /start чтобы начать заново."
    )
    context.user_data.clear()
    return ConversationHandler.END

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"Ошибка: {context.error}")

# ========== ЗАПУСК ==========
def main():
    logger.info("🚀 Запуск бота...")
    logger.info(f"👤 Администратор ID: {ADMIN_CHAT_ID}")
    
    try:
        application = Application.builder().token(BOT_TOKEN).build()
        
        payment_conv_handler = ConversationHandler(
            entry_points=[CallbackQueryHandler(handle_payment, pattern='^send_receipt$')],
            states={
                FIO_PARTICIPANT: [MessageHandler(filters.TEXT & ~filters.COMMAND, fio_participant)],
                FIO_PAYER: [MessageHandler(filters.TEXT & ~filters.COMMAND, fio_payer)],
                PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, phone)],
                RECEIPT_PHOTO: [MessageHandler(filters.PHOTO | filters.Document.ALL, receipt_photo)],
            },
            fallbacks=[CommandHandler('cancel', cancel)],
            name="payment_conversation",
            persistent=False,
        )
        
        sochi_conv_handler = ConversationHandler(
            entry_points=[CallbackQueryHandler(handle_sochi_contract, pattern='^sochi_contract_signed$')],
            states={
                SOCHI_WAIT_CONTRACT: [MessageHandler(filters.PHOTO | filters.Document.ALL, sochi_wait_contract)],
                SOCHI_FIO: [MessageHandler(filters.TEXT & ~filters.COMMAND, sochi_fio)],
                SOCHI_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, sochi_phone)],
            },
            fallbacks=[CommandHandler('cancel', cancel)],
            name="sochi_conversation",
            persistent=False,
        )
        
        application.add_handler(CommandHandler('start', start))
        application.add_handler(CommandHandler('cancel', cancel))
        application.add_handler(payment_conv_handler)
        application.add_handler(sochi_conv_handler)
        
        application.add_handler(CallbackQueryHandler(handle_camp_selection, pattern='^camp:'))
        application.add_handler(CallbackQueryHandler(handle_service_category, pattern='^service_category:'))
        application.add_handler(CallbackQueryHandler(handle_service_selection, pattern='^service:'))
        application.add_handler(CallbackQueryHandler(handle_agree, pattern='^agree$'))
        application.add_handler(CallbackQueryHandler(handle_sochi_contract, pattern='^sochi_download_contract$'))
        application.add_handler(CallbackQueryHandler(handle_payment, pattern='^(show_requisites|send_receipt|contact_admin)$'))
        application.add_handler(CallbackQueryHandler(handle_back_to_services, pattern='^back_to_services$'))
        
        application.add_error_handler(error_handler)
        
        logger.info("✅ Бот запущен!")
        application.run_polling(drop_pending_updates=True)
        
    except Exception as e:
        logger.error(f"💥 Критическая ошибка: {e}")
        raise

if __name__ == '__main__':
    main()
