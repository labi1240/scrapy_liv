import json
import logging

import openai
from scrapy.utils.project import get_project_settings

# Set up basic logging
logging.basicConfig(level=logging.ERROR)

def process_data_with_openai(data):
    settings = get_project_settings()
    openai_api_key = settings.get('OPENAI_API_KEY')
    try:
        response = openai.Completion.create(
            engine="davinci",
            prompt=json.dumps(data),
            temperature=0.5,
            max_tokens=1024,
            top_p=1.0,
            frequency_penalty=0.0,
            presence_penalty=0.0,
            api_key=openai_api_key
        )
        return response
    except Exception as e:
        logging.error(f"Error processing data with OpenAI: {e}")
        return None
