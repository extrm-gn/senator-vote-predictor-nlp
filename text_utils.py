import requests
import time

def get_translation(text, target_language="en", pause_duration=0):
    # Make the API request
    url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=auto&tl={target_language}&dt=t&q={text}"
    response = requests.get(url)

    # Check if the response status is OK
    timeout = 1  # seconds

    # Send the GET request
    response = requests.get(url, timeout=timeout)
    time.sleep(pause_duration)

    # Check if the request was successful
    if response.status_code == 200:
        # Parse the response JSON data
        translation_data = response.json()
        translated_text = translation_data[0][0][0]
        print(f"{text} *** {translated_text}")
        return translated_text
    else:
        raise Exception(f"Error: Unable to fetch translation. Status code: {response.status_code}")

