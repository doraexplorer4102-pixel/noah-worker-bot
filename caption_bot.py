"""
Trading Noah Caption Bot
- Zero external dependencies (pure Python stdlib only)
- Works on any Python version
"""
import os
import json
import base64
import ssl
import urllib.request
import urllib.error
import time

# ── CONFIG ────────────────────────────────────────────────────────
TOKEN          = os.getenv("TOKEN", "8942186437:AAHE30DBEMKD6ybjTkUhCOKAGceDhMyqpL8")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "AQ.Ab8RN6L9QxPa4bcuGVcCK9rUDcBNrOKIClcUiWyrJDt7V9wZKg")
OWNER_ID       = int(os.getenv("OWNER_ID", "8004113948"))

TG_BASE    = f"https://api.telegram.org/bot{TOKEN}"
TG_FILE    = f"https://api.telegram.org/file/bot{TOKEN}"
GEMINI_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    f"gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
)

SSL_CTX = ssl.create_default_context()
SSL_CTX.check_hostname = False
SSL_CTX.verify_mode = ssl.CERT_NONE

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

WRITING STYLE RULES:
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

OUTPUT: Give exactly 3 caption variations:

CAPTION 1 - EMOTIONAL/STORY
[caption here]

CAPTION 2 - RESULTS/PROOF
[caption here]

CAPTION 3 - URGENT/CTA
[caption here]

