def format_telegram_message(company_data: dict) -> str:
    interp = company_data.get("interpretation", {})

    message = (
        f"Company Name: {company_data.get('company_name', 'N/A')}\n"
        f"Results Quality: {interp.get('result_quality', 'N/A')}\n"
        f"Key Positives: {', '.join(interp.get('key_positives', []))}\n"
        f"Key Negatives: {', '.join(interp.get('key_negatives', []))}\n"
        f"Summary: {company_data.get('summary', 'N/A')}\n"
        f"Sentiment: {interp.get('overall_sentiment', 'N/A')}\n"
        f"Final Score: {company_data.get('final_score', 'N/A')}\n"
    )
    return message