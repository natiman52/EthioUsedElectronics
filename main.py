import json
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto, ReplyKeyboardRemove
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, ConversationHandler, filters
import re
from telegram.constants import ParseMode

from config import *
from database import init_db,fetchall_ids, get_user_info,update_user_status,save_user, update_status, get_status, save_item, get_user_full_name, update_item_field, get_user_location, get_final_item, mark_item_posted, fetch_user, get_bot_stats, set_user_status

user_data = {}
pending_rejections = {}


# --- NEW HELPER FUNCTION TO STORE PHOTO IN PRIVATE CHANNEL ---
async def store_photo_in_channel(context: ContextTypes.DEFAULT_TYPE, file_id: str) -> str:
    """
    Sends a photo to a private channel and returns the new, permanent file_id.
    
    You must define PRIVATE_STORAGE_CHANNEL_ID in config.py.
    The bot must be an administrator in this channel.
    """
    try:
        # Send the photo using its temporary file_id
        # We use a simple caption to help identify the stored photo in the channel logs
        msg = await context.bot.send_photo(
            chat_id=PRIVATE_STORAGE_CHANNEL_ID,
            photo=file_id,
            caption=f"Stored media for later use.",
            parse_mode=ParseMode.MARKDOWN
        )
        # The message object contains the new, permanent file_id
        return msg.photo[-1].file_id
    except Exception as e:
        print(f"Error storing photo in channel: {e}")
        return file_id

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    first_name = update.effective_user.first_name or "there"

    try:
        member = await context.bot.get_chat_member(required_channel, user_id)
        if member.status not in ["member", "creator", "administrator"]:
            raise Exception("Not joined")
    except Exception:
        join_button = InlineKeyboardButton("Join Channel", url=f"https://t.me/{required_channel[1:]}")
        joined_button = InlineKeyboardButton("Joined ✅", callback_data="check_join")
        keyboard = InlineKeyboardMarkup([[join_button], [joined_button]])
        await update.message.reply_text(f"👋 Welcome {first_name}!\n\nYou must join our channel to continue.\n\nChannel: {required_channel}", reply_markup=keyboard)
        return

    status = get_status(user_id)

    if status is None:
        kb = ReplyKeyboardMarkup([[KeyboardButton("Register")]], resize_keyboard=True)
        await update.message.reply_text(f"👋 Welcome {first_name}!\n\nYou need to register before using the bot.\n\nTo post on <b>Ethio Used Electronics</b>, please register first by submitting your National ID and the account number you'll use to receive payments.\n\nThis verification helps us keep the platform safe and prevent scams.", parse_mode=ParseMode.HTML, reply_markup=kb)
        return

    elif status == "pending":
        await update.message.reply_text("⌛ Your registration is *Pending* review by admin.", parse_mode="Markdown", reply_markup=ReplyKeyboardMarkup([[KeyboardButton("Check Status")]], resize_keyboard=True))

    elif status == "rejected":
        await update.message.reply_text("❌ Your registration was *Rejected*.\nPlease contact support or try again.", parse_mode="Markdown", reply_markup=ReplyKeyboardMarkup([[KeyboardButton("Register")]], resize_keyboard=True))

    elif status == "approved":
        kb = ReplyKeyboardMarkup([[KeyboardButton("Sell"), KeyboardButton("Buy")]], resize_keyboard=True)
        await update.message.reply_text(f"🎉 Welcome back, {first_name}!\nYou're already *approved*.\nChoose what you want to do:", parse_mode="Markdown", reply_markup=kb)

