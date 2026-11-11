import os
import io
import csv
import sqlite3
import logging
from datetime import datetime

import jdatetime
from dotenv import load_dotenv
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)
from telegram.ext import (
    Application,
    ApplicationHandlerStop,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_IDS = [int(x.strip()) for x in os.getenv("ADMIN_ID", "").split(",") if x.strip()]
_group = os.getenv("GROUP_ID", "").strip()
GROUP_ID = int(_group) if _group else None

logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    handlers=[logging.FileHandler("bot.log", encoding="utf-8"), logging.StreamHandler()],
)

DB_FILE = "rasad.db"
PAGE = 5
NAME, GRADE, FEEDBACK = range(3)
SKIP = "⏭ رد کردن"
skip_keyboard = ReplyKeyboardMarkup([[SKIP]], resize_keyboard=True, one_time_keyboard=True)

WELCOME = (
    "به سامانه «رصد» خوش آمدید 🌱\n"
    "(سامانه انتقادات، پیشنهادات و نظرات والدین، دانش‌آموزان و اساتید "
    "مدرسه دوره اول خردمندان پاژ)\n\n"
    "لطفاً اطلاعات زیر را مرحله‌به‌مرحله کامل کنید تا در اسرع وقت "
    "نسبت به نظرات شما پاسخگو باشیم."
)


# ---------------- دیتابیس ----------------
def db(query, params=(), fetch=False):
    conn = sqlite3.connect(DB_FILE)
    try:
        cur = conn.execute(query, params)
        result = cur.fetchall() if fetch else cur.lastrowid
        conn.commit()
        return result
    finally:
        conn.close()


def init_db():
    db(
        """CREATE TABLE IF NOT EXISTS feedbacks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created TEXT,
            name TEXT,
            grade TEXT,
            text TEXT,
            user_id INTEGER,
            username TEXT,
            replied INTEGER DEFAULT 0,
            reply_text TEXT
        )"""
    )


def shamsi_now():
    return jdatetime.datetime.now().strftime("%Y/%m/%d  %H:%M")


def fmt(r):
    """r = (id, created, name, grade, text, user_id, username, replied, reply_text)"""
    status = "✅ پاسخ داده شده" if r[7] else "⏳ بدون پاسخ"
    who = f"@{r[6]}" if r[6] else "بدون یوزرنیم"
    body = r[4][:3000]
    msg = (
        f"📩 نظر شماره {r[0]}  ({status})\n\n"
        f"👤 نام: {r[2]}\n"
        f"🎓 پایه: {r[3]}\n"
        f"🕒 زمان: {r[1]}\n"
        f"🔗 تلگرام: {who}\n"
        f"🆔 آیدی: {r[5]}\n\n"
        f"💬 متن:\n{body}"
    )
    if r[7] and r[8]:
        msg += f"\n\n↩️ پاسخ ارسال‌شده:\n{r[8][:500]}"
    return msg


def reply_kb(r):
    label = "✉️ پاسخ مجدد" if r[7] else "✉️ پاسخ"
    return InlineKeyboardMarkup([[InlineKeyboardButton(label, callback_data=f"reply:{r[0]}")]])


# ---------------- فرم کاربران ----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text(WELCOME)
    await update.message.reply_text(
        "👤 نام و نام خانوادگی (اختیاری)\n"
        "اگر نمی‌خواهید بنویسید، دکمه «رد کردن» را بزنید.",
        reply_markup=skip_keyboard,
    )
    return NAME


async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    context.user_data["name"] = "ناشناس" if text == SKIP else text
    await update.message.reply_text(
        "🎓 پایه تحصیلی (اختیاری)\n"
        "مثال: پایه چهارم. یا دکمه «رد کردن» را بزنید.",
        reply_markup=skip_keyboard,
    )
    return GRADE


