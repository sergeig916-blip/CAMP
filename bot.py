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
(FIO_PARTICIPANT, FIO_PAYER, PHONE, RECEIPT_PHOTO) = range(4)
SOCHI_WAIT_CONTRACT = 4

# ========== ДАННЫЕ ==========
PDF_LINK = "https://clck.ru/3RuZKG"
REQUISITES_LINK = PDF_LINK

# ========== ДАННЫЕ КЭМПОВ ==========
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

# ========== УСЛУГИ ==========
def format_price(price: int) -> str:
    """Форматирует цену с пробелом между тысячами и символом ₽"""
    return f"{price:,}".replace(",", " ") + "₽"

def get_camp_price_multiplier(camp_id: str) -> int:
    """Возвращает множитель цены для кэмпа."""
    if camp_id == "khamovniki":
        return 1
    elif camp_id == "sochi":
        return 1  # У Сочи свои цены
    else:
        return 0  # 0 как маркер, что используются базовые цены 39 990

# Базовые услуги (только основные категории) с ценами
BASE_SERVICES = {
    "camp": {
        "name": "🏕️ КЭМП",
        "options": [
            {
                "name": "10 дней",
                "base_price": 39990,
                "id": "camp_10_days",
                "type": "camp_10_days",
                "has_suboptions": True
            },
            {
                "name": "1 день",
                "base_price": 5990,
                "id": "camp_1_day",
                "type": "camp_1_day"
            }
        ]
    },
    "training": {
        "name": "⚽ ТРЕНИРОВКИ",
        "options": [
            {
                "name": "тренировка - 1 шт",
                "base_price": 1600,
                "id": "training_1",
                "type": "training_1"
            },
            {
                "name": "абонемент - 5 занятий",
                "base_price": 7000,
                "price_per": 1400,
                "id": "training_5",
                "type": "training_5"
            },
            {
                "name": "абонемент - 10 занятий",
                "base_price": 11500,
                "price_per": 1150,
                "id": "training_10",
                "type": "training_10"
            }
        ]
    },
    "other": {
        "name": "📦 ПРОЧЕЕ",
        "options": [
            {
                "name": "оплата после \"пробного дня\"",
                "base_price": 39000,
                "id": "trial_day",
                "type": "trial_day"
            },
            {
                "name": "форма",
                "base_price": 4500,
                "id": "uniform",
                "type": "uniform"
            }
        ]
    }
}

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

# Для Хамовников повышенные цены (тоже БЕЗ ЦЕНЫ в кнопках смен)
KHAMOVNIKI_SHIFTS = [
    {"name": "смена 1", "dates": "01-12 июнь", "id": "camp_10_days_1"},
    {"name": "смена 2", "dates": "15-26 июнь", "id": "camp_10_days_2"},
    {"name": "смена 3", "dates": "29.06-10.07", "id": "camp_10_days_3"},
    {"name": "смена 4", "dates": "13-24 июль", "id": "camp_10_days_4"},
    {"name": "смена 5", "dates": "27.07-07.08", "id": "camp_10_days_5"},
    {"name": "смена 6", "dates": "10-21 авг", "id": "camp_10_days_6"},
    {"name": "смена 7", "dates": "24-27 авг", "id": "camp_10_days_7"}
]

KHAMOVNIKI_SERVICES = {
    "training": {
        "name": "⚽ ТРЕНИРОВКИ",
        "options": [
            {"name": "тренировка - 1 шт", "price": 1890, "id": "training_1", "type": "training_1"},
            {"name": "абонемент - 5 занятий", "price": 7450, "price_per": 1490, "id": "training_5", "type": "training_5"},
            {"name": "абонемент - 10 занятий", "price": 12900, "price_per": 1290, "id": "training_10", "type": "training_10"}
        ]
    },
    "other": {
        "name": "📦 ПРОЧЕЕ",
        "options": [
            {"name": "оплата после \"пробного дня\"", "price": 65000, "id": "trial_day", "type": "trial_day"},
            {"name": "форма", "price": 4500, "id": "uniform", "type": "uniform"}
        ]
    }
}

# Сочи — двухуровневое меню с правильными названиями
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

