import time
from io import BytesIO
from PIL import Image
from flask import Flask, jsonify, request, render_template, g, url_for, session, redirect, send_file, flash, abort, \
    jsonify, send_from_directory
from werkzeug.utils import secure_filename
from flask_restful import Api, Resource
from pymongo import MongoClient
import pdf2image
from reportlab.pdfgen import canvas
from PyPDF2 import PdfFileWriter, PdfFileReader
import os
import glob
from binascii import a2b_base64

UPLOAD_FOLDER = "images"

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

ALLOWED_EXTENSIONS = set(['pdf', 'png', 'jpg', 'jpeg', 'gif'])

app = Flask(__name__)
api = Api(app)
app.secret_key = 'qweasb@#12344'

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

client = MongoClient('mongodb+srv://shivam:shivam@cluster0-3mbds.mongodb.net/test?retryWrites=true&w=majority')
db = client.get_database('docsign')
users = db.users


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# @app.route('/download', methods=['POST'])
def generate_pdf():
    # list_of_file = glob.glob('images/*')
    # latest_file = max(list_of_file, key=os.path.getmtime)
    # picture_path = latest_file
    user=session['user']
    picture_path="images/" + user + '_sign_' + ".png"
    temp_path="temp_pdf/" + user + '_pdf_' + ".pdf"
    # c = canvas.Canvas('D:/uploads/temp.pdf')
    c=canvas.Canvas(temp_path)
    c.drawImage(picture_path, 150, 110, width=180, height=80, mask='auto')
    c.save()
    # sign_path = '~/Downloads/uploads/temp.pdf'
    # input_path = '~/Downloads/uploads/' + session['user'] + '.pdf'
    sign_path="temp_pdf/" + user + '_pdf_' + ".pdf"
    input_path="images/" + user + '_to_sign_' + ".pdf"
    watermark = PdfFileReader(open(sign_path, "rb"))
    input_file = PdfFileReader(open(input_path, "rb"))
    output_file = PdfFileWriter()
    input_page = input_file.getPage(0)
    input_page.mergePage(watermark.getPage(0))
    output_file.addPage(input_page)
    # folder_path = 'D:/uploads/'
    # output_path = folder_path + 'signed' + '.pdf'
    output_path="final_pdf/" + user + '_signed_' + '.pdf'
    with open(output_path, "wb") as outputStream:
        output_file.write(outputStream)
    return render_template("test.html")


@app.route('/return')
def return_files():
    try:
        user=session['user']
        # filepath='final_pdf/' + user + '_signed_' + ".pdf"
        return send_file("final_pdf/" + user + '_signed_' + '.pdf',as_attachment=True)
        # return send_file('~/Downloads/signed.pdf', as_attachment=True)
    except Exception as e:
        return str(e)


@app.route('/', methods=['POST', 'GET'])
def index():
    if request.method == 'POST':
        session.pop('user', None)
        users = db.users
        login_user = users.find_one({'user_id': request.form['user']})
        if login_user:
            p = request.form['password']
            if p == login_user['pw']:
                session['user'] = login_user['user_id']
                user = login_user['user_name']
                # user = {'username': user}
                return redirect(url_for('protected'))
            return "Invalid userID or password"
        return "Invalid Credentials"
    return render_template('index.html')


@app.route('/register', methods=['POST', 'GET'])
def register():
    if request.method == 'POST':
        users = db.users
        existing_user = users.find_one({'user_id': request.form['userid']})

        if existing_user is None:
            users.insert(
                {'user_id': request.form['userid'], 'pw': request.form['pass'], 'user_name': request.form['username']})
            session['user_name'] = request.form['username']
            return redirect(url_for('index'))

        return " User already registered! "
    return render_template('register.html')


@app.route('/protected')
def protected():
    if g.user:
        return render_template('upload.html',user=session['user'])
        # return render_template('draw.html', user=session['user'])
    return redirect(url_for('index'))


@app.before_request
def before_request():
    g.user = None

    if 'user' in session:
        g.user = session['user']


@app.route('/dropsession')
def dropsession():
    session.pop('user', None)
    return render_template('index.html')


@app.route('/upload')
def upload_form():
    return render_template('upload.html')


@app.route('/upload', methods=['POST'])
def upload_file():
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            flash('No file selected for uploading')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            # filename = secure_filename(file.filename)
            filename = session['user']+'_to_sign_' + ".pdf"
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            flash('File successfully uploaded')
            # return redirect('/upload')
            return render_template('draw.html')
        else:
            flash('Allowed file types are txt, pdf, png, jpg, jpeg, gif')
            return redirect(request.url)


@app.route('/upload-sign', methods=['POST'])
def uploadsign():
    user = session['user']
    data = request.json
    base64String = data['image'].replace("data:image/png;base64,", "")
    binary_data = a2b_base64(base64String)
    seconds = str(time.time())
    # filaname = "images/" + user + '_sign_' + seconds + ".png"
    filaname="images/" + user + '_sign_' + ".png"
    fd = open(filaname, 'wb')
    fd.write(binary_data)
    fd.close()
    generate_pdf()
    # return_files()
    # return render_template('upload.html')
    return jsonify(data=filaname, message="uploaded")


if __name__ == "__main__":
    app.run(debug=True)
