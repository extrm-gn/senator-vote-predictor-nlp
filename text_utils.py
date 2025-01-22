import requests


def get_translation(text, target_language="en"):
    # Make the API request
    url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=auto&tl={target_language}&dt=t&q={text}"
    response = requests.get(url)

    # Check if the response status is OK
    if response.status_code != 200:
        return f"Error: Unable to fetch translation (Status code: {response.status_code})"

    try:
        # Parse the JSON response
        data = response.json()

        # Extract translated text from the first sentence
        translated_text = data[0][0][0]  # Translation

        return translated_text

    except (ValueError, IndexError, TypeError) as e:
        return f"Error processing response: {e}"

