import os
import sqlite3
from datetime import datetime
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    ConversationHandler,
    filters,
)

# الحالات الخاصة بالحوار
HOURS, WAGE = range(2)

# إنشاء قاعدة البيانات والجدول إذا لم تكن موجودة
def init_db():
    conn = sqlite3.connect("work_hours.db")
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS work_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            date TEXT,
            hours REAL,
            hourly_wage REAL
        )
    ''')
    conn.commit()
    conn.close()

# لوحة الأزرار الرئيسية
def main_keyboard():
    return ReplyKeyboardMarkup(
        [["تسجيل ساعات العمل"], ["تقرير الساعات والأجر"]],
        resize_keyboard=True
    )

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "مرحباً بك! اختر من القائمة أدناه لتسجيل ساعات عملك أو عرض التقرير:",
        reply_markup=main_keyboard()
    )

# بداية حوار تسجيل الساعات
async def add_hours_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("كم عدد الساعات التي عملتها اليوم؟")
    return HOURS

async def get_hours(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        hours = float(update.message.text)
        context.user_data['hours'] = hours
        await update.message.reply_text("ما هو أجرك للساعة الواحدة؟")
        return WAGE
    except ValueError:
        await update.message.reply_text("الرجاء إدخال رقم صحيح لعدد الساعات.")
        return HOURS

async def get_wage(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        wage = float(update.message.text)
        hours = context.user_data.get('hours')
        user_id = update.effective_user.id
        today = datetime.now().strftime("%Y-%m-%d")

        conn = sqlite3.connect("work_hours.db")
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO work_logs (user_id, date, hours, hourly_wage) VALUES (?, ?, ?, ?)",
            (user_id, today, hours, wage)
        )
        conn.commit()
        conn.close()

        total_day_wage = hours * wage
        await update.message.reply_text(
            f"تم تسجيل {hours} ساعة بأجر {wage} للساعة.\nإجمالي أجر اليوم: {total_day_wage:.2f}",
            reply_markup=main_keyboard()
        )
        return ConversationHandler.END
    except ValueError:
        await update.message.reply_text("الرجاء إدخال رقم صحيح للأجر.")
        return WAGE

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("تم إلغاء العملية.", reply_markup=main_keyboard())
    return ConversationHandler.END

async def show_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    conn = sqlite3.connect("work_hours.db")
    cursor = conn.cursor()
    cursor.execute("SELECT hours, hourly_wage FROM work_logs WHERE user_id = ?", (user_id,))
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        await update.message.reply_text("لا توجد بيانات مسجلة بعد.", reply_markup=main_keyboard())
        return

    total_hours = sum(row[0] for row in rows)
    total_earnings = sum(row[0] * row[1] for row in rows)

    await update.message.reply_text(
        f"📊 تقرير العمل الخاص بك:\n\n"
        f"⏱ إجمالي الساعات المسجلة: {total_hours:.2f} ساعة\n"
        f"💰 إجمالي الأجر المستحق: {total_earnings:.2f}\n"
        f"📅 عدد أيام العمل المسجلة: {len(rows)} يوم",
        reply_markup=main_keyboard(),
        parse_mode="Markdown"
    )

TOKEN = "8665377975:AAGS3rFg_WceKK_10kByc7KCwiHOGuy8A4"

if name == "main":
    init_db()

    import http.server
    import socketserver
    import threading
[19/09/2026 22:56] Bilal Voice: def run_dummy_server():
        port = int(os.environ.get("PORT", 8080))
        handler = http.server.SimpleHTTPRequestHandler
        with socketserver.TCPServer(("", port), handler) as httpd:
            httpd.serve_forever()

    threading.Thread(target=run_dummy_server, daemon=True).start()

    print("البوت يعمل الآن...")
    app = ApplicationBuilder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^تسجيل ساعات العمل$"), add_hours_start)],
        states={
            HOURS: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_hours)],
            WAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_wage)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(conv_handler)
    app.add_handler(MessageHandler(filters.Regex("^تقرير الساعات والأجر$"), show_report))

    app.run_polling()
