import os
import json
import random
import html
from datetime import datetime, timedelta, timezone

from telegram import (
    Update,
    ChatPermissions,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)

from telegram.constants import ParseMode

from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)


# =========================================================
#                         الإعدادات
# =========================================================

TOKEN = os.getenv("8859579637:AAGOWlE3uVrtnwTAVxr46c8xGjbJOdEu5aA")

# آيدي المطور
DEVELOPER_ID = 8768074696

# رابط القناة
CHANNEL_URL = "https://t.me/nidaa1233"

# ملف قاعدة البيانات
DATABASE_FILE = "data.json"


# =========================================================
#                       نظام الرتب
# =========================================================

RANKS = {
    "مالك اساسي": 100,
    "مالك": 90,
    "مشرف": 80,
    "منشئ": 70,
    "مدير": 60,
    "ادمن": 50,
    "مميز": 10,
    "عضو": 0,
}

RANK_ORDER = [
    "مالك اساسي",
    "مالك",
    "مشرف",
    "منشئ",
    "مدير",
    "ادمن",
    "مميز",
]


# =========================================================
#                     قاعدة البيانات
# =========================================================

def default_database():

    return {
        "ranks": {},
        "warnings": {},
        "muted": {},
        "restricted": {},
        "banned": {},
        "developer": DEVELOPER_ID
    }


def load_database():

    if not os.path.exists(DATABASE_FILE):

        return default_database()

    try:

        with open(
            DATABASE_FILE,
            "r",
            encoding="utf-8"
        ) as file:

            data = json.load(file)

        return data

    except Exception:

        return default_database()


def save_database(data):

    try:

        with open(
            DATABASE_FILE,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                data,
                file,
                ensure_ascii=False,
                indent=4
            )

    except Exception as error:

        print("Database error:", error)


db = load_database()


# =========================================================
#                      أدوات المستخدم
# =========================================================

def mention(user):

    name = user.full_name or user.first_name or "مستخدم"

    name = html.escape(name)

    return (
        f'<a href="tg://user?id={user.id}">'
        f'{name}'
        f'</a>'
    )


def user_data(user):

    return {
        "id": user.id,
        "name": user.full_name or user.first_name,
        "username": user.username
    }


def user_mention_from_data(user):

    name = html.escape(
        user.get("name", "مستخدم")
    )

    user_id = user.get("id")

    return (
        f'<a href="tg://user?id={user_id}">'
        f'{name}'
        f'</a>'
    )


# =========================================================
#                    التحقق من أدمن تيليغرام
# =========================================================

async def telegram_admin(chat_id, user_id, context):

    try:

        member = await context.bot.get_chat_member(
            chat_id,
            user_id
        )

        return member.status in [
            "administrator",
            "creator",
            "owner"
        ]

    except Exception:

        return False


# =========================================================
#                       نظام الرتب
# =========================================================

def get_rank(chat_id, user_id):

    chat_id = str(chat_id)
    user_id = str(user_id)

    if chat_id not in db["ranks"]:

        return "عضو"

    return db["ranks"][chat_id].get(
        user_id,
        "عضو"
    )


def set_rank(chat_id, user, rank):

    chat_id = str(chat_id)

    if chat_id not in db["ranks"]:

        db["ranks"][chat_id] = {}

    db["ranks"][chat_id][str(user.id)] = rank

    save_database(db)


def remove_rank(chat_id, user_id):

    chat_id = str(chat_id)
    user_id = str(user_id)

    if chat_id in db["ranks"]:

        if user_id in db["ranks"][chat_id]:

            del db["ranks"][chat_id][user_id]

    save_database(db)


def rank_power(rank):

    return RANKS.get(
        rank,
        0
    )


async def can_manage(update, context, minimum_rank="ادمن"):

    chat = update.effective_chat
    user = update.effective_user

    if chat.type == "private":

        return user.id == DEVELOPER_ID

    # أدمن تيليغرام الحقيقي
    if await telegram_admin(
        chat.id,
        user.id,
        context
    ):

        return True

    # رتبة البوت الداخلية
    user_rank = get_rank(
        chat.id,
        user.id
    )

    return (
        rank_power(user_rank)
        >=
        rank_power(minimum_rank)
    )


# =========================================================
#                    إنشاء قاعدة المجموعة
# =========================================================

def ensure_chat(category, chat_id):

    chat_id = str(chat_id)

    if chat_id not in db[category]:

        db[category][chat_id] = {}


# =========================================================
#                       قائمة الأوامر
# =========================================================