Ready to copy-paste. No extra explanation."""


# ── HTTP HELPERS ──────────────────────────────────────────────────
def http_get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "TradingNoahBot/1.0"})
    with urllib.request.urlopen(req, context=SSL_CTX, timeout=30) as resp:
        return resp.read()


def http_post_json(url, data):
    body = json.dumps(data).encode("utf-8")
    req = urllib.request.Request(
        url, data=body,
        headers={"Content-Type": "application/json", "User-Agent": "TradingNoahBot/1.0"},
        method="POST"
    )
    with urllib.request.urlopen(req, context=SSL_CTX, timeout=60) as resp:
        return json.loads(resp.read().decode("utf-8"))


def tg_post(method, data):
    return http_post_json(f"{TG_BASE}/{method}", data)


def tg_post_safe(method, data):
    """Same as tg_post but never raises — returns None on error"""
    try:
        return tg_post(method, data)
    except Exception as e:
        print(f"[{method}] {e}")
        return None


# ── TELEGRAM WRAPPERS ─────────────────────────────────────────────
def send_message(chat_id, text):
    return tg_post("sendMessage", {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown"
    })


def edit_message(chat_id, message_id, text):
    return tg_post_safe("editMessageText", {
        "chat_id": chat_id,
        "message_id": message_id,
        "text": text
    })


def delete_message(chat_id, message_id):
    return tg_post_safe("deleteMessage", {
        "chat_id": chat_id,
        "message_id": message_id
    })


def get_file(file_id):
    result = tg_post("getFile", {"file_id": file_id})
    return result["result"]["file_path"]


def download_file(file_path):
    return http_get(f"{TG_FILE}/{file_path}")


def get_updates(offset=0, timeout=25):
    return tg_post("getUpdates", {
        "offset": offset,
        "timeout": timeout,
        "allowed_updates": ["message"]
    })


# ── GEMINI API ────────────────────────────────────────────────────
def gemini_image(image_bytes, mime_type, extra=""):
    b64 = base64.b64encode(image_bytes).decode()
    user_text = "Analyze this image and generate 3 Trading Noah Hinglish captions."
    if extra:
        user_text += f"\nExtra context: {extra}"
    payload = {
        "contents": [{"parts": [
            {"text": STYLE_PROMPT},
            {"inline_data": {"mime_type": mime_type, "data": b64}},
            {"text": user_text},
        ]}],
        "generationConfig": {"temperature": 0.9, "maxOutputTokens": 2000},
    }
    result = http_post_json(GEMINI_URL, payload)
    return result["candidates"][0]["content"]["parts"][0]["text"]


def gemini_text(description):
    payload = {
        "contents": [{"parts": [
            {"text": STYLE_PROMPT},
            {"text": "Generate 3 Trading Noah Hinglish captions for:\n\n" + description},
        ]}],
        "generationConfig": {"temperature": 0.9, "maxOutputTokens": 2000},
    }
    result = http_post_json(GEMINI_URL, payload)
    return result["candidates"][0]["content"]["parts"][0]["text"]


# ── HANDLERS ─────────────────────────────────────────────────────
def handle_start(chat_id):
    send_message(chat_id,
        "🔥 *Trading Noah Caption Bot*\n\n"
        "Send me:\n"
        "📸 Photo — 3 viral captions generated\n"
        "🎥 Video — thumbnail analyzed, captions generated\n"
        "✍️ Text — describe content, captions generated\n\n"
        "Ready to copy-paste in your style! 🚀"
    )


def handle_photo(chat_id, photo_list, caption=""):
    wait = send_message(chat_id, "🔍 Analyzing photo... please wait ⏳")
    wait_id = wait["result"]["message_id"]
    try:
        best = max(photo_list, key=lambda p: p.get("file_size", 0))
        img_bytes = download_file(get_file(best["file_id"]))
        captions = gemini_image(img_bytes, "image/jpeg", caption)
        delete_message(chat_id, wait_id)
        send_message(chat_id, "✅ *Your 3 captions are ready:*\n\n" + captions)
    except Exception as e:
        print(f"[photo error] {e}")
        edit_message(chat_id, wait_id, "❌ Error: " + str(e) + "\n\nTry again bhai!")


def handle_video(chat_id, video, caption=""):
    wait = send_message(chat_id, "🎥 Got video! Analyzing thumbnail... ⏳")
    wait_id = wait["result"]["message_id"]
    try:
        thumbnail = video.get("thumbnail") or video.get("thumb")
        if thumbnail:
            img_bytes = download_file(get_file(thumbnail["file_id"]))
            captions = gemini_image(img_bytes, "image/jpeg", caption or "trading video")
        else:
            captions = gemini_text(caption or "trading results video, Quotex signals, wins")
        delete_message(chat_id, wait_id)
        send_message(chat_id, "✅ *Your 3 captions are ready:*\n\n" + captions)
    except Exception as e:
        print(f"[video error] {e}")
        edit_message(chat_id, wait_id, "❌ Error: " + str(e) + "\n\nTry again bhai!")


def handle_document(chat_id, document, caption=""):
    mime = document.get("mime_type", "")
    if not mime.startswith("image/"):
        send_message(chat_id, "📸 Send photos or videos only bhai!")
        return
    wait = send_message(chat_id, "🔍 Analyzing image... ⏳")
    wait_id = wait["result"]["message_id"]
    try:
        img_bytes = download_file(get_file(document["file_id"]))
        captions = gemini_image(img_bytes, mime, caption)
        delete_message(chat_id, wait_id)
        send_message(chat_id, "✅ *Your 3 captions are ready:*\n\n" + captions)
    except Exception as e:
        print(f"[document error] {e}")
        edit_message(chat_id, wait_id, "❌ Error: " + str(e) + "\n\nTry again bhai!")


def handle_text_msg(chat_id, text):
    if not text.strip():
        return
    wait = send_message(chat_id, "✍️ Generating captions... ⏳")
    wait_id = wait["result"]["message_id"]
    try:
        captions = gemini_text(text)
        delete_message(chat_id, wait_id)
        send_message(chat_id, "✅ *Your 3 captions are ready:*\n\n" + captions)
    except Exception as e:
        print(f"[text error] {e}")
        edit_message(chat_id, wait_id, "❌ Error: " + str(e) + "\n\nTry again bhai!")


def process_update(update):
    msg = update.get("message")
    if not msg:
        return
    chat_id = msg["chat"]["id"]
    text    = msg.get("text", "")
    caption = msg.get("caption", "")

    if text == "/start":
        handle_start(chat_id)
    elif "photo" in msg:
        handle_photo(chat_id, msg["photo"], caption)
    elif "video" in msg:
        handle_video(chat_id, msg["video"], caption)
    elif "document" in msg:
        handle_document(chat_id, msg["document"], caption)
    elif text:
        handle_text_msg(chat_id, text)


# ── STARTUP: KILL OLD SESSION ─────────────────────────────────────
def kill_old_session():
    """
    Fully clears any existing Telegram session before polling.
    This prevents 409 Conflict errors.
    """
    print("🔄 Clearing old sessions...")

    # 1. Delete webhook (clears webhook mode)
    tg_post_safe("deleteWebhook", {"drop_pending_updates": True})
    time.sleep(2)

    # 2. logOut kicks any other polling session off
    tg_post_safe("logOut", {})
    time.sleep(3)

    # 3. close terminates the current server connection
    tg_post_safe("close", {})
    time.sleep(5)

    print("✅ Old session cleared — starting fresh")


# ── MAIN ──────────────────────────────────────────────────────────
def main():
    print("🚀 Trading Noah Caption Bot starting...")
    print(f"   Token  : {TOKEN[:20]}...")
    print(f"   Gemini : {GEMINI_API_KEY[:20]}...")
    print(f"   Owner  : {OWNER_ID}")

    kill_old_session()

    offset = 0
    consecutive_errors = 0
    print("✅ Bot running — waiting for messages...")

    while True:
        try:
            updates = get_updates(offset=offset, timeout=25)
            consecutive_errors = 0
            for update in updates.get("result", []):
                offset = update["update_id"] + 1
                try:
                    process_update(update)
                except Exception as e:
                    print(f"[process_update error] {e}")

        except urllib.error.HTTPError as e:
            consecutive_errors += 1
            print(f"[HTTP error] {e.code} {e.reason}")
            if e.code == 409:
                # Another instance running — wait longer then retry
                print("409 Conflict — waiting 15s then retrying...")
                time.sleep(15)
                kill_old_session()
            elif e.code == 401:
                print("401 Unauthorized — check your TOKEN in Railway Variables!")
                time.sleep(30)
            else:
                wait = min(5 * consecutive_errors, 60)
                time.sleep(wait)

        except urllib.error.URLError as e:
            consecutive_errors += 1
            print(f"[network error] {e} — retrying in 5s")
            time.sleep(5)

        except Exception as e:
            consecutive_errors += 1
            print(f"[polling error] {e} — retrying in 5s")
            time.sleep(5)


if __name__ == "__main__":
    main()
