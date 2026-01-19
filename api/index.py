from flask import Flask, request, jsonify
from flask_cors import CORS
import google.generativeai as genai
import base64
import io
import os
from PIL import Image

app = Flask(__name__)
CORS(app)

# Haal de sleutel op uit Vercel instellingen
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
genai.configure(api_key=GEMINI_API_KEY)

@app.route('/api/analyze', methods=['POST'])
def analyze():
    try:
        data = request.json
        if not data or 'image' not in data:
            return jsonify({'error': 'No image'}), 400
            
        # 1. Plaatje decoderen
        image_data = data['image'].split(',')[1]
        img = Image.open(io.BytesIO(base64.b64decode(image_data)))
        
        # 2. Gemini Model laden
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # 3. De Verbeterde Instructie (Prompt)
        prompt = f"""
        Je bent een hulp voor blinden. Bekijk deze foto van: {data.get('product', 'product')}.
        ZOEK DE HOUDBAARHEIDSDATUM (THT/EXP/BB).
        
        Instructies:
        - Zoek agressief naar datums (dd-mm-jj, mm/jjjj, etc).
        - Het kan gedraaid staan of onduidelijk zijn.
        - Negeer barcodes.
        
        ANTWOORD FORMAAT:
        - Datum gevonden? -> Antwoord ALLEEN de datum in het Engels (bijv: "12 Dec 2025").
        - Geen datum? -> Antwoord ALLEEN: "NULL"
        """
        
        response = model.generate_content([prompt, img])
        result = response.text.strip()
        
        # 4. Resultaat verwerken
        found = "NULL" not in result
        
        return jsonify({
            'date_found': found,
            'date': result if found else "",
            'speech_text': f"The date is {result}" if found else "No date found, try turning the package."
        })
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Nodig voor Vercel om te starten
if __name__ == '__main__':
    app.run()
