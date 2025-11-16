import os
from dotenv import load_dotenv
from groq import Groq
import json

load_dotenv()

def text_to_json_retriver(prompt: str, company_data: str):
    client = Groq(api_key=os.getenv("llm_api_key"))

    final_prompt = f"""{prompt}
                <company_text>
                {company_data}
                </company_text>
                """

    completion = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": "You are a strict JSON extraction model."},
            {"role": "user", "content": final_prompt}
        ],
        temperature=0,
        max_completion_tokens=2048,
        top_p=1,
        stream=True,
    )

    chunks = []
    for chunk in completion:
        delta = chunk.choices[0].delta
        if delta is not None and getattr(delta, "content", None):
            chunks.append(delta.content)

    output = "".join(chunks).strip()
    if not output:
        raise ValueError("LLM returned empty output, cannot parse JSON")
    if output.startswith("```"):
        output = output.split("```", 1)[1]
    if "```" in output:
        output = output.rsplit("```", 1)[0]
    output = output.strip()
    return json.loads(output)

