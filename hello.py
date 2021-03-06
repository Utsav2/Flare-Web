import os
from flask import Flask, render_template, request, jsonify, send_from_directory 
from flask.ext.sqlalchemy import SQLAlchemy
import jinja2
from sqlalchemy.ext.declarative import declarative_base
import json
import hashlib
from werkzeug import secure_filename
import logging
import sys
import traceback


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
    image = db.Column(db.String )
    id = db.Column(db.String(100), primary_key=True)

    def __init__(self, type_request, imei, description, number, timestamp, country, area=None, locality=None, latitude=None, longitude=None):

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


class Number(db.Model):

    type_number = db.Column(db.String(10))
    number = db.Column(db.String(15), primary_key=True)

    def __init__(self, type_number, number):
        self.type_number = type_number
        self.number=number

    def __repr__(self):
        return self.number


@app.route('/')
def hello():

    return render_template("index.html")

def get_number_of_reports():
    return 5

@app.route('/upload', methods = ['POST'])
def upload():

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
 
        report = Report(type_request, imei, description, number, time, country, area, locality, latitude, longitude)

        try:

            db.session.add(report)
            db.session.commit() 

        except Exception:

            # exc_type, exc_value, exc_traceback = sys.exc_info()
            # lines = traceback.format_exception(exc_type, exc_value, exc_traceback)
            # print ''.join('!! ' + line for line in lines)

            print "Error in uploading data, rolling back session"
            db.session.rollback()

    elif type_request == "SMS":
        print "reached here"
        country = request.form['Country']
        print "reached here"
        description = request.form['Description']
        print "reached here"
        time = request.form['Time']
        print "reached here"
        imei = request.form['IMEI']
        print "reached here"
        number = request.form['Number']
        print "reached here"
        id = hashlib.sha224(imei + time).hexdigest()
        print "reached here"
        report = Report(type_request, imei, description, number, time, country)
        print "reached here"
        try:
            db.session.add(report)
            db.session.commit() 
        except Exception:
            print "Error in uploading data, rolling back session"
            db.session.rollback()


    return jsonify("")


@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'],
                               filename)


@app.route('/deleteMineData', methods=['GET'])
def delete_mine():

    imei = request.args.get('IMEI')

    time = request.args.get('Time')

    id = hashlib.sha224(imei + time).hexdigest()

    delete_mine = db.session.query(Report).filter_by(id = id).first()

    try:

        db.session.delete(delete_mine)

        db.session.commit()

    except:

        db.session.rollback()

    return jsonify("")


@app.route('/register', methods = ['GET'])
def register():

    type_number = request.type["Type"]
    number = request.form["Number"]

    number_ = Number(type_number, number)

    try:
        db.session.add(number_)
        db.session.commit()
    except:
        db.session.rollback()
        print "Error in registering"

    return jsonify("");

@app.route('/getMineData', methods = ['GET'])
def initiate():

    administrative_area = request.args.get("area", "")

    country = request.args.get("country")

    queries = ""

    if len(administrative_area) == 0 :

        queries = db.session.query(Report).filter(Report.country.ilike(country))

    else:

        queries = db.session.query(Report).filter(Report.country.ilike(country), Report.area.ilike(administrative_area))


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

        elif mine.type_request=="SMS":
            my_dict['imei'] = mine.imei
            my_dict['timestamp'] = mine.timestamp
            my_dict['type'] = mine.type_request
            my_dict['description'] = mine.description

        mine_array.append(my_dict)  

    json_mines = json.dumps(mine_array)

    return json_mines


if __name__ == "__main__":
    app.run(debug = True)

