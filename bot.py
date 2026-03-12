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

# Старый админ (для отчетов)
ADMIN_CHAT_ID = 42038232
ADMIN_USERNAME = "Dmitry_Kh_87"
ADMIN_PHONE = "89855796779"

# Новый менеджер (для связи и тоже для отчетов)
MANAGER_CHAT_ID = 1457666818
MANAGER_USERNAME = "SBall_manager"
MANAGER_PHONE = "89855796779"

# Список всех, кто получает уведомления
NOTIFY_IDS = [ADMIN_CHAT_ID, MANAGER_CHAT_ID]  # Оба получают отчеты

# Ссылка на согласие на обработку персональных данных
PERSONAL_DATA_CONSENT_LINK = "https://sportlead.ru/media/sball/company_Soglasie_na_obrabotku_personalnyh_dannyh.docx"

# Состояния для ConversationHandler
(FIO_PARTICIPANT, FIO_PAYER, PHONE, EMAIL, RECEIPT_PHOTO) = range(5)
(SOCHI_EMAIL, SOCHI_WAIT_CONTRACT, SOCHI_CATEGORY, SOCHI_SHIFT) = range(5, 9)

# ========== QR-КОДЫ ДЛЯ ОПЛАТЫ ==========
# Все QR-коды как PNG (фото)
QR_FILES = {
    "solntsevo": {
        "type": "png",
        "file_id": "AgACAgIAAxkBAAIC0mmrICbDGZNa7VoXNbR9xlnsEpfWAAIXGGsb8aNZSVMAAa8_oHRJyAEAAwIAA3gAAzoE",
        "description": "🏕️ Солнцево"
    },
    "tushino": {
        "type": "png",
        "file_id": "AgACAgIAAxkBAAIC0mmrICbDGZNa7VoXNbR9xlnsEpfWAAIXGGsb8aNZSVMAAa8_oHRJyAEAAwIAA3gAAzoE",
        "description": "🏕️ Тушино"
    },
    "kuzminki": {
        "type": "png",
        "file_id": "AgACAgIAAxkBAAICt2mq8lvFWHDIx6X1vb0GKEFXfk0FAAJoFmsb8aNZSfp8PkP0s5S3AQADAgADeAADOgQ",
        "description": "🏕️ Кузьминки"
    },
    "khamovniki": {
        "type": "png",
        "file_id": "AgACAgIAAxkBAAICy2mrF3gDxG-v86_d5npcoeMQONqSAALXF2sb8aNZSccXmEjwHAeAAQADAgADeQADOgQ",
        "description": "🏕️ Хамовники"
    },
    "sochi": {
        "type": "png",
        "file_id": "AgACAgIAAxkBAAICy2mrF3gDxG-v86_d5npcoeMQONqSAALXF2sb8aNZSccXmEjwHAeAAQADAgADeQADOgQ",
        "description": "🏕️ Сочи"
    }
}

# ========== ДАННЫЕ ==========
# Ссылки на оферты для каждого кэмпа
OFFER_LINKS = {
    "solntsevo": "https://sportlead.ru/media/sball/company_Oferta_kemp_IP_Zubanova_Solntsevo_2026.docx",
    "tushino": "https://sportlead.ru/media/sball/company_Oferta_kemp_IP_Zubanova_Tushino_2026.docx",
    "kuzminki": "https://sportlead.ru/media/sball/company_Oferta_kemp_IP_Zubanova_Kuzminki_2026.docx",
    "khamovniki": "https://sportlead.ru/media/sball/company_Oferta_kemp_ShMP_2026.docx",
    "sochi": ""  # для Сочи договор не нужен, только согласие на ПД
}

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

