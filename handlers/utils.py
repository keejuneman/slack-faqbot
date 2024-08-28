import json

def load_faq_data():
    with open('data/faq.json', 'r', encoding='utf-8') as f:
        return json.load(f)
