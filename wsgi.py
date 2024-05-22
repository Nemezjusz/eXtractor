from flask import Flask, render_template, request, redirect, send_file
from openai import OpenAI
from constants import API_KEY
import os, werkzeug
from pptx import Presentation

client = OpenAI(api_key=API_KEY)

app = Flask(__name__)

# Configure the upload folder and allowed extensions
app.config['UPLOAD_FOLDER'] = 'uploads/'  # make sure this directory exists
app.config['ALLOWED_EXTENSIONS'] = {'pdf', 'docx', 'txt'}
app.config['PPTX_FOLDER'] = 'presentations/'  # folder to store pptx files

os.makedirs(app.config['PPTX_FOLDER'], exist_ok=True)

def extract_info(transcript):
    completion = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are an information extraction assistant, skilled in extracting information"},
            {"role": "user", "content": f"Find information about deadline in following text: {transcript}. Return text in following format: 'Date of the deadline: <found date>'"}
        ]
    )
    return completion.choices[0].message.content

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def create_presentation(text, filename):
    prs = Presentation()
    slide_layout = prs.slide_layouts[1]
    slide = prs.slides.add_slide(slide_layout)
    title = slide.shapes.title
    content = slide.placeholders[1]

    title.text = "Extracted Information"
    content.text = text

    pptx_path = os.path.join(app.config['PPTX_FOLDER'], filename)
    prs.save(pptx_path)
    return pptx_path

@app.route('/')
def index():
    return render_template("main.html", transcript="Text will appear here.", pptx_file=None)

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'audiofile' not in request.files:
        return redirect(request.url)

    file = request.files['audiofile']
    if file.filename == '':
        return redirect(request.url)

    if file and allowed_file(file.filename):
        filename = werkzeug.utils.secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        with open(filepath, 'r', encoding='utf-8') as f:
            text = f.read()

        extracted_text = extract_info(text)
        pptx_filename = filename.rsplit('.', 1)[0] + '.pptx'
        pptx_path = create_presentation(extracted_text, pptx_filename)

        return render_template("main.html", transcript=extracted_text, pptx_file=pptx_filename)

    return redirect(request.url)

@app.route('/download/<filename>')
def download_file(filename):
    return send_file(os.path.join(app.config['PPTX_FOLDER'], filename), as_attachment=True)

if __name__ == '__main__':
    app.run()
