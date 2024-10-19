import logging
from flask import Flask, request, send_from_directory, jsonify
from flask_cors import CORS
from gradio_client import Client, file
import os
import tempfile
import base64

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)  # This will enable CORS for all routes

# Get the directory of the current script
current_dir = os.path.dirname(os.path.abspath(__file__))

@app.route('/')
def serve_html():
    return send_from_directory(current_dir, 'index.html')

@app.route('/generated_audio.wav')
def serve_audio():
    return send_from_directory(current_dir, 'generated_audio.wav')

@app.route('/generate-audio', methods=['POST'])
def generate_audio():
    client = Client("tonyassi/voice-clone")
    
    data = request.json
    text = data.get('text', '')
    ref_audio_base64 = data.get('refAudio', '')

    logger.debug(f"Received request: text={text}, ref_audio_length={len(ref_audio_base64)}")

    try:
        # Save the base64 audio to a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_audio:
            temp_audio.write(base64.b64decode(ref_audio_base64))
            temp_audio_path = temp_audio.name

        result = client.predict(
            text=text,
            audio=file(temp_audio_path),
            api_name="/predict"
        )
        logger.debug(f"Gradio client result: {result}")

        if isinstance(result, str) and os.path.exists(result):
            new_file_path = os.path.join(current_dir, "generated_audio.wav")
            os.replace(result, new_file_path)
            logger.info(f"Audio generated successfully: {new_file_path}")
            return jsonify({"success": True, "file": "generated_audio.wav"})
        else:
            error_msg = "Unexpected result format from API or file not found"
            logger.error(error_msg)
            return jsonify({"success": False, "error": error_msg})

    except Exception as e:
        error_msg = f"Gradio client error: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return jsonify({"success": False, "error": error_msg})
    finally:
        # Clean up the temporary file
        if 'temp_audio_path' in locals():
            os.unlink(temp_audio_path)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))