async def commands_menu(update, context):

    keyboard = InlineKeyboardMarkup([

        [
            InlineKeyboardButton(
                "الاوامر الادمنية",
                callback_data="admin_commands"
            )
        ],

        [
            InlineKeyboardButton(
                "اوامر الاعضاء",
                callback_data="member_commands"
            )
        ],

    ])

    text = (
        "مرحبا عزيزي في قائمة الاوامر\n"
        "ـــــــــــــــــــــــــــــــــــــــــــــ\n"
        "اختر القائمة التي تريدها"
    )

    try:

        photos = await context.bot.get_user_profile_photos(
            DEVELOPER_ID,
            limit=1
        )

        if photos.total_count > 0:

            await update.message.reply_photo(
                photo=photos.photos[0][0].file_id,
                caption=text,
                reply_markup=keyboard
            )

        else:

            await update.message.reply_text(
                text,
                reply_markup=keyboard
            )

    except Exception:

        await update.message.reply_text(
            text,
            reply_markup=keyboard
        )


# =========================================================
#                  قائمة أوامر الأعضاء
# =========================================================

MEMBER_COMMANDS_TEXT = """
• أهلاً بك عزيزي

━━━━━━━━━━━━

• اسمي
• افتاري
• افتاراتي
• بايو
• رتبتي
• المطور
• المالك
• المشرفين
• الرابط
• السورس
• قناتي
• الاوامر

━━━━━━━━━━━━
"""


# =========================================================
#                قائمة الأوامر الإدارية
# =========================================================

ADMIN_COMMANDS_TEXT = """
• أهلاً بك عزيزي

- قائمة اوامر الادمنيه

━━━━━━━━━━━━

- اوامر الرفع والتنزيل :

• رفع مالك اساسي
• رفع مالك
• رفع مشرف
• رفع منشئ
• رفع مدير
• رفع ادمن
• رفع مميز

• تنزيل مالك اساسي
• تنزيل مالك
• تنزيل مشرف
• تنزيل منشئ
• تنزيل مدير
• تنزيل ادمن
• تنزيل مميز

• تنزيل الكل

━━━━━━━━━━━━

- اوامر المسح :

• مسح المحظورين
• مسح المكتومين
• مسح المقيدين
• مسح التحذيرات

• مسح + العدد
مثال:
مسح 10

• مسح بالرد

━━━━━━━━━━━━

- اوامر الإدارة :

• حظر
• الغاء الحظر
• طرد
• كتم
• الغاء الكتم
• تقييد
• فك التقييد
• تحذير

━━━━━━━━━━━━
"""


# =========================================================
#                    أمر المطور
# =========================================================

async def show_developer(update, context):

    try:

        developer = await context.bot.get_chat(
            DEVELOPER_ID
        )

        username = (
            f"@{developer.username}"
            if developer.username
            else "لا يوجد"
        )

        text = (
            "𝑩𝑶𝑻 𝑫𝑬𝑽  ••  𝕯 | 𝑴𝑨𝑹𝑻𝑬𝑵\n"
            "━━━━━━━━━━━━\n"
            f"الاسم : {html.escape(developer.full_name)}\n"
            f"اليوزر : {username}\n"
            f"الايدي : <code>{developer.id}</code>\n"
            f"التاغ : {mention(developer)}"
        )

        keyboard = InlineKeyboardMarkup([

            [
                InlineKeyboardButton(
                    "قناتي",
                    url=CHANNEL_URL
                )
            ]

        ])

        photos = await context.bot.get_user_profile_photos(
            DEVELOPER_ID,
            limit=1
        )

        if photos.total_count > 0:

            await update.message.reply_photo(
                photo=photos.photos[0][0].file_id,
                caption=text,
                parse_mode=ParseMode.HTML,
                reply_markup=keyboard
            )

        else:

            await update.message.reply_text(
                text,
                parse_mode=ParseMode.HTML,
                reply_markup=keyboard
            )

    except Exception as error:

        print(error)

        await update.message.reply_text(
            "تعذر جلب معلومات المطور."
        )


# =========================================================
#                         اسمي
# =========================================================

async def show_my_name(update, context):

    user = update.effective_user

    username = (
        f"@{user.username}"
        if user.username
        else "لا يوجد"
    )

    text = (
        f"اسمك : {user.full_name}\n"
        f"اليوزر : {username}\n"
        f"الايدي : <code>{user.id}</code>"
    )

    await update.message.reply_text(
        text,
        parse_mode=ParseMode.HTML
    )


# =========================================================
#                         رتبتي
# =========================================================

async def show_my_rank(update, context):

    chat_id = update.effective_chat.id
    user_id = update.effective_user.id

    rank = get_rank(
        chat_id,
        user_id
    )

    # إذا أدمن حقيقي في تيليغرام
    if await telegram_admin(
        chat_id,
        user_id,
        context
    ):

        telegram_status = "أدمن تيليغرام"

    else:

        telegram_status = None

    text = f"رتبتك في Martiin : {rank}"

    if telegram_status:

        text += (
            f"\nرتبتك في تيليغرام : "
            f"{telegram_status}"
        )

    await update.message.reply_text(
        text
    )


