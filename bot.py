import os
import logging
import sys
import re
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ForceReply
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, MessageHandler,
    filters, ContextTypes, ConversationHandler
)

# ========== КОНФИГУРАЦИЯ ==========
BOT_TOKEN = "8355392266:AAHLDpU6Zn7TInLt1ULj8cgcATM0rk3NgUk"

# ВАШ ID
ADMIN_CHAT_ID = 246014045
ADMIN_USERNAME = "Dmitry_Kh_87"
ADMIN_PHONE = "89855796779"

# Состояния для ConversationHandler
(FIO_PARTICIPANT, FIO_PAYER, PHONE, EMAIL, RECEIPT_PHOTO) = range(5)
(SOCHI_EMAIL, SOCHI_WAIT_CONTRACT, SOCHI_CATEGORY, SOCHI_SHIFT) = range(5, 9)

# ========== ДАННЫЕ ==========
PDF_LINK = "https://clck.ru/3RuZKG"
QR_LINK = "https://clck.ru/3RuZZA"
REQUISITES_LINK = PDF_LINK

# ========== ДАННЫЕ ПРОГРАММ ==========
CAMPS = [
    {
        "name": "🏕️ Солнцево (городской)",
        "address": "Ул. Богданова д. 19",
        "id": "solntsevo",
        "legal_entity": "ООО ШМП",
        "type": "city",
        "offer_text": "Школа мяча. Футбольный дневной КЭМП в Солнцево",
        "base_price_10": 39990,
        "base_price_1": 5990
    },
    {
        "name": "🏕️ Сочи (с ночёвкой)",
        "address": "Парк отель Сочи",
        "id": "sochi",
        "legal_entity": "ООО ШМП",
        "type": "overnight",
        "offer_text": "Школа мяча. Футбольный КЭМП в Сочи",
        "base_price_10": 0,
        "base_price_1": 0
    },
    {
        "name": "🏕️ Тушино (городской)",
        "address": "Ул. Лодочная д. 15 стр. 1А",
        "id": "tushino",
        "legal_entity": "ИП Зубанова / счет ШМП",
        "type": "city",
        "offer_text": "Школа мяча. Футбольный дневной КЭМП в Тушино",
        "base_price_10": 39990,
        "base_price_1": 5990
    },
    {
        "name": "🏕️ Кузьминки (городской)",
        "address": "Ул. Академика Скрябина д. 23 стр. 2",
        "id": "kuzminki",
        "legal_entity": "ИП Зубанова / счёт ДХ",
        "type": "city",
        "offer_text": "Школа мяча. Футбольный дневной КЭМП в Кузьминках",
        "base_price_10": 39990,
        "base_price_1": 5990
    },
    {
        "name": "🏕️ Хамовники (городской)",
        "address": "Ул. Плющиха 57а",
        "id": "khamovniki",
        "legal_entity": "ООО ШМП",
        "type": "city",
        "offer_text": "Школа мяча. Футбольный дневной КЭМП в Хамовниках",
        "base_price_10": 69990,
        "base_price_1": 7900
    }
]

# ========== УСЛУГИ ==========
def format_price(price: int) -> str:
    """Форматирует цену с пробелом между тысячами и символом ₽"""
    return f"{price:,}".replace(",", " ") + "₽"

# Подменю для 10 дней (смены) — БЕЗ ЦЕНЫ в кнопках, даты в скобках
CAMP_SHIFTS = [
    {"name": "смена 1", "dates": "01-12 июнь", "id": "camp_10_days_1"},
    {"name": "смена 2", "dates": "15-26 июнь", "id": "camp_10_days_2"},
    {"name": "смена 3", "dates": "29.06-10.07", "id": "camp_10_days_3"},
    {"name": "смена 4", "dates": "13-24 июль", "id": "camp_10_days_4"},
    {"name": "смена 5", "dates": "27.07-07.08", "id": "camp_10_days_5"},
    {"name": "смена 6", "dates": "10-21 авг", "id": "camp_10_days_6"},
    {"name": "смена 7", "dates": "24-27 авг", "id": "camp_10_days_7"}
]

# ТРЕНИРОВКИ
TRAINING_SERVICES = [
    {"name": "тренировка - 1 шт", "price": 1600, "id": "training_1"},
    {"name": "абонемент - 5 занятий", "price": 7000, "price_per": 1400, "id": "training_5"},
    {"name": "абонемент - 10 занятий", "price": 11500, "price_per": 1150, "id": "training_10"}
]

