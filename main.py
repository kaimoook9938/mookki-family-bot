from fastapi import FastAPI, Request
from dotenv import load_dotenv
from openai import OpenAI
import requests
import os
import base64

app = FastAPI()

load_dotenv()

# =========================
# ENV
# =========================

CHANNEL_ACCESS_TOKEN = os.getenv("CHANNEL_ACCESS_TOKEN")
FAMILY_GROUP_ID = os.getenv("FAMILY_GROUP_ID")
IMGBB_API_KEY = os.getenv("IMGBB_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# =========================
# OPENAI
# =========================

client = OpenAI(
    api_key=OPENAI_API_KEY
)

# =========================
# MAP USER
# =========================

name_map = {
    "869 🐢🎁🪯💰💲": "น้าปุ้ม",
    "Mom": "แม่",
    "Friend": "น้องเฟรนด์",
    "PEMIKA'": "น้องป้อม",
    "จินตนา ศรีจันทร์": "ป้าอ้อย",
    "ปังปัง": "น้องปังคุง",
    "เปิ้ล🌹💰💵💵💵💰🌹242": "น้าเปิ้ล",
    "Kaimook🌿🩵": "คุณไข่มุก"
}

# =========================
# GET PROFILE
# =========================

def get_profile(user_id):

    url = f"https://api.line.me/v2/bot/profile/{user_id}"

    headers = {
        "Authorization": f"Bearer {CHANNEL_ACCESS_TOKEN}"
    }

    response = requests.get(url, headers=headers)

    return response.json()

# =========================
# REPLY MESSAGE
# =========================

def reply_message(reply_token, text):

    url = "https://api.line.me/v2/bot/message/reply"

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {CHANNEL_ACCESS_TOKEN}"
    }

    data = {
        "replyToken": reply_token,
        "messages": [
            {
                "type": "text",
                "text": text
            }
        ]
    }

    requests.post(url, headers=headers, json=data)

# =========================
# PUSH MESSAGE
# =========================

def push_message(to, text):

    url = "https://api.line.me/v2/bot/message/push"

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {CHANNEL_ACCESS_TOKEN}"
    }

    data = {
        "to": to,
        "messages": [
            {
                "type": "text",
                "text": text
            }
        ]
    }

    requests.post(url, headers=headers, json=data)

# =========================
# GET IMAGE CONTENT
# =========================

def get_image_content(message_id):

    url = f"https://api-data.line.me/v2/bot/message/{message_id}/content"

    headers = {
        "Authorization": f"Bearer {CHANNEL_ACCESS_TOKEN}"
    }

    response = requests.get(url, headers=headers)

    return response.content

# =========================
# UPLOAD TO IMGBB
# =========================

def upload_to_imgbb(image_binary):

    base64_image = base64.b64encode(image_binary)

    url = "https://api.imgbb.com/1/upload"

    payload = {
        "key": IMGBB_API_KEY,
        "image": base64_image
    }

    response = requests.post(url, data=payload)

    data = response.json()

    return data["data"]["url"]

# =========================
# AI ANALYZE ORDER
# =========================

def analyze_order(image_url):

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {
                "role": "system",
                "content": """
อ่านข้อความจากรูปออเดอร์อาหาร

ให้วิเคราะห์ว่าเป็น:
- GrabFood
- LINE MAN
- ShopeeFood

แล้วสรุปให้อ่านง่ายแบบนี้:

แพลตฟอร์ม: xxx
เลขออเดอร์: xxxx

รายการ:
- เมนู x จำนวน

หมายเหตุ:
- ถ้ามี

รวมทั้งหมด: xx บาท
วิธีชำระเงิน: xxx

ตอบสั้น อ่านง่าย
"""
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "อ่านข้อความในรูปนี้"
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": image_url
                        }
                    }
                ]
            }
        ]
    )

    return response.choices[0].message.content

# =========================
# HOME
# =========================

@app.get("/")
def home():
    return {"message": "AI BOT READY"}

# =========================
# WEBHOOK
# =========================

@app.post("/webhook")
async def webhook(request: Request):

    body = await request.json()

    print(body)

    events = body.get("events", [])

    for event in events:

        if event.get("type") != "message":
            continue

        message_type = event["message"].get("type")

        reply_token = event["replyToken"]

        user_id = event["source"]["userId"]

        # =========================
        # USER NAME
        # =========================

        profile = get_profile(user_id)

        display_name = profile.get(
            "displayName",
            "คนในครอบครัว"
        )

        real_name = name_map.get(
            display_name,
            display_name
        )

        print(f"{real_name} ส่ง {message_type}")

        # =========================
        # IMAGE MESSAGE
        # =========================

        if message_type == "image":

            try:

                print(f"{real_name} ส่งรูปมา 📸")

                # message id
                message_id = event["message"]["id"]

                # โหลดรูปจาก LINE
                image_binary = get_image_content(
                    message_id
                )

                # upload รูป
                image_url = upload_to_imgbb(
                    image_binary
                )

                print(image_url)

                # AI อ่านออเดอร์
                summary = analyze_order(
                    image_url
                )

                print(summary)

                # ส่งเข้ากลุ่ม
                push_message(
                    FAMILY_GROUP_ID,
                    summary
                )

                # ตอบกลับ
                reply_message(
                    reply_token,
                    "อ่านออเดอร์แล้ว 😼"
                )

            except Exception as e:

                print("ERROR:", e)

                reply_message(
                    reply_token,
                    "อ่านรูปไม่สำเร็จ 😭"
                )

        # =========================
        # TEXT MESSAGE
        # =========================

        elif message_type == "text":

            try:

                user_text = event["message"]["text"]

                push_message(
                    FAMILY_GROUP_ID,
                    user_text
                )

                reply_message(
                    reply_token,
                    "ส่งข้อความเข้ากลุ่มแล้ว 😼"
                )

            except Exception as e:

                print("ERROR:", e)

                reply_message(
                    reply_token,
                    "ส่งข้อความไม่สำเร็จ 😭"
                )

    return {"status": "ok"}