import google.generativeai as genai
import pandas as pd
import pdfplumber
import camelot
import json
api_key="AIzaSyAryPtRQUMCOSnVx-R9E5KfDdCVd0ELQj8"
genai.configure(api_key=api_key)  
model = genai.GenerativeModel("gemini-2.0-flash")

def api_call(prompt):
    conversation.append({"role": "user", "parts": [prompt] })
    response = model.generate_content(conversation)
    final_output = response.text
    conversation.append({"role": "assistant", "parts": [final_output]})
    return final_output
def init_conversation():
    global conversation
    conversation=[{"role": "user", "parts": ['''Your name is StrataBot. You are an intelligent chatbot designed to summarize structured data and provide instant query-based insights. 
            Whether you're dealing with databases, spreadsheets, or APIs, you help users extract meaningful information effortlessly. 
            Stay in character and always introduce yourself as StrataBot when responding.''']},  
    ]
def new_file(filename):
    if '.pdf' in filename:
        #PDF
        tables = camelot.read_pdf(filename, pages="1")
        table_dict_list = tables[0].df.to_dict(orient="records")  # Convert to list of dictionaries

        # Convert to JSON
        table_json = json.dumps(table_dict_list, indent=2)
        conversation.append({"role": "user", "parts": [f"Here is a JSON table extracted from the PDF named '{filename}':\n{table_json}\n\nYou can use this data to answer my questions. Also remember the filename as i might query with reference to the filename aswell"]})
    if ('.xlsx' in filename) or ('.xls' in filename):
        df = pd.read_excel(filename)
        data_json = json.dumps(df.to_dict(orient="records"), indent=2)
        conversation.append({"role": "user", "parts": [f"Here is a JSON table extracted from the Excel named '{filename}':\n{table_json}\n\nYou can use this data to answer my questions. Also remember the filename as i might query with reference to the filename aswell"]})

