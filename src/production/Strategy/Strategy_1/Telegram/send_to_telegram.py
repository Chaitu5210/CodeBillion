import requests

BOT_TOKEN = "8212881730:AAESYCH_R3xs1qE1d2kBgTvGPZNc5zchHhg"
CHANNEL_ID = "-1003471829850"

def send_to_telegram(text: str):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHANNEL_ID,
        "text": text,
    }
    print("Sending message to Telegram channel...")
    response = requests.post(url, data=payload)
    if response.status_code == 200:
        print("Message sent successfully!")
    else:
        print("Failed to send message.")