# Подменю для 10 дней (смены) — обновленный формат дат
CAMP_SHIFTS = [
    {"name": "смена 1", "dates": "01.06-12.06", "id": "camp_10_days_1"},
    {"name": "смена 2", "dates": "15.06-26.06", "id": "camp_10_days_2"},
    {"name": "смена 3", "dates": "29.06-10.07", "id": "camp_10_days_3"},
    {"name": "смена 4", "dates": "13.07-24.07", "id": "camp_10_days_4"},
    {"name": "смена 5", "dates": "27.07-07.08", "id": "camp_10_days_5"},
    {"name": "смена 6", "dates": "10.08-21.08", "id": "camp_10_days_6"},
    {"name": "смена 7", "dates": "24.08-28.08", "id": "camp_10_days_7"}
]

# ТРЕНИРОВКИ
TRAINING_SERVICES = [
    {"name": "тренировка - 1 шт", "price": 1600, "id": "training_1"},
    {"name": "абонемент - 5 занятий", "price": 7000, "price_per": 1400, "id": "training_5"},
    {"name": "абонемент - 10 занятий", "price": 11500, "price_per": 1150, "id": "training_10"}
]

# ПРОЧЕЕ - добавлена кнопка "Индивидуальные условия"
OTHER_SERVICES = [
    {"name": "оплата после \"пробного дня\"", "price": 39000, "id": "trial_day"},
    {"name": "форма", "price": 4500, "id": "uniform"},
    {"name": "📝 Индивидуальные условия", "price": 0, "id": "individual"}
]

# Хамовники — повышенные цены
KHAMOVNIKI_TRAINING = [
    {"name": "тренировка - 1 шт", "price": 1890, "id": "training_1"},
    {"name": "абонемент - 5 занятий", "price": 7450, "price_per": 1490, "id": "training_5"},
    {"name": "абонемент - 10 занятий", "price": 12900, "price_per": 1290, "id": "training_10"}
]

KHAMOVNIKI_OTHER = [
    {"name": "оплата после \"пробного дня\"", "price": 65000, "id": "trial_day"},
    {"name": "форма", "price": 4500, "id": "uniform"},
    {"name": "📝 Индивидуальные условия", "price": 0, "id": "individual"}
]

# Специальная услуга для Сочи (после загрузки договора)
SOCHI_SERVICE = {
    "name": "🏕️ Поездка в Сочи",
    "price": 0,
    "id": "sochi_trip"
}

# Сочи — категории и смены (оставлено для совместимости, но теперь не используется)
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
    
    # Проверяем Сочи (специальная услуга)
    if service_id == "sochi_trip":
        return 0
    
    # Проверяем старые категории Сочи (для совместимости)
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
    
    # Проверяем специальную услугу Сочи
    if service_id == "sochi_trip":
        return "🏕️ Поездка в Сочи"
    
    # Проверяем индивидуальные условия
    if service_id == "individual":
        return "📝 Индивидуальные условия"
    
    # Проверяем старые категории Сочи (для совместимости)
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
        [InlineKeyboardButton("📞 Связаться с менеджером", callback_data="contact_admin")],
        [InlineKeyboardButton("🔙 Назад к программам", callback_data="back_to_camps")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_sochi_email_sent_keyboard():
    """Клавиатура после отправки email"""
    keyboard = [
        [InlineKeyboardButton("✅ Я получил и подписал договор", callback_data="sochi_got_contract")],
        [InlineKeyboardButton("📞 Связаться с менеджером", callback_data="contact_admin")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_contract_upload_keyboard(has_files=False):
    """Кнопка загрузки договора"""
    keyboard = []
    if has_files:
        keyboard.append([InlineKeyboardButton("✅ Договор загружен", callback_data="contract_uploaded")])
    else:
        keyboard.append([InlineKeyboardButton("⏳ Сначала загрузите файлы", callback_data="noop")])
    keyboard.append([InlineKeyboardButton("📞 Связаться с менеджером", callback_data="contact_admin")])
    keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="back_to_previous")])
    return InlineKeyboardMarkup(keyboard)

def get_sochi_categories_keyboard():
    """Категории Сочи (больше не используется, оставлено для совместимости)"""
    keyboard = []
    return InlineKeyboardMarkup(keyboard)

def get_sochi_shifts_keyboard(category_id):
    """Смены для выбранной категории Сочи (больше не используется)"""
    keyboard = []
    return InlineKeyboardMarkup(keyboard)

