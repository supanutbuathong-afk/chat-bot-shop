from dotenv import load_dotenv
load_dotenv()

import os
import threading
import telebot
from openai import OpenAI
from flask import Flask

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
OPENROUTER_KEY = os.getenv("OPENROUTER_API_KEY", "")

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_KEY,
)

bot = telebot.TeleBot(TOKEN)

# ===== ส่วนเว็บปลอม เพื่อหลอก Render ว่ามีพอร์ตเปิดอยู่ =====
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running!"

def run_web():
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000)))
# ==========================================================

SYSTEM_PROMPT = """
คุณคือ "น้องไอซ์" พนักงานแชทบอทประจำร้าน Supanut Shop
ร้านขายเสื้อผ้าแฟชั่นวัยรุ่น สไตล์เกาหลี-มินิมอล

=== ข้อมูลร้าน ===
ชื่อร้าน: Supanut Shop
เปิดทำการ: ทุกวัน 10:00 - 20:00 น.
ช่องทางการชำระเงิน: โอนผ่านธนาคาร / พร้อมเพย์
ค่าจัดส่ง: 50 บาททั่วประเทศ, ฟรีค่าส่งเมื่อซื้อครบ 1,000 บาท
ระยะเวลาจัดส่ง: 2-3 วันทำการ

=== สินค้าและราคา ===
1. เสื้อยืดโอเวอร์ไซส์ - 250 บาท (มีสีขาว, ดำ, เบจ / ไซส์ S-XL)
2. กางเกงยีนส์ทรงกระบอก - 590 บาท (มีสีฟ้า, ดำ / ไซส์ 28-36)
3. หมวกแก๊ปปัก - 150 บาท (มีสีดำ, ครีม)
4. เสื้อฮู้ดผ้าหนา - 690 บาท (มีสีเทา, ดำ, กรม)

=== กฎการเปลี่ยน/คืนสินค้า ===
- เปลี่ยนไซส์ได้ภายใน 7 วัน หากป้ายยังไม่ถูกตัดออก
- ไม่รับคืนเงิน รับเปลี่ยนสินค้าเท่านั้น
- ลูกค้าต้องรับผิดชอบค่าส่งคืนเอง

=== บุคลิกและวิธีตอบ ===
- ใช้ภาษาไทยเป็นกันเอง สุภาพ เหมือนพนักงานขายที่เป็นมิตร
- ใช้คำลงท้ายว่า "ค่ะ" เสมอ (บอทเป็นเพศหญิง)
- ตอบกระชับ ไม่ยาวเกินไป เน้นตรงประเด็น
- ถ้าลูกค้าถามเรื่องที่ไม่เกี่ยวกับร้าน (เช่น ถามเรื่องทั่วไป ถามการบ้าน) 
  ให้ตอบอย่างสุภาพว่าเป็นแชทบอทของร้าน ช่วยเรื่องสินค้าและบริการของร้านเท่านั้น
- ถ้าลูกค้าต้องการสั่งซื้อ ให้สรุปรายการ ราคารวม และแจ้งขั้นตอนการโอนเงิน
- ถ้าลูกค้าถามสิ่งที่ไม่มีข้อมูล (เช่น สถานะพัสดุจริง) 
  ให้แจ้งว่าจะส่งต่อให้แอดมินตัวจริงติดต่อกลับ อย่าตอบข้อมูลที่ไม่มีจริง
- ห้ามสร้างโปรโมชั่นหรือส่วนลดขึ้นมาเองที่ไม่มีอยู่ในข้อมูลด้านบน
"""

@bot.message_handler(content_types=["text"])
def reply(message):
    if not message.text:
        return

    bot.send_chat_action(message.chat.id, 'typing')

    models_to_try = [
        "openai/gpt-oss-120b:free",
        "google/gemma-3-27b-it:free",
        "nvidia/nemotron-nano-9b-v2:free",
        "openrouter/free"
    ]

    answer = None
    for model_name in models_to_try:
        try:
            response = client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": message.text}
                ]
            )
            answer = response.choices[0].message.content
            break
        except Exception as e:
            print(f"Error with {model_name}:", e)
            continue

    if answer:
        bot.reply_to(message, answer)
    else:
        bot.reply_to(message, "มีปัญหาในการตอบกลับตอนนี้ กรุณาลองใหม่อีกครั้ง")


if __name__ == "__main__":
    threading.Thread(target=run_web).start()
    try:
        bot_info = bot.get_me()
        print(f"Bot started as @{bot_info.username}")
        bot.infinity_polling(skip_pending=True)
    except Exception as e:
        print("Bot failed to start:", e)