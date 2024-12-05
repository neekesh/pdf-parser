import os
from flask import Flask, request, jsonify, abort, send_file
from pdf_parser import extract_tables, UUID
from werkzeug.utils import secure_filename
import magic
import zipfile
from io import BytesIO
from threading import Thread

# Initialize Flask application
app = Flask(__name__)

# Set up directories for uploaded PDFs and generated CSVs
current_dir = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(current_dir, 'uploads', 'pdf')  # Directory for uploaded PDFs
CSV_FOLDER = os.path.join(current_dir, 'uploads', 'csv')    # Directory for extracted CSVs

# Ensure the directories exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(CSV_FOLDER, exist_ok=True)

# Configure Flask app for upload and CSV directories
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['CSV_FOLDER'] = CSV_FOLDER

# Helper Function: Check if a file is a valid PDF
def is_pdf(file) -> bool:
    """
    Determines if a file is a valid PDF based on its MIME type.

    Args:
        file: A file object to check.

    Returns:
        bool: True if the file is a PDF, otherwise False.
    """
    mime = magic.Magic(mime=True)
    mime_type = mime.from_buffer(file.read(1024))  # Read first 1024 bytes
    file.seek(0)  # Reset file pointer after reading
    return mime_type == 'application/pdf'

@app.route('/', methods=["POST"])
def home():
    """
    Endpoint to upload multiple PDF files and process them to extract tables into CSVs.

    Request:
        POST with multipart/form-data containing a 'files' field with one or more PDF files.

    Returns:
        JSON response with a list of unique IDs and filenames for processed files.
    """
    # Check if 'files' is part of the request
    if 'files' not in request.files:
        return jsonify({"error": "No files part in the request"}), 400

    files = request.files.getlist('files')  # Get list of files from the request
    if not files or files[0].filename == '':
        return jsonify({"error": "No files selected for upload"}), 400

    response = []
    for file in files:
        # Validate file type
        if not is_pdf(file):
            return jsonify({"message": "All files should be PDFs"}), 400

        # Secure the filename and save the file to the upload folder
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        # Generate a unique ID for the file and process it
        uid = UUID()
        response.append(
            {
                "uid": uid,
                "file_name": filename,
            }
        )
        # Extract tables from the PDF and save the CSVs to the appropriate folder
        Thread(
            target=extract_tables,
             args=(f'{app.config["UPLOAD_FOLDER"]}/{filename}', f'{app.config["CSV_FOLDER"]}/{uid}'),
        ).start()


    return jsonify({"data": response}), 200

@app.route("/<uid>", methods=["GET"])
def get_csv(uid):
    """
    Endpoint to retrieve CSV(s) for a processed PDF.

    Args:
        uid: Unique ID associated with the processed file.

    Returns:
        - Single CSV file for download if only one CSV is generated.
        - ZIP file containing all CSVs if multiple are generated.
        - Error response if processing failed or files are missing.
    """
    csv_dir = f'{app.config["CSV_FOLDER"]}/{uid}'

    # Check the status file for success or error
    try:
        with open(f"{csv_dir}/response.txt", "r") as file:
            lines = file.readlines()
            first_line = lines[0].strip()

            if first_line != "success":
                # Extract error details from the status file
                error_msg = first_line.split(",")
                return jsonify({"error": error_msg[1]}), int(error_msg[0])
    except FileNotFoundError:
        return jsonify({"error": "Status file not found"}), 404

    # Gather all CSV files related to the UID
    all_items = os.listdir(csv_dir)
    csv_files = [
        os.path.join(csv_dir, item)
        for item in all_items
        if os.path.isfile(os.path.join(csv_dir, item)) and item.endswith(".csv")
    ]

    if len(csv_files) == 1:
        # If there's only one CSV, send it directly
        return send_file(
            csv_files[0],
            as_attachment=True, 
            download_name=os.path.basename(csv_files[0]), 
            mimetype='application/csv',
            )

    # If multiple CSV files exist, package them into a ZIP file
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for file_path in csv_files:
            if os.path.exists(file_path):
                zip_file.write(file_path, os.path.basename(file_path))
            else:
                return jsonify({"error": f"File {file_path} not found"}), 404

    zip_buffer.seek(0)  # Reset the buffer position
    return send_file(
        zip_buffer, 
        as_attachment=True,
        download_name="tables.zip",
        mimetype='application/zip',
        )

if __name__ == '__main__':
    # Run the Flask app in debug mode
    app.run(debug=True)