# ПРОЧЕЕ
OTHER_SERVICES = [
    {"name": "оплата после \"пробного дня\"", "price": 39000, "id": "trial_day"},
    {"name": "форма", "price": 4500, "id": "uniform"}
]

# Хамовники — повышенные цены
KHAMOVNIKI_TRAINING = [
    {"name": "тренировка - 1 шт", "price": 1890, "id": "training_1"},
    {"name": "абонемент - 5 занятий", "price": 7450, "price_per": 1490, "id": "training_5"},
    {"name": "абонемент - 10 занятий", "price": 12900, "price_per": 1290, "id": "training_10"}
]

KHAMOVNIKI_OTHER = [
    {"name": "оплата после \"пробного дня\"", "price": 65000, "id": "trial_day"},
    {"name": "форма", "price": 4500, "id": "uniform"}
]

# Сочи — категории и смены
SOCHI_CATEGORIES = [
    {
        "name": "«Спортсмен» (без сопровождения)",
        "id": "sochi_sportsman",
        "options": [
            {"name": "Смена МАЙ 02-08", "price": 89990, "id": "sochi_sportsman_may"},
            {"name": "Смена ИЮНЬ 19-27", "price": 114990, "id": "sochi_sportsman_june"},
            {"name": "Смена ИЮЛЬ 4-11", "price": 102490, "id": "sochi_sportsman_july"},
            {"name": "Смена АВГУСТ 1-8", "price": 102490, "id": "sochi_sportsman_august"}
        ]
    },
    {
        "name": "«Спортсмен + родитель»",
        "id": "sochi_family",
        "options": [
            {"name": "Смена МАЙ 02-08", "price": 139990, "id": "sochi_family_may"},
            {"name": "Смена ИЮНЬ 19-27", "price": 183990, "id": "sochi_family_june"},
            {"name": "Смена ИЮЛЬ 4-11", "price": 161990, "id": "sochi_family_july"},
            {"name": "Смена АВГУСТ 1-8", "price": 161990, "id": "sochi_family_august"}
        ]
    },
    {
        "name": "«Сопровождающий» (любой участник не принимающий участия в тренировках)",
        "id": "sochi_accompanist",
        "options": [
            {"name": "Смена МАЙ 02-08", "price": 59990, "id": "sochi_accompanist_may"},
            {"name": "Смена ИЮНЬ 19-27", "price": 77990, "id": "sochi_accompanist_june"},
            {"name": "Смена ИЮЛЬ 4-11", "price": 68990, "id": "sochi_accompanist_july"},
            {"name": "Смена АВГУСТ 1-8", "price": 68990, "id": "sochi_accompanist_august"}
        ]
    }
]

# ========== ЛОГИРОВАНИЕ ==========
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# ========== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ==========
def get_service_price(service_id: str, camp_id: str = None) -> int:
    """Получает цену услуги по ID"""
    # Проверяем смены обычных кэмпов
    for shift in CAMP_SHIFTS:
        if shift["id"] == service_id:
            camp = next((c for c in CAMPS if c["id"] == camp_id), None)
            if camp:
                return camp["base_price_10"]
            return 39990
    
    # Проверяем тренировки
    if camp_id == "khamovniki":
        services = KHAMOVNIKI_TRAINING
    else:
        services = TRAINING_SERVICES
    for s in services:
        if s["id"] == service_id:
            return s["price"]
    
    # Проверяем прочее
    if camp_id == "khamovniki":
        services = KHAMOVNIKI_OTHER
    else:
        services = OTHER_SERVICES
    for s in services:
        if s["id"] == service_id:
            return s["price"]
    
    # Проверяем Сочи
    for cat in SOCHI_CATEGORIES:
        for opt in cat["options"]:
            if opt["id"] == service_id:
                return opt["price"]
    
    return 0

def get_service_name(service_id: str, camp_id: str = None) -> str:
    """Получает название услуги по ID"""
    # Проверяем смены
    for shift in CAMP_SHIFTS:
        if shift["id"] == service_id:
            return f"10 дней {shift['name']} ({shift['dates']})"
    
    # Проверяем тренировки
    for s in TRAINING_SERVICES:
        if s["id"] == service_id:
            return s["name"]
    
    # Проверяем прочее
    for s in OTHER_SERVICES:
        if s["id"] == service_id:
            return s["name"]
    
    # Проверяем Сочи
    for cat in SOCHI_CATEGORIES:
        for opt in cat["options"]:
            if opt["id"] == service_id:
                return f"{cat['name']} - {opt['name']}"
    
    return service_id

