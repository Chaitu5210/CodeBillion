from Telegram.retrive_telegram_messages import retrive_telegram_messages
from Telegram.send_to_telegram import send_to_telegram
from Helpers.telegram_data_handler import format_telegram_message
from Helpers.score_generator import calculate_result_score
from Helpers.json_updator import json_updator
from memory import Memory
from json_extractor import text_to_json_retriver
from constants import prompt_templates
import threading
def consume_forever():
    while True:
        message = Memory.get()
        print("New Message Has Been Received...")
        if message:
            print("Sending The Message To The Analyzer...")
            company_data = text_to_json_retriver(prompt_templates, message)
            company_score = calculate_result_score(company_data)
            company_data = json_updator(company_data, company_score)
            telegram_message = format_telegram_message(company_data)
            print("Sending The Analyzed Message To Telegram Channel...")
            send_to_telegram(telegram_message)
            print("")



def orchestrate__strategy():
    print("Starting Orchestration For Strategy 1...")
    consumer_thread = threading.Thread(target=consume_forever, daemon=True)
    consumer_thread.start()
    print("Consumer thread started, now starting Telegram bot...")

    retrive_telegram_messages()

if __name__ == "__main__":
    orchestrate__strategy()