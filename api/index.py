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
        if not data or 'image' not in data:
            return jsonify({'error': 'No image'}), 400
            
        # Decodeer afbeelding
        image_data = data['image'].split(',')[1]
        img = Image.open(io.BytesIO(base64.b64decode(image_data)))
        
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # HIER IS DE MAGIE: Een veel betere instructie
        prompt = f"""
        Je bent een visuele assistent voor blinden. Bekijk deze foto van een: {data.get('product', 'product')}.
        
        Jouw ENIGE doel is de houdbaarheidsdatum vinden (zoals EXP, THT, BB, of gewoon een datum).
        
        Instructies:
        1. Zoek agressief naar cijfers die op een datum lijken (dd-mm-jj of mm/jj).
        2. De datum kan verticaal staan, gestippeld zijn, of moeilijk leesbaar.
        3. Negeer streepjescodes of andere nummers.
        4. Als je twijfelt, gok de meest waarschijnlijke datum.
        
        ANTWOORD:
        - Heb je een datum? -> Antwoord ALLEEN de datum in het Engels (bijv: "15 March 2025"). Geen hele zinnen.
        - Zie je écht niks? -> Antwoord ALLEEN met het woord: "NULL"
        """
        
        response = model.generate_content([prompt, img])
        result = response.text.strip()
        
        # Check of hij NULL zegt
        found = "NULL" not in result
        
        return jsonify({
            'date_found': found,
            'date': result if found else "",
            'speech_text': f"The date is {result}" if found else "No date found, please try rotating the package."
        })
            
    except Exception as e:
        # Dit helpt ons debuggen als er toch iets mis is
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run()
