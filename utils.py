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
        file: A file object to check. This should be an open file in binary mode (e.g., 'rb').

    Returns:
        bool: True if the file is a PDF, otherwise False.
    """
    try:
        mime = magic.Magic(mime=True)  # Instantiate magic to get MIME type
        mime_type = mime.from_buffer(file.read(1024))  # Read first 1024 bytes for MIME type detection
        file.seek(0)  # Reset the file pointer to the beginning after reading
        return mime_type == 'application/pdf'  # Return True if it's a PDF
    except Exception as e:
        print(f"Error in is_pdf function: {e}")
        return False  # Return False if there's an error

def UUID() -> str:
    """
    Generate a unique identifier based on the current date and time.

    Returns:
        str: A string formatted as 'YYYYMMDD_HHMMSS', representing the current timestamp in microseconds.
    """
    try:
        current_time = datetime.datetime.now()  # Get the current date and time
        return current_time.strftime("%Y%m%d_%H%M%S%f")  # Format the timestamp as a string
    except Exception as e:
        print(f"Error in UUID function: {e}")
        return ""  # Return empty string in case of error

def check_rows(table) -> bool:
    """
    Checks if all rows in the table have the same number of elements.

    Args:
        table (list of list): A nested list where each sublist represents a row in the table.

    Returns:
        bool: True if all rows have the same length, False otherwise.
    """
    try:
        # Initialize expected_row_length to None, indicating it hasn't been set yet
        expected_row_length = None
        
        for row in table:
            # Filter out None values from the current row
            filtered_row = [item for item in row if item is not None]

            # Set the expected_row_length if it's not set yet
            if expected_row_length is None:
                expected_row_length = len(filtered_row)
            elif len(filtered_row) != expected_row_length:
                return False  # Return False if the current row length doesn't match the expected length

        return True  # Return True if all rows have consistent lengths
    except Exception as e:
        print(f"Error in check_rows function: {e}")
        return False  # Return False if there's an error

def extract_tables(source: str, target: str) -> None:
    """
    Extracts tables from a PDF file and saves them as CSV files. If no tables are found,
    a response file indicating the status is created.

    Args:
        source (str): The file path of the source PDF file to extract tables from.
        target (str): The directory path where the extracted CSV files and response file will be saved.

    Returns:
        None: This function does not return any value, but it writes files to the target directory.
    """
    try:
        # Ensure the target directory exists, creating it if necessary
        os.makedirs(target, exist_ok=True)
        
        # Create a response file to indicate the processing status
        with open(f"{target}/response.txt", "w") as f:
            f.write("200, Extracting data in progress")  # Initial status as in-progress

        try:
            # Open the PDF file using pdfplumber
            with pdfplumber.open(source) as pdf:
                for i, page in enumerate(pdf.pages, start=1):
                    # Extract tables from the current page
                    tables = page.extract_tables()

                    # If no tables are found on this page, write a response indicating this
                    if len(tables) == 0:
                        with open(f"{target}/response.txt", "w") as f:
                            f.write("200, No tables found")  # Status code 200: No tables found
                        return
                    
                    # Loop through each table found on the current page
                    for table_index, table in enumerate(tables, start=1):

                        # Check if the filtered table is properly structured
                        if not check_rows(table):
                            with open(f"{target}/response.txt", "w") as f:
                                f.write("400, Tables are not properly structured")  # Status code 400: Structure issue
                            return

                        # Define the CSV file name based on the page number and table index
                        csv_file = f"{target}/page_{i}_table_no_{table_index}.csv"

                        # Write the filtered table data to the CSV file
                        try:
                            with open(csv_file, "w", newline="") as f:
                                writer = csv.writer(f)
                                writer.writerows(filtered_table)
                        except IOError as e:
                            print(f"Error writing CSV file {csv_file}: {e}")
                            with open(f"{target}/response.txt", "w") as f:
                                f.write(f"500, Error writing CSV file {csv_file}")  # Status code 500: File write error
                            return

        except pdfplumber.utils.PDFSyntaxError as e:
            print(f"PDF syntax error: {e}")
            with open(f"{target}/response.txt", "w") as f:
                f.write("500, PDF Syntax Error")  # Status code 500: PDF syntax error
            return

        except Exception as e:
            print(f"Error processing PDF file: {e}")
            with open(f"{target}/response.txt", "w") as f:
                f.write(f"500, Error processing PDF file: {e}")  # Status code 500: General error
            return

        # If tables were successfully extracted, write a success response
        with open(f"{target}/response.txt", "w") as f:
            f.write("success")  # Status code 200: Extraction success

    except Exception as e:
        print(f"Error in extract_tables function: {e}")
        # Write a response in case of any top-level error
        with open(f"{target}/response.txt", "w") as f:
            f.write(f"500, Error: {e}")  # Status code 500: General error