def get_camp_main_menu_keyboard(camp_id):
    """Главное меню программы (для обычных программ)"""
    keyboard = [
        [InlineKeyboardButton("🏕️ КЭМП", callback_data="service_category:camp")],
        [InlineKeyboardButton("⚽ ТРЕНИРОВКИ", callback_data="service_category:training")],
        [InlineKeyboardButton("📦 ПРОЧЕЕ", callback_data="service_category:other")],
        [InlineKeyboardButton("📞 Связаться с менеджером", callback_data="contact_admin")],
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
        [InlineKeyboardButton("📞 Связаться с менеджером", callback_data="contact_admin")],
        [InlineKeyboardButton("🔙 Назад", callback_data="back_to_main_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_camp_shifts_keyboard(camp_id):
    """Список смен для 10 дней"""
    keyboard = []
    for shift in CAMP_SHIFTS:
        button_text = f"{shift['name']} ({shift['dates']})"
        keyboard.append([InlineKeyboardButton(button_text, callback_data=f"service:{shift['id']}")])
    
    keyboard.append([InlineKeyboardButton("📞 Связаться с менеджером", callback_data="contact_admin")])
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
    
    keyboard.append([InlineKeyboardButton("📞 Связаться с менеджером", callback_data="contact_admin")])
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
            f"{s['name']}" + (f" - {format_price(s['price'])}" if s['price'] > 0 else ""),
            callback_data=f"service:{s['id']}"
        )])
    
    keyboard.append([InlineKeyboardButton("📞 Связаться с менеджером", callback_data="contact_admin")])
    keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="back_to_main_menu")])
    return InlineKeyboardMarkup(keyboard)