# ========== КЛАВИАТУРЫ ==========
def get_camps_keyboard():
    """Клавиатура выбора программы"""
    keyboard = []
    for camp in CAMPS:
        keyboard.append([InlineKeyboardButton(camp["name"], callback_data=f"camp:{camp['id']}")])
    return InlineKeyboardMarkup(keyboard)

def get_back_to_camps_keyboard():
    """Кнопка возврата к программам"""
    keyboard = [[InlineKeyboardButton("🔙 Назад к программам", callback_data="back_to_camps")]]
    return InlineKeyboardMarkup(keyboard)

def get_sochi_pd_agree_keyboard():
    """Клавиатура согласия на ПД для Сочи"""
    keyboard = [
        [InlineKeyboardButton("✅ Даю согласие на обработку персональных данных", callback_data="sochi_pd_agree")],
        [InlineKeyboardButton("🔙 Назад к программам", callback_data="back_to_camps")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_sochi_email_sent_keyboard():
    """Клавиатура после отправки email"""
    keyboard = [
        [InlineKeyboardButton("✅ Я получил и подписал договор", callback_data="sochi_got_contract")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_contract_upload_keyboard(has_files=False):
    """Кнопка загрузки договора"""
    if has_files:
        keyboard = [[InlineKeyboardButton("✅ Договор загружен", callback_data="contract_uploaded")]]
    else:
        keyboard = [[InlineKeyboardButton("⏳ Сначала загрузите файлы", callback_data="noop")]]
    return InlineKeyboardMarkup(keyboard)

def get_sochi_categories_keyboard():
    """Категории Сочи"""
    keyboard = []
    for cat in SOCHI_CATEGORIES:
        # Сокращаем длинные названия для кнопок
        name = cat["name"]
        if len(name) > 40:
            name = cat["name"][:40] + "…"
        keyboard.append([InlineKeyboardButton(name, callback_data=f"sochi_category:{cat['id']}")])
    
    keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="back_to_main_menu")])
    return InlineKeyboardMarkup(keyboard)

def get_sochi_shifts_keyboard(category_id):
    """Смены для выбранной категории Сочи"""
    keyboard = []
    for cat in SOCHI_CATEGORIES:
        if cat["id"] == category_id:
            for opt in cat["options"]:
                keyboard.append([InlineKeyboardButton(
                    f"{opt['name']} - {format_price(opt['price'])}",
                    callback_data=f"service:{opt['id']}"
                )])
            break
    
    keyboard.append([InlineKeyboardButton("🔙 Назад к категориям", callback_data="back_to_sochi_categories")])
    return InlineKeyboardMarkup(keyboard)

def get_camp_main_menu_keyboard(camp_id):
    """Главное меню программы (для обычных программ)"""
    keyboard = [
        [InlineKeyboardButton("🏕️ КЭМП", callback_data="service_category:camp")],
        [InlineKeyboardButton("⚽ ТРЕНИРОВКИ", callback_data="service_category:training")],
        [InlineKeyboardButton("📦 ПРОЧЕЕ", callback_data="service_category:other")],
        [InlineKeyboardButton("🔙 Назад к программам", callback_data="back_to_camps")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_camp_options_keyboard(camp_id):
    """Кнопки для КЭМП (10 дней / 1 день)"""
    camp = next((c for c in CAMPS if c["id"] == camp_id), None)
    if not camp:
        return InlineKeyboardMarkup([[]])
    
    keyboard = [
        [InlineKeyboardButton(
            f"10 дней - {format_price(camp['base_price_10'])}",
            callback_data=f"base_service:camp_10_days"
        )],
        [InlineKeyboardButton(
            f"1 день - {format_price(camp['base_price_1'])}",
            callback_data=f"base_service:camp_1_day"
        )],
        [InlineKeyboardButton("🔙 Назад", callback_data="back_to_main_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_camp_shifts_keyboard(camp_id):
    """Список смен для 10 дней"""
    keyboard = []
    for shift in CAMP_SHIFTS:
        button_text = f"{shift['name']} ({shift['dates']})"
        keyboard.append([InlineKeyboardButton(button_text, callback_data=f"service:{shift['id']}")])
    
    keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="back_to_camp_options")])
    return InlineKeyboardMarkup(keyboard)

def get_training_keyboard(camp_id):
    """Кнопки для тренировок"""
    if camp_id == "khamovniki":
        services = KHAMOVNIKI_TRAINING
    else:
        services = TRAINING_SERVICES
    
    keyboard = []
    for s in services:
        text = s["name"]
        if "price_per" in s:
            text += f" - {format_price(s['price'])} ({format_price(s['price_per'])}/занятие)"
        else:
            text += f" - {format_price(s['price'])}"
        keyboard.append([InlineKeyboardButton(text, callback_data=f"service:{s['id']}")])
    
    keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="back_to_main_menu")])
    return InlineKeyboardMarkup(keyboard)