# =========================================================
#                        افتاري
# =========================================================

async def show_avatar(update, context):

    user = update.effective_user

    # إذا كان بالرد نجيب افتار الشخص
    if update.message.reply_to_message:

        user = update.message.reply_to_message.from_user

    try:

        photos = await context.bot.get_user_profile_photos(
            user.id,
            limit=1
        )

        if photos.total_count == 0:

            await update.message.reply_text(
                "هذا المستخدم ما عندوش صورة بروفايل متاحة."
            )

            return

        await update.message.reply_photo(
            photo=photos.photos[0][0].file_id,
            caption=f"افتار {mention(user)}",
            parse_mode=ParseMode.HTML
        )

    except Exception:

        await update.message.reply_text(
            "ماقدرتش نجيب صورة البروفايل."
        )


# =========================================================
#                       افتاراتي
# =========================================================

async def show_avatars(update, context):

    user = update.effective_user

    try:

        photos = await context.bot.get_user_profile_photos(
            user.id,
            limit=10
        )

        if photos.total_count == 0:

            await update.message.reply_text(
                "ما عندكش صور بروفايل متاحة."
            )

            return

        count = min(
            photos.total_count,
            10
        )

        await update.message.reply_text(
            f"عندك {photos.total_count} صورة بروفايل.\n"
            f"راح نعرض لك آخر {count} صور."
        )

        for photo_group in photos.photos:

            await update.message.reply_photo(
                photo=photo_group[-1].file_id
            )

    except Exception as error:

        print(error)

        await update.message.reply_text(
            "ماقدرتش نجيب الافتارات."
        )


# =========================================================
#                         بايو
# =========================================================

async def show_bio(update, context):

    user = update.effective_user

    if update.message.reply_to_message:

        user = update.message.reply_to_message.from_user

    try:

        chat = await context.bot.get_chat(
            user.id
        )

        bio = getattr(
            chat,
            "bio",
            None
        )

        if bio:

            text = (
                f"بايو {mention(user)}\n"
                "━━━━━━━━━━━━\n"
                f"{html.escape(bio)}"
            )

        else:

            text = (
                f"بايو {mention(user)}\n"
                "━━━━━━━━━━━━\n"
                "لا يوجد بايو متاح."
            )

        await update.message.reply_text(
            text,
            parse_mode=ParseMode.HTML
        )

    except Exception:

        await update.message.reply_text(
            "تعذر جلب البايو."
        )


# =========================================================
#                         المالك
# =========================================================

async def show_owner(update, context):

    if update.effective_chat.type == "private":

        await update.message.reply_text(
            "هذا الأمر خاص بالمجموعات."
        )

        return

    try:

        admins = await context.bot.get_chat_administrators(
            update.effective_chat.id
        )

        owner = None

        for admin in admins:

            if admin.status in [
                "creator",
                "owner"
            ]:

                owner = admin.user
                break

        if not owner:

            await update.message.reply_text(
                "تعذر العثور على المالك."
            )

            return

        username = (
            f"@{owner.username}"
            if owner.username
            else "لا يوجد"
        )

        text = (
            "مالك المجموعة\n"
            "━━━━━━━━━━━━\n"
            f"الاسم : {html.escape(owner.full_name)}\n"
            f"اليوزر : {username}\n"
            f"الايدي : <code>{owner.id}</code>\n"
            f"التاغ : {mention(owner)}"
        )

        photos = await context.bot.get_user_profile_photos(
            owner.id,
            limit=1
        )

        if photos.total_count > 0:

            await update.message.reply_photo(
                photo=photos.photos[0][0].file_id,
                caption=text,
                parse_mode=ParseMode.HTML
            )

        else:

            await update.message.reply_text(
                text,
                parse_mode=ParseMode.HTML
            )

    except Exception:

        await update.message.reply_text(
            "تعذر جلب معلومات المالك."
        )


# =========================================================
#                       المشرفين
# =========================================================

async def show_admins(update, context):

    if update.effective_chat.type == "private":

        await update.message.reply_text(
            "هذا الأمر خاص بالمجموعات."
        )

        return

    try:

        admins = await context.bot.get_chat_administrators(
            update.effective_chat.id
        )

        text = (
            "مشرفين المجموعة\n"
            "━━━━━━━━━━━━\n"
        )

        number = 0

        for admin in admins:

            number += 1

            text += (
                f"{number}. "
                f"{mention(admin.user)}\n"
            )

        await update.message.reply_text(
            text,
            parse_mode=ParseMode.HTML
        )

    except Exception:

        await update.message.reply_text(
            "تعذر جلب المشرفين."
        )


# =========================================================
#                         الرابط
# =========================================================

