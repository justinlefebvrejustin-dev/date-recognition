from flask import Flask, request, jsonify
from flask_cors import CORS
import google.generativeai as genai
import base64
import io
import os
from PIL import Image

app = Flask(__name__)
CORS(app)

GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
genai.configure(api_key=GEMINI_API_KEY)

# HIER IS DE FIX: 3 routes voor dezelfde functie
@app.route('/api/analyze', methods=['GET', 'POST'])
@app.route('/analyze', methods=['GET', 'POST'])
def analyze():
    # Even checken of het een GET request is (voor testen in browser)
    if request.method == 'GET':
        return jsonify({"status": "API is online! Gebruik POST om te scannen."})

    try:
        data = request.json
        if not data or 'image' not in data:
            return jsonify({'error': 'Geen afbeelding ontvangen'}), 400
            
        image_data = data['image'].split(',')[1]
        product_name = data.get('product', 'Product')
        
        image_bytes = base64.b64decode(image_data)
        img = Image.open(io.BytesIO(image_bytes))
        
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        prompt = f"""
        Dit is een: {product_name}.
        Zoek de houdbaarheidsdatum (EXP/BBE/THT).
        
        INSTRUCTIES:
        1. Datum gevonden? -> Schrijf ALLEEN de datum in Engelse woorden (bijv: "12 March 2025").
           Noem NIET de productnaam.
        
        2. Geen datum? -> Antwoord EXACT: "Geen datum gevonden".
        """
        
        response = model.generate_content([prompt, img])
        result_text = response.text.strip()
        
        if "Geen datum gevonden" in result_text:
            return jsonify({
                'date_found': False,
                'speech_text': f"No date found."
            })
        else:
            return jsonify({
                'date_found': True,
                'date': result_text,
                'speech_text': f"The date is {result_text}"
            })
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run()
