import os
import logging
import sys
import re
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
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
def get_camp_price_multiplier(camp_id: str) -> int:
    """Возвращает множитель цены для кэмпа."""
    if camp_id == "khamovniki":
        return 1
    elif camp_id == "sochi":
        return 1  # У Сочи свои цены в SOCHI_SERVICES
    else:
        return 0  # 0 как маркер, что используются базовые цены 39 990

def format_service_name(service_type: str, camp_id: str = None) -> str:
    """Форматирует название услуги в зависимости от кэмпа."""
    if service_type == "camp_10_days":
        return "10 дней"
    elif service_type == "camp_1_day":
        return "1 день"
    return service_type

SERVICES = {
    "camp": {
        "name": "🏕️ КЭМП",
        "options": [
            {
                "name": "10 дней - смена 1", "dates": "01-12 июнь", "base_price": 39990,
                "id": "camp_10_days_1", "type": "camp_10_days"
            },
            {
                "name": "10 дней - смена 2", "dates": "15-26 июнь", "base_price": 39990,
                "id": "camp_10_days_2", "type": "camp_10_days"
            },
            {
                "name": "10 дней - смена 3", "dates": "29.06-10.07", "base_price": 39990,
                "id": "camp_10_days_3", "type": "camp_10_days"
            },
            {
                "name": "10 дней - смена 4", "dates": "13-24 июль", "base_price": 39990,
                "id": "camp_10_days_4", "type": "camp_10_days"
            },
            {
                "name": "10 дней - смена 5", "dates": "27.07-07.08", "base_price": 39990,
                "id": "camp_10_days_5", "type": "camp_10_days"
            },
            {
                "name": "10 дней - смена 6", "dates": "10-21 авг", "base_price": 39990,
                "id": "camp_10_days_6", "type": "camp_10_days"
            },
            {
                "name": "10 дней - смена 7", "dates": "24-27 авг", "base_price": 39990,
                "id": "camp_10_days_7", "type": "camp_10_days"
            },
            {
                "name": "1 день", "dates": "", "base_price": 5990,
                "id": "camp_1_day", "type": "camp_1_day"
            }
        ]
    },
    "training": {
        "name": "⚽ ТРЕНИРОВКИ",
        "options": [
            {
                "name": "тренировка - 1 шт", "base_price": 1600,
                "id": "training_1", "type": "training_1"
            },
            {
                "name": "абонемент - 5 занятий", "base_price": 7000, "price_per": 1400,
                "id": "training_5", "type": "training_5"
            },
            {
                "name": "абонемент - 10 занятий", "base_price": 11500, "price_per": 1150,
                "id": "training_10", "type": "training_10"
            }
        ]
    },
    "other": {
        "name": "📦 ПРОЧЕЕ",
        "options": [
            {
                "name": "оплата после \"пробного дня\"", "base_price": 39000,
                "id": "trial_day", "type": "trial_day"
            },
            {
                "name": "форма", "base_price": 4500,
                "id": "uniform", "type": "uniform"
            }
        ]
    }
}