# ========== КЛАВИАТУРЫ ==========
def get_camps_keyboard():
    keyboard = []
    for camp in CAMPS:
        keyboard.append([InlineKeyboardButton(camp["name"], callback_data=f"camp:{camp['id']}")])
    return InlineKeyboardMarkup(keyboard)

def get_service_categories_keyboard(is_sochi=False):
    if is_sochi:
        keyboard = [[InlineKeyboardButton("🏕️ КЭМП", callback_data="service_category:camp")]]
    else:
        keyboard = [
            [InlineKeyboardButton("🏕️ КЭМП", callback_data="service_category:camp")],
            [InlineKeyboardButton("⚽ ТРЕНИРОВКИ", callback_data="service_category:training")],
            [InlineKeyboardButton("📦 ПРОЧЕЕ", callback_data="service_category:other")]
        ]
    return InlineKeyboardMarkup(keyboard)

def get_base_services_keyboard(category, camp_id=None):
    """Показывает основные услуги (с ценами)"""
    keyboard = []
    
    if camp_id == "khamovniki" and category in KHAMOVNIKI_SERVICES:
        services = KHAMOVNIKI_SERVICES
    else:
        services = BASE_SERVICES
    
    if category in services:
        for option in services[category]["options"]:
            if "price" in option:
                price = option["price"]
            elif "base_price" in option:
                multiplier = get_camp_price_multiplier(camp_id)
                price = option["base_price"] if multiplier == 0 else int(option["base_price"] * multiplier)
            else:
                price = 0
            
            price_text = format_price(price)
            if option.get("price_per"):
                price_text += f" ({format_price(option['price_per'])}/занятие)"
            
            button_text = f"{option['name']} - {price_text}"
            keyboard.append([InlineKeyboardButton(button_text, callback_data=f"base_service:{option['id']}")])
    
    keyboard.append([InlineKeyboardButton("🔙 Назад к категориям", callback_data="back_to_categories")])
    return InlineKeyboardMarkup(keyboard)

def get_camp_shifts_keyboard(camp_id=None):
    """Показывает список смен для 10 дней — БЕЗ ЦЕНЫ, дата в скобках"""
    keyboard = []
    
    if camp_id == "khamovniki":
        shifts = KHAMOVNIKI_SHIFTS
        for shift in shifts:
            button_text = f"{shift['name']} ({shift['dates']})"
            keyboard.append([InlineKeyboardButton(button_text, callback_data=f"service:{shift['id']}")])
    else:
        shifts = CAMP_SHIFTS
        for shift in shifts:
            button_text = f"{shift['name']} ({shift['dates']})"
            keyboard.append([InlineKeyboardButton(button_text, callback_data=f"service:{shift['id']}")])
    
    keyboard.append([InlineKeyboardButton("🔙 Назад к услугам", callback_data="back_to_base_services")])
    return InlineKeyboardMarkup(keyboard)

def get_sochi_categories_keyboard():
    """Показывает категории для Сочи (без цен)"""
    keyboard = []
    for category in SOCHI_CATEGORIES:
        # Для длинных названий делаем перенос
        name = category["name"]
        if len(name) > 40:
            # Простой перенос для очень длинных названий
            parts = name.split(" (")
            if len(parts) > 1:
                name = f"{parts[0]}\n({parts[1]}"
        keyboard.append([InlineKeyboardButton(name, callback_data=f"sochi_category:{category['id']}")])
    
    keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="back_to_categories")])
    return InlineKeyboardMarkup(keyboard)

def get_sochi_shifts_keyboard(category_id):
    """Показывает смены для выбранной категории Сочи (с ценами)"""
    keyboard = []
    
    for category in SOCHI_CATEGORIES:
        if category["id"] == category_id:
            for option in category["options"]:
                button_text = f"{option['name']} - {format_price(option['price'])}"
                keyboard.append([InlineKeyboardButton(button_text, callback_data=f"service:{option['id']}")])
            break
    
    keyboard.append([InlineKeyboardButton("🔙 Назад к категориям", callback_data="back_to_sochi_categories")])
    return InlineKeyboardMarkup(keyboard)

def get_agree_keyboard():
    keyboard = [[InlineKeyboardButton("✅ СОГЛАСЕН", callback_data="agree")]]
    return InlineKeyboardMarkup(keyboard)

