"""
Trading Noah Caption Bot — OpenAI Vision
- Zero external dependencies (pure Python stdlib)
- Works on ANY Python version
- OpenAI GPT-4o Vision for image analysis
"""
import os
import json
import base64
import ssl
import urllib.request
import urllib.error
import time

# ── CONFIG ────────────────────────────────────────────────────────
TOKEN        = os.getenv("TOKEN",        "8942186437:AAHE30DBEMKD6ybjTkUhCOKAGceDhMyqpL8")
OPENAI_KEY   = os.getenv("OPENAI_KEY",   "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")
OWNER_ID     = int(os.getenv("OWNER_ID", "8004113948"))

TG_BASE  = f"https://api.telegram.org/bot{TOKEN}"
TG_FILE  = f"https://api.telegram.org/file/bot{TOKEN}"
OAI_URL  = "https://api.openai.com/v1/chat/completions"

SSL_CTX = ssl.create_default_context()
SSL_CTX.check_hostname = False
SSL_CTX.verify_mode    = ssl.CERT_NONE

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


def http_post_json(url, data, headers=None):
    body = json.dumps(data).encode("utf-8")
    h = {"Content-Type": "application/json", "User-Agent": "TradingNoahBot/1.0"}
    if headers:
        h.update(headers)
    req = urllib.request.Request(url, data=body, headers=h, method="POST")
    with urllib.request.urlopen(req, context=SSL_CTX, timeout=90) as resp:
        return json.loads(resp.read().decode("utf-8"))


def tg_post(method, data):
    return http_post_json(f"{TG_BASE}/{method}", data)


def tg_post_safe(method, data):
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


# ── OPENAI VISION API ─────────────────────────────────────────────
def openai_image(image_bytes, extra=""):
    b64 = base64.b64encode(image_bytes).decode()
    user_text = "Analyze this image and generate 3 Trading Noah Hinglish captions."
    if extra:
        user_text += f"\nExtra context: {extra}"

    payload = {
        "model": "gpt-4o",
        "max_tokens": 2000,
        "messages": [
            {"role": "system", "content": STYLE_PROMPT},
            {"role": "user", "content": [
                {"type": "text",      "text": user_text},
                {"type": "image_url", "image_url": {
                    "url": f"data:image/jpeg;base64,{b64}",
                    "detail": "high"
                }}
            ]}
        ]
    }
    result = http_post_json(OAI_URL, payload, {
        "Authorization": f"Bearer {OPENAI_KEY}"
    })
    return result["choices"][0]["message"]["content"]


def openai_text(description):
    payload = {
        "model": "gpt-4o",
        "max_tokens": 2000,
        "messages": [
            {"role": "system", "content": STYLE_PROMPT},
            {"role": "user",   "content": "Generate 3 Trading Noah Hinglish captions for:\n\n" + description}
        ]
    }
    result = http_post_json(OAI_URL, payload, {
        "Authorization": f"Bearer {OPENAI_KEY}"
    })
    return result["choices"][0]["message"]["content"]


# ── HANDLERS ──────────────────────────────────────────────────────
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
    wait    = send_message(chat_id, "🔍 Analyzing photo... please wait ⏳")
    wait_id = wait["result"]["message_id"]
    try:
        best      = max(photo_list, key=lambda p: p.get("file_size", 0))
        img_bytes = download_file(get_file(best["file_id"]))
        captions  = openai_image(img_bytes, caption)
        delete_message(chat_id, wait_id)
        send_message(chat_id, "✅ *Your 3 captions are ready:*\n\n" + captions)
    except Exception as e:
        print(f"[photo error] {e}")
        edit_message(chat_id, wait_id, "❌ Error: " + str(e) + "\n\nTry again bhai!")


def handle_video(chat_id, video, caption=""):
    wait    = send_message(chat_id, "🎥 Got video! Analyzing thumbnail... ⏳")
    wait_id = wait["result"]["message_id"]
    try:
        thumbnail = video.get("thumbnail") or video.get("thumb")
        if thumbnail:
            img_bytes = download_file(get_file(thumbnail["file_id"]))
            captions  = openai_image(img_bytes, caption or "trading video")
        else:
            captions  = openai_text(caption or "trading results video, Quotex signals, wins")
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
    wait    = send_message(chat_id, "🔍 Analyzing image... ⏳")
    wait_id = wait["result"]["message_id"]
    try:
        img_bytes = download_file(get_file(document["file_id"]))
        captions  = openai_image(img_bytes, caption)
        delete_message(chat_id, wait_id)
        send_message(chat_id, "✅ *Your 3 captions are ready:*\n\n" + captions)
    except Exception as e:
        print(f"[document error] {e}")
        edit_message(chat_id, wait_id, "❌ Error: " + str(e) + "\n\nTry again bhai!")


def handle_text_msg(chat_id, text):
    if not text.strip():
        return
    wait    = send_message(chat_id, "✍️ Generating captions... ⏳")
    wait_id = wait["result"]["message_id"]
    try:
        captions = openai_text(text)
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


# ── KILL OLD SESSION ──────────────────────────────────────────────
def kill_old_session():
    print("🔄 Clearing old Telegram sessions...")
    tg_post_safe("deleteWebhook", {"drop_pending_updates": True})
    time.sleep(2)
    tg_post_safe("logOut", {})
    time.sleep(3)
    tg_post_safe("close", {})
    time.sleep(5)
    print("✅ Old session cleared")


# ── MAIN ──────────────────────────────────────────────────────────
def main():
    print("🚀 Trading Noah Caption Bot starting...")
    print(f"   Token    : {TOKEN[:20]}...")
    print(f"   OpenAI   : {OPENAI_KEY[:20]}...")
    print(f"   Owner    : {OWNER_ID}")

    kill_old_session()

    offset            = 0
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
            print(f"[HTTP {e.code}] {e.reason}")
            if e.code == 409:
                print("409 Conflict — waiting 15s then clearing session...")
                time.sleep(15)
                kill_old_session()
            elif e.code == 401:
                print("401 Unauthorized — check TOKEN in Railway Variables!")
                time.sleep(30)
            else:
                time.sleep(min(5 * consecutive_errors, 60))

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
