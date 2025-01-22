import requests

def translate_text(text, target_language="en"):
    # URL of the Google Translate API endpoint
    url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=auto&tl={target_language}&dt=t&q={text}"

    # Send the GET request
    response = requests.get(url)

    # Check if the request was successful
    if response.status_code == 200:
        # Parse the response JSON data
        translation_data = response.json()
        translated_text = translation_data[0][0][0]
        return translated_text
    else:
        return "Error: Unable to fetch translation."

# Example usage
text_to_translate = "anong ginagawa mo boss"
translated_text = translate_text(text_to_translate)
print(f"Translated Text: {translated_text}")