def get_other_keyboard(camp_id):
    """Кнопки для прочего"""
    if camp_id == "khamovniki":
        services = KHAMOVNIKI_OTHER
    else:
        services = OTHER_SERVICES
    
    keyboard = []
    for s in services:
        keyboard.append([InlineKeyboardButton(
            f"{s['name']} - {format_price(s['price'])}",
            callback_data=f"service:{s['id']}"
        )])
    
    keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="back_to_main_menu")])
    return InlineKeyboardMarkup(keyboard)

def get_payment_keyboard():
    """Кнопка оплаты"""
    keyboard = [[InlineKeyboardButton("💳 Оплатить", callback_data="show_requisites")]]
    return InlineKeyboardMarkup(keyboard)

def get_receipt_keyboard():
    """Кнопка отправки чека"""
    keyboard = [[InlineKeyboardButton("📤 Отправить чек об оплате", callback_data="send_receipt")]]
    return InlineKeyboardMarkup(keyboard)

# ========== ОБРАБОТЧИКИ ==========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /start"""
    context.user_data.clear()
    await update.message.reply_text(
        "🏕️ <b>Выберите программу:</b>",
        parse_mode='HTML',
        reply_markup=get_camps_keyboard()
    )

async def handle_camp_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Выбор программы"""
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
            # Сочи: согласие на ПД
            text = (
                f"<b>Вы выбрали:</b>\n"
                f"🏕️ {camp['offer_text']}\n"
                f"📍 {camp['address']}\n\n"
                f"Для продолжения необходимо дать согласие на обработку персональных данных."
            )
            
            await query.edit_message_text(
                text=text,
                parse_mode='HTML',
                reply_markup=get_sochi_pd_agree_keyboard()
            )
        else:
            # Обычные программы: оферта
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
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("✅ СОГЛАСЕН", callback_data="agree")
                ]])
            )

async def handle_sochi_pd_agree(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Согласие на ПД для Сочи"""
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        text="📝 Введите ваш email для получения договора:",
        parse_mode='HTML'
    )
    return SOCHI_EMAIL

async def handle_sochi_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получение email для Сочи"""
    email = update.message.text.strip()
    logger.info(f"Получен email для Сочи: {email}")
    
    if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
        await update.message.reply_text(
            "Пожалуйста, введите корректный email (например, name@domain.ru)"
        )
        return SOCHI_EMAIL
    
    context.user_data["sochi_email"] = email
    
    user = update.effective_user
    camp = context.user_data.get("selected_camp", {}).get("name", "Не выбран")
    
    # Уведомление менеджеру
    notification = (
        f"📧 НОВАЯ ЗАЯВКА (Сочи)\n"
        f"━━━━━━━━━━━━━━━\n"
        f"👤 Пользователь: {user.full_name}\n"
        f"🆔 ID: {user.id}\n"
        f"📱 Username: @{user.username or 'нет'}\n"
        f"📧 Email: {email}\n"
        f"━━━━━━━━━━━━━━━\n"
        f"🏕️ Программа: {camp}\n"
        f"━━━━━━━━━━━━━━━\n"
        f"Менеджеру: отправить договор на указанный email"
    )
    
    try:
        await context.bot.send_message(
            chat_id=ADMIN_CHAT_ID,
            text=notification
        )
    except Exception as e:
        logger.error(f"Ошибка при отправке уведомления: {e}")
    
    await update.message.reply_text(
        "✅ Спасибо! Ваши данные отправлены менеджеру.\n"
        "Договор будет отправлен на указанный email в ближайшее время.\n\n"
        "После получения и подписания договора, нажмите кнопку ниже:",
        reply_markup=get_sochi_email_sent_keyboard()
    )
    
    return ConversationHandler.END

async def handle_sochi_got_contract(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Пользователь получил и подписал договор"""
    query = update.callback_query
    await query.answer()
    
    context.user_data["sochi_files"] = []
    
    await query.message.edit_text(
        "📎 Пожалуйста, отправьте скан или фото ВСЕХ СТРАНИЦ подписанного договора.\n"
        "После загрузки всех страниц нажмите кнопку «✅ Договор загружен»",
        reply_markup=get_contract_upload_keyboard(has_files=False)
    )
    return SOCHI_WAIT_CONTRACT

