from flask import current_app
# import json
import requests


def translate(text, dest_language):
    """
    """
    if 'MS_TRANSLATOR_KEY' not in current_app.config or not current_app.config['MS_TRANSLATOR_KEY']:
        return 'Error: the translation service is not configured.'

    auth = {
        'Ocp-Apim-Subscription-Key': current_app.config['MS_TRANSLATOR_KEY'],
        'Content-Type': 'application/json'
    }

    # r = requests.post(
    #     'https://api.cognitive.microsofttranslator.com/translate?api-version=3.0&from={}&to={}'.format(
    #         source_language, dest_language
    #     ), headers=auth, json=[{'Text': text}]
    # )

    r = requests.post(
        'https://api.cognitive.microsofttranslator.com/translate?api-version=3.0&to={}'.format(
            dest_language
        ), headers=auth, json=[{'Text': text}]
    )

    # r = requests.get(
    #     'https://api.microsofttranslator.com/v2/Ajax.svc/Translate?text={}&from={}&to={}'.format(
    #         text, source_language, dest_language
    #     ), headers=auth
    # )

    if r.status_code != 200:
        return 'Error: the translation service failed.'

    # utf-8-sig is Microsoft variant of utf-8
    # return json.loads(r.content.decode('utf-8-sig'))
    response = r.json()
    return response[0]['translations'][0]['text']
