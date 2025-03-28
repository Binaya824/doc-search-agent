from flask import Flask, request, jsonify
from flask_cors import CORS
from index import send_message
import os
from werkzeug.utils import secure_filename
from extractor import extract_pdf_content , format_json , generate_html_from_json
import json

app = Flask(__name__)
CORS(app)


# Configure upload folder and allowed extensions
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'html', 'docx'}

# Ensure upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

def allowed_file(filename):
    """
    Check if the uploaded file has an allowed extension.
    
    :param filename: Name of the file to check
    :return: Boolean indicating if file is allowed
    """
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/api/model', methods=['POST'])
def api():
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400
    
    prompt = data.get("prompt")
    content = data.get("content")
    
    response = send_message(content , prompt)
    return jsonify({
        "message": "Data received",
        "data": response
    }), 200


@app.route('/api/upload', methods=['POST'])
def upload_file():
    """
    Handle file uploads with validation and error handling.
    
    :return: JSON response with upload status and file details
    """
    # Check if the post request has the file part
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    
    file = request.files['file']

    print("file ))))))))))))))))" , file)
    
    # If user does not select file, browser also submit an empty part without filename
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    
    # Check if file is allowed
    if file and allowed_file(file.filename):
        # Secure the filename to prevent security issues
        filename = secure_filename(file.filename)
        
        # Save the file
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        result = extract_pdf_content(filepath)
        print("result ))))))))))))))))" , result)
        formatted_result = format_json(result)
        html = generate_html_from_json(formatted_result)
        print(html)
        # print(json.dumps(formatted_result, indent=2))
        
        return jsonify({
            "message": "File uploaded successfully",
            "filename": filename,
            "filepath": filepath,
            "html": html
        }), 200
    
    return jsonify({"error": "File type not allowed"}), 400


@app.route('/api', methods=['GET'])
def api_get():
    return jsonify({
        "message": "GET request received",
    }), 200

if __name__ == '__main__':
    app.run(debug=True)