async def show_link(update, context):

    chat = update.effective_chat

    if chat.type == "private":

        await update.message.reply_text(
            "هذا الأمر خاص بالمجموعات."
        )

        return

    try:

        if chat.username:

            link = f"https://t.me/{chat.username}"

        else:

            invite = await context.bot.export_chat_invite_link(
                chat.id
            )

            link = invite

        await update.message.reply_text(
            f"رابط المجموعة:\n\n{link}"
        )

    except Exception:

        await update.message.reply_text(
            "البوت يحتاج صلاحية دعوة المستخدمين للحصول على الرابط."
        )


# =========================================================
#                         السورس
# =========================================================

async def show_source(update, context):

    keyboard = InlineKeyboardMarkup([

        [
            InlineKeyboardButton(
                "قناتي",
                url=CHANNEL_URL
            )
        ]

    ])

    await update.message.reply_text(
        "𝑾𝑬𝑳𝑪𝑶𝑴𝑬 𝑻𝑶 𝑴𝑨𝑹𝑻𝑬𝑵 🍃🎗🤍",
        reply_markup=keyboard
    )


# =========================================================
#                         قناتي
# =========================================================

async def show_channel(update, context):

    keyboard = InlineKeyboardMarkup([

        [
            InlineKeyboardButton(
                "دخول القناة",
                url=CHANNEL_URL
            )
        ]

    ])

    await update.message.reply_text(
        "هذه هي القناة الرسمية.",
        reply_markup=keyboard
    )


# =========================================================
#                       رفع رتبة
# =========================================================

async def promote_user(update, context, rank):

    if update.effective_chat.type == "private":

        await update.message.reply_text(
            "هذا الأمر خاص بالمجموعات."
        )

        return

    if not update.message.reply_to_message:

        await update.message.reply_text(
            "لازم ترد على رسالة العضو."
        )

        return

    user = update.effective_user
    target = update.message.reply_to_message.from_user
    chat_id = update.effective_chat.id

    allowed = await can_manage(
        update,
        context,
        "ادمن"
    )

    if not allowed:

        await update.message.reply_text(
            "ما عندكش صلاحية لاستعمال هذا الأمر."
        )

        return

    sender_rank = get_rank(
        chat_id,
        user.id
    )

    # المطور عنده كامل الصلاحيات
    if user.id != DEVELOPER_ID:

        # أدمن تيليغرام نعتبره بصلاحية كبيرة
        is_tg_admin = await telegram_admin(
            chat_id,
            user.id,
            context
        )

        if not is_tg_admin:

            # لا يمكن رفع شخص لرتبة أعلى منك
            if rank_power(rank) >= rank_power(sender_rank):

                await update.message.reply_text(
                    "ما تقدرش ترفع عضو لرتبة مساوية أو أعلى من رتبتك."
                )

                return

    set_rank(
        chat_id,
        target,
        rank
    )

    await update.message.reply_text(
        f"تم رفع {mention(target)} إلى {rank}",
        parse_mode=ParseMode.HTML
    )


# =========================================================
#                       تنزيل رتبة
# =========================================================

async def demote_user(update, context, rank):

    if not update.message.reply_to_message:

        await update.message.reply_text(
            "لازم ترد على رسالة العضو."
        )

        return

    if not await can_manage(
        update,
        context,
        "ادمن"
    ):

        await update.message.reply_text(
            "ما عندكش صلاحية."
        )

        return

    target = update.message.reply_to_message.from_user
    chat_id = update.effective_chat.id

    current_rank = get_rank(
        chat_id,
        target.id
    )

    if current_rank != rank:

        await update.message.reply_text(
            f"هذا العضو رتبته الحالية: {current_rank}"
        )

        return

    remove_rank(
        chat_id,
        target.id
    )

    await update.message.reply_text(
        f"تم تنزيل {mention(target)} من رتبة {rank}",
        parse_mode=ParseMode.HTML
    )


# =========================================================
#                       تنزيل الكل
# =========================================================

async def demote_all(update, context):

    if not await can_manage(
        update,
        context,
        "مالك"
    ):

        await update.message.reply_text(
            "هذا الأمر يحتاج رتبة مالك أو أعلى."
        )

        return

    if not update.message.reply_to_message:

        await update.message.reply_text(
            "لازم ترد على العضو."
        )

        return

    target = update.message.reply_to_message.from_user

    remove_rank(
        update.effective_chat.id,
        target.id
    )

    await update.message.reply_text(
        f"تم تنزيل جميع رتب {mention(target)}",
        parse_mode=ParseMode.HTML
    )


# =========================================================
#                           حظر
# =========================================================

