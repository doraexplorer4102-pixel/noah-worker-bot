"""
Trading Noah Caption Bot — OpenAI Vision
Pure Python stdlib. Zero dependencies. Any Python version.
"""
import os
import json
import base64
import ssl
import urllib.request
import urllib.error
import time

# ── CONFIG ────────────────────────────────────────────────────────
TOKEN      = os.getenv("TOKEN",      "8942186437:AAGvAGbKv1kD5tXNaGoNTEqKcoZLJOdVVck")
OPENAI_KEY = os.getenv("OPENAI_KEY", "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")
OWNER_ID   = int(os.getenv("OWNER_ID", "8004113948"))

TG_BASE = f"https://api.telegram.org/bot{TOKEN}"
TG_FILE = f"https://api.telegram.org/file/bot{TOKEN}"
OAI_URL = "https://api.openai.com/v1/chat/completions"

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


def http_post_json(url, data, extra_headers=None):
    body = json.dumps(data).encode("utf-8")
    headers = {"Content-Type": "application/json", "User-Agent": "TradingNoahBot/1.0"}
    if extra_headers:
        headers.update(extra_headers)
    req = urllib.request.Request(url, data=body, headers=headers, method="POST")
    with urllib.request.urlopen(req, context=SSL_CTX, timeout=90) as resp:
        return json.loads(resp.read().decode("utf-8"))


def tg_post(method, data):
    return http_post_json(f"{TG_BASE}/{method}", data)


def tg_safe(method, data):
    try:
        return tg_post(method, data)
    except Exception as e:
        print(f"[{method} ignored] {e}")
        return None


# ── TELEGRAM WRAPPERS ─────────────────────────────────────────────
def send_msg(chat_id, text):
    # Use plain text only — no special formatting to avoid errors
    return tg_post("sendMessage", {"chat_id": chat_id, "text": text})


def edit_msg(chat_id, mid, text):
    return tg_safe("editMessageText", {"chat_id": chat_id, "message_id": mid, "text": text})


def del_msg(chat_id, mid):
    return tg_safe("deleteMessage", {"chat_id": chat_id, "message_id": mid})


def tg_get_file(file_id):
    r = tg_post("getFile", {"file_id": file_id})
    return r["result"]["file_path"]


def tg_download(file_path):
    return http_get(f"{TG_FILE}/{file_path}")


def get_updates(offset=0):
    # Long polling — 20 second timeout, simple params
    return tg_post("getUpdates", {"offset": offset, "timeout": 20})


# ── OPENAI ────────────────────────────────────────────────────────
def ai_image(img_bytes, extra=""):
    b64 = base64.b64encode(img_bytes).decode()
    user_text = "Analyze this image and generate 3 Trading Noah Hinglish captions."
    if extra:
        user_text += " Context: " + extra
    payload = {
        "model": "gpt-4o",
        "max_tokens": 2000,
        "messages": [
            {"role": "system", "content": STYLE_PROMPT},
            {"role": "user", "content": [
                {"type": "text", "text": user_text},
                {"type": "image_url", "image_url": {
                    "url": "data:image/jpeg;base64," + b64,
                    "detail": "high"
                }}
            ]}
        ]
    }
    r = http_post_json(OAI_URL, payload, {"Authorization": "Bearer " + OPENAI_KEY})
    return r["choices"][0]["message"]["content"]


def ai_text(desc):
    payload = {
        "model": "gpt-4o",
        "max_tokens": 2000,
        "messages": [
            {"role": "system", "content": STYLE_PROMPT},
            {"role": "user",   "content": "Generate 3 Trading Noah Hinglish captions for: " + desc}
        ]
    }
    r = http_post_json(OAI_URL, payload, {"Authorization": "Bearer " + OPENAI_KEY})
    return r["choices"][0]["message"]["content"]


# ── HANDLERS ──────────────────────────────────────────────────────
def on_start(chat_id):
    send_msg(chat_id,
        "🔥 Trading Noah Caption Bot\n\n"
        "Send me:\n"
        "📸 Photo — 3 viral captions generated\n"
        "🎥 Video — thumbnail analyzed, captions generated\n"
        "✍️ Text — describe content, captions generated\n\n"
        "Ready to copy-paste in your style! 🚀"
    )


