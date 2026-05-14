from fastapi import FastAPI, Request
from dotenv import load_dotenv
from openai import OpenAI
import requests
import os
import base64

# =========================
# LOAD ENV
# =========================

load_dotenv()

CHANNEL_ACCESS_TOKEN = os.getenv(
    "CHANNEL_ACCESS_TOKEN"
)

FAMILY_GROUP_ID = os.getenv(
    "FAMILY_GROUP_ID"
)

IMGBB_API_KEY = os.getenv(
    "IMGBB_API_KEY"
)

OPENAI_API_KEY = os.getenv(
    "OPENAI_API_KEY"
)

print("TOKEN:", CHANNEL_ACCESS_TOKEN)
print("GROUP:", FAMILY_GROUP_ID)

# =========================
# APP
# =========================

app = FastAPI()

# =========================
# OPENAI
# =========================

client = OpenAI(
    api_key=OPENAI_API_KEY
)

# =========================
# USER MAP
# =========================

name_map = {
    "Kaimook🌿🩵": "คุณไข่มุก"
}

# =========================
# DAILY ORDERS
# =========================

daily_orders = []

# =========================
# GET PROFILE
# =========================

def get_profile(user_id):

    url = (
        f"https://api.line.me/v2/bot/profile/{user_id}"
    )

    headers = {
        "Authorization":
        f"Bearer {CHANNEL_ACCESS_TOKEN}"
    }

    response = requests.get(
        url,
        headers=headers
    )

    return response.json()

# =========================
# REPLY MESSAGE
# =========================

def reply_message(reply_token, text):

    url = "https://api.line.me/v2/bot/message/reply"

    headers = {
        "Content-Type": "application/json",
        "Authorization":
        f"Bearer {CHANNEL_ACCESS_TOKEN}"
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

    response = requests.post(
        url,
        headers=headers,
        json=data
    )

    print(
        "REPLY STATUS:",
        response.status_code
    )

    print(
        "REPLY RESPONSE:",
        response.text
    )

# =========================
# PUSH MESSAGE
# =========================

def push_message(to, text):

    url = "https://api.line.me/v2/bot/message/push"

    headers = {
        "Content-Type": "application/json",
        "Authorization":
        f"Bearer {CHANNEL_ACCESS_TOKEN}"
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

    response = requests.post(
        url,
        headers=headers,
        json=data
    )

    print(
        "PUSH STATUS:",
        response.status_code
    )

    print(
        "PUSH RESPONSE:",
        response.text
    )

# =========================
# GET IMAGE CONTENT
# =========================

def get_image_content(message_id):

    url = (
        f"https://api-data.line.me/v2/bot/message/"
        f"{message_id}/content"
    )

    headers = {
        "Authorization":
        f"Bearer {CHANNEL_ACCESS_TOKEN}"
    }

    response = requests.get(
        url,
        headers=headers
    )

    return response.content

# =========================
# UPLOAD IMAGE
# =========================

def upload_to_imgbb(image_binary):

    base64_image = base64.b64encode(
        image_binary
    )

    url = "https://api.imgbb.com/1/upload"

    payload = {
        "key": IMGBB_API_KEY,
        "image": base64_image
    }

    response = requests.post(
        url,
        data=payload
    )

    data = response.json()

    print(data)

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
คุณคือ AI อ่านออเดอร์ร้านอาหารเดลิเวอรี่

ให้ดูจากรูปแล้ววิเคราะห์ก่อนว่าเป็นแอปอะไร

กฎการดู:

- ถ้ามีคำว่า LINE MAN
หรือโลโก้สีเขียว
ให้ตอบว่าเป็น LINE MAN

- ถ้ามีคำว่า Grab
ให้ตอบว่าเป็น GrabFood

- ถ้ามีคำว่า ShopeeFood
หรือธีมสีส้ม
ให้ตอบว่าเป็น ShopeeFood

จากนั้นสรุปข้อมูลให้อ่านง่ายตามนี้:

====================

แอป: xxx

เลขออเดอร์: xxxx

ชื่อลูกค้า: xxxx

รายการอาหาร:
- เมนู x จำนวน

หมายเหตุ:
- ถ้ามี

ยอดรวม: xx บาท

วิธีชำระเงิน: xxx

====================

กฎสำคัญ:
- ห้ามมั่วข้อมูล
- ถ้ามองไม่ชัดให้บอกว่าไม่ชัด
- อ่านตัวเลขให้แม่น
- ตอบภาษาไทย
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
# DAILY SUMMARY
# =========================

def daily_summary():

    total_orders = len(daily_orders)

    summary_text = f"""
📊 สรุปวันนี้

จำนวนออเดอร์:
{total_orders}
"""

    push_message(
        FAMILY_GROUP_ID,
        summary_text
    )

    daily_orders.clear()

# =========================
# HOME
# =========================

@app.get("/")
def home():

    return {
        "message": "BOT ONLINE"
    }

# =========================
# WEBHOOK
# =========================

@app.post("/webhook")
async def webhook(request: Request):

    body = await request.json()

    print(body)

    events = body.get("events", [])

    for event in events:

        # รับเฉพาะ message
        if event.get("type") != "message":
            continue

        source = event.get("source", {})

        source_type = source.get("type")

        message = event.get("message", {})

        message_type = message.get("type")

        reply_token = event.get("replyToken")

        user_id = source.get("userId")

        # =========================
        # USER PROFILE
        # =========================

        if user_id:

            profile = get_profile(user_id)

            display_name = profile.get(
                "displayName",
                "Unknown"
            )

        else:

            display_name = "GROUP USER"

        real_name = name_map.get(
            display_name,
            display_name
        )

        print(
            f"{real_name} ส่ง {message_type}"
        )

        # =========================
        # IMAGE
        # =========================

        if message_type == "image":

            try:

                message_id = message["id"]

                # โหลดรูป
                image_binary = get_image_content(
                    message_id
                )

                # upload รูป
                image_url = upload_to_imgbb(
                    image_binary
                )

                print(image_url)

                # AI อ่านรูป
                summary = analyze_order(
                    image_url
                )

                print(summary)

                # เก็บ order
                daily_orders.append(summary)

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
        # TEXT
        # =========================

        elif message_type == "text":

            try:

                user_text = message["text"]

                # =====================
                # SUMMARY COMMAND
                # =====================

                if user_text == "/summary":

                    daily_summary()

                    reply_message(
                        reply_token,
                        "ส่งสรุปรายวันแล้ว 😼"
                    )

                    continue

                # ส่งข้อความเข้ากลุ่ม
                push_message(
                    FAMILY_GROUP_ID,
                    user_text
                )

                # reply กลับ
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

    return {
        "status": "ok"
    }