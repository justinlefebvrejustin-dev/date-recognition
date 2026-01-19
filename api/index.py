from flask import Flask, request, jsonify, make_response
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

# 1. DE HOMEPAGE ROUTE (Dit fixt je 404 error!)
@app.route('/', methods=['GET'])
def home():
    # We lezen het index.html bestand uit de map erboven
    try:
        # Pad bepalen naar index.html (staat 1 mapje hoger dan api/)
        current_dir = os.path.dirname(os.path.abspath(__file__))
        html_path = os.path.join(current_dir, '..', 'index.html')
        
        with open(html_path, 'r', encoding='utf-8') as f:
            content = f.read()
            return make_response(content)
    except Exception as e:
        return f"Error loading site: {str(e)}", 500

# 2. DE API ROUTE (Voor het scannen)
@app.route('/api/analyze', methods=['POST'])
@app.route('/analyze', methods=['POST'])
def analyze():
    try:
        data = request.json
        if not data or 'image' not in data:
            return jsonify({'error': 'No image data'}), 400
            
        image_data = data['image'].split(',')[1]
        product_name = data.get('product', 'Product')
        
        image_bytes = base64.b64decode(image_data)
        img = Image.open(io.BytesIO(image_bytes))
        
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        prompt = f"""
        Dit is een: {product_name}.
        Zoek de houdbaarheidsdatum.
        
        Regels:
        1. Datum gevonden? -> Schrijf ALLEEN de datum in het Engels (bijv: "12 March 2025").
        2. Geen datum? -> Antwoord EXACT: "Geen datum gevonden".
        """
        
        response = model.generate_content([prompt, img])
        result_text = response.text.strip()
        
        if "Geen datum gevonden" in result_text:
            return jsonify({
                'date_found': False,
                'speech_text': "No date found. Try turning the product."
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
