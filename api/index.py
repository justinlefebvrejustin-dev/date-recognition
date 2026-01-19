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

# --- LET OP: GEEN ROUTE VOOR '/' HIERONDER ---

@app.route('/api/analyze', methods=['GET', 'POST'])
def analyze():
    # Als iemand dit via de browser probeert te openen (GET request)
    if request.method == 'GET':
        return "IK BEN WAKKER - API WERKT (Maar ga terug naar de homepage!)"

    try:
        data = request.json
        # Check of er data is
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
        Datum gevonden? -> Schrijf ALLEEN de datum in Engels (12 March 2025).
        Geen datum? -> "Geen datum gevonden".
        """
        
        response = model.generate_content([prompt, img])
        result_text = response.text.strip()
        
        if "Geen datum gevonden" in result_text:
            return jsonify({'date_found': False, 'speech_text': "No date found."})
        else:
            return jsonify({'date_found': True, 'date': result_text, 'speech_text': f"Date is {result_text}"})
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Dit is nodig voor Vercel
app = app
