# PDF Table Extractor API

This project is a Flask-based API for extracting tables from PDF files and converting them into CSV format. It allows users to upload PDFs, process them in the background, and download the extracted CSV files.

## Features

- Upload one or multiple PDF files for processing.
- Automatically extracts tables from PDFs using `pdfplumber`.
- Saves extracted tables as CSV files.
- Returns error messages if no tables are found or an issue occurs.
- Provides a unique ID for each processed file.
- Allows retrieval of processed files (CSV or ZIP) by unique ID.

---

## Project Structure
```
project/
│
├── uploads/
│   └── (both pdf and csv files will be stored here)
│
├── requirements.txt (requirements.txt)
├── main.py
└── utils.py
```

## Requirements

- Python 3.7+
- pip for managing dependencies.

### Dependencies

Install the required Python packages using:

```bash
pip install -r requirements.txt
```

The main dependencies are:

- Flask: To create the API.
pdfplumber: For extracting tables from PDF files.
- PyPDFium2: For PDF handling.
- magic: For file type validation.
- ReportLab: For generating test PDFs.

## API Endpoints
1. Upload PDF Files
- URL: /
- Method: POST
- Description: Upload one or more PDF files for table extraction.
- Request:
    - Content-Type: multipart/form-data
    - Field: files (one or more PDF files)
-  Response:
    - Success:
```
{
    "data": [
        {
            "uid": "20231204_123456",
            "file_name": "example.pdf"
        }
    ]
}
```
- Error:

```
{ "error": "All files should be PDFs" }
```
## 2. Download Extracted Files

- URL: /<uid>
- Method: GET
- Description: Retrieve CSVs or a ZIP archive for a processed PDF using its unique ID.
- Response:
    - Success (Single CSV): Returns the CSV file for download.
    - Success (Multiple Tables): Returns a ZIP archive containing all CSVs.
    - Error (No Tables): Returns a 200 status with the message No tables found.
## Running the Application
- Start the Flask server:

```
python app.py
```
- The server will run on http://127.0.0.1:5000.

- If you have docker installed then you can use 
```
docker-compose up
```

# Example Usage
Upload a PDF
- Use a tool like curl or Postman to test the upload endpoint:

```
curl -X POST -F "files=@path/to/sample.pdf" http://127.0.0.1:5000/
```
Retrieve Processed Files
Access the generated CSVs or ZIP archive:

```
curl -X GET http://127.0.0.1:5000/<uid> --output output.zip
```


## Known Limitations
- Only tables detected by pdfplumber are extracted; some complex table formats may not be recognized.
- Large PDFs may take longer to process.
- Error handling assumes specific scenarios; more edge cases can be handled.