async def get_grade(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    context.user_data["grade"] = "نامشخص" if text == SKIP else text
    await update.message.reply_text(
        "📝 لطفاً نظر، انتقاد یا پیشنهاد خود را درباره مدرسه بنویسید.\n"
        "ما در اسرع وقت پاسخگو خواهیم بود.\n\n"
        "(این بخش اجباری است)",
        reply_markup=ReplyKeyboardRemove(),
    )
    return FEEDBACK


async def get_feedback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if len(text) < 5:
        await update.message.reply_text("⚠️ متن خیلی کوتاه است. لطفاً نظر خود را کامل‌تر بنویسید.")
        return FEEDBACK

    user = update.effective_user
    name = context.user_data.get("name", "ناشناس")
    grade = context.user_data.get("grade", "نامشخص")
    now = shamsi_now()
    context.user_data.clear()

    # 1) ذخیره در دیتابیس
    try:
        fid = db(
            "INSERT INTO feedbacks (created, name, grade, text, user_id, username) VALUES (?,?,?,?,?,?)",
            (now, name, grade, text, user.id, user.username or ""),
        )
        row = db("SELECT * FROM feedbacks WHERE id=?", (fid,), fetch=True)[0]
    except Exception as e:
        logging.exception("DB error: %s", e)
        await update.message.reply_text("❌ خطایی در ثبت نظر رخ داد. لطفاً دوباره /start را بزنید.")
        return ConversationHandler.END

    # 2) اول به کاربر جواب بده
    await update.message.reply_text(
        "✅ نظر شما با موفقیت ثبت شد.\n"
        "از اینکه وقت گذاشتید و نظرتان را با ما در میان گذاشتید سپاسگزاریم 🌷\n\n"
        "برای ثبت نظر جدید، /start را بزنید."
    )

    # 3) بعد به ادمین‌ها و گروه خبر بده
    targets = list(ADMIN_IDS) + ([GROUP_ID] if GROUP_ID else [])
    for chat_id in targets:
        try:
            await context.bot.send_message(chat_id=chat_id, text=fmt(row), reply_markup=reply_kb(row))
        except Exception as e:
            logging.error("Could not send to %s: %s", chat_id, e)

    return ConversationHandler.END


async def feedback_invalid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("⚠️ لطفاً نظر خود را به صورت متن بنویسید.")
    return FEEDBACK


async def text_only(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("⚠️ لطفاً فقط متن ارسال کنید.")


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text(
        "لغو شد. هر زمان خواستید /start را بزنید.",
        reply_markup=ReplyKeyboardRemove(),
    )
    return ConversationHandler.END


async def fallback_msg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("برای ثبت نظر، دستور /start را بزنید 🌱")


# ---------------- پنل مدیریت ----------------
async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("⛔ شما دسترسی به پنل مدیریت ندارید.")
        return
    kb = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("📋 همه نظرات", callback_data="adm:list:all:0"),
                InlineKeyboardButton("📭 بدون پاسخ", callback_data="adm:list:new:0"),
            ],
            [
                InlineKeyboardButton("📊 آمار", callback_data="adm:stats"),
                InlineKeyboardButton("📥 فایل اکسل", callback_data="adm:csv"),
            ],
        ]
    )
    await update.message.reply_text("🛠 پنل مدیریت سامانه رصد", reply_markup=kb)


async def admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    if q.from_user.id not in ADMIN_IDS:
        await q.answer("دسترسی ندارید", show_alert=True)
        return
    await q.answer()
    chat_id = q.from_user.id
    parts = q.data.split(":")
    action = parts[1]

    if action == "list":
        mode, offset = parts[2], int(parts[3])
        where = "WHERE replied=0" if mode == "new" else ""
        total = db(f"SELECT COUNT(*) FROM feedbacks {where}", fetch=True)[0][0]
        rows = db(
            f"SELECT * FROM feedbacks {where} ORDER BY id DESC LIMIT ? OFFSET ?",
            (PAGE, offset),
            fetch=True,
        )
        if not rows:
            await context.bot.send_message(chat_id, "موردی وجود ندارد.")
            return
        for r in rows:
            await context.bot.send_message(chat_id, fmt(r), reply_markup=reply_kb(r))
        nxt = offset + PAGE
        if nxt < total:
            kb = InlineKeyboardMarkup(
                [[InlineKeyboardButton("⬇️ ۵ تای بعدی", callback_data=f"adm:list:{mode}:{nxt}")]]
            )
            await context.bot.send_message(chat_id, f"نمایش {min(nxt, total)} از {total}", reply_markup=kb)

    elif action == "stats":
        total = db("SELECT COUNT(*) FROM feedbacks", fetch=True)[0][0]
        replied = db("SELECT COUNT(*) FROM feedbacks WHERE replied=1", fetch=True)[0][0]
        today = jdatetime.datetime.now().strftime("%Y/%m/%d")
        today_count = db(
            "SELECT COUNT(*) FROM feedbacks WHERE created LIKE ?", (today + "%",), fetch=True
        )[0][0]
        await context.bot.send_message(
            chat_id,
            f"📊 آمار سامانه رصد\n\n"
            f"کل نظرات: {total}\n"
            f"امروز: {today_count}\n"
            f"پاسخ داده‌شده: {replied}\n"
            f"بدون پاسخ: {total - replied}",
        )

    elif action == "csv":
        rows = db(
            "SELECT id, created, name, grade, text, user_id, username, replied, reply_text "
            "FROM feedbacks ORDER BY id",
            fetch=True,
        )
        sio = io.StringIO()
        w = csv.writer(sio)
        w.writerow(["شماره", "زمان", "نام", "پایه", "نظر", "آیدی تلگرام", "یوزرنیم", "پاسخ داده شده", "متن پاسخ"])
        w.writerows(rows)
        data = io.BytesIO(sio.getvalue().encode("utf-8-sig"))
        data.name = "rasad_feedbacks.csv"
        await context.bot.send_document(chat_id, document=data, filename="rasad_feedbacks.csv")