async def handle_sochi_file_upload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Загрузка файлов договора для Сочи"""
    user = update.effective_user
    
    if not (update.message.document or update.message.photo):
        return SOCHI_WAIT_CONTRACT
    
    file_info = {
        "type": "document" if update.message.document else "photo",
        "file_id": update.message.document.file_id if update.message.document else update.message.photo[-1].file_id
    }
    
    if "sochi_files" not in context.user_data:
        context.user_data["sochi_files"] = []
    
    context.user_data["sochi_files"].append(file_info)
    
    # Отправляем файл админу
    camp = context.user_data.get("selected_camp", {}).get("name", "Не выбран")
    email = context.user_data.get("sochi_email", "Не указан")
    
    caption = (f"📄 Страница договора (Сочи)\n"
              f"━━━━━━━━━━━━━━━\n"
              f"👤 Пользователь: {user.full_name}\n"
              f"🆔 ID: {user.id}\n"
              f"📱 Username: @{user.username or 'нет'}\n"
              f"📧 Email: {email}\n"
              f"━━━━━━━━━━━━━━━\n"
              f"🏕️ Программа: {camp}\n"
              f"📄 Страница #{len(context.user_data['sochi_files'])}\n"
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
    except Exception as e:
        logger.error(f"Ошибка при отправке файла: {e}")
    
    await update.message.reply_text(
        f"✅ Страница {len(context.user_data['sochi_files'])} получена. "
        f"Если это последняя страница, нажмите кнопку ниже.",
        reply_markup=get_contract_upload_keyboard(has_files=True)
    )
    
    return SOCHI_WAIT_CONTRACT

async def handle_contract_uploaded(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Завершение загрузки договора"""
    query = update.callback_query
    await query.answer()
    
    if not context.user_data.get("sochi_files"):
        await query.message.edit_text(
            "❌ Вы не загрузили ни одного файла. Пожалуйста, сначала загрузите скан договора.",
            reply_markup=get_contract_upload_keyboard(has_files=False)
        )
        return SOCHI_WAIT_CONTRACT
    
    user = update.effective_user
    camp = context.user_data.get("selected_camp", {}).get("name", "Не выбран")
    files_count = len(context.user_data["sochi_files"])
    email = context.user_data.get("sochi_email", "Не указан")
    
    # Уведомление админу
    notification = (f"📄 ЗАГРУЗКА ДОГОВОРА ЗАВЕРШЕНА\n"
                   f"━━━━━━━━━━━━━━━\n"
                   f"👤 Пользователь: {user.full_name}\n"
                   f"🆔 ID: {user.id}\n"
                   f"📱 Username: @{user.username or 'нет'}\n"
                   f"📧 Email: {email}\n"
                   f"━━━━━━━━━━━━━━━\n"
                   f"🏕️ Программа: {camp}\n"
                   f"📄 Загружено страниц: {files_count}\n"
                   f"━━━━━━━━━━━━━━━")
    
    try:
        await context.bot.send_message(
            chat_id=ADMIN_CHAT_ID,
            text=notification
        )
    except Exception as e:
        logger.error(f"Ошибка при уведомлении админа: {e}")
    
    await query.message.edit_text(
        "✅ Спасибо! Договор получен.\n\n"
        "<b>Выберите тип участия:</b>",
        parse_mode='HTML',
        reply_markup=get_sochi_categories_keyboard()
    )
    
    context.user_data.pop("sochi_files", None)
    return ConversationHandler.END