def get_sochi_contract_keyboard():
    """Только кнопка подтверждения, без кнопки скачивания"""
    keyboard = [
        [InlineKeyboardButton("✅ Я подписал договор", callback_data="sochi_contract_signed")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_contract_uploaded_keyboard(has_files=False):
    """Кнопка для подтверждения загрузки всех страниц договора.
    Если has_files=False, кнопка неактивна (просто текст без callback)"""
    if has_files:
        keyboard = [
            [InlineKeyboardButton("✅ Договор загружен", callback_data="contract_uploaded")]
        ]
    else:
        keyboard = [
            [InlineKeyboardButton("⏳ Сначала загрузите файлы", callback_data="noop")]
        ]
    return InlineKeyboardMarkup(keyboard)

def get_payment_keyboard():
    keyboard = [
        [InlineKeyboardButton("💳 Оплатить", callback_data="show_requisites")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_receipt_keyboard():
    keyboard = [
        [InlineKeyboardButton("📤 Отправить чек об оплате", callback_data="send_receipt")],
        [InlineKeyboardButton("📞 Задать вопрос администратору", callback_data="contact_admin")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_contact_admin_keyboard():
    keyboard = [
        [InlineKeyboardButton("📞 Написать администратору", url=f"https://t.me/{ADMIN_USERNAME}")],
        [InlineKeyboardButton("🔙 Назад к услугам", callback_data="back_to_services")]
    ]
    return InlineKeyboardMarkup(keyboard)

# ========== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ==========
def get_service_price(service_id: str, camp_id: str = None) -> int:
    """Получает цену услуги с учётом кэмпа."""
    if camp_id == "sochi":
        for category in SOCHI_CATEGORIES:
            for opt in category["options"]:
                if opt["id"] == service_id:
                    return opt["price"]
    elif camp_id == "khamovniki":
        # Проверяем смены (10 дней)
        for shift in KHAMOVNIKI_SHIFTS:
            if shift["id"] == service_id:
                return 69990  # цена для Хамовников
        # Проверяем другие услуги
        for cat in KHAMOVNIKI_SERVICES.values():
            for opt in cat["options"]:
                if opt["id"] == service_id:
                    return opt["price"]
    else:
        # Проверяем смены (10 дней)
        for shift in CAMP_SHIFTS:
            if shift["id"] == service_id:
                multiplier = get_camp_price_multiplier(camp_id)
                base_price = 39990
                return base_price if multiplier == 0 else int(base_price * multiplier)
        
        # Проверяем другие услуги
        for cat in BASE_SERVICES.values():
            for opt in cat["options"]:
                if opt["id"] == service_id:
                    if "price" in opt:
                        return opt["price"]
                    elif "base_price" in opt:
                        multiplier = get_camp_price_multiplier(camp_id)
                        return opt["base_price"] if multiplier == 0 else int(opt["base_price"] * multiplier)
    return 0

def get_service_name(service_id: str, camp_id: str = None) -> str:
    """Получает название услуги по ID."""
    if camp_id == "sochi":
        for category in SOCHI_CATEGORIES:
            for opt in category["options"]:
                if opt["id"] == service_id:
                    # Для отображения используем короткое название без цен
                    return f"{category['name']} - {opt['name']}"
    elif camp_id == "khamovniki":
        for shift in KHAMOVNIKI_SHIFTS:
            if shift["id"] == service_id:
                return f"10 дней {shift['name']} ({shift['dates']})"
        for cat in KHAMOVNIKI_SERVICES.values():
            for opt in cat["options"]:
                if opt["id"] == service_id:
                    return opt["name"]
    else:
        for shift in CAMP_SHIFTS:
            if shift["id"] == service_id:
                return f"10 дней {shift['name']} ({shift['dates']})"
        for cat in BASE_SERVICES.values():
            for opt in cat["options"]:
                if opt["id"] == service_id:
                    return opt["name"]
    return service_id

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
        context.user_data["sochi_files"] = []  # Для хранения загруженных файлов договора
        
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
                f"5. Прислать скан или фото ВСЕХ СТРАНИЦ подписанного договора в данный чат.\n"
                f"   После загрузки всех страниц нажмите кнопку «✅ Договор загружен»"
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
    
    if query.data == "sochi_contract_signed":
        # Показываем кнопку, но она неактивна, пока нет файлов
        await query.message.reply_text(
            "📎 Пожалуйста, отправьте скан или фото ВСЕХ СТРАНИЦ подписанного договора.\n"
            "После загрузки всех страниц кнопка станет активной.",
            reply_markup=get_contract_uploaded_keyboard(has_files=False)
        )
        return SOCHI_WAIT_CONTRACT

async def handle_sochi_file_upload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка загруженных файлов договора для Сочи"""
    user = update.effective_user
    
    if not (update.message.document or update.message.photo):
        # Если это не файл, игнорируем (обработчик сообщений не для этого состояния)
        return SOCHI_WAIT_CONTRACT
    
    # Сохраняем информацию о файле
    file_info = {
        "type": "document" if update.message.document else "photo",
        "file_id": update.message.document.file_id if update.message.document else update.message.photo[-1].file_id,
        "message_id": update.message.message_id
    }
    
    if "sochi_files" not in context.user_data:
        context.user_data["sochi_files"] = []
    
    context.user_data["sochi_files"].append(file_info)
    
    # Отправляем файл админу
    camp = context.user_data.get("selected_camp", {}).get("name", "Не выбран")
    
    caption = (f"📄 Страница договора (Сочи)\n"
              f"━━━━━━━━━━━━━━━\n"
              f"👤 Пользователь: {user.full_name}\n"
              f"🆔 ID: {user.id}\n"
              f"📱 Username: @{user.username or 'нет'}\n"
              f"━━━━━━━━━━━━━━━\n"
              f"🏕️ Кэмп: {camp}\n"
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
        logger.error(f"Ошибка при отправке файла договора: {e}")
    
    # Обновляем клавиатуру - делаем кнопку активной, если есть файлы
    await update.message.reply_text(
        f"✅ Страница {len(context.user_data['sochi_files'])} получена. "
        f"Если это последняя страница, нажмите кнопку ниже.",
        reply_markup=get_contract_uploaded_keyboard(has_files=True)
    )
    
    return SOCHI_WAIT_CONTRACT

async def handle_contract_uploaded(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка нажатия кнопки 'Договор загружен'"""
    query = update.callback_query
    await query.answer()
    
    # Проверяем, были ли загружены файлы
    if not context.user_data.get("sochi_files"):
        await query.message.edit_text(
            "❌ Вы не загрузили ни одного файла. Пожалуйста, сначала загрузите скан договора.",
            reply_markup=get_contract_uploaded_keyboard(has_files=False)
        )
        return SOCHI_WAIT_CONTRACT
    
    user = update.effective_user
    camp = context.user_data.get("selected_camp", {}).get("name", "Не выбран")
    files_count = len(context.user_data["sochi_files"])
    
    # Уведомляем админа, что пользователь завершил загрузку
    notification = (f"📄 ЗАГРУЗКА ДОГОВОРА ЗАВЕРШЕНА\n"
                   f"━━━━━━━━━━━━━━━\n"
                   f"👤 Пользователь: {user.full_name}\n"
                   f"🆔 ID: {user.id}\n"
                   f"📱 Username: @{user.username or 'нет'}\n"
                   f"━━━━━━━━━━━━━━━\n"
                   f"🏕️ Кэмп: {camp}\n"
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
        "<b>Какой формат поездки вы выбираете?🌝</b>",
        parse_mode='HTML',
        reply_markup=get_sochi_categories_keyboard()
    )
    
    # Очищаем список файлов
    context.user_data.pop("sochi_files", None)
    
    return ConversationHandler.END

async def handle_agree(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_reply_markup(reply_markup=None)
    
    is_sochi = context.user_data.get("is_sochi", False)
    
    if is_sochi:
        await query.message.reply_text(
            text="<b>Какой формат поездки вы выбираете?🌝</b>",
            parse_mode='HTML',
            reply_markup=get_sochi_categories_keyboard()
        )
    else:
        await query.message.reply_text(
            text="<b>Какая услуга вас интересует?</b>",
            parse_mode='HTML',
            reply_markup=get_service_categories_keyboard(is_sochi)
        )

async def handle_service_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    category = query.data.split(":")[1]
    is_sochi = context.user_data.get("is_sochi", False)
    camp = context.user_data.get("selected_camp", {})
    
    if is_sochi:
        if category == "camp":
            await query.edit_message_text(
                text="<b>Выберите формат поездки:</b>",
                parse_mode='HTML',
                reply_markup=get_sochi_categories_keyboard()
            )
    else:
        await query.edit_message_text(
            text=f"<b>Выберите услугу:</b>",
            parse_mode='HTML',
            reply_markup=get_base_services_keyboard(category, camp.get("id"))
        )

async def handle_sochi_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Выбор категории в Сочи"""
    query = update.callback_query
    await query.answer()
    
    category_id = query.data.split(":")[1]
    
    # Находим название категории
    category_name = ""
    for cat in SOCHI_CATEGORIES:
        if cat["id"] == category_id:
            category_name = cat["name"]
            break
    
    await query.edit_message_text(
        text=f"<b>Выберите смену:</b>",
        parse_mode='HTML',
        reply_markup=get_sochi_shifts_keyboard(category_id)
    )

async def handle_back_to_sochi_categories(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Возврат к категориям Сочи"""
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        text="<b>Какой формат поездки вы выбираете?🌝</b>",
        parse_mode='HTML',
        reply_markup=get_sochi_categories_keyboard()
    )

async def handle_base_service(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка выбора базовой услуги (10 дней или 1 день)"""
    query = update.callback_query
    await query.answer()
    
    service_id = query.data.split(":")[1]
    camp = context.user_data.get("selected_camp")
    
    if service_id == "camp_10_days":
        # Показываем список смен (без цен)
        await query.edit_message_text(
            text="<b>Выберите смену:</b>",
            parse_mode='HTML',
            reply_markup=get_camp_shifts_keyboard(camp.get("id") if camp else None)
        )
    else:
        # Для 1 дня или других услуг
        await handle_service_selection(update, context, service_id)

async def handle_service_selection(update: Update, context: ContextTypes.DEFAULT_TYPE, service_id=None):
    """Выбор конкретной услуги"""
    if not service_id:
        query = update.callback_query
        await query.answer()
        service_id = query.data.split(":")[1]
    else:
        query = update.callback_query
    
    camp = context.user_data.get("selected_camp")
    is_sochi = context.user_data.get("is_sochi", False)
    
    price = get_service_price(service_id, camp.get("id") if camp else None)
    service_name = get_service_name(service_id, camp.get("id") if camp else None)
    
    context.user_data["selected_service"] = {
        "id": service_id,
        "name": service_name,
        "price": price
    }
    
    price_text = format_price(price)
    
    text = (
        f"<b>🏟 Вы выбрали УСЛУГУ:</b>\n"
        f"{service_name} - {price_text}\n\n"
        f"<b>📍 {camp['name'] if camp else 'Кэмп'}</b>\n"
        f"{camp['address'] if camp else ''}"
    )
    
    await query.edit_message_text(
        text=text,
        parse_mode='HTML',
        reply_markup=get_payment_keyboard()
    )

async def handle_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == "show_requisites":
        camp = context.user_data.get("selected_camp", {})
        legal = camp.get("legal_entity", "Школа мяча")
        
        await query.message.reply_text(
            text=f"📄 <a href='{REQUISITES_LINK}'>PDF реквизиты \"{legal}\"</a>\n\n"
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
    
    elif query.data == "noop":
        # Заглушка для неактивной кнопки
        await query.answer("Сначала загрузите файлы договора", show_alert=True)

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
             f"Телефон: 8-985-579-67-79\n\n"
             f"Нажмите кнопку ниже, чтобы написать администратору в Telegram:",
        parse_mode='HTML',
        reply_markup=get_contact_admin_keyboard()
    )

async def handle_back_to_base_services(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Возврат к базовым услугам из списка смен"""
    query = update.callback_query
    await query.answer()
    
    camp = context.user_data.get("selected_camp", {})
    
    await query.edit_message_text(
        text="<b>Выберите услугу:</b>",
        parse_mode='HTML',
        reply_markup=get_base_services_keyboard("camp", camp.get("id"))
    )

async def handle_back_to_categories(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Возврат к выбору категорий"""
    query = update.callback_query
    await query.answer()
    
    is_sochi = context.user_data.get("is_sochi", False)
    
    if is_sochi:
        await query.edit_message_text(
            text="<b>Какой формат поездки вы выбираете?🌝</b>",
            parse_mode='HTML',
            reply_markup=get_sochi_categories_keyboard()
        )
    else:
        await query.edit_message_text(
            text="<b>Какая услуга вас интересует?</b>",
            parse_mode='HTML',
            reply_markup=get_service_categories_keyboard(is_sochi)
        )

async def handle_back_to_services(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Возврат к услугам после контакта с админом"""
    query = update.callback_query
    await query.answer()
    
    is_sochi = context.user_data.get("is_sochi", False)
    camp = context.user_data.get("selected_camp", {})
    
    if is_sochi:
        await query.message.reply_text(
            text="<b>Какой формат поездки вы выбираете?🌝</b>",
            parse_mode='HTML',
            reply_markup=get_sochi_categories_keyboard()
        )
    else:
        await query.message.reply_text(
            text="<b>Какая услуга вас интересует?</b>",
            parse_mode='HTML',
            reply_markup=get_service_categories_keyboard(is_sochi)
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
        "Введите <b>телефон для связи</b> (например, 89001234567):",
        parse_mode='HTML',
        reply_markup=ForceReply(input_field_placeholder="89001234567")
    )
    return PHONE

async def phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    phone_input = update.message.text.strip()
    logger.info(f"Получен телефон: {phone_input}")
    
    # Простая проверка: удаляем все не-цифры и проверяем длину
    digits = re.sub(r'\D', '', phone_input)
    if len(digits) == 11 and digits.startswith(('7', '8')):
        # Приводим к формату 8...
        formatted = f"8{digits[1:4]}-{digits[4:7]}-{digits[7:9]}-{digits[9:11]}"
        context.user_data["phone"] = formatted
    elif len(digits) == 10:
        # Если ввели 10 цифр без кода
        formatted = f"8{digits[0:3]}-{digits[3:6]}-{digits[6:8]}-{digits[8:10]}"
        context.user_data["phone"] = formatted
    else:
        await update.message.reply_text(
            "Пожалуйста, введите корректный номер телефона (например, 89001234567)"
        )
        return PHONE
    
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
    service_name = service_data.get("name", "Не выбрана")
    service_price = service_data.get("price", 0)
    
    caption = (
        f"💰 НОВАЯ ОПЛАТА\n"
        f"━━━━━━━━━━━━━━━\n"
        f"👤 Пользователь: {user.full_name}\n"
        f"🆔 ID: {user.id}\n"
        f"📱 Username: @{user.username or 'нет'}\n"
        f"━━━━━━━━━━━━━━━\n"
        f"🏕️ Кэмп: {camp}\n"
        f"📋 Услуга: {service_name}\n"
        f"💵 Сумма: {format_price(service_price)}\n"
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
        
        # Компактная версия благодарности
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
                SOCHI_WAIT_CONTRACT: [
                    MessageHandler(filters.PHOTO | filters.Document.ALL, handle_sochi_file_upload),
                    CallbackQueryHandler(handle_contract_uploaded, pattern='^contract_uploaded$'),
                    CallbackQueryHandler(handle_payment, pattern='^noop$')
                ],
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
        application.add_handler(CallbackQueryHandler(handle_sochi_category, pattern='^sochi_category:'))
        application.add_handler(CallbackQueryHandler(handle_back_to_sochi_categories, pattern='^back_to_sochi_categories$'))
        application.add_handler(CallbackQueryHandler(handle_base_service, pattern='^base_service:'))
        application.add_handler(CallbackQueryHandler(handle_service_selection, pattern='^service:'))
        application.add_handler(CallbackQueryHandler(handle_agree, pattern='^agree$'))
        application.add_handler(CallbackQueryHandler(handle_payment, pattern='^(show_requisites|send_receipt|contact_admin)$'))
        application.add_handler(CallbackQueryHandler(handle_back_to_base_services, pattern='^back_to_base_services$'))
        application.add_handler(CallbackQueryHandler(handle_back_to_categories, pattern='^back_to_categories$'))
        application.add_handler(CallbackQueryHandler(handle_back_to_services, pattern='^back_to_services$'))
        
        application.add_error_handler(error_handler)
        
        logger.info("✅ Бот запущен!")
        application.run_polling(drop_pending_updates=True)
        
    except Exception as e:
        logger.error(f"💥 Критическая ошибка: {e}")
        raise

if __name__ == '__main__':
    main()
