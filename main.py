import os
from flask import Flask, request, jsonify, send_file
from utils import extract_tables, UUID, is_pdf
from werkzeug.utils import secure_filename
import zipfile
from io import BytesIO
from threading import Thread

# Initialize Flask application
app = Flask(__name__)

# Set up directories for uploaded PDFs and generated CSVs
current_dir = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(current_dir, 'uploads', 'pdf')  # Directory for uploaded PDFs
CSV_FOLDER = os.path.join(current_dir, 'uploads', 'csv')    # Directory for extracted CSVs

# Ensure the directories exist, create them if they don't
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(CSV_FOLDER, exist_ok=True)

# Configure Flask app for upload and CSV directories
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['CSV_FOLDER'] = CSV_FOLDER

@app.route('/', methods=["POST"])
def home():
    """
    Endpoint to upload multiple PDF files and process them to extract tables into CSVs.

    Request:
        POST with multipart/form-data containing a 'files' field with one or more PDF files.

    Returns:
        JSON response with a list of unique IDs and filenames for processed files, or error message.
    """
    # Ensure 'files' field exists in the request
    if 'files' not in request.files:
        return jsonify({"error": "No files part in the request"}), 400  # Return error if 'files' not present

    files = request.files.getlist('files')  # Get list of uploaded files
    if not files or files[0].filename == '':
        return jsonify({"error": "No files selected for upload"}), 400  # Handle empty file uploads

    response = []
    for file in files:
        # Validate file type (must be a PDF)
        if not is_pdf(file):
            return jsonify({"message": "All files should be PDFs"}), 400  # Return error if file is not a PDF

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
        
        # Start a separate thread for processing to avoid blocking the main thread
        Thread(
            target=extract_tables,
            args=(f'{app.config["UPLOAD_FOLDER"]}/{filename}', f'{app.config["CSV_FOLDER"]}/{uid}')
        ).start()

    return jsonify({"data": response}), 200  # Return a list of processed files with their unique IDs

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
    csv_dir = f'{app.config["CSV_FOLDER"]}/{uid}'  # Directory where CSV files are stored

    # Check the status file for success or error during processing
    try:
        with open(f"{csv_dir}/response.txt", "r") as file:
            lines = file.readlines()
            first_line = lines[0].strip()  # Get the first line to check status

            try:
                if first_line != "success":
                    # Attempt to split the first line and handle possible errors
                    msg = first_line.split(",")
                    if len(msg) < 2:
                        # Handle the case where the error message format is incorrect
                        raise ValueError("Error message format is invalid in the response file")
                    return jsonify({"error": msg[1]}), int(msg[0])
            except ValueError as e:
                # Handle cases where splitting the error message or parsing fails
                return jsonify({"error": f"Error parsing response file: {str(e)}"}), 400
            except Exception as e:
                # Catch any other unexpected errors
                return jsonify({"error": f"An unexpected error occurred: {str(e)}"}), 500

    except FileNotFoundError:
        return jsonify({"error": "Status file not found"}), 404  # Return error if status file is missing

    # Gather all CSV files associated with this unique ID
    all_items = os.listdir(csv_dir)
    csv_files = [
        os.path.join(csv_dir, item)
        for item in all_items
        if os.path.isfile(os.path.join(csv_dir, item)) and item.endswith(".csv")
    ]

    if len(csv_files) == 1:
        # If only one CSV file exists, send it directly for download
        return send_file(
            csv_files[0],
            as_attachment=True, 
            download_name=os.path.basename(csv_files[0]), 
            mimetype='application/csv',
        )

    # If multiple CSV files exist, compress them into a ZIP file and send as a download
    zip_buffer = BytesIO()
    try:
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for file_path in csv_files:
                if os.path.exists(file_path):
                    zip_file.write(file_path, os.path.basename(file_path))
                else:
                    return jsonify({"error": f"File {file_path} not found"}), 404  # Handle missing files
    except Exception as e:
        return jsonify({"error": f"Error creating ZIP file: {e}"}), 500  # Handle errors in creating ZIP file

    zip_buffer.seek(0)  # Reset the buffer position for sending
    return send_file(
        zip_buffer, 
        as_attachment=True,
        download_name="tables.zip",
        mimetype='application/zip',
    )

if __name__ == '__main__':
    # Run the Flask app in debug mode for development purposes
    app.run(debug=True)