async def ban_member(update, context):

    if not await can_manage(
        update,
        context,
        "ادمن"
    ):

        await update.message.reply_text(
            "ما عندكش صلاحية الحظر."
        )

        return

    if not update.message.reply_to_message:

        await update.message.reply_text(
            "رد على رسالة العضو."
        )

        return

    target = update.message.reply_to_message.from_user
    chat_id = update.effective_chat.id

    try:

        await context.bot.ban_chat_member(
            chat_id,
            target.id
        )

        ensure_chat(
            "banned",
            chat_id
        )

        db["banned"][str(chat_id)][str(target.id)] = user_data(
            target
        )

        save_database(db)

        await update.message.reply_text(
            f"تم حظر {mention(target)}",
            parse_mode=ParseMode.HTML
        )

    except Exception:

        await update.message.reply_text(
            "البوت يحتاج صلاحية حظر المستخدمين."
        )


# =========================================================
#                        الغاء الحظر
# =========================================================

async def unban_member(update, context):

    if not await can_manage(
        update,
        context,
        "ادمن"
    ):

        await update.message.reply_text(
            "ما عندكش صلاحية."
        )

        return

    if not update.message.reply_to_message:

        await update.message.reply_text(
            "رد على رسالة العضو."
        )

        return

    target = update.message.reply_to_message.from_user
    chat_id = update.effective_chat.id

    try:

        await context.bot.unban_chat_member(
            chat_id,
            target.id,
            only_if_banned=True
        )

        if str(chat_id) in db["banned"]:

            db["banned"][str(chat_id)].pop(
                str(target.id),
                None
            )

        save_database(db)

        await update.message.reply_text(
            f"تم الغاء حظر {mention(target)}",
            parse_mode=ParseMode.HTML
        )

    except Exception:

        await update.message.reply_text(
            "حدث خطأ أثناء الغاء الحظر."
        )


# =========================================================
#                           طرد
# =========================================================

async def kick_member(update, context):

    if not await can_manage(
        update,
        context,
        "ادمن"
    ):

        await update.message.reply_text(
            "ما عندكش صلاحية."
        )

        return

    if not update.message.reply_to_message:

        await update.message.reply_text(
            "رد على رسالة العضو."
        )

        return

    target = update.message.reply_to_message.from_user
    chat_id = update.effective_chat.id

    try:

        await context.bot.ban_chat_member(
            chat_id,
            target.id
        )

        await context.bot.unban_chat_member(
            chat_id,
            target.id
        )

        await update.message.reply_text(
            f"تم طرد {mention(target)}",
            parse_mode=ParseMode.HTML
        )

    except Exception:

        await update.message.reply_text(
            "البوت يحتاج صلاحية حظر المستخدمين."
        )


# =========================================================
#                           كتم
# =========================================================

async def mute_member(update, context):

    if not await can_manage(
        update,
        context,
        "ادمن"
    ):

        await update.message.reply_text(
            "ما عندكش صلاحية."
        )

        return

    if not update.message.reply_to_message:

        await update.message.reply_text(
            "رد على رسالة العضو."
        )

        return

    target = update.message.reply_to_message.from_user
    chat_id = update.effective_chat.id

    try:

        permissions = ChatPermissions(
            can_send_messages=False
        )

        await context.bot.restrict_chat_member(
            chat_id,
            target.id,
            permissions=permissions
        )

        ensure_chat(
            "muted",
            chat_id
        )

        db["muted"][str(chat_id)][str(target.id)] = user_data(
            target
        )

        save_database(db)

        await update.message.reply_text(
            f"تم كتم {mention(target)}",
            parse_mode=ParseMode.HTML
        )

    except Exception:

        await update.message.reply_text(
            "البوت يحتاج صلاحية تقييد الأعضاء."
        )


# =========================================================
#                       الغاء الكتم
# =========================================================

async def unmute_member(update, context):

    if not await can_manage(
        update,
        context,
        "ادمن"
    ):

        await update.message.reply_text(
            "ما عندكش صلاحية."
        )

        return

    if not update.message.reply_to_message:

        await update.message.reply_text(
            "رد على رسالة العضو."
        )

        return

    target = update.message.reply_to_message.from_user
    chat_id = update.effective_chat.id

    try:

        permissions = ChatPermissions(
            can_send_messages=True,
            can_send_audios=True,
            can_send_documents=True,
            can_send_photos=True,
            can_send_videos=True,
            can_send_video_notes=True,
            can_send_voice_notes=True,
            can_send_polls=True,
            can_send_other_messages=True,
            can_add_web_page_previews=True
        )

        await context.bot.restrict_chat_member(
            chat_id,
            target.id,
            permissions=permissions
        )

        if str(chat_id) in db["muted"]:

            db["muted"][str(chat_id)].pop(
                str(target.id),
                None
            )

        save_database(db)

        await update.message.reply_text(
            f"تم الغاء كتم {mention(target)}",
            parse_mode=ParseMode.HTML
        )

    except Exception:

        await update.message.reply_text(
            "حدث خطأ."
        )


# =========================================================
#                         تقييد
# =========================================================

