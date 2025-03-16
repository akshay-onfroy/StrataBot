from flask import Flask, request, jsonify, render_template
import os
from werkzeug.utils import secure_filename
import google.generativeai as genai
import pandas as pd
from datetime import datetime
import pdfplumber
import camelot
import json

app = Flask(__name__)

# Configure upload folder
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Store uploaded files information
uploaded_files = []

# Initialize Gemini API
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel("gemini-2.0-flash")

# Initialize conversation
def init_conversation():
    global conversation
    conversation = [{"role": "user", "parts": ['''Your name is StrataBot. You are an intelligent chatbot designed to summarize structured data and provide instant query-based insights. 
            Whether you're dealing with databases, spreadsheets, or APIs, you help users extract meaningful information effortlessly. 
            Stay in character and always introduce yourself as StrataBot when responding.''']}]

init_conversation()
#This API call is written in such way that history of conversation is remembered by the the model (Chain-of-taughts knowledge) 
def api_call(prompt):
    conversation.append({"role": "user", "parts": [prompt]})
    response = model.generate_content(conversation)
    final_output = response.text
    conversation.append({"role": "assistant", "parts": [final_output]})
    return final_output
#This happens when a new file is added
def new_file(filename):
    if '.pdf' in filename:
        # PDF
        tables = camelot.read_pdf(filename, pages="1")
        table_dict_list = tables[0].df.to_dict(orient="records")  # Convert to list of dictionaries

        # Convert to JSON
        table_json = json.dumps(table_dict_list, indent=2)
        conversation.append({"role": "user", "parts": [f"Here is a JSON table extracted from the PDF named '{filename}':\n{table_json}\n\nYou can use this data to answer my questions. Also remember the filename as I might query with reference to the filename as well."]})
    
    elif ('.xlsx' in filename) or ('.xls' in filename):
        # Excel
        df = pd.read_excel(filename)
        
        # Convert Timestamp objects to strings
        for col in df.columns:
            if pd.api.types.is_datetime64_any_dtype(df[col]):
                df[col] = df[col].dt.strftime('%Y-%m-%d %H:%M:%S')
        
        # Convert DataFrame to list of dictionaries
        data_dict = df.to_dict(orient="records")
        
        # Convert to JSON
        data_json = json.dumps(data_dict, indent=2)
        conversation.append({"role": "user", "parts": [f"Here is a JSON table extracted from the Excel file named '{filename}':\n{data_json}\n\nYou can use this data to answer my questions. Also remember the filename as I might query with reference to the filename as well."]})

@app.route('/')
def index():
    return render_template('index.html')  # Serve your HTML file

@app.route('/upload', methods=['POST'])
def upload_file():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file part'})
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No selected file'})
        
        if file:
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            
            # Store file information
            file_info = {
                'filename': filename,
                'filepath': file_path,
                'size': os.path.getsize(file_path)
            }
            uploaded_files.append(file_info)
            
            # Process the file
            new_file(file_path)
            
            return jsonify({'message': 'File uploaded successfully', 'file_info': file_info})
    
    except Exception as e:
        return jsonify({'error': f'Error uploading file: {str(e)}'})

@app.route('/files', methods=['GET'])
def list_files():
    return jsonify({'uploaded_files': uploaded_files})

@app.route('/query', methods=['POST'])
@app.route('/query', methods=['POST'])
def query_file():
    try:
        query = request.form.get('query', '').strip()
        
        if not query:
            return jsonify({'error': 'Query is required'})
        
        # Check if any files have been uploaded
        if not uploaded_files:
            return jsonify({'error': 'No files have been uploaded yet'})
        
        # Use the most recently uploaded file
        file_info = uploaded_files[-1]
        filename = file_info['filename']
        
        # Process the query
        result = api_call(query)
        
        return jsonify({'result': result, 'filename': filename})
    
    except Exception as e:
        return jsonify({'error': f'Error processing query: {str(e)}'})
if __name__ == '__main__':
    app.run(debug=True)