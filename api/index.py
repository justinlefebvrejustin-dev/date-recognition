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

# --- JOUW WEBSITE HTML ZIT NU HIER IN ---
HTML_PAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Date Recognition</title>
    <script src="https://cdn.jsdelivr.net/npm/@tensorflow/tfjs@1.3.1/dist/tf.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/@teachablemachine/image@0.8/dist/teachablemachine-image.min.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, sans-serif; background: #ffffff; min-height: 100vh; padding: 20px; color: #1a1a1a; }
        .container { max-width: 600px; margin: 0 auto; padding: 40px 20px; }
        h1 { font-size: 2.5em; margin-bottom: 10px; font-weight: 600; }
        .subtitle { color: #666; margin-bottom: 40px; font-size: 1.1em; }
        .status { padding: 16px; border-radius: 8px; margin-bottom: 30px; display: none; border-left: 4px solid; }
        .status.info { background: #e3f2fd; border-color: #2196F3; color: #1565c0; display: block; }
        .status.success { background: #e8f5e9; border-color: #4CAF50; color: #2e7d32; }
        .status.error { background: #ffebee; border-color: #f44336; color: #c62828; }
        .status.warning { background: #fff3e0; border-color: #ff9800; color: #e65100; }
        #video-container { width: 100%; margin-bottom: 30px; border-radius: 8px; overflow: hidden; display: none; background: #000; }
        #video { width: 100%; display: block; }
        button { width: 100%; padding: 18px; font-size: 1.1em; border: none; border-radius: 8px; cursor: pointer; margin-bottom: 15px; }
        #startBtn { background: #2196F3; color: white; }
        #captureBtn { background: #2196F3; color: white; display: none; }
        .result-container { display: none; margin-top: 30px; padding: 24px; background: #f5f5f5; border-radius: 8px; border-left: 4px solid #2196F3; }
        .result-container.show { display: block; }
        .advice { margin-top: 20px; padding: 16px; background: white; border-radius: 6px; border-left: 3px solid #2196F3; }
        .loading { display: none; text-align: center; margin: 30px 0; }
        .loading.show { display: block; }
        .spinner { border: 3px solid #f3f3f3; border-top: 3px solid #2196F3; border-radius: 50%; width: 50px; height: 50px; animation: spin 1s linear infinite; margin: 0 auto 15px; }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
        #preview-img { width: 100%; border-radius: 8px; margin-bottom: 20px; display: none; }
        .footer { text-align: center; color: #999; margin-top: 60px; font-size: 0.9em; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Date Recognition</h1>
        <p class="subtitle">Scan packaging to recognize expiration dates via voice</p>
        <div id="status" class="status info">Loading models...</div>
        <div id="video-container"><video id="video" autoplay playsinline></video></div>
        <button id="startBtn" style="display:none;">Start Camera</button>
        <button id="captureBtn">Scan Product</button>
        <div class="loading" id="loading"><div class="spinner"></div><p>Analyzing...</p></div>
        <div class="result-container" id="result">
            <img id="preview-img" alt="Scanned photo">
            <div class="result-text" id="result-text"></div>
        </div>
    </div>
    <div class="footer">Created for better accessibility</div>
    <script>
        const MODEL_URL = 'https://teachablemachine.withgoogle.com/models/hgp4ntk2z/';
        const adviceLibrary = {
            "Butter": "This is butter. Look on top of the lid.",
            "Soda can": "This is a soda can. The date is usually at the bottom.",
            "Slices of meat": "This is sliced meat. The date is usually on top of the package.",
            "Milk": "This is milk. The date is usually on the top rim or cap.",
            "Snack": "This is a snack. Look for a white box on the back.",
            "Background": "I don't see a product, please hold it closer to the camera."
        };
        let stream = null; let model = null;
        const video = document.getElementById('video');
        const startBtn = document.getElementById('startBtn');
        const captureBtn = document.getElementById('captureBtn');
        const status = document.getElementById('status');
        const loading = document.getElementById('loading');
        const resultContainer = document.getElementById('result');
        const resultText = document.getElementById('result-text');
        const videoContainer = document.getElementById('video-container');
        const previewImg = document.getElementById('preview-img');

        function updateStatus(message, type = 'info') {
            status.textContent = message;
            status.className = `status ${type}`;
            status.style.display = 'block';
        }

        async function loadModel() {
            try {
                const modelURL = MODEL_URL + 'model.json';
                const metadataURL = MODEL_URL + 'metadata.json';
                model = await tmImage.load(modelURL, metadataURL);
                updateStatus('Model loaded! Click "Start Camera"', 'success');
                startBtn.style.display = 'block';
            } catch (error) {
                updateStatus('Error loading model: ' + error, 'error');
            }
        }

        startBtn.addEventListener('click', async () => {
            try {
                stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: 'environment' } });
                video.srcObject = stream;
                videoContainer.style.display = 'block';
                captureBtn.style.display = 'block';
                startBtn.style.display = 'none';
                updateStatus('Camera active', 'success');
            } catch (err) { updateStatus('Camera access denied.', 'error'); }
        });

        captureBtn.addEventListener('click', async () => {
            const canvas = document.createElement('canvas');
            canvas.width = video.videoWidth; canvas.height = video.videoHeight;
            canvas.getContext('2d').drawImage(video, 0, 0);
            const imageData = canvas.toDataURL('image/jpeg', 0.8);
            previewImg.src = imageData; previewImg.style.display = 'block';
            if (stream) stream.getTracks().forEach(track => track.stop());
            videoContainer.style.display = 'none'; captureBtn.style.display = 'none';
            loading.classList.add('show'); updateStatus('Analyzing...', 'info');

            try {
                const img = new Image(); img.src = imageData; await img.decode();
                const prediction = await model.predict(img);
                const topPrediction = prediction.reduce((max, p) => p.probability > max.probability ? p : max);
                
                const response = await fetch('/api/analyze', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ image: imageData, product: topPrediction.className })
                });
                const result = await response.json();
                loading.classList.remove('show');

                if (result.date_found) {
                    resultText.innerHTML = `<strong>Date found</strong>${result.date}`;
                    updateStatus('Success', 'success');
                    speak(result.speech_text);
                } else {
                    const advice = adviceLibrary[topPrediction.className] || "Try rotating the product.";
                    resultText.innerHTML = `<strong>No date found</strong><div class="advice">💡 ${advice}</div>`;
                    updateStatus('No date found', 'warning');
                    speak(`No date found. ${advice}`);
                }
                resultContainer.classList.add('show');
                startBtn.style.display = 'block'; startBtn.textContent = 'Scan again';
            } catch (error) {
                loading.classList.remove('show');
                updateStatus('Error: ' + error, 'error');
                startBtn.style.display = 'block';
            }
        });

        function speak(text) {
            if ('speechSynthesis' in window) {
                const utterance = new SpeechSynthesisUtterance(text);
                utterance.lang = 'en-US';
                speechSynthesis.speak(utterance);
            }
        }
        
        startBtn.addEventListener('click', () => {
            if (startBtn.textContent.includes('Scan')) {
                resultContainer.classList.remove('show'); previewImg.style.display = 'none';
                startBtn.textContent = 'Start Camera';
            }
        });
        loadModel();
    </script>
</body>
</html>
"""

@app.route('/', methods=['GET'])
def home():
    return make_response(HTML_PAGE)

@app.route('/api/analyze', methods=['POST'])
def analyze():
    try:
        data = request.json
        if not data or 'image' not in data: return jsonify({'error': 'No image'}), 400
        image_data = data['image'].split(',')[1]
        product_name = data.get('product', 'Product')
        img = Image.open(io.BytesIO(base64.b64decode(image_data)))
        model = genai.GenerativeModel('gemini-1.5-flash')
        prompt = f"Dit is: {product_name}. Vind de houdbaarheidsdatum. Antwoord ALLEEN datum in Engels of 'Geen datum gevonden'."
        response = model.generate_content([prompt, img])
        result = response.text.strip()
        
        if "Geen datum gevonden" in result:
            return jsonify({'date_found': False, 'speech_text': "No date found."})
        return jsonify({'date_found': True, 'date': result, 'speech_text': f"Date is {result}"})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run()
