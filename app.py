import tempfile
import os
from flask import Flask, request, send_file, jsonify
from gradio_client import Client

app = Flask(__name__)

@app.route('/generate-audio', methods=['POST'])
def generate_audio():
    client = Client("tonyassi/voice-clone")
    
    data = request.json
    text = data.get('text', '')
    ref_audio_base64 = data.get('refAudio', '')

    try:
        # Create a temporary directory for our files
        with tempfile.TemporaryDirectory() as temp_dir:
            # Save the reference audio to a temporary file
            temp_audio_path = os.path.join(temp_dir, 'ref_audio.wav')
            with open(temp_audio_path, 'wb') as f:
                f.write(base64.b64decode(ref_audio_base64))

            # Generate the audio
            result = client.predict(
                text=text,
                audio=temp_audio_path,
                api_name="/predict"
            )

            # If the result is a file path, it's likely on a different file system
            # So we need to copy it to our temporary directory
            if isinstance(result, str) and os.path.exists(result):
                output_path = os.path.join(temp_dir, 'generated_audio.wav')
                shutil.copy(result, output_path)
            else:
                return jsonify({"success": False, "error": "Unexpected result format from API"})

            # Send the file directly from the temporary directory
            return send_file(output_path, as_attachment=True, download_name='generated_audio.wav')

    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))