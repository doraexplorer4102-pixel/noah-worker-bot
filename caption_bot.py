import os
import asyncio
import httpx
import base64
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    MessageHandler,
    CommandHandler,
    ContextTypes,
    filters,
)
from telegram.constants import ParseMode

# ── CONFIG ────────────────────────────────────────────────────────
TOKEN          = "8942186437:AAHz_eL2DcVPdvnf8JlE7duiGEyQGBUF6FI"
GEMINI_API_KEY = "AQ.Ab8RN6L9QxPa4bcuGVcCK9rUDcBNrOKIClcUiWyrJDt7V9wZKg"
OWNER_ID       = 8004113948

GEMINI_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    "gemini-1.5-flash:generateContent?key=" + GEMINI_API_KEY
)

# ── STYLE PROMPT ──────────────────────────────────────────────────
STYLE_PROMPT = """You are a Hinglish social media caption writer for Trading Noah (@TRADELIKENOAH), India's top binary trader on Quotex.

ANALYZE the image carefully and detect what type it is:
- WITHDRAWAL PROOF: focus on big money, inspire others
- TRADING RESULTS (win/loss stats): show accuracy, FOMO
- LIFESTYLE (cars, house, travel, family): emotional storytelling, dream life
- MEMBER FEEDBACK/TESTIMONIAL: social proof, trust
- MOTIVATIONAL: personal struggle to success story
- VIP JOIN PROCESS: step by step, urgent CTA
- BONUS/OFFER: highlight promo code NOAH50, urgency

WRITING STYLE RULES (strictly follow):
1. Mix Hindi + English naturally (Hinglish)
2. Emotional and personal tone - speak directly to bhai/tu/tum
3. Use CAPS for urgency on key words
4. Heavy relevant emojis
5. Create FOMO - waqt nikal jaayega, ab number tera hai, sirf ek step door
6. Social proof - 10000+ members, 93-96% accuracy, India top trader
7. ALWAYS end with: message VIP on @TRADELIKENOAH
8. Punchy, aggressive, real - not corporate
9. Short paragraphs with line breaks

KEY FACTS:
- Platform: Quotex
- Register: https://broker-qx.pro/sign-up/?lid=1504736
- Promo code: NOAH50 (50% bonus)
- Min deposit: $20
- Daily signals: 10-20
- Accuracy: 93-96%
- Contact: @TRADELIKENOAH

OUTPUT: Give exactly 3 caption variations with these headers:

CAPTION 1 - EMOTIONAL/STORY
[caption here]

CAPTION 2 - RESULTS/PROOF
[caption here]

CAPTION 3 - URGENT/CTA
[caption here]

Ready to copy-paste. No extra explanation."""


# ── GEMINI CALLS ──────────────────────────────────────────────────
async def analyze_image(image_bytes: bytes, mime_type: str, extra: str = "") -> str:
    b64 = base64.b64encode(image_bytes).decode()
    user_text = "Analyze this image and generate 3 Trading Noah Hinglish captions."
    if extra:
        user_text += f"\nExtra context: {extra}"

    payload = {
        "contents": [{
            "parts": [
                {"text": STYLE_PROMPT},
                {"inline_data": {"mime_type": mime_type, "data": b64}},
                {"text": user_text},
            ]
        }],
        "generationConfig": {"temperature": 0.9, "maxOutputTokens": 2000},
    }
    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.post(GEMINI_URL, json=payload)
        r.raise_for_status()
        return r.json()["candidates"][0]["content"]["parts"][0]["text"]


async def analyze_text(description: str) -> str:
    payload = {
        "contents": [{
            "parts": [
                {"text": STYLE_PROMPT},
                {"text": f"Generate 3 Trading Noah Hinglish captions for:\n\n{description}"},
            ]
        }],
        "generationConfig": {"temperature": 0.9, "maxOutputTokens": 2000},
    }
    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.post(GEMINI_URL, json=payload)
        r.raise_for_status()
        return r.json()["candidates"][0]["content"]["parts"][0]["text"]


# ── HELPERS ───────────────────────────────────────────────────────
async def send_captions(msg, captions: str):
    await msg.reply_text(
        "✅ *Your 3 captions are ready:*\n\n" + captions,
        parse_mode=ParseMode.MARKDOWN,
    )


# ── HANDLERS ──────────────────────────────────────────────────────
async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🔥 *Trading Noah Caption Bot*\n\n"
        "Send me:\n"
        "📸 Photo — I analyze & generate 3 viral captions\n"
        "🎥 Video — I analyze thumbnail & generate captions\n"
        "✍️ Text — Describe content, I generate captions\n\n"
        "Captions are in your Trading Noah Hinglish style, ready to copy-paste! 🚀",
        parse_mode=ParseMode.MARKDOWN,
    )


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    extra = update.message.caption or ""
    wait = await update.message.reply_text("🔍 Analyzing photo... please wait ⏳")
    try:
        photo_file = await context.bot.get_file(update.message.photo[-1].file_id)
        img_bytes = bytes(await photo_file.download_as_bytearray())
        captions = await analyze_image(img_bytes, "image/jpeg", extra)
        await wait.delete()
        await send_captions(update.message, captions)
    except Exception as e:
        print(f"[photo] {e}")
        await wait.edit_text(f"❌ Something went wrong: {e}\n\nTry again bhai!")


async def handle_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    extra = update.message.caption or ""
    wait = await update.message.reply_text("🎥 Got video! Analyzing thumbnail... ⏳")
    try:
        video = update.message.video
        if video.thumbnail:
            thumb_file = await context.bot.get_file(video.thumbnail.file_id)
            img_bytes = bytes(await thumb_file.download_as_bytearray())
            captions = await analyze_image(img_bytes, "image/jpeg", extra or "trading video")
        else:
            captions = await analyze_text(extra or "trading results video, Quotex signals, wins")
        await wait.delete()
        await send_captions(update.message, captions)
    except Exception as e:
        print(f"[video] {e}")
        await wait.edit_text(f"❌ Something went wrong: {e}\n\nTry again bhai!")


async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    doc = update.message.document
    extra = update.message.caption or ""
    if not doc.mime_type or not doc.mime_type.startswith("image/"):
        await update.message.reply_text("📸 Send photos or videos only bhai!")
        return
    wait = await update.message.reply_text("🔍 Analyzing image... ⏳")
    try:
        doc_file = await context.bot.get_file(doc.file_id)
        img_bytes = bytes(await doc_file.download_as_bytearray())
        captions = await analyze_image(img_bytes, doc.mime_type, extra)
        await wait.delete()
        await send_captions(update.message, captions)
    except Exception as e:
        print(f"[document] {e}")
        await wait.edit_text(f"❌ Something went wrong: {e}\n\nTry again bhai!")


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if not text:
        return
    wait = await update.message.reply_text("✍️ Generating captions... ⏳")
    try:
        captions = await analyze_text(text)
        await wait.delete()
        await send_captions(update.message, captions)
    except Exception as e:
        print(f"[text] {e}")
        await wait.edit_text(f"❌ Something went wrong: {e}\n\nTry again bhai!")


# ── MAIN ──────────────────────────────────────────────────────────
async def main():
    print("🚀 Trading Noah Caption Bot starting...")
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.VIDEO, handle_video))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    print("✅ Bot running — polling for updates...")
    await app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    asyncio.run(main())