async def restrict_member(update, context):

    if not await can_manage(
        update,
        context,
        "ادمن"
    ):

        await update.message.reply_text(
            "ما عندكش صلاحية."
        )

        return

    if not update.message.reply_to_message:

        await update.message.reply_text(
            "رد على رسالة العضو."
        )

        return

    target = update.message.reply_to_message.from_user
    chat_id = update.effective_chat.id

    try:

        permissions = ChatPermissions(
            can_send_messages=True,
            can_send_audios=False,
            can_send_documents=False,
            can_send_photos=False,
            can_send_videos=False,
            can_send_video_notes=False,
            can_send_voice_notes=False,
            can_send_polls=False,
            can_send_other_messages=False,
            can_add_web_page_previews=False
        )

        await context.bot.restrict_chat_member(
            chat_id,
            target.id,
            permissions=permissions
        )

        ensure_chat(
            "restricted",
            chat_id
        )

        db["restricted"][str(chat_id)][str(target.id)] = user_data(
            target
        )

        save_database(db)

        await update.message.reply_text(
            f"تم تقييد {mention(target)}",
            parse_mode=ParseMode.HTML
        )

    except Exception:

        await update.message.reply_text(
            "البوت يحتاج صلاحية تقييد الأعضاء."
        )


# =========================================================
#                       فك التقييد
# =========================================================

async def unrestrict_member(update, context):

    if not await can_manage(
        update,
        context,
        "ادمن"
    ):

        await update.message.reply_text(
            "ما عندكش صلاحية."
        )

        return

    if not update.message.reply_to_message:

        await update.message.reply_text(
            "رد على رسالة العضو."
        )

        return

    target = update.message.reply_to_message.from_user
    chat_id = update.effective_chat.id

    try:

        permissions = ChatPermissions(
            can_send_messages=True,
            can_send_audios=True,
            can_send_documents=True,
            can_send_photos=True,
            can_send_videos=True,
            can_send_video_notes=True,
            can_send_voice_notes=True,
            can_send_polls=True,
            can_send_other_messages=True,
            can_add_web_page_previews=True
        )

        await context.bot.restrict_chat_member(
            chat_id,
            target.id,
            permissions=permissions
        )

        if str(chat_id) in db["restricted"]:

            db["restricted"][str(chat_id)].pop(
                str(target.id),
                None
            )

        save_database(db)

        await update.message.reply_text(
            f"تم فك تقييد {mention(target)}",
            parse_mode=ParseMode.HTML
        )

    except Exception:

        await update.message.reply_text(
            "حدث خطأ أثناء فك التقييد."
        )


# =========================================================
#                         تحذير
# =========================================================

async def warn_member(update, context):

    if not await can_manage(
        update,
        context,
        "ادمن"
    ):

        await update.message.reply_text(
            "ما عندكش صلاحية."
        )

        return

    if not update.message.reply_to_message:

        await update.message.reply_text(
            "رد على رسالة العضو."
        )

        return

    target = update.message.reply_to_message.from_user
    chat_id = str(update.effective_chat.id)

    ensure_chat(
        "warnings",
        chat_id
    )

    user_id = str(target.id)

    if user_id not in db["warnings"][chat_id]:

        db["warnings"][chat_id][user_id] = {
            "user": user_data(target),
            "count": 0
        }

    db["warnings"][chat_id][user_id]["count"] += 1

    count = db["warnings"][chat_id][user_id]["count"]

    save_database(db)

    await update.message.reply_text(
        f"تم تحذير {mention(target)}\n"
        f"التحذيرات: {count}/3",
        parse_mode=ParseMode.HTML
    )


# =========================================================
#                    مسح المحظورين
# =========================================================

async def clear_banned(update, context):

    if not await can_manage(
        update,
        context,
        "مشرف"
    ):

        await update.message.reply_text(
            "ما عندكش صلاحية."
        )

        return

    chat_id = str(update.effective_chat.id)

    users = db["banned"].get(
        chat_id,
        {}
    )

    count = 0

    for user_id in list(users.keys()):

        try:

            await context.bot.unban_chat_member(
                update.effective_chat.id,
                int(user_id),
                only_if_banned=True
            )

            count += 1

        except Exception:

            pass

    db["banned"][chat_id] = {}

    save_database(db)

    await update.message.reply_text(
        f"تم مسح المحظورين وفك الحظر عن {count} عضو."
    )


# =========================================================
#                    مسح المكتومين
# =========================================================

