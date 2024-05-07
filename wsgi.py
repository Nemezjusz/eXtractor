from flask import Flask, render_template, request, redirect
from openai import OpenAI
from constants import API_KEY
import os, werkzeug

client = OpenAI(api_key=API_KEY)

app = Flask(__name__)

# Configure the upload folder and allowed extensions
app.config['UPLOAD_FOLDER'] = 'uploads/'  # make sure this directory exists
app.config['ALLOWED_EXTENSIONS'] = {'pdf', 'docx', 'txt'}


def extract_info(transcript):
    completion = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a information extraction assistant, skilled in extracting information"},
            {"role": "user", "content": f"Find information about date of transaction in following text: {transcript}"}
        ]
    )
    return completion.choices[0].message.content


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


@app.route('/')
def index():

    return render_template("main.html", transcript="Text will appear here.")


@app.route('/upload', methods=['POST'])
def upload_file():
    # check if the post request has the file part
    if 'audiofile' not in request.files:
        return redirect(request.url)

    file = request.files['audiofile']
    # if user does not select file, browser also
    # submit an empty part without filename
    if file.filename == '':
        return redirect(request.url)


    if file and allowed_file(file.filename):
        filename = werkzeug.utils.secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        with open(filepath, 'r', encoding='utf-8') as f:
            text = f.read()

        text = extract_info(text)

        return render_template("main.html", transcript=text)

    return redirect(request.url)



if __name__ == '__main__':
    app.run()