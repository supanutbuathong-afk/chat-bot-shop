from dotenv import load_dotenv
load_dotenv()  # โหลดค่าจาก .env เข้ามาใช้

import os
import telebot
from openai import OpenAI

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
OPENROUTER_KEY = os.getenv("OPENROUTER_API_KEY", "")

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_KEY,
)

bot = telebot.TeleBot(TOKEN)

SYSTEM_PROMPT = """"
คุณคือบอทของร้าน Supanut Shop ขายเสื้อผ้าวัยรุ่น
สินค้าที่มี:
- เสื้อยืด ราคา 250 บาท
- กางเกงยีนส์ ราคา 590 บาท
- หมวก ราคา 150 บาท
เปิด 10:00 - 20:00 ทุกวัน
ตอบลูกค้าสุภาพ เป็นกันเอง กระชับ
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
            break  # ถ้าได้คำตอบแล้วหยุดลูปเลย
        except Exception as e:
            print(f"Error with {model_name}:", e)
            continue  # ถ้า error ลองตัวถัดไป

    if answer:
        bot.reply_to(message, answer)
    else:
        bot.reply_to(message, "มีปัญหาในการตอบกลับตอนนี้ กรุณาลองใหม่อีกครั้ง")


if __name__ == "__main__":
    try:
        bot_info = bot.get_me()
        print(f"Bot started as @{bot_info.username}")
        bot.infinity_polling(skip_pending=True)
    except Exception as e:
        print("Bot failed to start:", e)