async def clear_muted(update, context):

    if not await can_manage(
        update,
        context,
        "مشرف"
    ):

        await update.message.reply_text(
            "ما عندكش صلاحية."
        )

        return

    chat_id = str(update.effective_chat.id)

    users = db["muted"].get(
        chat_id,
        {}
    )

    permissions = ChatPermissions(
        can_send_messages=True,
        can_send_audios=True,
        can_send_documents=True,
        can_send_photos=True,
        can_send_videos=True,
        can_send_video_notes=True,
        can_send_voice_notes=True,
        can_send_polls=True,
        can_send_other_messages=True,
        can_add_web_page_previews=True
    )

    count = 0

    for user_id in list(users.keys()):

        try:

            await context.bot.restrict_chat_member(
                update.effective_chat.id,
                int(user_id),
                permissions=permissions
            )

            count += 1

        except Exception:

            pass

    db["muted"][chat_id] = {}

    save_database(db)

    await update.message.reply_text(
        f"تم مسح المكتومين وفك الكتم عن {count} عضو."
    )


# =========================================================
#                    مسح المقيدين
# =========================================================

async def clear_restricted(update, context):

    if not await can_manage(
        update,
        context,
        "مشرف"
    ):

        await update.message.reply_text(
            "ما عندكش صلاحية."
        )

        return

    chat_id = str(update.effective_chat.id)

    users = db["restricted"].get(
        chat_id,
        {}
    )

    permissions = ChatPermissions(
        can_send_messages=True,
        can_send_audios=True,
        can_send_documents=True,
        can_send_photos=True,
        can_send_videos=True,
        can_send_video_notes=True,
        can_send_voice_notes=True,
        can_send_polls=True,
        can_send_other_messages=True,
        can_add_web_page_previews=True
    )

    count = 0

    for user_id in list(users.keys()):

        try:

            await context.bot.restrict_chat_member(
                update.effective_chat.id,
                int(user_id),
                permissions=permissions
            )

            count += 1

        except Exception:

            pass

    db["restricted"][chat_id] = {}

    save_database(db)

    await update.message.reply_text(
        f"تم مسح المقيدين وفك القيود عن {count} عضو."
    )


# =========================================================
#                    مسح التحذيرات
# =========================================================

async def clear_warnings(update, context):

    if not await can_manage(
        update,
        context,
        "ادمن"
    ):

        await update.message.reply_text(
            "ما عندكش صلاحية."
        )

        return

    chat_id = str(update.effective_chat.id)

    db["warnings"][chat_id] = {}

    save_database(db)

    await update.message.reply_text(
        "تم مسح جميع التحذيرات."
    )


# =========================================================
#                     مسح عدد رسائل
# =========================================================

async def delete_messages(update, context, number):

    if not await can_manage(
        update,
        context,
        "ادمن"
    ):

        await update.message.reply_text(
            "ما عندكش صلاحية."
        )

        return

    if number < 1:

        return

    # حد للحماية
    number = min(number, 100)

    chat_id = update.effective_chat.id
    message_id = update.message.message_id

    deleted = 0

    for i in range(number):

        try:

            await context.bot.delete_message(
                chat_id,
                message_id - i
            )

            deleted += 1

        except Exception:

            pass


# =========================================================
#                       مسح بالرد
# =========================================================

async def delete_reply(update, context):

    if not await can_manage(
        update,
        context,
        "ادمن"
    ):

        await update.message.reply_text(
            "ما عندكش صلاحية."
        )

        return

    if not update.message.reply_to_message:

        await update.message.reply_text(
            "رد على الرسالة التي تريد حذفها."
        )

        return

    try:

        await update.message.reply_to_message.delete()

        await update.message.delete()

    except Exception:

        await update.message.reply_text(
            "البوت يحتاج صلاحية حذف الرسائل."
        )


# =========================================================
#                         الأزرار
# =========================================================

async def callback_handler(update, context):

    query = update.callback_query

    data = query.data

    chat_id = query.message.chat.id
    user_id = query.from_user.id

    if data == "member_commands":

        await query.answer()

        try:

            await query.edit_message_caption(
                caption=MEMBER_COMMANDS_TEXT,
                reply_markup=InlineKeyboardMarkup([

                    [
                        InlineKeyboardButton(
                            "رجوع",
                            callback_data="back"
                        )
                    ]

                ])
            )

        except Exception:

            await query.edit_message_text(
                MEMBER_COMMANDS_TEXT,
                reply_markup=InlineKeyboardMarkup([

                    [
                        InlineKeyboardButton(
                            "رجوع",
                            callback_data="back"
                        )
                    ]

                ])
            )

        return

    if data == "admin_commands":

        # داخل الغروب للأدمن فقط
        if query.message.chat.type != "private":

            allowed = await telegram_admin(
                chat_id,
                user_id,
                context
            )

            rank = get_rank(
                chat_id,
                user_id
            )

            if not allowed and rank_power(rank) < rank_power("ادمن"):

                await query.answer(
                    "هذه القائمة خاصة بالأدمنية فقط.",
                    show_alert=True
                )

                return

        await query.answer()

        try:

            await query.edit_message_caption(
                caption=ADMIN_COMMANDS_TEXT,
                reply_markup=InlineKeyboardMarkup([

                    [
                        InlineKeyboardButton(
                            "رجوع",
                            callback_data="back"
                        )
                    ]

                ])
            )

        except Exception:

            await query.edit_message_text(
                ADMIN_COMMANDS_TEXT,
                reply_markup=InlineKeyboardMarkup([

                    [
                        InlineKeyboardButton(
                            "رجوع",
                            callback_data="back"
                        )
                    ]

                ])
            )

        return

    if data == "back":

        keyboard = InlineKeyboardMarkup([

            [
                InlineKeyboardButton(
                    "الاوامر الادمنية",
                    callback_data="admin_commands"
                )
            ],

            [
                InlineKeyboardButton(
                    "اوامر الاعضاء",
                    callback_data="member_commands"
                )
            ]

        ])

        text = (
            "مرحبا عزيزي في قائمة الاوامر\n"
            "ـــــــــــــــــــــــــــــــــــــــــــــ\n"
            "اختر القائمة التي تريدها"
        )

        try:

            await query.edit_message_caption(
                caption=text,
                reply_markup=keyboard
            )

        except Exception:

            await query.edit_message_text(
                text,
                reply_markup=keyboard
            )


