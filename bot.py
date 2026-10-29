import asyncio
import logging
import json
import os
import random
import string
import threading
import urllib.request
from datetime import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer

from baleio import Bot, Dispatcher, md
from baleio.client.default import DefaultBotProperties
from baleio.enums import ParseMode
from baleio.filters import CommandStart
from baleio.types import Message, CallbackQuery, InputFile
from baleio.utils import InlineKeyboardBuilder
from baleio.fsm import FSMContext, StatesGroup, State
from baleio.fsm.storage.memory import MemoryStorage

# ================= تنظیمات =================
TOKEN = "1890317645:KASCVcx5ObzLAIyzN-3c0-BIpYmOg31dNbc"
ADMIN_ID = 123456789                    # ⚠️ شناسه عددی خودت
GROUP_CHAT_ID = "@testsoheli"           # ⚠️ آیدی کانال/گروه

SUPPORT_ID = "amani_amirhossein"
SUPPORT_LINK = f"https://ble.ir/{SUPPORT_ID}"

PORT = int(os.environ.get("PORT", 8080))
BOT_VERSION = "3.1.0-final"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)
log = logging.getLogger("bot")

# ================= محتوای ثابت =================
BASE_NAME = "پایگاه علمی آموزشی امام موسی بن جعفر (علیه‌السلام)"
BASE_ADDRESS = "میدان آزادی، شهرک شهید فکوری"
EITAA_LINK = "https://eitaa.com/Research20"

# ================= بازی‌ها =================
GAMES = {
    "sky": {
        "title": "✈️ نبرد آسمان",
        "tagline": "تا انتها پرواز کن!",
        "poster": "https://cdn.imgurl.ir/uploads/h668816_.png",
        "online": "https://nabard-aseman.a42464849.workers.dev/",
        "bazaar": "https://cafebazaar.ir/app/co.median.android.zpdqbwe",
        "desc": (
            "یک بازی سه‌بعدی خلبانی که توی مرورگر و موبایل اجرا می‌شه.\n"
            "بدون نصب، بدون حجم اضافه — فقط بازی کن!\n\n"
            "🎮 **چطور بازی می‌کنی؟**\n"
            "با هواپیمات پرواز می‌کنی، از موانع و دشمن‌ها رد می‌شی،\n"
            "گوی‌های آبی جمع می‌کنی و سعی می‌کنی رکورد بزنی.\n"
            "هرچی جلوتر بری، سطحت بالاتر می‌ره و بازی سخت‌تر می‌شه."
        ),
        "features": (
            "✈️ ۵ هواپیمای مختلف (جنگنده، بمب‌افکن، جت، قدیمی، سفینه)\n"
            "🎭 ۴ شخصیت خلبان با استایل متفاوت\n"
            "🎨 ۸ طرح بدنه برای سفارشی‌سازی هواپیما\n"
            "💨 ۶ رنگ دود برای هواپیما\n"
            "🌊 ۵ محیط پرواز (دریا آبی، اقیانوس سبز، دریاچه صورتی، آب یخی، گدازه نارنجی)\n"
            "🛡️ ۴ قدرت ویژه (سپر، آهنربا، اسلوموشن، کاهش مصرف)\n"
            "🏅 ۷ نشان افتخار برای دستاوردها\n"
            "💎 الماس برای ادامه بازی بعد از باخت\n"
            "🪙 سکه برای خرید آیتم‌ها\n"
            "🎮 پشتیبانی از دسته بازی (PlayStation, Xbox و...)\n"
            "📱 کنترل لمسی، ژیروسکوپ یا موس\n"
            "🏆 گواهی رسمی رکورد و مسابقه هفتگی"
        ),
        "prize": "🏆 **مسابقه هفتگی:** گواهی رکورد خودت رو بگیر، برای ما بفرست و توی مسابقه هفتگی شرکت کن — جایزه الماس ببر!",
    },
    "light": {
        "title": "🚦 چالش چراغ‌ها",
        "tagline": "ذهنت را به چالش بکش!",
        "poster": "https://cdn.imgurl.ir/uploads/c776047_.jpg",
        "online": "https://chalesh-light.a42464849.workers.dev/",
        "bazaar": "https://cafebazaar.ir/app/co.median.android.bnpewlk",
        "desc": (
            "یک بازی پازل جذاب و اعتیادآور!\n\n"
            "هدف بازی ساده است: تمام چراغ‌های روشن را خاموش کن. "
            "اما هر کلیک روی یک چراغ، خودش و چهار چراغ کناری‌اش را تغییر می‌دهد. "
            "پس باید با دقت و استراتژی حرکت کنی!"
        ),
        "features": (
            "🎚️ ۵ سطح سختی از خیلی آسون تا خیلی سخت\n"
            "🔲 شبکه‌های ۳×۳ تا ۱۰×۱۰\n"
            "🎨 ۸ تم رنگی قابل خرید با امتیاز\n"
            "⏱️ چالش زمانی هیجان‌انگیز\n"
            "🏅 سیستم رکورد و جدول امتیازات\n"
            "🌐 ۳ زبان: فارسی، انگلیسی، عربی\n"
            "🌗 ۳ تم ظاهری: تیره، روشن، نئون\n"
            "🎵 موسیقی و افکت‌های صوتی"
        ),
        "prize": "🧠 آماده‌ای ذهنت را به چالش بکشی؟",
    },
}