def on_photo(chat_id, photos, caption=""):
    w = send_msg(chat_id, "🔍 Analyzing photo... please wait ⏳")
    wid = w["result"]["message_id"]
    try:
        best = max(photos, key=lambda p: p.get("file_size", 0))
        img  = tg_download(tg_get_file(best["file_id"]))
        caps = ai_image(img, caption)
        del_msg(chat_id, wid)
        send_msg(chat_id, "✅ Your 3 captions are ready:\n\n" + caps)
    except Exception as e:
        print("[photo]", e)
        edit_msg(chat_id, wid, "❌ Error: " + str(e) + "\n\nTry again bhai!")


def on_video(chat_id, video, caption=""):
    w = send_msg(chat_id, "🎥 Got video! Analyzing thumbnail... ⏳")
    wid = w["result"]["message_id"]
    try:
        thumb = video.get("thumbnail") or video.get("thumb")
        if thumb:
            img  = tg_download(tg_get_file(thumb["file_id"]))
            caps = ai_image(img, caption or "trading video")
        else:
            caps = ai_text(caption or "trading results video Quotex signals wins")
        del_msg(chat_id, wid)
        send_msg(chat_id, "✅ Your 3 captions are ready:\n\n" + caps)
    except Exception as e:
        print("[video]", e)
        edit_msg(chat_id, wid, "❌ Error: " + str(e) + "\n\nTry again bhai!")


def on_document(chat_id, doc, caption=""):
    mime = doc.get("mime_type", "")
    if not mime.startswith("image/"):
        send_msg(chat_id, "📸 Send photos or videos only bhai!")
        return
    w = send_msg(chat_id, "🔍 Analyzing image... ⏳")
    wid = w["result"]["message_id"]
    try:
        img  = tg_download(tg_get_file(doc["file_id"]))
        caps = ai_image(img, caption)
        del_msg(chat_id, wid)
        send_msg(chat_id, "✅ Your 3 captions are ready:\n\n" + caps)
    except Exception as e:
        print("[document]", e)
        edit_msg(chat_id, wid, "❌ Error: " + str(e) + "\n\nTry again bhai!")


def on_text(chat_id, text):
    if not text.strip():
        return
    w = send_msg(chat_id, "✍️ Generating captions... ⏳")
    wid = w["result"]["message_id"]
    try:
        caps = ai_text(text)
        del_msg(chat_id, wid)
        send_msg(chat_id, "✅ Your 3 captions are ready:\n\n" + caps)
    except Exception as e:
        print("[text]", e)
        edit_msg(chat_id, wid, "❌ Error: " + str(e) + "\n\nTry again bhai!")


def process(update):
    msg = update.get("message")
    if not msg:
        return
    chat_id = msg["chat"]["id"]
    text    = msg.get("text", "")
    caption = msg.get("caption", "")

    if text == "/start":          on_start(chat_id)
    elif "photo"    in msg:       on_photo(chat_id,    msg["photo"],    caption)
    elif "video"    in msg:       on_video(chat_id,    msg["video"],    caption)
    elif "document" in msg:       on_document(chat_id, msg["document"], caption)
    elif text:                    on_text(chat_id, text)


# ── MAIN ──────────────────────────────────────────────────────────
def main():
    print("🚀 Trading Noah Caption Bot starting...")
    print(f"   Token  : {TOKEN[:20]}...")
    print(f"   OpenAI : {OPENAI_KEY[:20]}...")
    print(f"   Owner  : {OWNER_ID}")

    # Clear any old webhook (ignore errors — bot might be fresh)
    tg_safe("deleteWebhook", {"drop_pending_updates": True})
    time.sleep(2)
    print("✅ Ready — polling for messages...")

    offset = 0
    while True:
        try:
            resp = get_updates(offset)
            for upd in resp.get("result", []):
                offset = upd["update_id"] + 1
                try:
                    process(upd)
                except Exception as e:
                    print("[process error]", e)

        except urllib.error.HTTPError as e:
            body = ""
            try: body = e.read().decode()
            except: pass
            print(f"[HTTP {e.code}] {e.reason} — {body}")
            if e.code == 409:
                print("409 Conflict — another instance running, waiting 30s...")
                time.sleep(30)
            elif e.code == 401:
                print("401 Unauthorized — TOKEN is wrong! Fix in Railway Variables.")
                time.sleep(60)
            elif e.code == 400:
                print("400 Bad Request — skipping, retrying in 5s...")
                time.sleep(5)
            else:
                time.sleep(10)

        except urllib.error.URLError as e:
            print(f"[network] {e} — retry in 5s")
            time.sleep(5)

        except Exception as e:
            print(f"[error] {e} — retry in 5s")
            time.sleep(5)


if __name__ == "__main__":
    main()
