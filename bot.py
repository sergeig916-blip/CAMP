# ========== УСЛУГИ С КОМПАКТНЫМИ НАЗВАНИЯМИ ДЛЯ КНОПОК ==========
SERVICES = {
    "camp": {
        "name": "🏕️ КЭМП",
        "options": [
            {"name": "10 дней - смена 1 (69 990р.)", "price": "69 990р.", "id": "camp_10_days_1", 
             "short": "10 дней (смена 1)"},
            {"name": "10 дней - смена 7 (69 990р.)", "price": "69 990р.", "id": "camp_10_days_7", 
             "short": "10 дней (смена 7)"},
            {"name": "1 день (7 900р.)", "price": "7 900р.", "id": "camp_1_day", 
             "short": "1 день"}
        ]
    },
    "training": {
        "name": "⚽ ТРЕНИРОВКИ",
        "options": [
            {"name": "Тренировка - 1 занятие (1 890р.)", "price": "1 890р.", "id": "training_1", 
             "short": "1 тренировка"},
            {"name": "Абонемент - 5 занятий (7 450р.)", "price": "7 450р. (1 490р./занятие)", "id": "training_5", 
             "short": "Абонемент 5 занятий"},
            {"name": "Абонемент - 10 занятий (12 900р.)", "price": "12 900р. (1 290р./занятие)", "id": "training_10", 
             "short": "Абонемент 10 занятий"}
        ]
    },
    "other": {
        "name": "📦 ПРОЧЕЕ",
        "options": [
            {"name": "Оплата после пробного дня (65 000р.)", "price": "65 000р.", "id": "trial_day", 
             "short": "Пробный день"},
            {"name": "Форма (4 500р.)", "price": "4 500р.", "id": "uniform", 
             "short": "Форма"}
        ]
    }
}

# Для Сочи свои цены
SOCHI_SERVICES = {
    "camp": {
        "name": "🏕️ КЭМП в Сочи",
        "options": [
            {"name": "Спортсмен (без сопровождения) - Май 02-08 (89 990р.)", "price": "89 990р.", 
             "id": "sochi_sportsman_may", "short": "Спортсмен (Май)"},
            {"name": "Спортсмен (без сопровождения) - Июнь 19-27 (114 990р.)", "price": "114 990р.", 
             "id": "sochi_sportsman_june", "short": "Спортсмен (Июнь)"},
            {"name": "Спортсмен (без сопровождения) - Июль 4-11 (102 490р.)", "price": "102 490р.", 
             "id": "sochi_sportsman_july", "short": "Спортсмен (Июль)"},
            {"name": "Спортсмен (без сопровождения) - Август 1-8 (102 490р.)", "price": "102 490р.", 
             "id": "sochi_sportsman_august", "short": "Спортсмен (Август)"},
            {"name": "Спортсмен + родитель - Май 02-08 (139 990р.)", "price": "139 990р.", 
             "id": "sochi_family_may", "short": "Спортсмен+род. (Май)"},
            {"name": "Спортсмен + родитель - Июнь 19-27 (183 990р.)", "price": "183 990р.", 
             "id": "sochi_family_june", "short": "Спортсмен+род. (Июнь)"},
            {"name": "Спортсмен + родитель - Июль 4-11 (161 990р.)", "price": "161 990р.", 
             "id": "sochi_family_july", "short": "Спортсмен+род. (Июль)"},
            {"name": "Спортсмен + родитель - Август 1-8 (161 990р.)", "price": "161 990р.", 
             "id": "sochi_family_august", "short": "Спортсмен+род. (Август)"},
            {"name": "Сопровождающий - Май 02-08 (59 990р.)", "price": "59 990р.", 
             "id": "sochi_accompanist_may", "short": "Сопровожд. (Май)"},
            {"name": "Сопровождающий - Июнь 19-27 (77 990р.)", "price": "77 990р.", 
             "id": "sochi_accompanist_june", "short": "Сопровожд. (Июнь)"},
            {"name": "Сопровождающий - Июль 4-11 (68 990р.)", "price": "68 990р.", 
             "id": "sochi_accompanist_july", "short": "Сопровожд. (Июль)"},
            {"name": "Сопровождающий - Август 1-8 (68 990р.)", "price": "68 990р.", 
             "id": "sochi_accompanist_august", "short": "Сопровожд. (Август)"}
        ]
    }
}

# В функции handle_payment полный текст инструкции:
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