# Для Хамовников повышенные цены
KHAMOVNIKI_SERVICES = {
    "camp": {
        "name": "🏕️ КЭМП",
        "options": [
            {
                "name": "10 дней - смена 1", "dates": "01-12 июнь", "price": 69990,
                "id": "camp_10_days_1", "type": "camp_10_days"
            },
            {
                "name": "10 дней - смена 2", "dates": "15-26 июнь", "price": 69990,
                "id": "camp_10_days_2", "type": "camp_10_days"
            },
            {
                "name": "10 дней - смена 3", "dates": "29.06-10.07", "price": 69990,
                "id": "camp_10_days_3", "type": "camp_10_days"
            },
            {
                "name": "10 дней - смена 4", "dates": "13-24 июль", "price": 69990,
                "id": "camp_10_days_4", "type": "camp_10_days"
            },
            {
                "name": "10 дней - смена 5", "dates": "27.07-07.08", "price": 69990,
                "id": "camp_10_days_5", "type": "camp_10_days"
            },
            {
                "name": "10 дней - смена 6", "dates": "10-21 авг", "price": 69990,
                "id": "camp_10_days_6", "type": "camp_10_days"
            },
            {
                "name": "10 дней - смена 7", "dates": "24-27 авг", "price": 69990,
                "id": "camp_10_days_7", "type": "camp_10_days"
            },
            {
                "name": "1 день", "dates": "", "price": 7900,
                "id": "camp_1_day", "type": "camp_1_day"
            }
        ]
    },
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

SOCHI_SERVICES = {
    "camp": {
        "name": "🏕️ КЭМП в Сочи",
        "options": [
            {
                "category": "Спортсмен (без сопровождения)",
                "options": [
                    {"name": "Смена МАЙ 02-08", "price": 89990, "id": "sochi_sportsman_may"},
                    {"name": "Смена ИЮНЬ 19-27", "price": 114990, "id": "sochi_sportsman_june"},
                    {"name": "Смена ИЮЛЬ 4-11", "price": 102490, "id": "sochi_sportsman_july"},
                    {"name": "Смена АВГУСТ 1-8", "price": 102490, "id": "sochi_sportsman_august"}
                ]
            },
            {
                "category": "Спортсмен + родитель",
                "options": [
                    {"name": "Смена МАЙ 02-08", "price": 139990, "id": "sochi_family_may"},
                    {"name": "Смена ИЮНЬ 19-27", "price": 183990, "id": "sochi_family_june"},
                    {"name": "Смена ИЮЛЬ 4-11", "price": 161990, "id": "sochi_family_july"},
                    {"name": "Смена АВГУСТ 1-8", "price": 161990, "id": "sochi_family_august"}
                ]
            },
            {
                "category": "Сопровождающий",
                "options": [
                    {"name": "Смена МАЙ 02-08", "price": 59990, "id": "sochi_accompanist_may"},
                    {"name": "Смена ИЮНЬ 19-27", "price": 77990, "id": "sochi_accompanist_june"},
                    {"name": "Смена ИЮЛЬ 4-11", "price": 68990, "id": "sochi_accompanist_july"},
                    {"name": "Смена АВГУСТ 1-8", "price": 68990, "id": "sochi_accompanist_august"}
                ]
            }
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

def get_services_keyboard(category, is_sochi=False, camp_id=None):
    keyboard = []
    
    if is_sochi:
        services = SOCHI_SERVICES
        if category in services:
            for group in services[category]["options"]:
                for option in group["options"]:
                    button_text = f"{group['category']} - {option['name']} - {option['price']}р."
                    keyboard.append([InlineKeyboardButton(button_text, callback_data=f"service:{option['id']}")])
    else:
        # Выбираем нужный прайс
        if camp_id == "khamovniki":
            services = KHAMOVNIKI_SERVICES
        else:
            services = SERVICES
        
        if category in services:
            for option in services[category]["options"]:
                if "dates" in option and option["dates"]:
                    full_text = f"{option['name']} {option['dates']}"
                else:
                    full_text = option['name']
                
                if "price" in option:
                    price_text = f"{option['price']}р."
                elif "base_price" in option:
                    multiplier = get_camp_price_multiplier(camp_id)
                    if multiplier == 0:
                        price = option['base_price']
                    else:
                        price = int(option['base_price'] * multiplier)
                    price_text = f"{price}р."
                else:
                    price_text = ""
                
                button_text = f"{full_text} - {price_text}"
                if "price_per" in option:
                    button_text += f" ({option['price_per']}р./занятие)"
                
                keyboard.append([InlineKeyboardButton(button_text, callback_data=f"service:{option['id']}")])
    
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
        [InlineKeyboardButton("💳 Оплатить", callback_data="show_requisites")],
        [InlineKeyboardButton("📞 Задать вопрос администратору", callback_data="contact_admin")]
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
def validate_phone(phone: str) -> bool:
    """Проверяет формат телефона: +7 900-234-45-45 или подобный."""
    phone = phone.strip()
    # Убираем возможные пробелы в начале/конце, но сохраняем формат для проверки
    pattern = r'^\+7\s?\d{3}-\d{3}-\d{2}-\d{2}$|^\+7\d{10}$|^8\d{10}$'
    return re.match(pattern, phone) is not None

def format_phone_for_display(phone: str) -> str:
    """Приводит телефон к единому формату для отображения."""
    digits = re.sub(r'\D', '', phone)
    if len(digits) == 11 and digits.startswith('8'):
        digits = '7' + digits[1:]
    if len(digits) == 11 and digits.startswith('7'):
        return f"+7 {digits[1:4]}-{digits[4:7]}-{digits[7:9]}-{digits[9:11]}"
    return phone

def get_service_price(service_id: str, camp_id: str = None) -> int:
    """Получает цену услуги с учётом кэмпа."""
    if camp_id == "sochi":
        for group in SOCHI_SERVICES["camp"]["options"]:
            for opt in group["options"]:
                if opt["id"] == service_id:
                    return opt["price"]
    elif camp_id == "khamovniki":
        for cat in KHAMOVNIKI_SERVICES.values():
            for opt in cat["options"]:
                if opt["id"] == service_id:
                    return opt["price"]
    else:
        for cat in SERVICES.values():
            for opt in cat["options"]:
                if opt["id"] == service_id:
                    if "base_price" in opt:
                        multiplier = get_camp_price_multiplier(camp_id)
                        return opt["base_price"] if multiplier == 0 else int(opt["base_price"] * multiplier)
                    return opt.get("price", 0)
    return 0

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
                f"5. Прислать скан подписанного договора в данный чат"
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
        # Только уведомление о скачивании, без лишней кнопки
        await query.message.reply_text(
            text=f"📄 Ссылка для скачивания: {PDF_LINK}",
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
            "<b>Какой формат поездки вы выбираете?🌝</b>",
            parse_mode='HTML',
            reply_markup=get_services_keyboard("camp", is_sochi=True)
        )
        
    except Exception as e:
        logger.error(f"Ошибка при отправке договора: {e}")
        await update.message.reply_text(
            "✅ Спасибо! Договор получен.\n\n"
            "<b>Какой формат поездки вы выбираете?🌝</b>",
            parse_mode='HTML',
            reply_markup=get_services_keyboard("camp", is_sochi=True)
        )
    
    return ConversationHandler.END

async def handle_agree(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_reply_markup(reply_markup=None)
    
    camp = context.user_data.get("selected_camp", {})
    is_sochi = context.user_data.get("is_sochi", False)
    
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
    
    if is_sochi and category != "camp":
        await query.answer("Для Сочи доступен только формат КЭМП", show_alert=True)
        return
    
    await query.edit_message_text(
        text=f"<b>Выберите услугу:</b>",
        parse_mode='HTML',
        reply_markup=get_services_keyboard(category, is_sochi, camp.get("id"))
    )

async def handle_service_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    service_id = query.data.split(":")[1]
    camp = context.user_data.get("selected_camp")
    is_sochi = context.user_data.get("is_sochi", False)
    
    selected_service = None
    
    if is_sochi:
        for group in SOCHI_SERVICES["camp"]["options"]:
            for opt in group["options"]:
                if opt["id"] == service_id:
                    selected_service = {
                        "name": f"{group['category']} - {opt['name']}",
                        "price": opt["price"],
                        "id": opt["id"]
                    }
                    break
    else:
        if camp and camp["id"] == "khamovniki":
            services_dict = KHAMOVNIKI_SERVICES
        else:
            services_dict = SERVICES
        
        for category in services_dict.values():
            for opt in category["options"]:
                if opt["id"] == service_id:
                    if "price" in opt:
                        price = opt["price"]
                    elif "base_price" in opt:
                        multiplier = get_camp_price_multiplier(camp["id"] if camp else None)
                        price = opt["base_price"] if multiplier == 0 else int(opt["base_price"] * multiplier)
                    else:
                        price = 0
                    
                    service_name = opt["name"]
                    if "dates" in opt and opt["dates"]:
                        service_name += f" {opt['dates']}"
                    
                    selected_service = {
                        "name": service_name,
                        "price": price,
                        "id": opt["id"],
                        "price_per": opt.get("price_per")
                    }
                    break
    
    if not selected_service:
        await query.answer("Ошибка выбора услуги", show_alert=True)
        return
    
    context.user_data["selected_service"] = selected_service
    
    price_text = f"{selected_service['price']}р."
    if selected_service.get("price_per"):
        price_text += f" ({selected_service['price_per']}р./занятие)"
    
    text = (
        f"<b>🏟 Вы выбрали УСЛУГУ:</b>\n"
        f"{selected_service['name']} - {price_text}\n\n"
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

async def handle_back_to_services(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    is_sochi = context.user_data.get("is_sochi", False)
    camp = context.user_data.get("selected_camp", {})
    
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
        "Введите <b>телефон для связи</b> в формате +7 900-234-45-45:",
        parse_mode='HTML'
    )
    return PHONE

async def phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    phone_input = update.message.text.strip()
    logger.info(f"Получен телефон: {phone_input}")
    
    if not validate_phone(phone_input):
        await update.message.reply_text(
            "❌ Неверный формат телефона.\n\n"
            "Пожалуйста, введите номер в формате:\n"
            "<b>+7 900-234-45-45</b> или <b>+79002344545</b>\n\n"
            "Попробуйте ещё раз:",
            parse_mode='HTML'
        )
        return PHONE
    
    formatted_phone = format_phone_for_display(phone_input)
    context.user_data["phone"] = formatted_phone
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
            "🌟 Спасибо, что выбираете Школа мяча! 🌟"
        )
    except Exception as e:
        logger.error(f"Ошибка при отправке админу: {e}")
        await update.message.reply_text(
            "✅ Спасибо! Ваш чек получен.\n"
            "🌟 Спасибо, что выбираете Школа мяча! 🌟"
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
