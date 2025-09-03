from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, CallbackQueryHandler, filters
from PIL import Image
from rembg import remove
import io

TOKEN = "8451491436:AAElgEmVJs-tIZayneLKuhRrJxtPo4iW3MI"

# Defaults
resize_width = 300
resize_height = 300
image_quality = 90
user_images = {}
user_lang = {}  # per-user language setting

# ---------------- LANGUAGE SYSTEM -----------------
def t(user_id, en_text, hi_text):
    if user_id in user_lang and user_lang[user_id] == "hi":
        return hi_text
    return en_text

async def set_lang(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if len(context.args) == 1 and context.args[0] in ["en", "hi"]:
        user_lang[user_id] = context.args[0]
        await update.message.reply_text(
            "✅ Language set to English" if context.args[0] == "en" else "✅ भाषा हिंदी में सेट हो गई"
        )
    else:
        await update.message.reply_text("⚠️ Use: /lang en OR /lang hi")

# ---------------- START -----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📐 Resize", callback_data="resize")],
        [InlineKeyboardButton("📉 Compression", callback_data="compression")],
        [InlineKeyboardButton("📂 PDF Mode", callback_data="pdf")],
        [InlineKeyboardButton("🪄 Background Remove", callback_data="bgremove")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "👋 Welcome! Choose an option below:\n(भाषा बदलने के लिए: /lang en या /lang hi)",
        reply_markup=reply_markup
    )

# ---------------- BUTTON HANDLER -----------------
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global user_images
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    if query.data == "resize":
        await query.edit_message_text(t(user_id,
            "📐 Use command: /resize width height\nExample: /resize 500 400",
            "📐 कमांड इस्तेमाल करें: /resize चौड़ाई ऊँचाई\nउदाहरण: /resize 500 400"
        ))

    elif query.data == "compression":
        await query.edit_message_text(t(user_id,
            "📉 Use command: /quality number (10-100)\nExample: /quality 70",
            "📉 कमांड इस्तेमाल करें: /quality संख्या (10-100)\nउदाहरण: /quality 70"
        ))

    elif query.data == "pdf":
        user_images[user_id] = []
        keyboard = [[InlineKeyboardButton("✅ Done (Create PDF)", callback_data="pdf_done")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(t(user_id,
            "📂 PDF Mode ON. Send me multiple images, then press Done ✅",
            "📂 PDF मोड चालू. मुझे कई तस्वीरें भेजें, फिर Done ✅ दबाएँ"
        ), reply_markup=reply_markup)

    elif query.data == "pdf_done":
        if user_id not in user_images or not user_images[user_id]:
            await query.edit_message_text(t(user_id,
                "⚠️ First send images.",
                "⚠️ पहले तस्वीरें भेजें।"
            ))
            return
        images = user_images[user_id]
        output = io.BytesIO()
        output.name = "output.pdf"
        images[0].save(output, save_all=True, append_images=images[1:], format="PDF")
        output.seek(0)
        await query.message.reply_document(document=output, filename="Converted.pdf", caption="✅ PDF ready!")
        del user_images[user_id]

    elif query.data == "bgremove":
        await query.edit_message_text(t(user_id,
            "🪄 Send me an image, I will remove the background.",
            "🪄 मुझे एक तस्वीर भेजें, मैं उसका बैकग्राउंड हटा दूँगा।"
        ))
        context.user_data["mode"] = "bgremove"

# ---------------- RESIZE -----------------
async def set_resize(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global resize_width, resize_height
    try:
        if len(context.args) == 2:
            resize_width = int(context.args[0])
            resize_height = int(context.args[1])
            await update.message.reply_text(f"✅ Resize size set to {resize_width}x{resize_height}")
        else:
            await update.message.reply_text("⚠️ Format galat hai. Example: /resize 500 400")
    except ValueError:
        await update.message.reply_text("⚠️ Sirf numbers dalo. Example: /resize 500 400")

# ---------------- QUALITY -----------------
async def set_quality(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global image_quality
    try:
        if len(context.args) == 1:
            q = int(context.args[0])
            if 10 <= q <= 100:
                image_quality = q
                await update.message.reply_text(f"✅ Image quality set to {image_quality}%")
            else:
                await update.message.reply_text("⚠️ Quality 10 se 100 ke beech honi chahiye")
        else:
            await update.message.reply_text("⚠️ Format galat hai. Example: /quality 70")
    except ValueError:
        await update.message.reply_text("⚠️ Sirf numbers dalo. Example: /quality 70")

# ---------------- HANDLE IMAGE -----------------
async def handle_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global resize_width, resize_height, image_quality, user_images
    user_id = update.message.from_user.id
    photo = update.message.photo[-1]
    file = await context.bot.get_file(photo.file_id)
    img_bytes = await file.download_as_bytearray()
    image = Image.open(io.BytesIO(img_bytes))

    # Background Remove
    if context.user_data.get("mode") == "bgremove":
        output = io.BytesIO()
        output.name = "no_bg.png"
        result = remove(image)
        result.save(output, format="PNG")
        output.seek(0)
        await update.message.reply_photo(photo=output, caption=t(user_id,
            "✅ Background removed!",
            "✅ बैकग्राउंड हटा दिया गया!"
        ))
        context.user_data["mode"] = None
        return

    # PDF Mode
    if user_id in user_images:
        user_images[user_id].append(image.convert("RGB"))
        await update.message.reply_text(t(user_id,
            "📸 Image added for PDF.",
            "📸 तस्वीर PDF में जोड़ दी गई।"
        ))
    else:
        # Normal Resize + Compression
        resized = image.resize((resize_width, resize_height))
        output = io.BytesIO()
        output.name = "compressed.jpg"
        resized.save(output, format="JPEG", quality=image_quality, optimize=True)
        output.seek(0)
        await update.message.reply_photo(
            photo=output,
            caption=f"✅ Resized to {resize_width}x{resize_height}, Quality={image_quality}%"
        )

# ---------------- MAIN -----------------
def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(CommandHandler("resize", set_resize))
    app.add_handler(CommandHandler("quality", set_quality))
    app.add_handler(CommandHandler("lang", set_lang))
    app.add_handler(MessageHandler(filters.PHOTO, handle_image))

    print("🤖 Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
