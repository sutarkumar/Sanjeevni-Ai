import os
import base64
from groq import Groq

GROQ_API_KEY = os.environ["GROQ_API_KEY"]
MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"

client = Groq(api_key=GROQ_API_KEY)


def encode_image(image_path: str) -> str:
    """Return base64-encoded JPEG for LLM ingestion."""
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode()


def analyze_image_with_query(query: str, encoded_image: str) -> str:
    resp = client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": query},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{encoded_image}"
                        },
                    },
                ],
            }
        ],
    )

    content = resp.choices[0].message.content
    if content is None:
        return "No response from model"

    return content.strip()