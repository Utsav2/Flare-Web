import os
from flask import Flask, render_template, request, jsonify, send_from_directory 
from flask.ext.sqlalchemy import SQLAlchemy
import jinja2
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy_imageattach.entity import Image, image_attachment
import json
import hashlib
from werkzeug import secure_filename

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'postgres://avodddfdxytrat:yFn8_7fiQEdlhkhPJ0UjsQukCJ@ec2-54-225-135-30.compute-1.amazonaws.com:5432/df09oj774bls87')
db = SQLAlchemy(app)

#regards to http://runnable.com/UiPcaBXaxGNYAAAL/how-to-upload-a-file-to-the-server-in-flask-for-python
#for images

app.config['UPLOAD_FOLDER'] = 'uploads/'
app.config['ALLOWED_EXTENSIONS'] = set(['png', 'jpg', 'jpeg', 'gif'])

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in app.config['ALLOWED_EXTENSIONS']


class Report(db.Model):

    type_request = db.Column(db.String(10))
    imei = db.Column(db.String(20))
    latitude = db.Column(db.String(15))
    longitude = db.Column(db.String(15))
    description = db.Column(db.String(400))
    number = db.Column(db.String(15))
    timestamp = db.Column(db.String(12))
    country = db.Column(db.String(30))
    area = db.Column(db.String(30))
    locality = db.Column(db.String(30))
    image = db.Column(db.LargeBinary)
    id = db.Column(db.String(100), primary_key=True)

    def __init__(self, type_request, imei, latitude, longitude, description, number, timestamp, country, area, locality, image=None):

        self.type_request = type_request
        self.imei = imei
        self.latitude = latitude
        self.longitude = longitude
        self.description = description
        self.number = number
        self.timestamp = timestamp
        self.country = country
        self.area = area
        self.locality = locality
        self.id = hashlib.sha224(imei + timestamp).hexdigest()


    def __repr__(self):
        return self.id


class ReportPicture(db.Model, Image):

    user_id = db.Column(db.String, db.ForeignKey('report.id'), primary_key=True)
    user = db.relationship('Report')    


@app.route('/')
def hello():

    return render_template("index.html")

def get_number_of_reports():
    return 5

@app.route('/upload', methods = ['POST'])
def upload():

    print "HELLO"

    type_request = request.form['Type']

    if type_request == "Internet":

        imei = request.form['IMEI']
        latitude = request.form['Latitude']
        longitude = request.form['Longitude']
        description = request.form['Description']
        number = request.form['Number']
        time = request.form['Time']
        address_json = request.form['Address']
        address = json.loads(address_json)
        country = address["Country"]
        area = address["Administrative Area"]
        locality = address["Locality"]
        id = hashlib.sha224(imei + time).hexdigest()
        file = request.files.get('image')

        if file and allowed_file[file.filename]:

            print "HI"

            # mimetype = file.content_type

            # img_str = file.read().encode('base64').replace('\n', '')

            # data_uri = 'data:%s;%s,%s' % (mimetype, 'base64', img_str)

            #file_input = open(file)

            report = Report(type_request, imei, latitude, longitude, description, number, time, country, area, locality)

        else:

            report = Report(type_request, imei, latitude, longitude, description, number, time, country, area, locality)


        try:

            db.session.add(report)
            db.session.commit() 

        except:

            print "Error in uploading data, rolling back session"
            db.session.rollback()

    return jsonify("")


@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'],
                               filename)


@app.route('/getMineData', methods = ['GET'])
def initiate():

    administrative_area = request.args.get("area", '')

    country = request.args.get("country")

    queries = ""

    if administrative_area == '':

        queries = db.session.query(Report).filter_by(country=country)

    else :

        queries = db.session.query(Report).filter_by(country=country, area=administrative_area)


    mine_array = []

    for mine in queries :

        my_dict = dict()

        if mine.type_request == "Internet":
            my_dict['latitude'] = mine.latitude
            my_dict['longitude'] = mine.longitude
            my_dict['description'] = mine.description
            my_dict['number'] = mine.number
            my_dict['imei'] = mine.imei
            my_dict['timestamp'] = mine.timestamp
            my_dict['type'] = mine.type_request

        mine_array.append(my_dict)  

    json_mines = json.dumps(mine_array)

    return json_mines


if __name__ == "__main__":
    app.run(debug = True)