async def check_join(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id

    try:
        member = await context.bot.get_chat_member(required_channel, user_id)
        if member.status in ["member", "creator", "administrator"]:
            await query.answer("✅ You joined the channel!")
            first_name = query.from_user.first_name or "there"
            await context.bot.send_message(chat_id=user_id, text=f"👋 <b>Welcome {first_name}!</b>\n\n<b>You need to register before using the bot.</b>\n\nTo post on <b>Ethio Used Electronics</b>, please register first by submitting your <b>National ID</b> and the <b>account number</b> you'll use to receive payments.\n\nThis verification helps us keep the platform safe and prevent scams.", parse_mode=ParseMode.HTML, reply_markup=ReplyKeyboardMarkup([[KeyboardButton("Register")]], resize_keyboard=True))
            try:
                await query.message.delete()
            except Exception:
                pass
            return
    except Exception as e:
        print("Join check error:", e)

    await query.answer("❌ Still not joined")
    join_button = InlineKeyboardButton("Join Channel", url=f"https://t.me/{required_channel[1:]}")
    joined_button = InlineKeyboardButton("Joined ✅", callback_data="check_join")
    keyboard = InlineKeyboardMarkup([[join_button], [joined_button]])
    await query.edit_message_text("❌ You must join the channel first.", reply_markup=keyboard)

async def register(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📝 Please enter your full name:")
    return ASK_NAME

async def ask_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["full_name"] = update.message.text.strip()
    await update.message.reply_text("📞 Now send your phone number:")
    return ASK_PHONE

async def ask_bank(update: Update, context: ContextTypes.DEFAULT_TYPE):
    phone = update.message.text.strip()
    if not phone.isdigit() or len(phone) < 9:
        await update.message.reply_text("❌ Invalid phone number. Please send only digits.")
        return ASK_PHONE
    context.user_data["phone"] = phone
    await update.message.reply_text("🏦 Please enter your <b>bank account number</b>.\n\nExample: <code>1000XXXXXXXXX</code>", parse_mode=ParseMode.HTML)
    return ASK_BANK

async def ask_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    bank_acc = update.message.text.strip()
    if not bank_acc.isdigit() or len(bank_acc) < 5:
        await update.message.reply_text("❌ Invalid account number. Please send only digits.")
        return ASK_BANK
    context.user_data["bank_account"] = bank_acc
    await update.message.reply_text("📍 Please enter your <b>location</b> (e.g., Addis Ababa, Mekelle, etc.):", parse_mode=ParseMode.HTML)
    return ASK_LOCATION

async def ask_front_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    location = update.message.text.strip()
    if not location:
        await update.message.reply_text("❌ Please enter a valid location.")
        return ASK_LOCATION
    context.user_data["location"] = location
    await update.message.reply_text("🪪 Please upload the <b>front side</b> of your National ID.", parse_mode=ParseMode.HTML)
    return ASK_FRONT_ID

async def ask_back_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.photo:
        await update.message.reply_text("❌ Please send a photo of your ID (front side).")
        return ASK_FRONT_ID
    temp_file_id = update.message.photo[-1].file_id
    permanent_file_id = await store_photo_in_channel(context, temp_file_id)
    context.user_data["front_id"] = permanent_file_id
    await update.message.reply_text("📸 Now please upload the <b>back side</b> of your National ID.", parse_mode=ParseMode.HTML)
    return ASK_BACK_ID

async def confirm_registration(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.photo:
        await update.message.reply_text("❌ Please send a photo of your ID (back side).")
        return ASK_BACK_ID
    temp_file_id = update.message.photo[-1].file_id
    permanent_file_id = await store_photo_in_channel(context, temp_file_id)
    context.user_data["back_id"] = permanent_file_id
    full_name = context.user_data["full_name"]
    phone = context.user_data["phone"]
    bank = context.user_data["bank_account"]
    location = context.user_data["location"] 
    front_id = context.user_data["front_id"]
    back_id = context.user_data["back_id"]
    text = f"📋 <b>Please confirm your registration details:</b>\n\n👤 <b>Name:</b> {full_name}\n📞 <b>Phone:</b> {phone}\n🏦 <b>Bank Account:</b> {bank}\n\n📍 <b>Location:</b> {location}\n\n🪪 <b>Your ID Photos:</b>"
    buttons = [[InlineKeyboardButton("✅ Confirm", callback_data="final_confirm"), InlineKeyboardButton("❌ Edit", callback_data="final_edit")]]
    media = [InputMediaPhoto(front_id, caption=text, parse_mode=ParseMode.HTML), InputMediaPhoto(back_id)]
    await update.message.reply_media_group(media)
    await update.message.reply_text("If everything looks correct, please confirm or edit below:", reply_markup=InlineKeyboardMarkup(buttons))
    return CONFIRM_ALL

async def finalize_registration(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    username = query.from_user.username or "None"
    full_name = context.user_data["full_name"]
    phone = context.user_data["phone"]
    bank_account = context.user_data["bank_account"]
    location = context.user_data["location"]
    front_id = context.user_data["front_id"]
    back_id = context.user_data["back_id"]
    save_user(user_id, full_name, phone, username, front_id, back_id, bank_account, location)
    kb = ReplyKeyboardMarkup([[KeyboardButton("Check Status")]], resize_keyboard=True)
    await query.edit_message_text("✅ <b>Registration submitted successfully!</b>\n\nPlease wait while the admin reviews your details.\n\nYou can check your application status anytime by pressing the <b>Check Status</b> button below 👇", parse_mode=ParseMode.HTML)
    await context.bot.send_message(chat_id=user_id, text="👇 Tap below to check your registration status:", reply_markup=kb)
    try:
        text = f"📥 <b>New Registration Request</b>\n\n🆔 <b>User ID:</b> <code>{user_id}</code>\n👤 <b>Name:</b> {full_name}\n📞 <b>Phone:</b> {phone}\n🏦 <b>Bank Account:</b> {bank_account}\n📍 <b>Location:</b> {location}\n🔗 <b>Username:</b> @{username if username != 'None' else '—'}\n\n⏳ Status: <b>Pending</b>"
        buttons = InlineKeyboardMarkup([[InlineKeyboardButton("✅ Approve", callback_data=f"approve_{user_id}"), InlineKeyboardButton("❌ Reject", callback_data=f"reject_{user_id}")]])
        media = [InputMediaPhoto(front_id, caption=text, parse_mode=ParseMode.HTML), InputMediaPhoto(back_id)]
        await context.bot.send_media_group(chat_id=admin_id, media=media)
        await context.bot.send_message(chat_id=admin_id, text="⚙️ Choose an action for this user:", reply_markup=buttons)
    except Exception as e:
        print("Failed to notify admin:", e)
    context.user_data.clear()
    return ConversationHandler.END

async def edit_registration(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("📝 Let's start over.\nPlease enter your full name:")
    return ASK_NAME

async def check_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    status = get_status(user_id)
    if status is None:
        kb = ReplyKeyboardMarkup([[KeyboardButton("Register")]], resize_keyboard=True)
        await update.message.reply_text("⚠️ You haven't registered yet.\n\nPlease register to use the bot features.", reply_markup=kb)
        return
    if status == "pending":
        kb = ReplyKeyboardMarkup([[KeyboardButton("Check Status")]], resize_keyboard=True)
        await update.message.reply_text("⌛ Your registration is *Pending* review by admin.\n\nWe'll notify you once your registration is approved.", parse_mode="Markdown", reply_markup=kb)
    elif status == "approved":
        kb = ReplyKeyboardMarkup([[KeyboardButton("Sell"), KeyboardButton("Buy")]], resize_keyboard=True)
        await update.message.reply_text("✅ *Approved!* 🎉\n\nYour registration has been approved. You can now:\n• Sell items\n• Post buy requests\n\nChoose what you want to do:", parse_mode="Markdown", reply_markup=kb)
    elif status == "rejected":
        kb = ReplyKeyboardMarkup([[KeyboardButton("Register")]], resize_keyboard=True)
        await update.message.reply_text("❌ *Registration Rejected*\n\nYour registration was not approved. Please:\n• Contact support for more information\n• Or try registering again with correct information", parse_mode="Markdown", reply_markup=kb)



async def approve_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = int(query.data.split("_")[1])
    update_user_status(user_id, "approved")
    await query.edit_message_text(f"✅ User {user_id} has been <b>Approved</b>.", parse_mode=ParseMode.HTML)
    try:
        kb = ReplyKeyboardMarkup([[KeyboardButton("Sell"), KeyboardButton("Buy")]], resize_keyboard=True)
        await context.bot.send_message(chat_id=user_id, text="🎉 <b>Your registration has been approved!</b>\nYou can now use all bot features.", parse_mode=ParseMode.HTML, reply_markup=kb)
    except Exception:
        pass

async def reject_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    admin_id = query.from_user.id
    user_id = int(query.data.split("_")[1])
    pending_rejections[admin_id] = {"user_id": user_id}
    await query.edit_message_text(f"📝 Please type the <b>reason for rejecting</b> user <code>{user_id}</code>.", parse_mode=ParseMode.HTML)
    return ASK_REJECT_REASON

async def get_reject_reason(update: Update, context: ContextTypes.DEFAULT_TYPE):
    admin_id = update.effective_user.id
    reason = update.message.text.strip()
    if not reason:
        await update.message.reply_text("⚠️ Please write a reason for rejection.")
        return ASK_REJECT_REASON
    pending_rejections[admin_id]["reason"] = reason
    buttons = InlineKeyboardMarkup([[InlineKeyboardButton("✅ Send to User", callback_data="send_rejection"), InlineKeyboardButton("✏️ Rewrite", callback_data="rewrite_rejection")]])
    preview = f"❌ <b>Rejection Reason Preview</b>\n\n<i>{reason}</i>\n\nDo you want to send this reason to the user or rewrite it?"
    await update.message.reply_text(preview, parse_mode=ParseMode.HTML, reply_markup=buttons)
    return CONFIRM_REJECTION

async def handle_rejection_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    admin_id = query.from_user.id
    data = query.data
    await query.answer()
    if admin_id not in pending_rejections:
        await query.edit_message_text("⚠️ No pending rejection found.")
        return ConversationHandler.END
    user_id = pending_rejections[admin_id]["user_id"]
    reason = pending_rejections[admin_id].get("reason", "")
    if data == "rewrite_rejection":
        await query.edit_message_text("✏️ Please type the new rejection reason:")
        return ASK_REJECT_REASON
    elif data == "send_rejection":
        update_user_status(user_id, "rejected")
        await query.edit_message_text(f"✅ Rejection sent to user <code>{user_id}</code>.", parse_mode=ParseMode.HTML)
        try:
            await context.bot.send_message(chat_id=user_id, text=f"❌ <b>Your registration has been rejected.</b>\n\n<b>Reason:</b> {reason}\n\nPlease contact support or try again later.", parse_mode=ParseMode.HTML)
        except Exception as e:
            print(f"Could not send rejection message to user {user_id}: {e}")
        del pending_rejections[admin_id]
        return ConversationHandler.END

async def sell_entry(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    status = get_status(user_id)
    if status != "approved":
        await update.message.reply_text("❌ You must be approved to sell items.")
        return ConversationHandler.END
    if "sell" in context.user_data:
        del context.user_data["sell"]
    if "edit_fields" in context.user_data:
        del context.user_data["edit_fields"]  
    if "edit_field_name" in context.user_data:
        del context.user_data["edit_field_name"]
    kb = ReplyKeyboardMarkup(sell_categories, resize_keyboard=True)
    await update.message.reply_text("📦 What type of item do you want to sell?", reply_markup=kb)
    return SELL_CATEGORY

async def sell_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    category = update.message.text
    if category == "⬅️ Back":
        kb = ReplyKeyboardMarkup([[KeyboardButton("Sell"), KeyboardButton("Buy")]], resize_keyboard=True)
        await update.message.reply_text("⬅️ Back to main menu.", reply_markup=kb)
        return ConversationHandler.END
    valid_categories = [c for row in sell_categories for c in row if c != "⬅️ Back"]
    if category not in valid_categories:
        await update.message.reply_text("⚠️ Please choose a valid category.")
        return SELL_CATEGORY
    context.user_data["sell"] = {"category": category, "answers": {}, "photos": []}
    context.user_data["sell"]["q_index"] = 0
    cancel_kb = ReplyKeyboardMarkup([[KeyboardButton("Cancel")]], resize_keyboard=True)
    first_q = category_questions[category][0]
    await update.message.reply_text(f"📝 {first_q}", reply_markup=cancel_kb)
    return SELL_DETAILS

async def sell_details(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if "sell" not in context.user_data:
        await update.message.reply_text("❌ Session expired. Please start over by clicking Sell.")
        return ConversationHandler.END
    data = context.user_data["sell"]
    if update.message.text == "Cancel":
        if "sell" in context.user_data:
            del context.user_data["sell"]
        kb = ReplyKeyboardMarkup([[KeyboardButton("Sell"), KeyboardButton("Buy")]], resize_keyboard=True)
        await update.message.reply_text("❌ Cancelled. Returning to main menu.", reply_markup=kb)
        return ConversationHandler.END
    category = data["category"]
    q_index = data["q_index"]
    question_list = category_questions[category]
    answer_key = question_list[q_index]
    data["answers"][answer_key] = update.message.text
    q_index += 1
    data["q_index"] = q_index
    if q_index < len(question_list):
        next_q = question_list[q_index]
        await update.message.reply_text(f"📝 {next_q}")
        return SELL_DETAILS
    await update.message.reply_text("📸 Now send photos of the item (you can send up to 5 photos). Send them one by one.", parse_mode="Markdown")
    return SELL_PHOTOS

async def sell_photos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = context.user_data["sell"]
    if update.message.text and update.message.text.lower() == "cancel":
        kb = ReplyKeyboardMarkup([[KeyboardButton("Sell"), KeyboardButton("Buy")]], resize_keyboard=True)
        await update.message.reply_text("❌ Cancelled. Returning to main menu.", reply_markup=kb)
        return ConversationHandler.END
    if not update.message.photo:
        await update.message.reply_text("📸 Please send a photo of the item.")
        return SELL_PHOTOS
    temp_file_id = update.message.photo[-1].file_id
    permanent_file_id = await store_photo_in_channel(context, temp_file_id)
    photos = data.get("photos", [])
    photos.append(permanent_file_id)
    data["photos"] = photos
    if len(photos) >= MAX_PHOTOS:
        await update.message.reply_text("⚠️ You've reached the maximum of 5 photos.")
        return await preview_post(update, context)
    kb = ReplyKeyboardMarkup([[KeyboardButton("Add another photo")], [KeyboardButton("Done"), KeyboardButton("Cancel")]], resize_keyboard=True)
    await update.message.reply_text("✅ Photo added.\nDo you want to add another?", reply_markup=kb)
    return SELL_PHOTOS

async def handle_photo_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.lower()
    if text == "add another photo":
        await update.message.reply_text("📸 Send the next photo:")
        return SELL_PHOTOS
    elif text == "done":
        data = context.user_data.get("sell", {})
        if not data.get("photos"):
            await update.message.reply_text("❗ You haven't added any photos yet.")
            return SELL_PHOTOS
        return await preview_post(update, context)
    elif text == "cancel":
        kb = ReplyKeyboardMarkup([[KeyboardButton("Sell"), KeyboardButton("Buy")]], resize_keyboard=True)
        await update.message.reply_text("❌ Cancelled. Returning to main menu.", reply_markup=kb)
        return ConversationHandler.END
    else:
        await update.message.reply_text("❗ Please choose a valid option.")
        return SELL_PHOTOS

async def preview_post(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = context.user_data["sell"]
    category = data["category"]
    answers = data["answers"]
    photos = data["photos"]
    user_id = update.effective_user.id
    if not photos:
        await update.message.reply_text("❗ You must send at least one photo.")
        return SELL_PHOTOS
    await update.message.reply_text("🖼 Generating preview...", reply_markup=ReplyKeyboardRemove())
    seller_name = get_user_full_name(user_id)
    seller_location = get_user_location(user_id)
    brand_model = answers.get('Brand & Model:', 'N/A')
    price = answers.get('Price (ETB):', 'N/A')
    caption = f"<b>{brand_model} | {price} BR</b>\n\n"
    caption += f"Device Type: <b>{category}</b>\n"
    display_mapping = SELL_DISPLAY_MAPPING.get(category, {})
    for question, answer in answers.items():
        if question == 'Price (ETB):' or question == 'Contact (Phone/Telegram):':
            continue
        display_name = display_mapping.get(question, question.replace(':', ''))
        caption += f"{display_name}: <b>{answer}</b>\n"
    price_value = answers.get('Price (ETB):', 'N/A')
    caption += f"Price: <b>{price_value} birr</b>\n"
    caption += f"Seller Name: <b>{seller_name}</b>\n"
    caption += f"Location: <b>{seller_location}</b>\n"
    contact = answers.get('Contact (Phone/Telegram):', 'N/A')
    caption += f"Contact: <b>{contact}</b>\n"
    caption += "\n@ethiousedelectronics"
    media_group = []
    for i, photo_id in enumerate(photos):
        if i == 0:
            media_group.append(InputMediaPhoto(media=photo_id, caption=caption, parse_mode=ParseMode.HTML))
        else:
            media_group.append(InputMediaPhoto(media=photo_id))
    await context.bot.send_media_group(chat_id=update.effective_chat.id, media=media_group)
    buttons = [[InlineKeyboardButton("✅ Post", callback_data="post_item"), InlineKeyboardButton("✏️ Edit", callback_data="edit_item"), InlineKeyboardButton("❌ Cancel", callback_data="cancel_item")]]
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Do you want to post this item?", reply_markup=InlineKeyboardMarkup(buttons))
    return SELL_CONFIRM

async def user_review_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    data = context.user_data.get("sell")
    if query.data == "cancel_item":
        try:
            await query.edit_message_text("❌ Your item submission has been cancelled.")
        except Exception:
            pass
        kb = ReplyKeyboardMarkup([[KeyboardButton("Sell"), KeyboardButton("Buy")]], resize_keyboard=True)
        await context.bot.send_message(chat_id=user_id, text="✅ Cancelled. You are back at the main menu.", reply_markup=kb)
        if "sell" in context.user_data:
            del context.user_data["sell"]
        return ConversationHandler.END
    elif query.data == "edit_item":
        if not data:
            await query.answer("⚠️ No active item to edit.")
            return SELL_CONFIRM
        category = data["category"]
        fields = list(data["answers"].keys())
        buttons = [[InlineKeyboardButton(f, callback_data=f"user_edit_{i}")] for i, f in enumerate(fields)]
        await query.edit_message_text(f"✏️ Choose a field to edit in *{category}*:", reply_markup=InlineKeyboardMarkup(buttons), parse_mode="Markdown")
        context.user_data["edit_fields"] = fields
        return EDIT_FIELD_SELECT
    elif query.data == "post_item":
        if not data:
            await query.answer("⚠️ No active item to post.")
            return SELL_CONFIRM
        await query.edit_message_text("⏳ Sending to admin for approval...")
        await send_to_admin(update, context, data)
        if "sell" in context.user_data:
            del context.user_data["sell"]
        if "edit_fields" in context.user_data:
            del context.user_data["edit_fields"]
        if "edit_field_name" in context.user_data:
            del context.user_data["edit_field_name"]
        kb = ReplyKeyboardMarkup([[KeyboardButton("Sell"), KeyboardButton("Buy")]], resize_keyboard=True)
        await context.bot.send_message(user_id, "✅ Your item has been sent to admin for approval.\nYou're now back at the main menu.", reply_markup=kb)
        return ConversationHandler.END

async def start_user_edit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = context.user_data.get("sell")
    if not data:
        await query.edit_message_text("⚠️ No active item to edit.")
        return ConversationHandler.END
    category = data["category"]
    fields = list(data["answers"].keys())
    buttons = [[InlineKeyboardButton(f, callback_data=f"user_edit_{i}")] for i, f in enumerate(fields)]
    await query.edit_message_text("✏️ Choose the field to edit:", reply_markup=InlineKeyboardMarkup(buttons))
    context.user_data["edit_fields"] = fields
    return EDIT_FIELD_SELECT

async def user_edit_field_select(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    index = int(query.data.split("_")[-1])
    field = context.user_data["edit_fields"][index]
    context.user_data["edit_field_name"] = field
    await query.edit_message_text(f"✍️ Send new value for *{field}*", parse_mode="Markdown")
    return EDIT_FIELD_VALUE

async def user_edit_field_value(update: Update, context: ContextTypes.DEFAULT_TYPE):
    new_value = update.message.text
    field = context.user_data.get("edit_field_name")
    data = context.user_data.get("sell")
    if not data or not field:
        await update.message.reply_text("⚠️ No active item to update. Please start over.")
        return ConversationHandler.END
    data["answers"][field] = new_value
    await update.message.reply_text("✅ Field updated successfully.")
    if "edit_fields" in context.user_data:
        del context.user_data["edit_fields"]
    if "edit_field_name" in context.user_data:
        del context.user_data["edit_field_name"]
    return await preview_post(update, context)

async def send_to_admin(update: Update, context: ContextTypes.DEFAULT_TYPE, data):
    user_id = update.effective_user.id
    username = update.effective_user.username or "N/A"
    category = data["category"]
    answers = data["answers"]
    photos = data["photos"]
    item_id = save_item(user_id, category, answers, photos)
    print(f"Sending item_id={item_id} to admin")
    seller_name = get_user_full_name(user_id)
    brand_model = answers.get('Brand & Model:', 'N/A')
    price = answers.get('Price (ETB):', 'N/A')
    caption = f"<b>📦 New Item Submission</b>\n\n<b>{brand_model} | {price} BR</b>\n\n"
    caption += f"Device Type: <b>{category}</b>\n"
    display_mapping = SELL_DISPLAY_MAPPING.get(category, {})
    for question, answer in answers.items():
        if question == 'Price (ETB):' or question == 'Contact (Phone/Telegram):':
            continue
        display_name = display_mapping.get(question, question.replace(':', ''))
        caption += f"{display_name}: <b>{answer}</b>\n"
    price_value = answers.get('Price (ETB):', 'N/A')
    caption += f"Price: <b>{price_value} birr</b>\n"
    caption += f"Seller Name: <b>{seller_name}</b>\n"
    contact = answers.get('Contact (Phone/Telegram):', 'N/A')
    caption += f"Contact: <b>{contact}</b>\n"
    caption += f"\n@ethiousedelectronics"
    media_group = [InputMediaPhoto(media=photos[0], caption=caption, parse_mode=ParseMode.HTML)]
    for photo_id in photos[1:]:
        media_group.append(InputMediaPhoto(media=photo_id))
    await context.bot.send_media_group(chat_id=admin_id, media=media_group)
    buttons = [[InlineKeyboardButton("✅ Approve", callback_data=f"admin_post_{item_id}"), InlineKeyboardButton("✏️ Edit", callback_data=f"admin_edit_{item_id}"), InlineKeyboardButton("❌ Cancel", callback_data=f"admin_cancel_{item_id}")]]
    markup = InlineKeyboardMarkup(buttons)
    await context.bot.send_message(chat_id=admin_id, text=f"🧐 <b>Admin — choose an action for item ID {item_id}</b>", parse_mode=ParseMode.HTML, reply_markup=markup)

async def admin_review_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    parts = query.data.split("_")
    action = parts[1]
    item_id = int(parts[2])
    if query.from_user.id != admin_id:
        await query.answer("❌ Only admin can perform this action.")
        return
    item = get_final_item(item_id)
    if not item:
        await query.edit_message_text("⚠️ Could not find item data.")
        return
    category = item["category"]
    answers = item["answers"]
    photos = item["photos"]
    if action == "post":
        if category.startswith("Buy Request: "):
            clean_category = category.replace("Buy Request: ", "")
            budget = answers.get("Budget (ETB):", "N/A")
            caption = f"<b>Looking to Buy {clean_category} | Budget: {budget}</b>\n\n"
            display_mapping = BUY_DISPLAY_MAPPING.get(clean_category, {})
            for question, answer in answers.items():
                if question == "Budget (ETB):":
                    continue
                display_name = display_mapping.get(question, question.replace(':', ''))
                caption += f"{display_name}: <b>{answer}</b>\n"
            caption += "\n@ethiousedelectronics"
            photo_path = BUY_CATEGORY_PHOTOS.get(clean_category, "photos/other.jpg")
            try:
                with open(photo_path, 'rb') as photo:
                    await context.bot.send_photo(chat_id=required_channel, photo=photo, caption=caption, parse_mode=ParseMode.HTML)
            except FileNotFoundError:
                await context.bot.send_message(chat_id=required_channel, text=caption, parse_mode=ParseMode.HTML)
        else:
            seller_name = get_user_full_name(item["user_id"])
            brand_model = answers.get('Brand & Model:', 'N/A')
            price = answers.get('Price (ETB):', 'N/A')
            caption = f"<b>{brand_model} | {price} BR</b>\n\n"
            caption += f"Device Type: <b>{category}</b>\n"
            display_mapping = SELL_DISPLAY_MAPPING.get(category, {})
            for question, answer in answers.items():
                if question == 'Price (ETB):' or question == 'Contact (Phone/Telegram):':
                    continue
                display_name = display_mapping.get(question, question.replace(':', ''))
                caption += f"{display_name}: <b>{answer}</b>\n"
            price_value = answers.get('Price (ETB):', 'N/A')
            caption += f"Price: <b>{price_value} birr</b>\n"
            caption += f"Seller Name: <b>{seller_name}</b>\n"
            contact = answers.get('Contact (Phone/Telegram):', 'N/A')
            caption += f"Contact: <b>{contact}</b>\n"
            caption += "\n@ethiousedelectronics"
            media_group = [InputMediaPhoto(media=photos[0], caption=caption, parse_mode=ParseMode.HTML)]
            for photo_id in photos[1:]:
                media_group.append(InputMediaPhoto(media=photo_id))
            await context.bot.send_media_group(chat_id=required_channel, media=media_group)
        mark_item_posted(item_id)
        await query.edit_message_text("✅ Posted to channel successfully.")
        return
    elif action == "edit":
        context.user_data["admin_edit_item_id"] = item_id
        context.user_data["admin_edit_item_data"] = item
        fields = list(item["answers"].keys())
        kb = ReplyKeyboardMarkup([fields[i:i + 2] for i in range(0, len(fields), 2)] + [["Cancel"]], resize_keyboard=True)
        await context.bot.send_message(chat_id=admin_id, text="✏️ Choose a field to edit:", reply_markup=kb)
        return ADMIN_EDIT_FIELD_SELECT
    elif action == "cancel":
        await query.edit_message_text("❌ Post cancelled by admin.")
        return

async def admin_edit_field_select(update: Update, context: ContextTypes.DEFAULT_TYPE):
    field = update.message.text
    if field == "Cancel":
        await update.message.reply_text("❌ Edit cancelled.", reply_markup=ReplyKeyboardRemove())
        return ConversationHandler.END
    item_id = context.user_data.get("admin_edit_item_id")
    if not item_id:
        await update.message.reply_text("⚠️ No active item to edit.")
        return ConversationHandler.END
    context.user_data["admin_edit_field"] = field
    await update.message.reply_text(f"✍️ Send new value for *{field}*:", parse_mode="Markdown", reply_markup=ReplyKeyboardRemove())
    return ADMIN_EDIT_FIELD_VALUE

async def admin_edit_field_value(update: Update, context: ContextTypes.DEFAULT_TYPE):
    new_value = update.message.text
    field = context.user_data.get("admin_edit_field")
    item_id = context.user_data.get("admin_edit_item_id")
    if not field or not item_id:
        await update.message.reply_text("⚠️ No active item to update.")
        return ConversationHandler.END
    update_item_field(item_id, field, new_value)
    await update.message.reply_text("✅ Field updated successfully!")
    item = get_final_item(item_id)
    if item:
        if item['category'].startswith("Buy Request: "):
            clean_category = item['category'].replace("Buy Request: ", "")
            budget = item["answers"].get("Budget (ETB):", "N/A")
            caption = f"<b>Looking to Buy {clean_category} | Budget: {budget}</b>\n\n"
            display_mapping = BUY_DISPLAY_MAPPING.get(clean_category, {})
            for question, answer in item["answers"].items():
                if question == "Budget (ETB):":
                    continue
                display_name = display_mapping.get(question, question.replace(':', ''))
                caption += f"{display_name}: <b>{answer}</b>\n"
            caption += f"\n📝 Updated Buy Request (ID: {item_id})"
            photo_path = BUY_CATEGORY_PHOTOS.get(clean_category, "photos/other.jpg")
            try:
                with open(photo_path, 'rb') as photo:
                    await context.bot.send_photo(chat_id=admin_id, photo=photo, caption=caption, parse_mode=ParseMode.HTML)
            except FileNotFoundError:
                await context.bot.send_message(chat_id=admin_id, text=caption, parse_mode=ParseMode.HTML)
        else:
            seller_name = get_user_full_name(item["user_id"])
            brand_model = item["answers"].get('Brand & Model:', 'N/A')
            price = item["answers"].get('Price (ETB):', 'N/A')
            caption = f"<b>{brand_model} | {price} BR</b>\n\n"
            caption += f"Device Type: <b>{item['category']}</b>\n"
            display_mapping = SELL_DISPLAY_MAPPING.get(item['category'], {})
            for question, answer in item["answers"].items():
                if question == 'Price (ETB):' or question == 'Contact (Phone/Telegram):':
                    continue
                display_name = display_mapping.get(question, question.replace(':', ''))
                caption += f"{display_name}: <b>{answer}</b>\n"
            price_value = item["answers"].get('Price (ETB):', 'N/A')
            caption += f"Price: <b>{price_value} birr</b>\n"
            caption += f"Seller Name: <b>{seller_name}</b>\n"
            contact = item["answers"].get('Contact (Phone/Telegram):', 'N/A')
            caption += f"Contact: <b>{contact}</b>\n"
            caption += f"\n📝 Updated Item (ID: {item_id})"
            media_group = [InputMediaPhoto(media=item["photos"][0], caption=caption, parse_mode=ParseMode.HTML)]
            for photo_id in item["photos"][1:]:
                media_group.append(InputMediaPhoto(media=photo_id))
            await context.bot.send_media_group(chat_id=admin_id, media=media_group)
        buttons = [[InlineKeyboardButton("✅ Approve", callback_data=f"admin_post_{item_id}"), InlineKeyboardButton("✏️ Edit", callback_data=f"admin_edit_{item_id}"), InlineKeyboardButton("❌ Cancel", callback_data=f"admin_cancel_{item_id}")]]
        markup = InlineKeyboardMarkup(buttons)
        await context.bot.send_message(chat_id=admin_id, text=f"🔄 Item updated! Choose an action for item ID {item_id}:", reply_markup=markup)
    if "admin_edit_item_id" in context.user_data:
        del context.user_data["admin_edit_item_id"]
    if "admin_edit_field" in context.user_data:
        del context.user_data["admin_edit_field"]
    if "admin_edit_item_data" in context.user_data:
        del context.user_data["admin_edit_item_data"]
    return ConversationHandler.END

async def buy_entry(update, context):
    user_id = update.effective_user.id
    status = get_status(user_id)
    if status != "approved":
        await update.message.reply_text("❌ You must be approved to buy items.")
        return ConversationHandler.END
    kb = ReplyKeyboardMarkup(buy_categories, resize_keyboard=True)
    await update.message.reply_text("🛒 What type of item do you want to buy?", reply_markup=kb)
    return BUY_CATEGORY

async def buy_category(update, context):
    category = update.message.text
    if category == "⬅️ Back":
        kb = ReplyKeyboardMarkup([[KeyboardButton("Sell"), KeyboardButton("Buy")]], resize_keyboard=True)
        await update.message.reply_text("⬅️ Back to main menu.", reply_markup=kb)
        return ConversationHandler.END
    if category not in buy_category_questions:
        await update.message.reply_text("⚠️ Please choose a valid category.")
        return BUY_CATEGORY
    context.user_data["buy_category"] = category
    context.user_data["buy_answers"] = {}
    context.user_data["buy_questions"] = buy_category_questions[category]
    context.user_data["buy_index"] = 0
    cancel_kb = ReplyKeyboardMarkup([[KeyboardButton("Cancel")]], resize_keyboard=True)
    first_q = buy_category_questions[category][0]
    await update.message.reply_text(f"📝 {first_q}", reply_markup=cancel_kb)
    return BUY_DETAILS

async def buy_details(update, context):
    if "buy_category" not in context.user_data:
        await update.message.reply_text("❌ Session expired. Please start over by clicking Buy.")
        return ConversationHandler.END
    data = context.user_data
    if update.message.text == "Cancel":
        if "buy_category" in context.user_data:
            del context.user_data["buy_category"]
        if "buy_answers" in context.user_data:
            del context.user_data["buy_answers"]
        if "buy_questions" in context.user_data:
            del context.user_data["buy_questions"]
        if "buy_index" in context.user_data:
            del context.user_data["buy_index"]
        kb = ReplyKeyboardMarkup([[KeyboardButton("Sell"), KeyboardButton("Buy")]], resize_keyboard=True)
        await update.message.reply_text("❌ Cancelled. Returning to main menu.", reply_markup=kb)
        return ConversationHandler.END
    category = data["buy_category"]
    questions = data["buy_questions"]
    q_index = data["buy_index"]
    answer_key = questions[q_index]
    data["buy_answers"][answer_key] = update.message.text
    q_index += 1
    data["buy_index"] = q_index
    if q_index < len(questions):
        next_q = questions[q_index]
        await update.message.reply_text(f"📝 {next_q}")
        return BUY_DETAILS
    return await preview_buy_post(update, context)

async def preview_buy_post(update, context):
    data = context.user_data
    category = data["buy_category"]
    answers = data["buy_answers"]
    user_id = update.effective_user.id
    buyer_location = get_user_location(user_id)
    budget = answers.get("Budget (ETB):", "N/A")
    caption = f"<b>Looking to Buy {category} | Budget: {budget}</b>\n\n"
    display_mapping = BUY_DISPLAY_MAPPING.get(category, {})
    for question, answer in answers.items():
        if question == "Budget (ETB):":
            continue
        display_name = display_mapping.get(question, question.replace(':', ''))
        caption += f"{display_name}: <b>{answer}</b>\n"
    caption += f"Location: <b>{buyer_location}</b>\n"
    caption += "\n@ethiousedelectronics"
    await update.message.reply_text("🖼 Generating preview...", reply_markup=ReplyKeyboardRemove())
    photo_path = BUY_CATEGORY_PHOTOS.get(category, "./photos/other.jpg")
    try:
        with open(photo_path, 'rb') as photo:
            await update.message.reply_photo(photo=photo, caption=caption, parse_mode=ParseMode.HTML)
    except FileNotFoundError:
        await update.message.reply_text(caption, parse_mode=ParseMode.HTML)
        await update.message.reply_text("📷 <b>Note: Category image not available</b>", parse_mode=ParseMode.HTML)
    buttons = [[InlineKeyboardButton("✅ Submit Buy Request", callback_data="confirm_buy"), InlineKeyboardButton("✏️ Edit", callback_data="edit_buy"), InlineKeyboardButton("❌ Cancel", callback_data="cancel_buy")]]
    await update.message.reply_text("Do you want to submit this buy request?", reply_markup=InlineKeyboardMarkup(buttons))
    return BUY_PREVIEW

async def user_review_buy_buttons(update, context):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    data = context.user_data
    if not data.get("buy_category"):
        await query.answer("⚠️ No active buy request.")
        return ConversationHandler.END
    if query.data == "confirm_buy":
        await query.edit_message_text("⏳ Sending your buy request to admin...")
        await send_buy_to_admin(update, context, data)
        if "buy_category" in context.user_data:
            del context.user_data["buy_category"]
        if "buy_answers" in context.user_data:
            del context.user_data["buy_answers"]
        if "buy_questions" in context.user_data:
            del context.user_data["buy_questions"]
        if "buy_index" in context.user_data:
            del context.user_data["buy_index"]
        kb = ReplyKeyboardMarkup([[KeyboardButton("Sell"), KeyboardButton("Buy")]], resize_keyboard=True)
        await context.bot.send_message(user_id, "✅ Your buy request has been sent to admin for approval.\nYou're now back at the main menu.", reply_markup=kb)
        return ConversationHandler.END
    elif query.data == "edit_buy":
        data = context.user_data
        if not data.get("buy_category"):
            await query.answer("⚠️ No active buy request.")
            return ConversationHandler.END
        category = data["buy_category"]
        questions = data["buy_questions"]
        buttons = [[InlineKeyboardButton(q, callback_data=f"buy_edit_{i}")] for i, q in enumerate(questions)]
        await query.edit_message_text(f"✏️ Choose a field to edit in *{category}*:", reply_markup=InlineKeyboardMarkup(buttons), parse_mode="Markdown")
        context.user_data["buy_edit_fields"] = questions
        return BUY_EDIT_FIELD_SELECT
    elif query.data == "cancel_buy":
        await query.edit_message_text("❌ Buy request cancelled.")
        if "buy_category" in context.user_data:
            del context.user_data["buy_category"]
        if "buy_answers" in context.user_data:
            del context.user_data["buy_answers"]
        if "buy_questions" in context.user_data:
            del context.user_data["buy_questions"]
        if "buy_index" in context.user_data:
            del context.user_data["buy_index"]
        kb = ReplyKeyboardMarkup([[KeyboardButton("Sell"), KeyboardButton("Buy")]], resize_keyboard=True)
        await context.bot.send_message(user_id, "🛒 You're back at the main menu.", reply_markup=kb)
        return ConversationHandler.END

async def send_buy_to_admin(update: Update, context: ContextTypes.DEFAULT_TYPE, data):
    user_id = update.effective_user.id
    username = update.effective_user.username or "N/A"
    category = data["buy_category"]
    answers = data["buy_answers"]
    item_id = save_item(user_id, f"Buy Request: {category}", answers, [])
    print(f"Sending buy request item_id={item_id} to admin")
    budget = answers.get("Budget (ETB):", "N/A")
    caption = f"<b>🛒 New Buy Request</b>\n\n<b>Looking to Buy {category} | Budget: {budget}</b>\n\n"
    display_mapping = BUY_DISPLAY_MAPPING.get(category, {})
    for question, answer in answers.items():
        if question == "Budget (ETB):":
            continue
        display_name = display_mapping.get(question, question.replace(':', ''))
        caption += f"{display_name}: <b>{answer}</b>\n"
    caption += f"\n@ethiousedelectronics"
    photo_path = BUY_CATEGORY_PHOTOS.get(category, "photos/other.jpg")
    try:
        with open(photo_path, 'rb') as photo:
            await context.bot.send_photo(chat_id=admin_id, photo=photo, caption=caption, parse_mode=ParseMode.HTML)
    except FileNotFoundError:
        await context.bot.send_message(chat_id=admin_id, text=caption, parse_mode=ParseMode.HTML)
    buttons = [[InlineKeyboardButton("✅ Approve", callback_data=f"admin_post_{item_id}"), InlineKeyboardButton("✏️ Edit", callback_data=f"admin_edit_{item_id}"), InlineKeyboardButton("❌ Cancel", callback_data=f"admin_cancel_{item_id}")]]
    markup = InlineKeyboardMarkup(buttons)
    await context.bot.send_message(chat_id=admin_id, text=f"🧐 <b>Admin — choose an action for buy request ID {item_id}</b>", parse_mode=ParseMode.HTML, reply_markup=markup)

async def buy_edit_field_select(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    index = int(query.data.split("_")[-1])
    field = context.user_data["buy_edit_fields"][index]
    context.user_data["buy_edit_field_name"] = field
    await query.edit_message_text(f"✍️ Send new value for *{field}*", parse_mode="Markdown")
    return BUY_EDIT_FIELD_VALUE

async def buy_edit_field_value(update: Update, context: ContextTypes.DEFAULT_TYPE):
    new_value = update.message.text
    field = context.user_data.get("buy_edit_field_name")
    data = context.user_data
    if not data.get("buy_category") or not field:
        await update.message.reply_text("⚠️ No active buy request to update. Please start over.")
        return ConversationHandler.END
    data["buy_answers"][field] = new_value
    await update.message.reply_text("✅ Field updated successfully.")
    if "buy_edit_fields" in context.user_data:
        del context.user_data["buy_edit_fields"]
    if "buy_edit_field_name" in context.user_data:
        del context.user_data["buy_edit_field_name"]
    return await preview_buy_post(update, context)

def is_admin(user_id):
    return user_id == admin_id

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != admin_id:
        await update.message.reply_text("❌ You are not authorized.")
        return
    text = "🛠 <b>Admin Panel</b>\n\nHere are the available admin commands:\n\n📊 /stats – View bot statistics\n👤 /user [user_id or @username] – View user info\n🚫 /ban [user_id or @username] – Ban user\n✅ /unban [user_id or @username] – Unban user\n📢 /broadcast – Send message or photo to all approved users\n\n💡 Only you (the admin) can use these commands."
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)

async def show_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ You are not authorized.")
        return
    stats = get_bot_stats()
    msg = f"📊 <b>Bot Statistics</b>\n\n👥 Total Users: <b>{stats['total_users']}</b>\n✅ Approved: <b>{stats['approved']}</b>\n⏳ Pending: <b>{stats['pending']}</b>\n🚫 Banned: <b>{stats['banned']}</b>\n\n📦 Total Posts: <b>{stats['total_items']}</b>\n📬 Posted to Channel: <b>{stats['posted']}</b>"
    await update.message.reply_text(msg, parse_mode=ParseMode.HTML)

async def user_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != admin_id:
        await update.message.reply_text("❌ You are not authorized.")
        return
    if len(context.args) < 1:
        await update.message.reply_text("Usage: /user <user_id or @username>")
        return
    identifier = context.args[0].strip()
    user_info = get_user_info(identifier,update)
    if(user_info):
        user_id, full_name, phone, username, front_id, back_id, status = user_info

        return
    text = f"👤 <b>User Information</b>\n\n🆔 <b>ID:</b> <code>{user_id}</code>\n👤 <b>Name:</b> {full_name}\n📞 <b>Phone:</b> {phone}\n🏦 <b>Bank Account:</b> {user[6] if len(user) > 6 else '—'}\n🔗 <b>Username:</b> @{username if username != 'None' else '—'}\n📋 <b>Status:</b> {status}\n📦 <b>Posts:</b> {posts}"
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)

async def ban_user_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ You are not authorized.")
        return
    if len(context.args) < 1:
        await update.message.reply_text("Usage: /ban <user_id|@username>")
        return
    identifier = context.args[0]
    set_user_status(identifier, "banned")
    await update.message.reply_text(f"🚫 User {identifier} has been banned.")

async def unban_user_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ You are not authorized.")
        return
    if len(context.args) < 1:
        await update.message.reply_text("Usage: /unban <user_id|@username>")
        return
    identifier = context.args[0]
    set_user_status(identifier, "approved")
    await update.message.reply_text(f"✅ User {identifier} has been unbanned.")

async def start_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != admin_id:
        await update.message.reply_text("❌ You are not authorized.")
        return ConversationHandler.END
    await update.message.reply_text("📢 Please send the message or photo (with caption) you want to broadcast to all approved users.")
    return BROADCAST_WAITING

async def handle_broadcast_preview(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != admin_id:
        await update.message.reply_text("❌ You are not authorized.")
        return ConversationHandler.END
    context.user_data["broadcast"] = {
        "text": update.message.text or update.message.caption or "",
        "photo": update.message.photo[-1].file_id if update.message.photo else None,
    }
    if update.message.photo:
        await update.message.reply_photo(photo=update.message.photo[-1].file_id, caption=f"{update.message.caption or ''}\n\n⚠️ Send this to all approved users?")
    else:
        await update.message.reply_text(f"{update.message.text}\n\n⚠️ Send this message to all approved users?")
    buttons = [[InlineKeyboardButton("✅ Confirm", callback_data="confirm_broadcast"), InlineKeyboardButton("❌ Cancel", callback_data="cancel_broadcast")]]
    await update.message.reply_text("Please confirm your broadcast choice:", reply_markup=InlineKeyboardMarkup(buttons))
    return BROADCAST_CONFIRM

async def handle_broadcast_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "cancel_broadcast":
        await query.edit_message_text("❌ Broadcast cancelled.")
        context.user_data.pop("broadcast", None)
        return ConversationHandler.END
    if query.data == "confirm_broadcast":
        broadcast_data = context.user_data.get("broadcast")
        if not broadcast_data:
            await query.edit_message_text("⚠️ No broadcast data found.")
            return ConversationHandler.END
        users = fetchall_ids()
        sent = 0
        for uid in users:
            try:
                if broadcast_data["photo"]:
                    await context.bot.send_photo(chat_id=uid, photo=broadcast_data["photo"], caption=broadcast_data["text"])
                else:
                    await context.bot.send_message(chat_id=uid, text=broadcast_data["text"])
                sent += 1
            except Exception:
                continue
        await query.edit_message_text(f"✅ Broadcast sent successfully to {sent} users.")
        context.user_data.pop("broadcast", None)
        return ConversationHandler.END

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    registration_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^Register$"), register)],
        states={
            ASK_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_phone)],
            ASK_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_bank)],
            ASK_BANK: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_location)],
            ASK_LOCATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_front_id)],
            ASK_FRONT_ID: [MessageHandler(filters.PHOTO, ask_back_id)],
            ASK_BACK_ID: [MessageHandler(filters.PHOTO, confirm_registration)],
            CONFIRM_ALL: [
                CallbackQueryHandler(finalize_registration, pattern="^final_confirm$"),
                CallbackQueryHandler(edit_registration, pattern="^final_edit$"),
            ],
        },
        fallbacks=[],
    )

    buy_conversation = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^Buy$"), buy_entry)],
        states={
            BUY_CATEGORY: [MessageHandler(filters.TEXT & ~filters.COMMAND, buy_category)],
            BUY_DETAILS: [MessageHandler(filters.TEXT & ~filters.COMMAND, buy_details)],
            BUY_PREVIEW: [CallbackQueryHandler(user_review_buy_buttons)],
            BUY_EDIT_FIELD_SELECT: [CallbackQueryHandler(buy_edit_field_select, pattern="^buy_edit_")],
            BUY_EDIT_FIELD_VALUE: [MessageHandler(filters.TEXT & ~filters.COMMAND, buy_edit_field_value)]
        },
        fallbacks=[CommandHandler("cancel", lambda u, c: ConversationHandler.END)],
    )

    sell_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^Sell$"), sell_entry)],
        states={
            SELL_CATEGORY: [MessageHandler(filters.TEXT & ~filters.COMMAND, sell_category)],
            SELL_DETAILS: [MessageHandler(filters.TEXT & ~filters.COMMAND, sell_details)],
            SELL_PHOTOS: [
                MessageHandler(filters.PHOTO, sell_photos),
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_photo_text)
            ],
            SELL_CONFIRM: [CallbackQueryHandler(user_review_buttons, pattern="^(post_item|edit_item|cancel_item)$")],
            EDIT_FIELD_SELECT: [CallbackQueryHandler(user_edit_field_select, pattern="^user_edit_")],
            EDIT_FIELD_VALUE: [MessageHandler(filters.TEXT & ~filters.COMMAND, user_edit_field_value)]
        },
        fallbacks=[CommandHandler("cancel", lambda u, c: ConversationHandler.END)],
        allow_reentry=True,
        per_message=False 
    )

    admin_edit_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(admin_review_buttons, pattern="^admin_(post|edit|cancel)_[0-9]+$")],
        states={
            ADMIN_EDIT_FIELD_SELECT: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_edit_field_select)],
            ADMIN_EDIT_FIELD_VALUE: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_edit_field_value)],
        },
        fallbacks=[CommandHandler("cancel", lambda u, c: ConversationHandler.END)],
        per_message=False
    )

    reject_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(reject_user, pattern="^reject_")],
        states={
            ASK_REJECT_REASON: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_reject_reason)],
            CONFIRM_REJECTION: [CallbackQueryHandler(handle_rejection_action, pattern="^(send_rejection|rewrite_rejection)$")],
        },
        fallbacks=[],
    )

    app.add_handler(reject_conv)
    app.add_handler(buy_conversation)
    app.add_handler(sell_conv)
    app.add_handler(admin_edit_conv)
    app.add_handler(registration_conv)

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(check_join, pattern="check_join"))
    app.add_handler(MessageHandler(filters.Regex("^Check Status$"), check_status))
    app.add_handler(CallbackQueryHandler(admin_review_buttons, pattern="^admin_(post|edit|cancel)_[0-9]+$"))
    app.add_handler(CommandHandler("admin", admin_panel))
    app.add_handler(CommandHandler("stats", show_stats))
    app.add_handler(CommandHandler("user", user_info))
    app.add_handler(CommandHandler("ban", ban_user_command))
    app.add_handler(CommandHandler("unban", unban_user_command))
    app.add_handler(CallbackQueryHandler(approve_user, pattern="^approve_"))

    app.add_handler(ConversationHandler(
        entry_points=[CommandHandler("broadcast", start_broadcast)],
        states={
            BROADCAST_WAITING: [MessageHandler(filters.ALL, handle_broadcast_preview)],
            BROADCAST_CONFIRM: [CallbackQueryHandler(handle_broadcast_confirm)],
        },
        fallbacks=[],
    ))

    print("Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    init_db()
    main()