async def reply_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    if q.from_user.id not in ADMIN_IDS:
        await q.answer("دسترسی ندارید", show_alert=True)
        return
    fid = int(q.data.split(":")[1])
    context.user_data["reply_to"] = fid
    await q.answer("پاسخ را در چت خصوصی بات بنویسید")
    try:
        await context.bot.send_message(
            q.from_user.id,
            f"✍️ متن پاسخ خود به نظر شماره {fid} را بنویسید و ارسال کنید.\n"
            "برای انصراف: /cancel",
        )
    except Exception as e:
        logging.error("Cannot DM admin %s: %s", q.from_user.id, e)


async def admin_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    fid = context.user_data.get("reply_to")
    if not fid or update.effective_user.id not in ADMIN_IDS:
        return  # اجازه بده بقیه هندلرها کار کنند
    rows = db("SELECT * FROM feedbacks WHERE id=?", (fid,), fetch=True)
    context.user_data.pop("reply_to", None)
    if not rows:
        await update.message.reply_text("نظر پیدا نشد.")
        raise ApplicationHandlerStop
    r = rows[0]
    answer = update.message.text.strip()
    try:
        await context.bot.send_message(
            chat_id=r[5],
            text="📬 پاسخ مدیریت مدرسه به نظر شما:\n\n" + answer,
        )
        db("UPDATE feedbacks SET replied=1, reply_text=? WHERE id=?", (answer, fid))
        await update.message.reply_text(f"✅ پاسخ برای نظر شماره {fid} ارسال شد.")
    except Exception as e:
        logging.error("Reply failed: %s", e)
        await update.message.reply_text(
            "❌ ارسال نشد. احتمالاً کاربر بات را بلاک کرده است."
        )
    raise ApplicationHandlerStop


def main():
    init_db()
    app = Application.builder().token(TOKEN).build()

    private = filters.ChatType.PRIVATE
    text_filter = filters.TEXT & ~filters.COMMAND & private

    # پنل مدیریت
    app.add_handler(CommandHandler("admin", admin_panel, filters=private))
    app.add_handler(CallbackQueryHandler(admin_callback, pattern=r"^adm:"))
    app.add_handler(CallbackQueryHandler(reply_button, pattern=r"^reply:\d+$"))
    app.add_handler(MessageHandler(text_filter, admin_text), group=-1)

    # فرم کاربران
    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start, filters=private)],
        states={
            NAME: [MessageHandler(text_filter, get_name),
                   MessageHandler(~filters.COMMAND & private, text_only)],
            GRADE: [MessageHandler(text_filter, get_grade),
                    MessageHandler(~filters.COMMAND & private, text_only)],
            FEEDBACK: [MessageHandler(text_filter, get_feedback),
                       MessageHandler(~filters.COMMAND & private, feedback_invalid)],
        },
        fallbacks=[CommandHandler("start", start, filters=private),
                   CommandHandler("cancel", cancel, filters=private)],
    )
    app.add_handler(conv)
    app.add_handler(CommandHandler("cancel", cancel, filters=private))
    app.add_handler(MessageHandler(private & ~filters.COMMAND, fallback_msg))

    logging.info("Rasad bot started...")
    app.run_polling()


if __name__ == "__main__":
    main()