import os
import asyncio
import httpx
import base64
import json
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, MessageHandler, CommandHandler,
    ContextTypes, filters
)
from telegram.constants import ParseMode

TOKEN = "8942186437:AAHz_eL2DcVPdvnf8JlE7duiGEyQGBUF6FI"
GEMINI_API_KEY = "AQ.Ab8RN6L9QxPa4bcuGVcCK9rUDcBNrOKIClcUiWyrJDt7V9wZKg"
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"

OWNER_ID = 8004113948  # Will be set on first /start

# ── STYLE SYSTEM PROMPT ────────────────────────────────────────────────────────
STYLE_PROMPT = """You are a Hinglish social media caption writer for Trading Noah (@TRADELIKENOAH), India's top binary trader on Quotex.

ANALYZE the image/video carefully and detect what type it is:
- WITHDRAWAL PROOF → focus on big money, inspire others
- TRADING RESULTS (win/loss stats) → show accuracy, FOMO
- LIFESTYLE (cars, house, travel, family) → emotional storytelling, dream life
- MEMBER FEEDBACK/TESTIMONIAL → social proof, trust
- MOTIVATIONAL → personal struggle to success story
- VIP JOIN PROCESS → step by step, urgent CTA
- BONUS/OFFER → highlight promo code NOAH50, urgency

WRITING STYLE RULES (strictly follow):
1. Mix Hindi + English naturally (Hinglish) - not pure Hindi, not pure English
2. Emotional and personal tone - speak directly to "bhai/tu/tum"
3. Use CAPS for urgency on key words
4. Heavy emojis - relevant ones, not random
5. Create FOMO - "waqt nikal jaayega", "ab number tera hai", "sirf ek step door"
6. Social proof - mention 10,000+ members, 93-96% accuracy, India's top trader
7. ALWAYS end with call to action: message "VIP" → @TRADELIKENOAH
8. Keep it punchy, aggressive, real - not corporate
9. Short paragraphs, line breaks for readability
10. Personal stories work best (maa-baap, dream car, struggle)

KEY FACTS TO USE:
- Platform: Quotex
- Register link: https://broker-qx.pro/sign-up/?lid=1504736
- Promo code: NOAH50 (50% bonus)
- Min deposit: $20-$30
- Daily signals: 10-20
- Accuracy: 93-96%
- Contact: @TRADELIKENOAH
- VIP group: free with deposit
- Sessions: Morning, Afternoon, Evening, Night, Late Night

OUTPUT FORMAT - Give me 3 caption variations:

CAPTION 1 - EMOTIONAL/STORY (long, personal)
CAPTION 2 - RESULTS/PROOF (medium, data-driven)  
CAPTION 3 - URGENT/CTA (short, aggressive)

Each caption should be ready to copy-paste directly to Telegram/Instagram. No explanation needed, just the captions."""


async def analyze_with_gemini(image_data: bytes, mime_type: str, extra_context: str = "") -> str:
    """Send image to Gemini and get caption"""
    b64_image = base64.b64encode(image_data).decode("utf-8")

    user_text = "Analyze this image/video thumbnail and generate 3 Trading Noah style Hinglish captions as instructed."
    if extra_context:
        user_text += f"\n\nExtra context from user: {extra_context}"

    payload = {
        "contents": [
            {
                "parts": [
                    {"text": STYLE_PROMPT},
                    {
                        "inline_data": {
                            "mime_type": mime_type,
                            "data": b64_image
                        }
                    },
                    {"text": user_text}
                ]
            }
        ],
        "generationConfig": {
            "temperature": 0.9,
            "maxOutputTokens": 2000
        }
    }

    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(GEMINI_URL, json=payload)
        resp.raise_for_status()
        data = resp.json()
        return data["candidates"][0]["content"]["parts"][0]["text"]