# =========================================================
#                       الردود العامة
# =========================================================

async def general_responses(update, context, text):

    lower = text.lower().strip()

    # مارتن
    if any(word in lower for word in [
        "مارتن",
        "martin",
        "martiin"
    ]):

        responses = [

            "عيون مارتن",
            "حبيبي 🤍",
            "تحت أمرك",
            "ني هنا يا لعزيز",
            "قول خويا",
            "نعم؟",
            "آمر يا الغالي",
            "مارتن معاك 🎗",
            "وش حاب؟",
            "تفضل نسمعلك",
            "هاني هنا 🤍",
        ]

        await update.message.reply_text(
            random.choice(responses)
        )

        return True

    # السلام
    if "سلام" in lower:

        responses = [

            "وعليكم السلام ورحمة الله وبركاته 🤍",
            "وعليكم السلام يا لعزيز",
            "أهلا وسهلا بيك 🤍",
            "وعليكم السلام خويا",
            "نورت المجموعة ✨",
        ]

        await update.message.reply_text(
            random.choice(responses)
        )

        return True

    # صباح الخير
    if "صباح الخير" in lower:

        await update.message.reply_text(
            random.choice([
                "صباح النور 🤍",
                "صباح الخير والبركة ✨",
                "نهارك مبروك",
                "صباحك جميل 🌝",
            ])
        )

        return True

    # مساء الخير
    if "مساء الخير" in lower:

        await update.message.reply_text(
            random.choice([
                "مساء النور 🤍",
                "مساء الخير والبركة",
                "مساءك جميل",
            ])
        )

        return True

    # باي
    if lower in [
        "باي",
        "bye",
        "باي باي"
    ]:

        await update.message.reply_text(
            random.choice([
                "وداعا يا حلو 🤍",
                "انتبه لنفسك",
                "في أمان الله",
                "نشوفك على خير",
                "باي يا لعزيز",
            ])
        )

        return True

    # تم
    if lower == "تم":

        await update.message.reply_text(
            random.choice([
                "تمت؟",
                "تمت بنجاح",
                "مليح",
                "تمام",
            ])
        )

        return True

    return False


# =========================================================
#                      معالج الرسائل
# =========================================================

async def handle_message(update, context):

    if not update.message:

        return

    if not update.message.text:

        return

    text = update.message.text.strip()
    lower = text.lower().strip()

    # =====================================================
    # الأوامر العامة
    # =====================================================

    if lower in [
        "الاوامر",
        "الأوامر",
        "اوامر",
        "أوامر"
    ]:

        await commands_menu(update, context)
        return

    if lower == "المطور":

        await show_developer(update, context)
        return

    if lower == "اسمي":

        await show_my_name(update, context)
        return

    if lower == "رتبتي":

        await show_my_rank(update, context)
        return

    if lower == "افتاري":

        await show_avatar(update, context)
        return

    if lower == "افتاراتي":

        await show_avatars(update, context)
        return

    if lower == "بايو":

        await show_bio(update, context)
        return

    if lower == "المالك":

        await show_owner(update, context)
        return

    if lower in [
        "المشرفين",
        "المشرف",
        "المشرفون"
    ]:

        await show_admins(update, context)
        return

    if lower == "الرابط":

        await show_link(update, context)
        return

    if lower == "السورس":

        await show_source(update, context)
        return

    if lower == "قناتي":

        await show_channel(update, context)
        return


    # =====================================================
    # أوامر الرفع
    # =====================================================

    promotions = {

        "رفع مالك اساسي": "مالك اساسي",
        "رفع مالك":