# ================= فایل ذخیره‌سازی =================
DATA_FILE = "requests.json"
REVIEW_FILE = "reviews.json"
STATS_FILE = "stats.json"

def load_json(file, default=None):
    if default is None:
        default = []
    try:
        if os.path.exists(file):
            with open(file, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception as e:
        log.error(f"خطا در خواندن {file}: {e}")
    return default

def save_json(file, data):
    try:
        with open(file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        log.error(f"خطا در ذخیره {file}: {e}")

def bump_stat(key):
    stats = load_json(STATS_FILE, default={})
    stats[key] = stats.get(key, 0) + 1
    save_json(STATS_FILE, stats)

def gen_tracking_id():
    year = datetime.now().year
    random_part = "".join(random.choices(string.digits, k=4))
    letter_part = "".join(random.choices(string.ascii_uppercase, k=2))
    return f"REQ-{year}-{random_part}{letter_part}"

def gen_review_id():
    year = datetime.now().year
    random_part = "".join(random.choices(string.digits, k=4))
    return f"REV-{year}-{random_part}"

def sep():
    return "━━━━━━━━━━━━━━━━"

def header(icon, title):
    return f"{icon} **{title}**\n{sep()}"

# ================= وضعیت FSM =================
class ExtraClassForm(StatesGroup):
    name = State()
    grade = State()
    subject = State()
    day = State()
    time = State()
    description = State()

class ReviewForm(StatesGroup):
    grade = State()
    class_name = State()
    rating = State()
    comment = State()

# ================= راه‌اندازی =================
dp = Dispatcher(storage=MemoryStorage())

# ================= ابزارهای کیبورد =================
def kb_main():
    kb = InlineKeyboardBuilder()
    kb.button(text="🏛️ معرفی پایگاه", callback_data="about")
    kb.button(text="📅 برنامه هفتگی", callback_data="program")
    kb.button(text="➕ درخواست کلاس فوق‌برنامه", callback_data="extra_start")
    kb.button(text="⭐ رضایت‌سنجی کلاس", callback_data="review_start")
    kb.button(text="🎮 بازی و سرگرمی", callback_data="games_menu")
    kb.button(text="📢 کانال ایتا", url=EITAA_LINK)
    kb.button(text="📞 پشتیبانی", url=SUPPORT_LINK)
    kb.button(text="ℹ️ درباره ربات", callback_data="bot_info")
    kb.adjust(1)
    return kb.as_markup()

def kb_back_main():
    kb = InlineKeyboardBuilder()
    kb.button(text="🏠 منوی اصلی", callback_data="back_main")
    kb.adjust(1)
    return kb.as_markup()

def kb_games_menu():
    kb = InlineKeyboardBuilder()
    kb.button(text="✈️ نبرد آسمان", callback_data="game_sky")
    kb.button(text="🚦 چالش چراغ‌ها", callback_data="game_light")
    kb.button(text="🏠 منوی اصلی", callback_data="back_main")
    kb.adjust(2, 1)
    return kb.as_markup()

def kb_game_detail(key):
    g = GAMES[key]
    kb = InlineKeyboardBuilder()
    kb.button(text="🎮 بازی آنلاین", url=g["online"])
    kb.button(text="📥 دانلود از بازار", url=g["bazaar"])
    kb.button(text="🔙 بازگشت به بازی‌ها", callback_data="games_menu")
    kb.button(text="🏠 منوی اصلی", callback_data="back_main")
    kb.adjust(2, 2)
    return kb.as_markup()

def kb_grades():
    kb = InlineKeyboardBuilder()
    kb.button(text="پایه هفتم", callback_data="grade_7")
    kb.button(text="پایه هشتم", callback_data="grade_8")
    kb.button(text="پایه نهم", callback_data="grade_9")
    kb.button(text="🏠 منوی اصلی", callback_data="back_main")
    kb.adjust(2, 1, 1)
    return kb.as_markup()

def kb_extra_grades():
    kb = InlineKeyboardBuilder()
    kb.button(text="هفتم", callback_data="ex_grade_7")
    kb.button(text="هشتم", callback_data="ex_grade_8")
    kb.button(text="نهم", callback_data="ex_grade_9")
    kb.button(text="🔙 انصراف", callback_data="back_main")
    kb.adjust(3, 1)
    return kb.as_markup()

def kb_days():
    kb = InlineKeyboardBuilder()
    kb.button(text="شنبه (پیش‌فرض)", callback_data="day_sat")
    kb.button(text="یکشنبه", callback_data="day_sun")
    kb.button(text="دوشنبه", callback_data="day_mon")
    kb.button(text="🔙 بازگشت", callback_data="ex_back_grade")
    kb.adjust(2, 1, 1)
    return kb.as_markup()

def kb_times():
    kb = InlineKeyboardBuilder()
    kb.button(text="بازه اول (۱۶:۰۰–۱۷:۰۰) (پیش‌فرض)", callback_data="time_1")
    kb.button(text="بازه دوم (۱۷:۱۵–اذان)", callback_data="time_2")
    kb.button(text="🔙 بازگشت", callback_data="ex_back_day")
    kb.adjust(1)
    return kb.as_markup()

def kb_preview_confirm():
    kb = InlineKeyboardBuilder()
    kb.button(text="✅ تایید و ارسال نهایی", callback_data="ex_confirm_send")
    kb.button(text="✏️ ویرایش توضیحات", callback_data="ex_edit_desc")
    kb.button(text="🔙 انصراف", callback_data="back_main")
    kb.adjust(1)
    return kb.as_markup()

def kb_review_grades():
    kb = InlineKeyboardBuilder()
    kb.button(text="هفتم", callback_data="rev_grade_7")
    kb.button(text="هشتم", callback_data="rev_grade_8")
    kb.button(text="نهم", callback_data="rev_grade_9")
    kb.button(text="🔙 انصراف", callback_data="back_main")
    kb.adjust(3, 1)
    return kb.as_markup()

def kb_ratings():
    kb = InlineKeyboardBuilder()
    kb.button(text="⭐ ۱", callback_data="rate_1")
    kb.button(text="⭐ ۲", callback_data="rate_2")
    kb.button(text="⭐ ۳", callback_data="rate_3")
    kb.button(text="⭐ ۴", callback_data="rate_4")
    kb.button(text="⭐ ۵", callback_data="rate_5")
    kb.button(text="🔙 انصراف", callback_data="back_main")
    kb.adjust(5, 1)
    return kb.as_markup()

# ================= برنامه هفتگی =================
WEEKLY = {
    "7": (
        "📚 **برنامه پایه هفتم (شنبه‌ها)**\n" + sep() + "\n\n"
        "⏰ ۱۶:۰۰ – ۱۷:۰۰ | 🧮 مفاهیم ریاضی + کارگاه خلاقیت علمی\n"
        "☕ ۱۷:۰۰ – ۱۷:۱۵ | استراحت و پذیرایی\n"
        "💬 ۱۷:۱۵ – اذان | مشاوره گروهی\n"
        "🕌 بعد از اذان | نماز جماعت در مسجد امیرالمؤمنین (ع)\n\n"
        "📍 شهرک شهید فکوری — پایگاه امام موسی بن جعفر (ع)"
    ),
    "8": (
        "📚 **برنامه پایه هشتم (شنبه‌ها)**\n" + sep() + "\n\n"
        "⏰ ۱۶:۰۰ – ۱۷:۰۰ | 🧮 مفاهیم ریاضی + کارگاه خلاقیت علمی\n"
        "☕ ۱۷:۰۰ – ۱۷:۱۵ | استراحت و پذیرایی\n"
        "💬 ۱۷:۱۵ – اذان | مشاوره گروهی\n"
        "🕌 بعد از اذان | نماز جماعت در مسجد امیرالمؤمنین (ع)\n\n"
        "📍 شهرک شهید فکوری — پایگاه امام موسی بن جعفر (ع)"
    ),
    "9": (
        "📚 **برنامه پایه نهم (شنبه‌ها)**\n" + sep() + "\n\n"
        "⏰ ۱۶:۰۰ – ۱۷:۰۰ | 🎯 آشنایی با مشاغل و رشته‌ها + کارگاه مسیر آینده\n"
        "☕ ۱۷:۰۰ – ۱۷:۱۵ | استراحت و پذیرایی\n"
        "💬 ۱۷:۱۵ – اذان | مشاوره گروهی\n"
        "🕌 بعد از اذان | نماز جماعت در مسجد امیرالمؤمنین (ع)\n\n"
        "📍 شهرک شهید فکوری — پایگاه امام موسی بن جعفر (ع)"
    ),
}

# ================= هندلرها =================
@dp.message(CommandStart())
async def start(message: Message):
    try:
        bump_stat("starts")
        welcome = (
            "✨ **به ربات معاونت علمی و پژوهشی خوش آمدید** ✨\n" + sep() + "\n"
            f"🏛️ {BASE_NAME}\n\n"
            "از منوی زیر انتخاب کنید 👇"
        )
        await message.answer(welcome, reply_markup=kb_main())
    except Exception as e:
        log.error(f"خطا در start: {e}")

@dp.callback_query()
async def handle_cb(call: CallbackQuery, state: FSMContext):
    try:
        await call.answer()
    except Exception:
        pass
    data = call.data

    try:
        if data == "back_main":
            await state.clear()
            await call.message.edit_text(
                "🏠 **منوی اصلی**\n" + sep() + "\n\nلطفاً یک گزینه را انتخاب کنید:",
                reply_markup=kb_main()
            )

        elif data == "about":
            text = (
                header("🏛️", BASE_NAME) + "\n\n"
                f"📍 {BASE_ADDRESS}\n\n"
                "این ربات توسط **معاونت علمی و پژوهشی** پایگاه راه‌اندازی شده است.\n\n"
                "🎯 **خدمات:**\n"
                "• کلاس‌های آموزشی ویژه متوسطه اول (هفتم، هشتم، نهم)\n"
                "• کارگاه‌های خلاقیت علمی و مسیر آینده\n"
                "• مشاوره گروهی و انگیزشی\n"
                "• بازی و سرگرمی آموزشی\n\n"
                f"📢 کانال ایتا: {EITAA_LINK}"
            )
            await call.message.edit_text(text, reply_markup=kb_back_main())

        elif data == "bot_info":
            text = (
                header("ℹ️", "درباره ربات") + "\n\n"
                f"🤖 **نسخه:** `{BOT_VERSION}`\n"
                f"🏛️ **پایگاه:** {BASE_NAME}\n"
                f"📞 **پشتیبانی:** @{SUPPORT_ID}\n\n"
                "✅ این ربات کاملاً **رایگان** و **بدون محدودیت زمانی** است.\n"
                "🟢 وضعیت: **همیشه فعال**\n\n"
                "🙏 از همراهی شما سپاسگزاریم."
            )
            await call.message.edit_text(text, reply_markup=kb_back_main())

        elif data == "program":
            await call.message.edit_text(
                "📅 **برنامه هفتگی**\n" + sep() + "\n\nلطفاً پایه تحصیلی خود را انتخاب کنید:",
                reply_markup=kb_grades()
            )

        elif data.startswith("grade_"):
            grade = data.split("_")[1]
            await call.message.edit_text(
                WEEKLY.get(grade, "برنامه‌ای یافت نشد."),
                reply_markup=kb_grades()
            )

        # ========== بازی و سرگرمی ==========
        elif data == "games_menu":
            bump_stat("games_menu")
            text = (
                header("🎮", "بازی و سرگرمی") + "\n\n"
                "یه گیم خوب، بهترین راه برای استراحت و شارژ مغزه! 😎\n\n"
                "یکی از بازی‌های زیر رو انتخاب کن:\n\n"
                "✈️ **نبرد آسمان** — پرواز هیجان‌انگیز سه‌بعدی\n"
                "🚦 **چالش چراغ‌ها** — پازل ذهنی جذاب\n\n"
                "🎁 هر دو بازی هم **آنلاین** و هم **قابل دانلود** هستن!"
            )
            await call.message.edit_text(text, reply_markup=kb_games_menu())

        elif data.startswith("game_"):
            key = data.split("_", 1)[1]
            g = GAMES.get(key)
            if not g:
                await call.message.edit_text(
                    "بازی یافت نشد.",
                    reply_markup=kb_games_menu()
                )
                return

            bump_stat(f"game_{key}")

            text = (
                f"{header('🎮', g['title'] + ' — ' + g['tagline'])}\n\n"
                f"{g['desc']}\n\n"
                f"{sep()}\n\n"
                f"✨ **امکانات:**\n{g['features']}\n\n"
                f"{sep()}\n\n"
                f"{g['prize']}\n\n"
                f"🔥 **پس منتظر چی هستی؟ همین الان شروع کن!**"
            )

            # ---------- تلاش ۱: ارسال عکس با URL ----------
            photo_sent = False
            try:
                await call.bot.send_photo(
                    chat_id=call.message.chat.id,
                    photo=g["poster"],
                    caption=text,
                    reply_markup=kb_game_detail(key)
                )
                photo_sent = True
                log.info(f"✅ پوستر بازی {key} با URL ارسال شد")
            except Exception as e1:
                log.error(f"❌ ارسال پوستر با URL ناموفق ({key}): {e1}")

            # ---------- تلاش ۲: InputFile از URL ----------
            if not photo_sent:
                try:
                    photo_input = InputFile.from_url(g["poster"])
                    await call.bot.send_photo(
                        chat_id=call.message.chat.id,
                        photo=photo_input,
                        caption=text,
                        reply_markup=kb_game_detail(key)
                    )
                    photo_sent = True
                    log.info(f"✅ پوستر بازی {key} با InputFile ارسال شد")
                except Exception as e2:
                    log.error(f"❌ ارسال پوستر با InputFile ناموفق ({key}): {e2}")

            # ---------- تلاش ۳: دانلود bytes و ارسال ----------
            if not photo_sent:
                try:
                    req = urllib.request.Request(
                        g["poster"],
                        headers={"User-Agent": "Mozilla/5.0"}
                    )
                    with urllib.request.urlopen(req, timeout=15) as resp:
                        img_bytes = resp.read()
                    await call.bot.send_photo(
                        chat_id=call.message.chat.id,
                        photo=InputFile(img_bytes, filename="poster.jpg"),
                        caption=text,
                        reply_markup=kb_game_detail(key)
                    )
                    photo_sent = True
                    log.info(f"✅ پوستر بازی {key} با bytes ارسال شد")
                except Exception as e3:
                    log.error(f"❌ ارسال پوستر با bytes ناموفق ({key}): {e3}")

            # ---------- Fallback نهایی: متن ----------
            if not photo_sent:
                log.warning(f"⚠️ همه روش‌های ارسال عکس شکست خورد — fallback به متن ({key})")
                try:
                    await call.message.edit_text(text, reply_markup=kb_game_detail(key))
                except Exception:
                    try:
                        await call.message.answer(text, reply_markup=kb_game_detail(key))
                    except Exception as e5:
                        log.error(f"ارسال پیام جدید ناموفق: {e5}")

        # ========== درخواست کلاس ==========
        elif data == "extra_start":
            await state.set_state(ExtraClassForm.name)
            await call.message.edit_text(
                header("➕", "درخواست برگزاری کلاس فوق‌برنامه") + "\n\n"
                "📌 **مرحله ۱ از ۶**\n\n"
                "لطفاً **نام و نام خانوادگی** خود را وارد کنید:\n"
                "(اختیاری — اگر نمی‌خواهید وارد کنید، دکمه زیر را بزنید)",
                reply_markup=InlineKeyboardBuilder()
                    .button(text="⏭️ رد کردن", callback_data="ex_skip_name")
                    .button(text="🏠 انصراف", callback_data="back_main")
                    .adjust(1).as_markup()
            )

        elif data == "ex_skip_name":
            await state.update_data(name="(وارد نشده)")
            await state.set_state(ExtraClassForm.grade)
            await call.message.edit_text(
                "📌 **مرحله ۲ از ۶**\n\n🎓 پایه تحصیلی خود را انتخاب کنید:",
                reply_markup=kb_extra_grades()
            )

        elif data.startswith("ex_grade_"):
            grade = data.split("_")[2]
            await state.update_data(grade=grade)
            await state.set_state(ExtraClassForm.subject)
            await call.message.edit_text(
                f"📌 **مرحله ۳ از ۶**\n\n"
                f"🎓 پایه: **{grade}**\n\n"
                "لطفاً **نام کلاس یا موضوع** درخواستی خود را بنویسید:\n"
                "(مثال: کلاس رباتیک، کارگاه نجوم و...)",
                reply_markup=kb_back_main()
            )

        elif data == "ex_back_grade":
            await state.set_state(ExtraClassForm.grade)
            await call.message.edit_text(
                "📌 **مرحله ۲ از ۶**\n\n🎓 پایه تحصیلی خود را انتخاب کنید:",
                reply_markup=kb_extra_grades()
            )

        elif data == "ex_back_day":
            await state.set_state(ExtraClassForm.day)
            await call.message.edit_text(
                "📌 **مرحله ۴ از ۶**\n\n"
                "📅 **روز برگزاری** را انتخاب کنید:\n\n"
                "💡 **توجه:** ۹۰٪ کلاس‌های علمی در روز **شنبه** برگزار می‌شوند. "
                "اگر روز دیگری مد نظر دارید، انتخاب کنید.",
                reply_markup=kb_days()
            )

        elif data.startswith("day_"):
            day_map = {"sat": "شنبه", "sun": "یکشنبه", "mon": "دوشنبه"}
            day = day_map.get(data.split("_")[1], "شنبه")
            await state.update_data(day=day)
            await state.set_state(ExtraClassForm.time)
            await call.message.edit_text(
                f"📌 **مرحله ۵ از ۶**\n\n"
                f"📅 روز: **{day}**\n\n"
                "⏰ **بازه زمانی** را انتخاب کنید:\n\n"
                "💡 **توجه:** معمولاً کلاس‌ها در **بازه اول** برگزار می‌شوند. "
                "اگر زمان دیگری مد نظر دارید، انتخاب کنید.",
                reply_markup=kb_times()
            )

        elif data.startswith("time_"):
            time_map = {"1": "بازه اول (۱۶:۰۰–۱۷:۰۰)", "2": "بازه دوم (۱۷:۱۵–اذان)"}
            time_slot = time_map.get(data.split("_")[1], "بازه اول")
            await state.update_data(time=time_slot)
            await state.set_state(ExtraClassForm.description)
            await call.message.edit_text(
                f"📌 **مرحله ۶ از ۶**\n\n"
                f"⏰ زمان: **{time_slot}**\n\n"
                "📄 **توضیحات (اختیاری)**\n\n"
                "اگر توضیح بیشتری دارید بنویسید، یا دکمه زیر را بزنید:",
                reply_markup=InlineKeyboardBuilder()
                    .button(text="⏭️ رد کردن و مشاهده پیش‌نمایش", callback_data="ex_skip_desc")
                    .button(text="🏠 انصراف", callback_data="back_main")
                    .adjust(1).as_markup()
            )

        elif data == "ex_skip_desc":
            await state.update_data(description="(بدون توضیح)")
            await show_preview(call, state)

        elif data == "ex_edit_desc":
            await state.set_state(ExtraClassForm.description)
            await call.message.edit_text(
                "📄 **ویرایش توضیحات**\n\n"
                "توضیحات جدید خود را وارد کنید یا دکمه زیر را بزنید:",
                reply_markup=InlineKeyboardBuilder()
                    .button(text="⏭️ بدون توضیح", callback_data="ex_skip_desc")
                    .button(text="🔙 بازگشت به پیش‌نمایش", callback_data="ex_show_preview")
                    .adjust(1).as_markup()
            )

        elif data == "ex_show_preview":
            await show_preview(call, state)

        elif data == "ex_confirm_send":
            await finalize_extra(call, state)

        # ========== رضایت‌سنجی ==========
        elif data == "review_start":
            await state.set_state(ReviewForm.grade)
            await call.message.edit_text(
                header("⭐", "رضایت‌سنجی کلاس") + "\n\n"
                "📌 **مرحله ۱ از ۴**\n\n"
                "لطفاً **پایه تحصیلی** خود را انتخاب کنید:",
                reply_markup=kb_review_grades()
            )

        elif data.startswith("rev_grade_"):
            grade = data.split("_")[2]
            await state.update_data(grade=grade)
            await state.set_state(ReviewForm.class_name)
            await call.message.edit_text(
                f"📌 **مرحله ۲ از ۴**\n\n"
                f"🎓 پایه: **{grade}**\n\n"
                "لطفاً **نام کلاسی** که در آن شرکت کرده‌اید را بنویسید:\n"
                "(مثال: ریاضی، رباتیک، نجوم و...)",
                reply_markup=kb_back_main()
            )

        elif data.startswith("rate_"):
            rating = data.split("_")[1]
            await state.update_data(rating=rating)
            await state.set_state(ReviewForm.comment)
            await call.message.edit_text(
                f"📌 **مرحله ۴ از ۴**\n\n"
                f"⭐ امتیاز: **{rating} از ۵**\n\n"
                "📝 لطفاً **نظر یا انتقاد** خود را درباره این کلاس بنویسید:\n"
                "(اختیاری — اگر نمی‌خواهید، دکمه زیر را بزنید)",
                reply_markup=InlineKeyboardBuilder()
                    .button(text="⏭️ رد کردن و ارسال", callback_data="rev_skip_comment")
                    .button(text="🏠 انصراف", callback_data="back_main")
                    .adjust(1).as_markup()
            )

        elif data == "rev_skip_comment":
            await finalize_review(call, state, comment="(بدون نظر)")

    except Exception as e:
        log.error(f"خطا در handle_cb (data={data}): {e}")

# ================= دریافت متن =================
@dp.message(ExtraClassForm.name)
async def got_name(message: Message, state: FSMContext):
    try:
        await state.update_data(name=message.text)
        await state.set_state(ExtraClassForm.grade)
        await message.answer(
            "📌 **مرحله ۲ از ۶**\n\n🎓 پایه تحصیلی خود را انتخاب کنید:",
            reply_markup=kb_extra_grades()
        )
    except Exception as e:
        log.error(f"خطا در got_name: {e}")

@dp.message(ExtraClassForm.subject)
async def got_subject(message: Message, state: FSMContext):
    try:
        await state.update_data(subject=message.text)
        await state.set_state(ExtraClassForm.day)
        await message.answer(
            "📌 **مرحله ۴ از ۶**\n\n"
            "📅 **روز برگزاری** را انتخاب کنید:\n\n"
            "💡 **توجه:** ۹۰٪ کلاس‌های علمی در روز **شنبه** برگزار می‌شوند. "
            "اگر روز دیگری مد نظر دارید، انتخاب کنید.",
            reply_markup=kb_days()
        )
    except Exception as e:
        log.error(f"خطا در got_subject: {e}")

@dp.message(ExtraClassForm.description)
async def got_desc(message: Message, state: FSMContext):
    try:
        await state.update_data(description=message.text)
        await show_preview(message, state)
    except Exception as e:
        log.error(f"خطا در got_desc: {e}")

@dp.message(ReviewForm.class_name)
async def got_review_class(message: Message, state: FSMContext):
    try:
        await state.update_data(class_name=message.text)
        await state.set_state(ReviewForm.rating)
        await message.answer(
            "📌 **مرحله ۳ از ۴**\n\n"
            "⭐ لطفاً امتیاز خود را انتخاب کنید:",
            reply_markup=kb_ratings()
        )
    except Exception as e:
        log.error(f"خطا در got_review_class: {e}")

@dp.message(ReviewForm.comment)
async def got_review_comment(message: Message, state: FSMContext):
    try:
        await finalize_review(message, state, comment=message.text)
    except Exception as e:
        log.error(f"خطا در got_review_comment: {e}")

# ================= پیش‌نمایش =================
async def show_preview(event, state: FSMContext):
    data = await state.get_data()
    if isinstance(event, CallbackQuery):
        answer_func = event.message.edit_text
        answer_cb = event.answer
    else:
        answer_func = event.answer
        answer_cb = None

    preview_text = (
        header("📋", "پیش‌نمایش درخواست شما") + "\n\n"
        "لطفاً اطلاعات زیر را بررسی کنید:\n\n"
        f"👤 **نام:** {data.get('name', '(وارد نشده)')}\n"
        f"🎓 **پایه:** {data.get('grade', '—')}\n"
        f"📚 **موضوع:** {data.get('subject', '—')}\n"
        f"📅 **روز:** {data.get('day', '—')}\n"
        f"⏰ **زمان:** {data.get('time', '—')}\n"
        f"📝 **توضیحات:** {data.get('description', '(بدون توضیح)')}\n\n"
        f"{sep()}\n"
        "اگر اطلاعات درست است، روی «تایید و ارسال نهایی» کلیک کنید."
    )
    try:
        await answer_func(preview_text, reply_markup=kb_preview_confirm())
        if answer_cb:
            await answer_cb("پیش‌نمایش آماده است")
    except Exception as e:
        log.error(f"خطا در نمایش پیش‌نمایش: {e}")

# ================= نهایی‌سازی درخواست =================
async def finalize_extra(event, state: FSMContext):
    data = await state.get_data()
    await state.clear()

    if isinstance(event, CallbackQuery):
        user = event.from_user
        answer_func = event.message.answer
        answer_cb = event.answer
    else:
        user = event.from_user
        answer_func = event.answer
        answer_cb = None

    username = user.username
    user_mention = f"@{username}" if username else "(ندارد)"

    tracking_id = gen_tracking_id()
    existing = load_json(DATA_FILE)
    existing_ids = {r.get("tracking_id") for r in existing}
    while tracking_id in existing_ids:
        tracking_id = gen_tracking_id()

    text = (
        "📬 **درخواست جدید کلاس فوق‌برنامه**\n" + sep() + "\n\n"
        f"🆔 **شماره پیگیری:** `{tracking_id}`\n"
        f"👤 نام: {data.get('name', '(وارد نشده)')}\n"
        f"🆔 شناسه عددی کاربر: `{user.id}`\n"
        f"🔗 نام کاربری: {user_mention}\n"
        f"🎓 پایه: {data.get('grade')}\n"
        f"📚 موضوع: {data.get('subject')}\n"
        f"📅 روز: {data.get('day')}\n"
        f"⏰ زمان: {data.get('time')}\n"
        f"📝 توضیحات: {data.get('description', '(بدون توضیح)')}"
    )

    sent_admin = False
    sent_group = False

    try:
        await event.bot.send_message(chat_id=ADMIN_ID, text=text)
        sent_admin = True
        log.info(f"✅ ارسال به مدیر موفق (ADMIN_ID={ADMIN_ID})")
    except Exception as e:
        log.error(f"❌ ارسال به مدیر ناموفق (ADMIN_ID={ADMIN_ID}): {e}")

    try:
        await event.bot.send_message(chat_id=GROUP_CHAT_ID, text=text)
        sent_group = True
        log.info(f"✅ ارسال به کانال موفق (GROUP_CHAT_ID={GROUP_CHAT_ID})")
    except Exception as e:
        log.error(f"❌ ارسال به کانال ناموفق (GROUP_CHAT_ID={GROUP_CHAT_ID}): {e}")

    try:
        existing.append({
            "tracking_id": tracking_id,
            "user_id": user.id,
            "username": username,
            "name": data.get("name", "(وارد نشده)"),
            "grade": data.get("grade"),
            "subject": data.get("subject"),
            "day": data.get("day"),
            "time": data.get("time"),
            "description": data.get("description", "(بدون توضیح)"),
            "timestamp": datetime.now().isoformat(),
            "status": "در حال بررسی"
        })
        save_json(DATA_FILE, existing)
        bump_stat("requests")
    except Exception as e:
        log.error(f"ذخیره در فایل ناموفق: {e}")

    confirm_text = (
        "✅ **درخواست شما با موفقیت ثبت شد.**\n" + sep() + "\n\n"
        f"🆔 **شماره پیگیری یکتای شما:**\n`{tracking_id}`\n\n"
        "📌 درخواست شما در حال **بررسی** توسط معاونت علمی و پژوهشی است.\n\n"
        "📋 **اطلاعات ثبت‌شده شما:**\n"
        f"👤 نام: {data.get('name', '(وارد نشده)')}\n"
        f"🎓 پایه: {data.get('grade')}\n"
        f"📚 موضوع: {data.get('subject')}\n"
        f"📅 روز: {data.get('day')}\n"
        f"⏰ زمان: {data.get('time')}\n"
        f"📝 توضیحات: {data.get('description', '(بدون توضیح)')}\n\n"
        f"{sep()}\n"
        f"🆔 برای **پیگیری** می‌توانید از طریق آیدی زیر اقدام کنید:\n@{SUPPORT_ID}\n\n"
        "🙏 **با تشکر فراوان از همراهی شما**"
    )

    if sent_admin or sent_group:
        try:
            await answer_func(confirm_text, reply_markup=kb_main())
            if answer_cb:
                await answer_cb("✅ درخواست ثبت شد")
        except Exception as e:
            log.error(f"ارسال پیام تأیید ناموفق: {e}")
    else:
        try:
            await answer_func(
                "⚠️ درخواست شما ثبت شد اما در ارسال با مشکل مواجه شدیم.\n"
                f"لطفاً مستقیماً با ما در ارتباط باشید:\n@{SUPPORT_ID}",
                reply_markup=kb_main()
            )
            if answer_cb:
                await answer_cb("⚠️ ارسال با مشکل مواجه شد")
        except Exception as e:
            log.error(f"ارسال پیام هشدار ناموفق: {e}")

# ================= نهایی‌سازی رضایت‌سنجی =================
async def finalize_review(event, state: FSMContext, comment: str):
    data = await state.get_data()
    await state.clear()

    if isinstance(event, CallbackQuery):
        user = event.from_user
        answer_func = event.message.answer
        answer_cb = event.answer
    else:
        user = event.from_user
        answer_func = event.answer
        answer_cb = None

    username = user.username
    user_mention = f"@{username}" if username else "(ندارد)"

    review_id = gen_review_id()

    text = (
        "⭐ **رضایت‌سنجی جدید کلاس**\n" + sep() + "\n\n"
        f"🆔 **شماره رضایت‌سنجی:** `{review_id}`\n"
        f"👤 کاربر: {user_mention}\n"
        f"🆔 شناسه عددی: `{user.id}`\n"
        f"🎓 پایه: {data.get('grade')}\n"
        f"📚 کلاس: {data.get('class_name')}\n"
        f"⭐ امتیاز: **{data.get('rating')} از ۵**\n"
        f"📝 نظر/انتقاد: {comment}"
    )

    sent_admin = False
    sent_group = False

    try:
        await event.bot.send_message(chat_id=ADMIN_ID, text=text)
        sent_admin = True
        log.info(f"✅ رضایت‌سنجی به مدیر ارسال شد ({ADMIN_ID})")
    except Exception as e:
        log.error(f"❌ ارسال رضایت‌سنجی به مدیر ناموفق ({ADMIN_ID}): {e}")

    try:
        await event.bot.send_message(chat_id=GROUP_CHAT_ID, text=text)
        sent_group = True
        log.info(f"✅ رضایت‌سنجی به کانال ارسال شد ({GROUP_CHAT_ID})")
    except Exception as e:
        log.error(f"❌ ارسال رضایت‌سنجی به کانال ناموفق ({GROUP_CHAT_ID}): {e}")

    try:
        reviews = load_json(REVIEW_FILE)
        reviews.append({
            "review_id": review_id,
            "user_id": user.id,
            "username": username,
            "grade": data.get("grade"),
            "class_name": data.get("class_name"),
            "rating": data.get("rating"),
            "comment": comment,
            "timestamp": datetime.now().isoformat()
        })
        save_json(REVIEW_FILE, reviews)
        bump_stat("reviews")
    except Exception as e:
        log.error(f"ذخیره رضایت‌سنجی ناموفق: {e}")

    confirm_text = (
        "✅ **رضایت‌سنجی شما با موفقیت ثبت شد.**\n" + sep() + "\n\n"
        f"🆔 **شماره رضایت‌سنجی:** `{review_id}`\n\n"
        "📋 **اطلاعات ثبت‌شده:**\n"
        f"🎓 پایه: {data.get('grade')}\n"
        f"📚 کلاس: {data.get('class_name')}\n"
        f"⭐ امتیاز: {data.get('rating')} از ۵\n"
        f"📝 نظر: {comment}\n\n"
        "🙏 **از اینکه در بهبود کیفیت کلاس‌ها به ما کمک کردید، صمیمانه سپاسگزاریم.**"
    )

    if sent_admin or sent_group:
        try:
            await answer_func(confirm_text, reply_markup=kb_main())
            if answer_cb:
                await answer_cb("✅ رضایت‌سنجی ثبت شد")
        except Exception as e:
            log.error(f"ارسال پیام تأیید رضایت‌سنجی ناموفق: {e}")
    else:
        try:
            await answer_func(
                "⚠️ رضایت‌سنجی شما ثبت شد اما در ارسال با مشکل مواجه شدیم.\n"
                f"لطفاً مستقیماً با ما در ارتباط باشید:\n@{SUPPORT_ID}",
                reply_markup=kb_main()
            )
            if answer_cb:
                await answer_cb("⚠️ ارسال با مشکل مواجه شد")
        except Exception as e:
            log.error(f"ارسال پیام هشدار رضایت‌سنجی ناموفق: {e}")

# ================= Keep-Alive =================
class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.end_headers()
        self.wfile.write(b"OK - Bot is alive forever (free)")

    def do_HEAD(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.end_headers()

    def log_message(self, fmt, *args):
        pass
def run_health_server():
    try:
        server = HTTPServer(("0.0.0.0", PORT), HealthHandler)
        log.info(f"🌐 Health server on port {PORT}")
        server.serve_forever()
    except Exception as e:
        log.error(f"Health server error: {e}")

def start_health_thread():
    t = threading.Thread(target=run_health_server, daemon=True)
    t.start()

# ================= اجرای مقاوم =================
async def bot_runner():
    while True:
        try:
            bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN))
            log.info(f"🚀 ربات نسخه {BOT_VERSION} روشن شد.")
            try:
                await bot.send_message(
                    chat_id=ADMIN_ID,
                    text=f"🟢 ربات روشن شد — نسخه {BOT_VERSION}\n⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                )
            except Exception as e:
                log.warning(f"heartbeat اولیه ارسال نشد: {e}")

            await dp.start_polling(bot)
        except Exception as e:
            log.error(f"💥 قطع شد: {e} — تلاش مجدد در ۱۰ ثانیه...")
            await asyncio.sleep(10)
        else:
            log.warning("⏹ polling متوقف شد — تلاش مجدد...")
            await asyncio.sleep(5)

async def heartbeat_loop():
    while True:
        await asyncio.sleep(1800)
        try:
            stats = load_json(STATS_FILE, default={})
            text = (
                "💚 **Heartbeat**\n" + sep() + "\n\n"
                f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
                f"📊 استارت‌ها: {stats.get('starts', 0)}\n"
                f"📬 درخواست‌ها: {stats.get('requests', 0)}\n"
                f"⭐ نظرات: {stats.get('reviews', 0)}\n"
                f"🎮 بازدید بازی‌ها: {stats.get('games_menu', 0)}\n"
                "🟢 وضعیت: فعال"
            )
            _b = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN))
            await _b.send_message(chat_id=ADMIN_ID, text=text)
        except Exception as e:
            log.warning(f"heartbeat ارسال نشد: {e}")

async def main():
    log.info("🔧 در حال راه‌اندازی...")
    start_health_thread()
    asyncio.create_task(heartbeat_loop())
    await bot_runner()

if __name__ == "__main__":
    asyncio.run(main())
