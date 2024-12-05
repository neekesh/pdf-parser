import csv
import datetime
import magic
import pdfplumber
import os



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


def UUID():
    """
    Generate a unique identifier based on the current date and time.
    
    Returns:
        str: A string formatted as 'YYYYMMDD_HHMMSS', representing the current timestamp.
    """
    current_time = datetime.datetime.now()
    # Format the current time into a string for unique identification
    return current_time.strftime("%Y%m%d_%H%M%S%f")


def extract_tables(source, target):
    """
    Extract tables from a PDF file and save them as CSV files. If no tables are found, 
    create a response file indicating the status.

    Args:
        source (str): The file path of the source PDF file.
        target (str): The directory path where the extracted CSV files and response file will be saved.

    Returns:
        None
    """
    # Ensure the target directory exists; create it if it doesn't
    os.makedirs(target, exist_ok=True)
    
    # Open the PDF file for processing
    with pdfplumber.open(source) as pdf:
        for i, page in enumerate(pdf.pages, start=1):
            # Extract tables from the current page
            tables = page.extract_tables()
            
            # Check if no tables are found
            if len(tables) == 0:
                # Write a response indicating no tables were found
                with open(f"{target}/response.txt", "w") as f:
                    f.write("200, No tables found")
                return
            
            # Loop through each table found on the current page
            for table_index, table in enumerate(tables, start=1):
                # Define the output CSV file name based on table index
                csv_file = f"{target}/page_{i}_table_no_{table_index}.csv"
                # Write the table data to the CSV file
                with open(csv_file, "w", newline="") as f:
                    writer = csv.writer(f)
                    writer.writerows(table)
    
    # If tables are successfully extracted, write a success response
    with open(f"{target}/response.txt", "w") as f:
        f.write("success")
