from pathlib import Path
import os

from dotenv import load_dotenv
from flask import Flask, jsonify, request, render_template
from werkzeug.utils import secure_filename
from ai import init_vertex_ai, get_image_hashtags

app = Flask(__name__)

# Load environment variables based on environment
if os.getenv('FLASK_ENV') == 'production':
    load_dotenv('.env')
else:
    load_dotenv('.env.dev')

# Initialize Vertex AI
GOOGLE_CLOUD_PROJECT = os.getenv('GOOGLE_CLOUD_PROJECT')
if not GOOGLE_CLOUD_PROJECT:
    raise ValueError("GOOGLE_CLOUD_PROJECT environment variable is required")
init_vertex_ai(GOOGLE_CLOUD_PROJECT)

# Configure upload folder
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

# Create uploads directory if it doesn't exist

Path(UPLOAD_FOLDER).mkdir(exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    """
    Check if the given filename has an allowed extension.

    Args:
        filename (str): The name of the file to check.

    Returns:
        bool: True if the file has an allowed extension, False otherwise.
    """
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/hashtags', methods=['POST'])
def upload_image():
    # Check if the post request has the file part
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    file = request.files['file']

    # If user does not select file, browser also
    # submit an empty part without filename
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = Path(app.config['UPLOAD_FOLDER']) / filename
        file.save(file_path)

        try:
            # Get hashtags from the image
            hashtags = get_image_hashtags(file_path)
            return jsonify({'hashtags': hashtags})
        except Exception as e:
            return jsonify({'error': f'Error analyzing image: {str(e)}'}), 500

    return jsonify({'error': 'File type not allowed'}), 400


@app.route("/")
def index():
    print("Hello, pwd: ", os.getcwd())
    return render_template("index.html")

if __name__ == '__main__':
    app.run(debug=True)
