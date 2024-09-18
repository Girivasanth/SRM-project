from flask import Flask, render_template, request, send_file, redirect, url_for
import pandas as pd
import os
import tempfile
from gretel_client import configure_session
from faker import Faker
import random


app = Flask(__name__)

faker = Faker()

# Function to synthesize column data
def synthesize_column_data(df):
    for col in df.columns:
        col_lower = col.lower()
        # Specific checks based on column names
        if 'name' in col_lower:  # For names (person or organization)
            df[col] = df[col].apply(lambda x: faker.name() if 'person' in col_lower else faker.company())
        elif 'address' in col_lower:  # Addresses
            df[col] = df[col].apply(lambda x: faker.address())
        elif 'email' in col_lower:  # Emails
            df[col] = df[col].apply(lambda x: faker.email())
        elif 'phone' in col_lower or 'contact' in col_lower:  # Phone numbers
            df[col] = df[col].apply(lambda x: faker.phone_number())
        elif 'product' in col_lower:  # Product-related columns
            df[col] = df[col].apply(lambda x: faker.catch_phrase())
        elif 'company' in col_lower:  # Company-related columns
            df[col] = df[col].apply(lambda x: faker.company())
        elif 'state' in col_lower:  # State-related columns
            df[col] = df[col].apply(lambda x: faker.state())
        elif 'country name' in col_lower:  # Country-related columns
            df[col] = df[col].apply(lambda x: faker.country())
        elif 'city' in col_lower:  # City-related columns
            df[col] = df[col].apply(lambda x: faker.city())
        elif pd.api.types.is_string_dtype(df[col]):  # Generic string columns
            df[col] = df[col].apply(lambda x: faker.word())
        elif pd.api.types.is_numeric_dtype(df[col]):  # Numeric columns
            df[col] = df[col].apply(lambda x: synthesize_numeric_column(df[col]))
        elif pd.api.types.is_datetime64_any_dtype(df[col]):  # Date/Time columns
            df[col] = df[col].apply(lambda x: faker.date_between(start_date="-10y", end_date="today"))
        else:  # Fallback for unknown types
            df[col] = df[col].apply(lambda x: faker.word())
    
    return df

def synthesize_numeric_column(column):
    if pd.api.types.is_integer_dtype(column):  # Integer column
        return faker.random_int(min=1, max=10000)
    elif pd.api.types.is_float_dtype(column):  # Float column
        return round(faker.pyfloat(left_digits=5, right_digits=2, positive=True), 2)

# Configure Gretel API
configure_session(api_key='grtuc8d12f0eebee3b191c31d6f01f6157741404d93eccb4573a83dea110bc5d409f')

# Route to render the index page (upload form)
@app.route('/Synthesis')
def index():
    return render_template('index.html')

# Route to handle the file upload, synthesize data, and display the result
@app.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        return 'No file uploaded', 400
    
    file = request.files['file']
    if file.filename == '':
        return 'No file selected', 400
    
    # Save file to temporary directory
    temp_file_path = os.path.join(tempfile.gettempdir(), file.filename)
    file.save(temp_file_path)

    # Read the CSV file with fallback encoding
    try:
        df = pd.read_csv(temp_file_path, encoding='utf-8')
    except UnicodeDecodeError:
        df = pd.read_csv(temp_file_path, encoding='ISO-8859-1')

    # Synthesize data
    synthesized_df = synthesize_column_data(df)

    # Save synthesized data to a new file
    synthesized_file_path = temp_file_path.replace(".csv", "_synthesized.csv")
    synthesized_df.to_csv(synthesized_file_path, index=False)

    # Convert the DataFrame to HTML table format
    synthesized_html = synthesized_df.to_html(classes='table table-striped')

    # Store file path in the session or pass it securely
    return render_template('result.html', table=synthesized_html, file_path=os.path.basename(synthesized_file_path))

# Route to handle downloading the synthesized CSV file
@app.route('/download/<path:filename>', methods=['GET'])
def download_file(filename):
    # Construct the full path for the file
    temp_file_path = os.path.join(tempfile.gettempdir(), filename)
    
    if os.path.exists(temp_file_path):
        return send_file(temp_file_path, as_attachment=True, download_name='synthesized_data.csv')
    else:
        return 'File not found', 404

if __name__ == '__main__':
    app.run(port=3000)