async def analyze_text_only(context_text: str) -> str:
    """Generate caption based on text description only"""
    payload = {
        "contents": [
            {
                "parts": [
                    {"text": STYLE_PROMPT},
                    {"text": f"Generate 3 Trading Noah style Hinglish captions for this content type/context:\n\n{context_text}"}
                ]
            }
        ],
        "generationConfig": {
            "temperature": 0.9,
            "maxOutputTokens": 2000
        }
    }

    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(GEMINI_URL, json=payload)
        resp.raise_for_status()
        data = resp.json()
        return data["candidates"][0]["content"]["parts"][0]["text"]


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    await update.message.reply_text(
        "🔥 *Trading Noah Caption Bot Ready!*\n\n"
        "Send me:\n"
        "📸 *Photo* → I'll generate viral captions\n"
        "🎥 *Video* → I'll analyze & generate captions\n"
        "✍️ *Text* → Describe the content, I'll generate captions\n\n"
        "Each time you get *3 caption variations* ready to copy-paste!\n\n"
        "Let's go bhai 🚀",
        parse_mode=ParseMode.MARKDOWN
    )


async def photo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id

    # Get caption text if any
    extra_context = update.message.caption or ""

    thinking_msg = await update.message.reply_text("🔍 Analyzing image... generating captions ⏳")

    try:
        # Download photo (highest quality)
        photo = update.message.photo[-1]
        file = await context.bot.get_file(photo.file_id)
        image_data = await file.download_as_bytearray()

        captions = await analyze_with_gemini(bytes(image_data), "image/jpeg", extra_context)

        await thinking_msg.delete()
        await update.message.reply_text(
            f"✅ *Here are your 3 captions:*\n\n{captions}",
            parse_mode=ParseMode.MARKDOWN
        )

    except Exception as e:
        await thinking_msg.edit_text(f"❌ Error: {e}\n\nTry again bhai!")
        print(f"Photo handler error: {e}")


async def video_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    extra_context = update.message.caption or ""

    thinking_msg = await update.message.reply_text("🎥 Video received! Analyzing thumbnail... ⏳")

    try:
        # Get video thumbnail for analysis
        video = update.message.video
        if video.thumbnail:
            file = await context.bot.get_file(video.thumbnail.file_id)
            image_data = await file.download_as_bytearray()
            captions = await analyze_with_gemini(bytes(image_data), "image/jpeg", extra_context or "This is a trading video")
        else:
            # No thumbnail — use text context
            desc = extra_context or "trading results video, wins, Quotex signals"
            captions = await analyze_text_only(desc)

        await thinking_msg.delete()
        await update.message.reply_text(
            f"✅ *Here are your 3 captions:*\n\n{captions}",
            parse_mode=ParseMode.MARKDOWN
        )

    except Exception as e:
        await thinking_msg.edit_text(f"❌ Error: {e}\n\nTry again bhai!")
        print(f"Video handler error: {e}")


async def document_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle files sent as documents (uncompressed)"""
    doc = update.message.document
    extra_context = update.message.caption or ""

    if not doc.mime_type or not doc.mime_type.startswith("image/"):
        await update.message.reply_text("📸 Please send photos or videos only bhai!")
        return

    thinking_msg = await update.message.reply_text("🔍 Analyzing image... generating captions ⏳")

    try:
        file = await context.bot.get_file(doc.file_id)
        image_data = await file.download_as_bytearray()
        captions = await analyze_with_gemini(bytes(image_data), doc.mime_type, extra_context)

        await thinking_msg.delete()
        await update.message.reply_text(
            f"✅ *Here are your 3 captions:*\n\n{captions}",
            parse_mode=ParseMode.MARKDOWN
        )

    except Exception as e:
        await thinking_msg.edit_text(f"❌ Error: {e}\n\nTry again bhai!")
        print(f"Document handler error: {e}")


async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle text descriptions to generate captions"""
    text = update.message.text.strip()

    if text.startswith("/"):
        return

    thinking_msg = await update.message.reply_text("✍️ Generating captions... ⏳")

    try:
        captions = await analyze_text_only(text)
        await thinking_msg.delete()
        await update.message.reply_text(
            f"✅ *Here are your 3 captions:*\n\n{captions}",
            parse_mode=ParseMode.MARKDOWN
        )
    except Exception as e:
        await thinking_msg.edit_text(f"❌ Error: {e}\n\nTry again bhai!")
        print(f"Text handler error: {e}")


async def main():
    print("🚀 Trading Noah Caption Bot starting...")
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.PHOTO, photo_handler))
    app.add_handler(MessageHandler(filters.VIDEO, video_handler))
    app.add_handler(MessageHandler(filters.Document.ALL, document_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))

    print("✅ Bot running! Send a photo or video to generate captions.")
    await app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    asyncio.run(main())
