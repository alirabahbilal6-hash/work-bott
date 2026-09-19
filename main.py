
import sqlite3
from datetime import datetime
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    ConversationLogic,
    filters,
)

# الحالات الخاصة بالحوار (Conversation States)
HOURS, WAGE = range(2)

# إنشاء قاعدة البيانات والجدول إذا لم تكن موجودة
def init_db():
    conn = sqlite3.connect("work_hours.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS work_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            date TEXT,
            hours REAL,
            hourly_wage REAL
        )
    """)
    conn.commit()
    conn.close()

# لوحة الأزرار الرئيسية
def main_keyboard():
    return ReplyKeyboardMarkup(
        [["تسجيل ساعات العمل", "تقرير الساعات والأجر"]],
        resize_keyboard=True
    )

# أمر البداية /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    init_db()
    await update.message.reply_text(
        "مرحباً بك في بوت تسجيل ساعات العمل والأجر!\nاختر أحد الخيارات من القائمة أدناه:",
        reply_markup=main_keyboard()
    )

# بداية عملية تسجيل الساعات
async def add_hours_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("كم عدد الساعات التي عملتها اليوم؟ (أدخل رقماً مثل: 8 أو 7.5)")
    return HOURS

# استقبال عدد الساعات والطلب الأجر
async def get_hours(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        hours = float(update.message.text.strip())
        context.user_data["hours"] = hours
        await update.message.reply_text("أدخل أجر الساعة الواحدة (مثال: 250):")
        return WAGE
    except ValueError:
        await update.message.reply_text("يرجى إدخال رقم صحيح أو عشري لعدد الساعات.")
        return HOURS

# حفظ البيانات في قاعدة البيانات
async def get_wage(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        wage = float(update.message.text.strip())
        hours = context.user_data.get("hours")
        user_id = update.effective_user.id
        date_str = datetime.now().strftime("%Y-%m-%d")

        conn = sqlite3.connect("work_hours.db")
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO work_logs (user_id, date, hours, hourly_wage) VALUES (?, ?, ?, ?)",
            (user_id, date_str, hours, wage)
        )
        conn.commit()
        conn.close()

        total_day = hours * wage
        await update.message.reply_text(
            f" تم حفظ البيانات بنجاح!\n"
            f"التاريخ: {date_str}\n"
            f"الساعات: {hours} ساعة\n"
            f"أجر اليوم: {total_day:.2f}",
            reply_markup=main_keyboard()
        )
        return ConversationHandler.END
    except ValueError:
        await update.message.reply_text("يرجى إدخال رقم صحيح لأجر الساعة.")
        return WAGE

# إلغاء العملية
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("تم إلغاء العملية.", reply_markup=main_keyboard())
    return ConversationHandler.END

# عرض التقرير المالي والساعات
async def show_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    conn = sqlite3.connect("work_hours.db")
    cursor = conn.cursor()
    cursor.execute(
        "SELECT hours, hourly_wage FROM work_logs WHERE user_id = ?",
        (user_id,)
    )
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        await update.message.reply_text("لا توجد أي سجلات محفوظة لك حتى الآن.", reply_markup=main_keyboard())
        return

    total_hours = sum(row[0] for row in rows)
    total_earnings = sum(row[0] * row[1] for row in rows)

    await update.message.reply_text(
        f"📊 تقرير العمل الخاص بك:\n\n"
        f" إجمالي الساعات المسجلة: {total_hours:.2f} ساعة\n"
        f"💰 إجمالي الأجر المستحق: {total_earnings:.2f}\n"
        f" عدد أيام العمل المسجلة: {len(rows)} يوم",
        reply_markup=main_keyboard(),
        parse_mode="Markdown"
    )
[19/09/2026 21:58] Bilal Voice: if name == "main":
    # ضع توكن البوت الخاص بك هنا
    TOKEN = "8665377975:AAGS1rFg_WcecKK_1OkByc7KCwiHOGuy8A4"
    
    app = ApplicationBuilder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^تسجيل ساعات العمل$"), add_hours_start)],
        states={
            HOURS: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_hours)],
            WAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_wage)],
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(conv_handler)
    app.add_handler(MessageHandler(filters.Regex("^تقرير الساعات والأجر$"), show_report))

    print("البوت يعمل الآن...")
    app.run_polling()
