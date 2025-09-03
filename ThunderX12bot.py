import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
from PIL import Image
import pytesseract
from rembg import remove
import filetype  # imghdr ke jagah use ho raha hai

# Telegram BOT Token (Render ya Local env se le raha hai)
TOKEN = os.getenv("8451491436:AAElgEmVJs-tIZayneLKuhRrJxtPo4iW3MI")

# 🔹 Start Command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🖼 Resize", callback_data="resize")],
        [InlineKeyboardButton("📦 Compress", callback_data="compress")],
        [InlineKeyboardButton("📄 Export to PDF", callback_data="pdf")],
        [InlineKeyboardButton("❌ Background Remover", callback_data="bg_remove")],
        [InlineKeyboardButton("🔠 Image to Text (OCR)", callback_data="ocr")],
        [InlineKeyboardButton("🌐 Change Language (Hindi/English)", callback_data="lang")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("👋 Welcome! Choose an option:", reply_markup=reply_markup)

# 🔹 Buttons handler
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data["action"] = query.data
    await query.edit_message_text(f"👉 Send me an image for *{query.data}*", parse_mode="Markdown")

# 🔹 Image Handler
async def handle_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    action = context.user_data.get("action")
    if not action:
        await update.message.reply_text("⚠️ Please select an option first by using /start")
        return

    photo = update.message.photo[-1]
    file = await photo.get_file()
    file_path = f"downloads/{file.file_id}.jpg"
    os.makedirs("downloads", exist_ok=True)
    await file.download_to_drive(file_path)

    # ✅ Filetype check (imghdr hata diya)
    kind = filetype.guess(file_path)
    if kind is None or "image" not in kind.mime:
        await update.message.reply_text("❌ This file is not a valid image.")
        return

    # 🔹 Action Perform
    if action == "resize":
        img = Image.open(file_path)
        img = img.resize((500, 500))
        output_path = f"downloads/resized_{file.file_id}.jpg"
        img.save(output_path)
        await update.message.reply_photo(photo=open(output_path, "rb"), caption="✅ Resized Image (500x500)")

    elif action == "compress":
        img = Image.open(file_path)
        output_path = f"downloads/compressed_{file.file_id}.jpg"
        img.save(output_path, optimize=True, quality=30)
        await update.message.reply_document(document=open(output_path, "rb"), caption="✅ Compressed Image")

    elif action == "pdf":
        img = Image.open(file_path).convert("RGB")
        output_path = f"downloads/{file.file_id}.pdf"
        img.save(output_path)
        await update.message.reply_document(document=open(output_path, "rb"), caption="✅ Exported as PDF")

    elif action == "bg_remove":
        with open(file_path, "rb") as inp:
            result = remove(inp.read())
        output_path = f"downloads/bg_removed_{file.file_id}.png"
        with open(output_path, "wb") as out:
            out.write(result)
        await update.message.reply_document(document=open(output_path, "rb"), caption="✅ Background Removed")

    elif action == "ocr":
        text = pytesseract.image_to_string(Image.open(file_path))
        await update.message.reply_text(f"🔠 Extracted Text:\n\n{text if text.strip() else '❌ No text found!'}")

    elif action == "lang":
        current = context.user_data.get("lang", "English")
        new_lang = "Hindi" if current == "English" else "English"
        context.user_data["lang"] = new_lang
        await update.message.reply_text(f"🌐 Language switched to {new_lang}")

# 🔹 Main function
def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.PHOTO, handle_image))

    print("🤖 Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
