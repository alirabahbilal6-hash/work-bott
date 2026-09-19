import logging
import sqlite3
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

# إعداد الـ Logging لمتابعة الأخطاء
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

# تعريف حالات الحوار (Conversation States)
HOURS, WAGE = range(2)


# 1. إنشاء قاعدة البيانات
def init_db():
  conn = sqlite3.connect("work_logs.db")
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


# 2. القائمة الرئيسية الأزرار
def main_keyboard():
  keyboard = [["تسجيل ساعات العمل", "عرض الحساب والإحصائيات"]]
  return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


# 3. الأوامر الرئيسية
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
  await update.message.reply_text(
      "مرحباً بك في بوت تسجيل العمل والإحصائيات!",
      reply_markup=main_keyboard(),
  )
  return ConversationHandler.END


# 4. بداية حوار تسجيل الساعات
async def start_log_work(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
  await update.message.reply_text(
      "أدخل عدد ساعات العمل لهذا اليوم:", reply_markup=ReplyKeyboardRemove()
  )
  return HOURS


async def get_hours(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
  try:
    hours = float(update.message.text)
    context.user_data["hours"] = hours
    await update.message.reply_text("أدخل أجر الساعة (مثال: 500):")
    return WAGE
  except ValueError:
    await update.message.reply_text("يرجى إدخال رقم صحيح لعدد الساعات.")
    return HOURS


async def get_wage(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
  try:
    wage = float(update.message.text)
    hours = context.user_data.get("hours", 0)
    user_id = update.message.from_user.id
    date_str = update.message.date.strftime("%Y-%m-%d")

    # حفظ البيانات في SQLite
    conn = sqlite3.connect("work_logs.db")
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO work_logs (user_id, date, hours, hourly_wage)
        VALUES (?, ?, ?, ?)
    """,
        (user_id, date_str, hours, wage),
    )
    conn.commit()
    conn.close()

    total = hours * wage
    await update.message.reply_text(
        f"تم الحفظ بنجاح!\nساعات العمل: {hours}\nالأجر اليومي: {total:.2f}",
        reply_markup=main_keyboard(),
    )
    return ConversationHandler.END
  except ValueError:
    await update.message.reply_text("يرجى إدخال رقم صحيح للأجر.")
    return WAGE


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
  await update.message.reply_text(
      "تم إلغاء العملية.", reply_markup=main_keyboard()
  )
  return ConversationHandler.END


# 5. تشغيل البوت والـ Handlers
def main():
  init_db()

  # ضع توكن البوت الخاص بك هنا
  TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"

  application = Application.builder().token(TOKEN).build()

  # إعداد ConversationHandler
  conv_handler = ConversationHandler(
      entry_points=[
          MessageHandler(
              filters.Regex("^(تسجيل ساعات العمل)$"), start_log_work
          )
      ],
      states={
          HOURS: [
              MessageHandler(filters.TEXT & ~filters.COMMAND, get_hours)
          ],
          WAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_wage)],
      },
      fallbacks=[CommandHandler("cancel", cancel)],
  )

  application.add_handler(CommandHandler("start", start))
  application.add_handler(conv_handler)

  application.run_polling()


if name == "main":
  main()
