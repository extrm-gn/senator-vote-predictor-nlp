import requests
import time
from tenacity import retry, stop_after_attempt, wait_fixed

@retry(stop=stop_after_attempt(3), wait=wait_fixed(2))  # Retry 3 times with a 2-second interval
def translate_text(text, target_language="en", pause_duration=0.5):
    """
    Translates the given text to the target language using the Google Translate API.
    Retries on failure with a fixed interval.
    """
    url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=auto&tl={target_language}&dt=t&q={text}"

    # Timeout for the request
    timeout = 5  # seconds

    # Send the GET request
    response = requests.get(url, timeout=timeout)
    time.sleep(pause_duration)

    # Check if the request was successful
    if response.status_code == 200:
        # Parse the response JSON data
        translation_data = response.json()
        translated_text = translation_data[0][0][0]
        print(f"translated {translated_text}")
        return translated_text
    else:
        raise Exception(f"Error: Unable to fetch translation. Status code: {response.status_code}")