def get_payment_keyboard():
    """Кнопка оплаты"""
    keyboard = [
        [InlineKeyboardButton("💳 Оплатить", callback_data="show_requisites")],
        [InlineKeyboardButton("📞 Связаться с менеджером", callback_data="contact_admin")],
        [InlineKeyboardButton("🔙 Назад", callback_data="back_to_services")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_receipt_keyboard():
    """Кнопки после показа реквизитов"""
    keyboard = [
        [InlineKeyboardButton("📤 Отправить чек об оплате", callback_data="send_receipt")],
        [InlineKeyboardButton("📞 Связаться с менеджером", callback_data="contact_admin")],
        [InlineKeyboardButton("🔙 Назад", callback_data="back_to_services")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_contact_admin_keyboard():
    """Кнопка связи с менеджером - теперь ведет на нового менеджера @SBall_manager"""
    keyboard = [
        [InlineKeyboardButton("📞 Написать менеджеру", url=f"https://t.me/{MANAGER_USERNAME}")],
        [InlineKeyboardButton("🔙 Назад к услугам", callback_data="back_to_services")]
    ]
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
        
        # Получаем ссылку на оферту для этого кэмпа
        offer_link = OFFER_LINKS.get(camp_id, "https://clck.ru/3RuZKG")
        
        if camp_id == "sochi":
            # Сочи: только согласие на ПД, без договора
            text = (
                f"<b>Вы выбрали:</b>\n"
                f"🏕️ {camp['offer_text']}\n"
                f"📍 {camp['address']}\n\n"
                f"📄 <a href='{PERSONAL_DATA_CONSENT_LINK}'>Согласие на обработку персональных данных</a>\n\n"
                f"Для продолжения необходимо дать согласие на обработку персональных данных."
            )
            
            await query.edit_message_text(
                text=text,
                parse_mode='HTML',
                reply_markup=get_sochi_pd_agree_keyboard()
            )
        else:
            # Обычные программы: оферта + согласие на ПД
            text = (
                f"<b>Вы выбрали:</b>\n"
                f"🏕️ {camp['offer_text']}\n"
                f"📍 {camp['address']}\n\n"
                f"📄 <a href='{offer_link}'>Оферта (PDF)</a>\n"
                f"📄 <a href='{PERSONAL_DATA_CONSENT_LINK}'>Согласие на обработку ПД</a>\n\n"
                f"Нажимая «Согласен», вы подтверждаете, что ознакомились и согласны с условиями оферты и согласия на обработку ПД."
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
    """Согласие на ПД для Сочи - переход к запросу email"""
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        text="📝 Введите ваш email для получения договора:",
        parse_mode='HTML',
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("📞 Связаться с менеджером", callback_data="contact_admin")
        ]])
    )
    return SOCHI_EMAIL

async def handle_sochi_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получение email для Сочи"""
    email = update.message.text.strip()
    user_id = update.effective_user.id
    
    logger.info(f"Пользователь {user_id} ввёл email для Сочи")
    
    if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
        await update.message.reply_text(
            "Пожалуйста, введите корректный email (например, name@domain.ru)"
        )
        return SOCHI_EMAIL
    
    context.user_data["sochi_email"] = email
    
    user = update.effective_user
    camp = context.user_data.get("selected_camp", {}).get("name", "Не выбран")
    
    # Уведомление ВСЕМ менеджерам
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
    
    for chat_id in NOTIFY_IDS:
        try:
            await context.bot.send_message(
                chat_id=chat_id,
                text=notification
            )
        except Exception as e:
            logger.error(f"Ошибка при отправке уведомления {chat_id}: {e}")
    
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
    
    user_id = update.effective_user.id
    logger.info(f"Пользователь {user_id} подтвердил получение договора")
    
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
    user_id = user.id
    
    if not (update.message.document or update.message.photo):
        return SOCHI_WAIT_CONTRACT
    
    file_info = {
        "type": "document" if update.message.document else "photo",
        "file_id": update.message.document.file_id if update.message.document else update.message.photo[-1].file_id
    }
    
    if "sochi_files" not in context.user_data:
        context.user_data["sochi_files"] = []
    
    context.user_data["sochi_files"].append(file_info)
    
    logger.info(f"Пользователь {user_id} загрузил страницу {len(context.user_data['sochi_files'])} договора")
    
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
    
    # Отправляем ВСЕМ менеджерам
    for chat_id in NOTIFY_IDS:
        try:
            if update.message.document:
                await context.bot.send_document(
                    chat_id=chat_id,
                    document=update.message.document.file_id,
                    caption=caption
                )
            else:
                await context.bot.send_photo(
                    chat_id=chat_id,
                    photo=update.message.photo[-1].file_id,
                    caption=caption
                )
        except Exception as e:
            logger.error(f"Ошибка при отправке файла {chat_id}: {e}")
    
    await update.message.reply_text(
        f"✅ Страница {len(context.user_data['sochi_files'])} получена. "
        f"Если это последняя страница, нажмите кнопку ниже.",
        reply_markup=get_contract_upload_keyboard(has_files=True)
    )
    
    return SOCHI_WAIT_CONTRACT

async def handle_contract_uploaded(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Завершение загрузки договора - переход к оплате Сочи"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    
    if not context.user_data.get("sochi_files"):
        logger.info(f"Пользователь {user_id} попытался завершить загрузку без файлов")
        await query.message.edit_text(
            "❌ Вы не загрузили ни одного файла. Пожалуйста, сначала загрузите скан договора.",
            reply_markup=get_contract_upload_keyboard(has_files=False)
        )
        return SOCHI_WAIT_CONTRACT
    
    user = update.effective_user
    camp = context.user_data.get("selected_camp", {}).get("name", "Не выбран")
    files_count = len(context.user_data["sochi_files"])
    email = context.user_data.get("sochi_email", "Не указан")
    
    logger.info(f"Пользователь {user_id} завершил загрузку договора ({files_count} стр.)")
    
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
    
    # Уведомляем ВСЕХ менеджеров
    for chat_id in NOTIFY_IDS:
        try:
            await context.bot.send_message(
                chat_id=chat_id,
                text=notification
            )
        except Exception as e:
            logger.error(f"Ошибка при уведомлении {chat_id}: {e}")
    
    # Устанавливаем специальную услугу для Сочи
    context.user_data["selected_service"] = {
        "id": "sochi_trip",
        "name": "🏕️ Поездка в Сочи",
        "price": 0
    }
    
    # Сразу переходим к оплате
    await query.message.edit_text(
        text=(
            f"<b>✅ Договор получен!</b>\n\n"
            f"<b>🏟 Вы выбрали:</b>\n"
            f"🏕️ Поездка в Сочи\n\n"
            f"<b>📍 Парк отель Сочи</b>"
        ),
        parse_mode='HTML',
        reply_markup=get_payment_keyboard()
    )
    
    context.user_data.pop("sochi_files", None)
    return ConversationHandler.END

async def handle_agree(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Согласие с офертой для обычных программ"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    logger.info(f"Пользователь {user_id} согласился с офертой")
    
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
    """Выбор категории в Сочи (больше не используется)"""
    pass

async def handle_service_selection(update: Update, context: ContextTypes.DEFAULT_TYPE, service_id=None):
    """Выбор конкретной услуги"""
    if not service_id:
        query = update.callback_query
        await query.answer()
        service_id = query.data.split(":")[1]
    else:
        query = update.callback_query
    
    user_id = update.effective_user.id
    camp = context.user_data.get("selected_camp")
    
    price = get_service_price(service_id, camp["id"] if camp else None)
    service_name = get_service_name(service_id, camp["id"] if camp else None)
    
    context.user_data["selected_service"] = {
        "id": service_id,
        "name": service_name,
        "price": price
    }
    
    logger.info(f"Пользователь {user_id} выбрал услугу в программе {camp['id'] if camp else 'unknown'}")
    
    # Для индивидуальных условий показываем специальный текст
    if service_id == "individual":
        display_text = (
            f"<b>📝 Вы выбрали:</b>\n"
            f"Индивидуальные условия\n\n"
            f"<b>📍 {camp['name']}</b>\n"
            f"{camp['address']}\n\n"
            f"<i>Стоимость будет рассчитана менеджером индивидуально</i>"
        )
    else:
        display_text = (
            f"<b>🏟 Вы выбрали:</b>\n"
            f"{service_name} - {format_price(price)}\n\n"
            f"<b>📍 {camp['name']}</b>\n"
            f"{camp['address']}"
        )
    
    await query.edit_message_text(
        text=display_text,
        parse_mode='HTML',
        reply_markup=get_payment_keyboard()
    )
    return ConversationHandler.END

async def handle_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка оплаты с индивидуальными QR-кодами"""
    query = update.callback_query
    await query.answer()
    
    if query.data == "show_requisites":
        camp = context.user_data.get("selected_camp", {})
        camp_id = camp.get("id")
        
        # Получаем данные для QR
        qr_data = QR_FILES.get(camp_id)
        
        # Текст инструкции
        text = (
            f"Для оплаты услуги, пожалуйста, воспользуйтесь нашим QR кодом:\n\n"
            f"⬇️ Для этого нужно:\n\n"
            f"1️⃣ Сохранить код в фотопленке;\n"
            f"2️⃣ Открыть приложение банка;\n"
            f"3️⃣ Нажать «Сканировать из файла» и выбрать в фотопленке QR код;\n"
            f"4️⃣ Вручную в назначении платежа указать ФИО участника + название услуги\n"
            f"5️⃣ Ввести верную сумму\n"
            f"6️⃣ Произвести оплату по реквизитам✅\n\n"
            f"✅ Пожалуйста, не забудьте прислать нам скриншот - подтверждение оплаты в следующем сообщении🙌"
        )
        
        # ДЛЯ ВСЕХ ПРОГРАММ ОТПРАВЛЯЕМ КАК ФОТО
        await query.message.reply_photo(
            photo=qr_data["file_id"],
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
    
    elif query.data == "contact_admin":
        await handle_contact_admin(update, context)

async def handle_contact_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Связь с менеджером - уведомления получают оба, клиент видит нового менеджера @SBall_manager"""
    query = update.callback_query
    user = update.effective_user
    user_id = user.id
    camp = context.user_data.get("selected_camp", {}).get("name", "Не выбран")
    service = context.user_data.get("selected_service", {}).get("name", "Не выбрана")
    
    logger.info(f"Пользователь {user_id} запросил связь с менеджером")
    
    # Уведомление для ВСЕХ менеджеров
    notification = (f"📞 ЗАПРОС СВЯЗИ\n"
                   f"━━━━━━━━━━━━━━━\n"
                   f"👤 Пользователь: {user.full_name}\n"
                   f"🆔 ID: {user.id}\n"
                   f"📱 Username: @{user.username or 'нет'}\n"
                   f"━━━━━━━━━━━━━━━\n"
                   f"🏕️ Программа: {camp}\n"
                   f"📋 Услуга: {service}\n"
                   f"━━━━━━━━━━━━━━━")
    
    # Отправляем уведомление всем
    for chat_id in NOTIFY_IDS:
        try:
            await context.bot.send_message(
                chat_id=chat_id,
                text=notification
            )
        except Exception as e:
            logger.error(f"Ошибка при уведомлении {chat_id}: {e}")
    
    # Показываем контакты НОВОГО менеджера
    await query.message.reply_text(
        text=f"📞 <b>Связь с менеджером</b>\n\n"
             f"Телефон: {MANAGER_PHONE}\n\n"
             f"Нажмите кнопку ниже, чтобы написать менеджеру в Telegram:",
        parse_mode='HTML',
        reply_markup=get_contact_admin_keyboard()
    )

async def fio_participant(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Шаг 1: ФИО участника"""
    user_id = update.effective_user.id
    context.user_data["fio_participant"] = update.message.text
    logger.info(f"Пользователь {user_id} ввёл ФИО участника (шаг 1/5)")
    await update.message.reply_text(
        "📝 Шаг 2 из 5\n\n"
        "Введите <b>ФИО плательщика</b>:",
        parse_mode='HTML'
    )
    return FIO_PAYER

async def fio_payer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Шаг 2: ФИО плательщика"""
    user_id = update.effective_user.id
    context.user_data["fio_payer"] = update.message.text
    logger.info(f"Пользователь {user_id} ввёл ФИО плательщика (шаг 2/5)")
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
    user_id = update.effective_user.id
    
    digits = re.sub(r'\D', '', phone_input)
    if len(digits) == 11 and digits.startswith(('7', '8')):
        formatted = f"8{digits[1:4]}-{digits[4:7]}-{digits[7:9]}-{digits[9:11]}"
        context.user_data["phone"] = formatted
        logger.info(f"Пользователь {user_id} ввёл телефон (шаг 3/5)")
    elif len(digits) == 10:
        formatted = f"8{digits[0:3]}-{digits[3:6]}-{digits[6:8]}-{digits[8:10]}"
        context.user_data["phone"] = formatted
        logger.info(f"Пользователь {user_id} ввёл телефон (шаг 3/5)")
    else:
        logger.info(f"Пользователь {user_id} ввёл некорректный телефон")
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
    user_id = update.effective_user.id
    
    if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
        logger.info(f"Пользователь {user_id} ввёл некорректный email")
        await update.message.reply_text(
            "Пожалуйста, введите корректный email (например, name@domain.ru)"
        )
        return EMAIL
    
    context.user_data["email"] = email
    logger.info(f"Пользователь {user_id} ввёл email (шаг 4/5)")
    
    await update.message.reply_text(
        "📝 Шаг 5 из 5\n\n"
        "Теперь отправьте <b>фото или скан чека об оплате</b>:",
        parse_mode='HTML'
    )
    return RECEIPT_PHOTO

async def receipt_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Шаг 5: чек об оплате - отправляется обоим менеджерам"""
    user = update.effective_user
    user_id = user.id
    
    if not (update.message.photo or update.message.document):
        await update.message.reply_text(
            "Пожалуйста, отправьте фото или скан чека об оплате"
        )
        return RECEIPT_PHOTO
    
    logger.info(f"Пользователь {user_id} отправил чек (шаг 5/5)")
    
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
    
    # Отправляем чек ВСЕМ менеджерам
    success = False
    for chat_id in NOTIFY_IDS:
        try:
            if update.message.photo:
                await context.bot.send_photo(
                    chat_id=chat_id,
                    photo=update.message.photo[-1].file_id,
                    caption=caption
                )
            else:
                await context.bot.send_document(
                    chat_id=chat_id,
                    document=update.message.document.file_id,
                    caption=caption
                )
            success = True
        except Exception as e:
            logger.error(f"Ошибка при отправке чека {chat_id}: {e}")
    
    if success:
        await update.message.reply_text(
            "✅ Спасибо! Чек получен. 🌟 Спасибо, что выбираете Школа мяча! 🌟"
        )
    else:
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
    """Возврат к категориям Сочи (больше не используется)"""
    pass

async def handle_back_to_services(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Возврат к услугам после контакта с менеджером или по кнопке назад"""
    query = update.callback_query
    await query.answer()
    
    camp = context.user_data.get("selected_camp")
    is_sochi = context.user_data.get("is_sochi", False)
    
    if is_sochi:
        # Для Сочи возвращаемся к оплате
        service_data = context.user_data.get("selected_service", {})
        if service_data:
            await query.message.reply_text(
                text=(
                    f"<b>🏟 Вы выбрали:</b>\n"
                    f"{service_data.get('name', 'Поездка в Сочи')}\n\n"
                    f"<b>📍 {camp['name']}</b>\n"
                    f"{camp['address']}"
                ),
                parse_mode='HTML',
                reply_markup=get_payment_keyboard()
            )
    else:
        await query.message.reply_text(
            text="<b>Какая услуга вас интересует?</b>",
            parse_mode='HTML',
            reply_markup=get_camp_main_menu_keyboard(camp["id"])
        )

async def handle_back_to_previous(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Возврат к предыдущему меню"""
    query = update.callback_query
    await query.answer()
    
    # Просто возвращаемся к выбору программы
    await query.message.reply_text(
        "🏕️ <b>Выберите программу:</b>",
        parse_mode='HTML',
        reply_markup=get_camps_keyboard()
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
    user_id = update.effective_user.id
    logger.info(f"Пользователь {user_id} отменил операцию")
    await update.message.reply_text(
        "Операция отменена. Нажмите /start чтобы начать заново."
    )
    context.user_data.clear()
    return ConversationHandler.END

# ========== ЗАПУСК ==========
def main():
    logger.info("🚀 Запуск бота...")
    logger.info(f"👤 Администратор ID: {ADMIN_CHAT_ID}")
    logger.info(f"👤 Менеджер ID: {MANAGER_CHAT_ID}")
    logger.info(f"👤 Менеджер username: @{MANAGER_USERNAME}")
    
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
        application.add_handler(CallbackQueryHandler(handle_service_selection, pattern='^service:'))
        application.add_handler(CallbackQueryHandler(handle_payment, pattern='^(show_requisites|send_receipt|contact_admin)$'))
        application.add_handler(CallbackQueryHandler(handle_back_to_camps, pattern='^back_to_camps$'))
        application.add_handler(CallbackQueryHandler(handle_back_to_main_menu, pattern='^back_to_main_menu$'))
        application.add_handler(CallbackQueryHandler(handle_back_to_camp_options, pattern='^back_to_camp_options$'))
        application.add_handler(CallbackQueryHandler(handle_back_to_services, pattern='^back_to_services$'))
        application.add_handler(CallbackQueryHandler(handle_back_to_previous, pattern='^back_to_previous$'))
        application.add_handler(CallbackQueryHandler(noop, pattern='^noop$'))
        
        application.add_error_handler(error_handler)
        
        logger.info("✅ Бот запущен!")
        application.run_polling(drop_pending_updates=True)
        
    except Exception as e:
        logger.error(f"💥 Критическая ошибка: {e}")
        raise

if __name__ == '__main__':
    main()
