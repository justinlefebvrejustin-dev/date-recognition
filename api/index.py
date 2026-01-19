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

@app.route('/api/analyze', methods=['POST'])
def analyze():
    try:
        data = request.json
        image_data = data['image'].split(',')[1]
        product_name = data.get('product', 'Product')
        
        image_bytes = base64.b64decode(image_data)
        img = Image.open(io.BytesIO(image_bytes))
        
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        prompt = f"""
        Dit is een: {product_name}.
        Zoek de houdbaarheidsdatum (EXP/BBE/THT).
        
        INSTRUCTIES:
        1. Datum gevonden? -> Schrijf ALLEEN de datum in Nederlandse woorden.
           Bijvoorbeeld: "twaalf maart tweeduizend vijfentwintig"
           Noem NIET de productnaam.
        
        2. Geen datum? -> Antwoord EXACT: "Geen datum gevonden".
        """
        
        response = model.generate_content([prompt, img])
        result_text = response.text.strip()
        
        if "Geen datum gevonden" in result_text:
            return jsonify({
                'date_found': False,
                'speech_text': f"Geen datum gevonden."
            })
        else:
            return jsonify({
                'date_found': True,
                'date': result_text,
                'speech_text': f"De datum is {result_text}"
            })
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500