async def handle_agree(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Согласие с офертой для обычных программ"""
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_reply_markup(reply_markup=None)
    
    camp = context.user_data.get("selected_camp")
    
    await query.message.reply_text(
        text="<b>Какая услуга вас интересует?</b>",
        parse_mode='HTML',
        reply_markup=get_camp_main_menu_keyboard(camp["id"])
    )

async def handle_service_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Выбор категории услуг для обычных программ"""
    query = update.callback_query
    await query.answer()
    
    category = query.data.split(":")[1]
    camp = context.user_data.get("selected_camp")
    
    if category == "camp":
        await query.edit_message_text(
            text="<b>Выберите услугу:</b>",
            parse_mode='HTML',
            reply_markup=get_camp_options_keyboard(camp["id"])
        )
    elif category == "training":
        await query.edit_message_text(
            text="<b>Выберите тренировку:</b>",
            parse_mode='HTML',
            reply_markup=get_training_keyboard(camp["id"])
        )
    elif category == "other":
        await query.edit_message_text(
            text="<b>Выберите услугу:</b>",
            parse_mode='HTML',
            reply_markup=get_other_keyboard(camp["id"])
        )

async def handle_base_service(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Выбор базовой услуги (10 дней / 1 день)"""
    query = update.callback_query
    await query.answer()
    
    service_id = query.data.split(":")[1]
    camp = context.user_data.get("selected_camp")
    
    if service_id == "camp_10_days":
        await query.edit_message_text(
            text="<b>Выберите смену:</b>",
            parse_mode='HTML',
            reply_markup=get_camp_shifts_keyboard(camp["id"])
        )
    else:
        # 1 день
        await handle_service_selection(update, context, service_id)

async def handle_sochi_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Выбор категории в Сочи"""
    query = update.callback_query
    await query.answer()
    
    category_id = query.data.split(":")[1]
    
    await query.edit_message_text(
        text="<b>Выберите смену:</b>",
        parse_mode='HTML',
        reply_markup=get_sochi_shifts_keyboard(category_id)
    )

async def handle_service_selection(update: Update, context: ContextTypes.DEFAULT_TYPE, service_id=None):
    """Выбор конкретной услуги"""
    if not service_id:
        query = update.callback_query
        await query.answer()
        service_id = query.data.split(":")[1]
    else:
        query = update.callback_query
    
    camp = context.user_data.get("selected_camp")
    
    price = get_service_price(service_id, camp["id"] if camp else None)
    service_name = get_service_name(service_id, camp["id"] if camp else None)
    
    context.user_data["selected_service"] = {
        "id": service_id,
        "name": service_name,
        "price": price
    }
    
    if camp["id"] == "sochi":
        # Для Сочи после выбора смены — сразу оплата
        await query.edit_message_text(
            text=(
                f"<b>🏟 Вы выбрали:</b>\n"
                f"{service_name} - {format_price(price)}\n\n"
                f"<b>📍 {camp['name']}</b>\n"
                f"{camp['address']}"
            ),
            parse_mode='HTML',
            reply_markup=get_payment_keyboard()
        )
        return ConversationHandler.END
    else:
        # Для обычных программ
        await query.edit_message_text(
            text=(
                f"<b>🏟 Вы выбрали УСЛУГУ:</b>\n"
                f"{service_name} - {format_price(price)}\n\n"
                f"<b>📍 {camp['name']}</b>\n"
                f"{camp['address']}"
            ),
            parse_mode='HTML',
            reply_markup=get_payment_keyboard()
        )
        return ConversationHandler.END

async def handle_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка оплаты"""
    query = update.callback_query
    await query.answer()
    
    if query.data == "show_requisites":
        camp = context.user_data.get("selected_camp", {})
        legal = camp.get("legal_entity", "Школа мяча")
        
        text = (
            f"📄 <a href='{REQUISITES_LINK}'>PDF реквизиты \"{legal}\"</a>\n\n"
            f"Для оплаты услуги по реквизитам, пожалуйста, воспользуйтесь нашим QR кодом:\n\n"
            f"⬇️ Для этого нужно:\n\n"
            f"1️⃣ Сохранить код в фотопленке;\n"
            f"2️⃣ Открыть приложение банка;\n"
            f"3️⃣ Нажать «Сканировать из файла» и выбрать в фотопленке QR код;\n"
            f"4️⃣ Вручную в назначении платежа указать ФИО участника + название услуги\n"
            f"5️⃣ Ввести верную сумму\n"
            f"6️⃣ Произвести оплату по реквизитам✅\n\n"
            f"✅ Пожалуйста, не забудьте прислать нам скриншот - подтверждение оплаты в следующем сообщении🙌"
        )
        
        await query.message.reply_photo(
            photo=QR_LINK,
            caption=text,
            parse_mode='HTML',
            reply_markup=get_receipt_keyboard()
        )
        
    elif query.data == "send_receipt":
        await query.message.reply_text(
            "📝 Шаг 1 из 5\n\n"
            "Введите <b>ФИО участника</b>:",
            parse_mode='HTML'
        )
        return FIO_PARTICIPANT

async def fio_participant(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Шаг 1: ФИО участника"""
    context.user_data["fio_participant"] = update.message.text
    await update.message.reply_text(
        "📝 Шаг 2 из 5\n\n"
        "Введите <b>ФИО плательщика</b>:",
        parse_mode='HTML'
    )
    return FIO_PAYER

async def fio_payer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Шаг 2: ФИО плательщика"""
    context.user_data["fio_payer"] = update.message.text
    await update.message.reply_text(
        "📝 Шаг 3 из 5\n\n"
        "Введите <b>телефон для связи</b> (например, 89001234567):",
        parse_mode='HTML',
        reply_markup=ForceReply(input_field_placeholder="89001234567")
    )
    return PHONE

async def phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Шаг 3: телефон"""
    phone_input = update.message.text.strip()
    
    digits = re.sub(r'\D', '', phone_input)
    if len(digits) == 11 and digits.startswith(('7', '8')):
        formatted = f"8{digits[1:4]}-{digits[4:7]}-{digits[7:9]}-{digits[9:11]}"
        context.user_data["phone"] = formatted
    elif len(digits) == 10:
        formatted = f"8{digits[0:3]}-{digits[3:6]}-{digits[6:8]}-{digits[8:10]}"
        context.user_data["phone"] = formatted
    else:
        await update.message.reply_text(
            "Пожалуйста, введите корректный номер телефона (например, 89001234567)"
        )
        return PHONE
    
    await update.message.reply_text(
        "📝 Шаг 4 из 5\n\n"
        "Введите <b>ваш email</b>:",
        parse_mode='HTML'
    )
    return EMAIL

async def email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Шаг 4: email"""
    email = update.message.text.strip()
    
    if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
        await update.message.reply_text(
            "Пожалуйста, введите корректный email (например, name@domain.ru)"
        )
        return EMAIL
    
    context.user_data["email"] = email
    
    await update.message.reply_text(
        "📝 Шаг 5 из 5\n\n"
        "Теперь отправьте <b>фото или скан чека об оплате</b>:",
        parse_mode='HTML'
    )
    return RECEIPT_PHOTO

async def receipt_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Шаг 5: чек об оплате"""
    user = update.effective_user
    
    if not (update.message.photo or update.message.document):
        await update.message.reply_text(
            "Пожалуйста, отправьте фото или скан чека об оплате"
        )
        return RECEIPT_PHOTO
    
    fio_participant = context.user_data.get("fio_participant", "Не указано")
    fio_payer = context.user_data.get("fio_payer", "Не указано")
    phone = context.user_data.get("phone", "Не указано")
    email = context.user_data.get("email", "Не указано")
    camp = context.user_data.get("selected_camp", {}).get("name", "Не выбран")
    service_data = context.user_data.get("selected_service", {})
    service_name = service_data.get("name", "Не выбрана")
    service_price = service_data.get("price", 0)
    
    caption = (
        f"💰 НОВАЯ ОПЛАТА\n"
        f"━━━━━━━━━━━━━━━\n"
        f"👤 Пользователь: {user.full_name}\n"
        f"🆔 ID: {user.id}\n"
        f"📱 Username: @{user.username or 'нет'}\n"
        f"━━━━━━━━━━━━━━━\n"
        f"🏕️ Программа: {camp}\n"
        f"📋 Услуга: {service_name}\n"
        f"💵 Сумма: {format_price(service_price)}\n"
        f"━━━━━━━━━━━━━━━\n"
        f"👶 ФИО участника: {fio_participant}\n"
        f"👨 ФИО плательщика: {fio_payer}\n"
        f"📞 Телефон: {phone}\n"
        f"📧 Email: {email}\n"
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
            "✅ Спасибо! Чек получен. 🌟 Спасибо, что выбираете Школа мяча! 🌟"
        )
    except Exception as e:
        logger.error(f"Ошибка при отправке админу: {e}")
        await update.message.reply_text(
            "✅ Спасибо! Ваш чек получен. 🌟 Спасибо, что выбираете Школа мяча! 🌟"
        )
    
    context.user_data.clear()
    return ConversationHandler.END

async def handle_back_to_camps(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Возврат к выбору программы"""
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "🏕️ <b>Выберите программу:</b>",
        parse_mode='HTML',
        reply_markup=get_camps_keyboard()
    )

async def handle_back_to_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Возврат в главное меню программы"""
    query = update.callback_query
    await query.answer()
    
    camp = context.user_data.get("selected_camp")
    
    await query.edit_message_text(
        text="<b>Какая услуга вас интересует?</b>",
        parse_mode='HTML',
        reply_markup=get_camp_main_menu_keyboard(camp["id"])
    )

async def handle_back_to_camp_options(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Возврат к выбору 10 дней / 1 день"""
    query = update.callback_query
    await query.answer()
    
    camp = context.user_data.get("selected_camp")
    
    await query.edit_message_text(
        text="<b>Выберите услугу:</b>",
        parse_mode='HTML',
        reply_markup=get_camp_options_keyboard(camp["id"])
    )

async def handle_back_to_sochi_categories(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Возврат к категориям Сочи"""
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        text="<b>Выберите тип участия:</b>",
        parse_mode='HTML',
        reply_markup=get_sochi_categories_keyboard()
    )

async def noop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Заглушка для неактивных кнопок"""
    query = update.callback_query
    await query.answer("Сначала выполните предыдущие действия", show_alert=True)

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик ошибок"""
    logger.error(f"Ошибка: {context.error}")

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отмена операции"""
    await update.message.reply_text(
        "Операция отменена. Нажмите /start чтобы начать заново."
    )
    context.user_data.clear()
    return ConversationHandler.END

# ========== ЗАПУСК ==========
def main():
    logger.info("🚀 Запуск бота...")
    logger.info(f"👤 Администратор ID: {ADMIN_CHAT_ID}")
    
    try:
        application = Application.builder().token(BOT_TOKEN).build()
        
        # ConversationHandler для оплаты (5 шагов)
        payment_conv_handler = ConversationHandler(
            entry_points=[CallbackQueryHandler(handle_payment, pattern='^send_receipt$')],
            states={
                FIO_PARTICIPANT: [MessageHandler(filters.TEXT & ~filters.COMMAND, fio_participant)],
                FIO_PAYER: [MessageHandler(filters.TEXT & ~filters.COMMAND, fio_payer)],
                PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, phone)],
                EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, email)],
                RECEIPT_PHOTO: [MessageHandler(filters.PHOTO | filters.Document.ALL, receipt_photo)],
            },
            fallbacks=[CommandHandler('cancel', cancel)],
            name="payment_conversation",
            persistent=False,
        )
        
        # ConversationHandler для email в Сочи
        sochi_email_conv_handler = ConversationHandler(
            entry_points=[CallbackQueryHandler(handle_sochi_pd_agree, pattern='^sochi_pd_agree$')],
            states={
                SOCHI_EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_sochi_email)],
            },
            fallbacks=[CommandHandler('cancel', cancel)],
            name="sochi_email_conversation",
            persistent=False,
        )
        
        # ConversationHandler для загрузки договора Сочи
        sochi_contract_conv_handler = ConversationHandler(
            entry_points=[CallbackQueryHandler(handle_sochi_got_contract, pattern='^sochi_got_contract$')],
            states={
                SOCHI_WAIT_CONTRACT: [
                    MessageHandler(filters.PHOTO | filters.Document.ALL, handle_sochi_file_upload),
                    CallbackQueryHandler(handle_contract_uploaded, pattern='^contract_uploaded$'),
                ],
            },
            fallbacks=[CommandHandler('cancel', cancel)],
            name="sochi_contract_conversation",
            persistent=False,
        )
        
        # Добавляем обработчики
        application.add_handler(CommandHandler('start', start))
        application.add_handler(CommandHandler('cancel', cancel))
        application.add_handler(payment_conv_handler)
        application.add_handler(sochi_email_conv_handler)
        application.add_handler(sochi_contract_conv_handler)
        
        # CallbackQueryHandler
        application.add_handler(CallbackQueryHandler(handle_camp_selection, pattern='^camp:'))
        application.add_handler(CallbackQueryHandler(handle_agree, pattern='^agree$'))
        application.add_handler(CallbackQueryHandler(handle_service_category, pattern='^service_category:'))
        application.add_handler(CallbackQueryHandler(handle_base_service, pattern='^base_service:'))
        application.add_handler(CallbackQueryHandler(handle_sochi_category, pattern='^sochi_category:'))
        application.add_handler(CallbackQueryHandler(handle_service_selection, pattern='^service:'))
        application.add_handler(CallbackQueryHandler(handle_payment, pattern='^(show_requisites|send_receipt)$'))
        application.add_handler(CallbackQueryHandler(handle_back_to_camps, pattern='^back_to_camps$'))
        application.add_handler(CallbackQueryHandler(handle_back_to_main_menu, pattern='^back_to_main_menu$'))
        application.add_handler(CallbackQueryHandler(handle_back_to_camp_options, pattern='^back_to_camp_options$'))
        application.add_handler(CallbackQueryHandler(handle_back_to_sochi_categories, pattern='^back_to_sochi_categories$'))
        application.add_handler(CallbackQueryHandler(noop, pattern='^noop$'))
        
        application.add_error_handler(error_handler)
        
        logger.info("✅ Бот запущен!")
        application.run_polling(drop_pending_updates=True)
        
    except Exception as e:
        logger.error(f"💥 Критическая ошибка: {e}")
        raise

if __name__ == '__main__':
    main()
