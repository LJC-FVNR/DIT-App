# -*- coding: utf-8 -*-
from flask import Flask, render_template, request, redirect, url_for
import pandas as pd
from werkzeug.utils import secure_filename
import os

app = Flask(__name__)
app.Debug = True
app.debug = True
app._static_folder = "static/static"
app.config['UPLOAD_FOLDER'] = 'static/data/'

# ---------Widgets Realization------------
WARNING = []
OUTPUT_RESULT = []  # [{title: "t", html: [script, div], tools: ['delete', 'download', ...]}, ...]

# ----------Global Variables----------
GLOBAL_VARIABLES = {
    "DATA_LOADED":False,
    "WARNING": []
    }


@app.route('/')
def login():
    return render_template('Login.html')

@app.route('/dp')
def data_processing():
    return render_template('Template.html', TITLE="Processing", 
                           GLOBAL_VARIABLES=GLOBAL_VARIABLES)

@app.route('/de')
def data_exploration():
    return render_template('Template.html', TITLE="Exploration", 
                           GLOBAL_VARIABLES=GLOBAL_VARIABLES)

@app.route('/st')
def setting():
    return render_template('Template.html', TITLE="setting", 
                           GLOBAL_VARIABLES=GLOBAL_VARIABLES)

@app.route("/dp", methods=['POST', 'GET'])
def upload_excel():
    if request.method == 'POST':
        file = request.files['file']
        file.save(os.path.join(app.config['UPLOAD_FOLDER'],secure_filename(file.filename)))
        f = file.read()
        data = pd.read_excel(f)
        GLOBAL_VARIABLES['DATA_NAME'] = secure_filename(file.filename)
        GLOBAL_VARIABLES["DATA_LOADED"] = True
        return render_template('Template.html', TITLE="Processing", 
                               GLOBAL_VARIABLES=GLOBAL_VARIABLES)


def format_result(title, script, div, tools:list):
    # title: "t", script, div, tools: ['delete', 'download', ...]}
    delete = """
            <button type="button" class="btn btn-sm btn-outline-secondary">
               <i class="bi bi-dash-circle"><span class="icon-text">Delete</span> </i>
            </button>
            """ if 'delete' in tools else ""
            
    download = """
                <button type="button" class="btn btn-sm btn-outline-secondary">
                <i class="bi bi-download"><span class="icon-text">Download</span></i>
                </button>
            """ if 'download' in tools else ""
            
    funcinfo = """
            <button type="button" class="btn btn-sm btn-outline-secondary">
                <i class="bi bi-question-circle">  <span class="icon-text">Func Info</span></i>
            </button>
        """ if 'funcinfo' in tools else ""
    tools=f'''
            {delete}{download}{funcinfo}
    '''
    html = f"""
    <div class="DITWidget">
        <div class="DITWidget-Title">
                <b contenteditable="true">■ {title} </b>
        </div>
        <!-- Main Content Here -->
                {script}
                {div}
        <div class="DITWidget-Tools btn-group">
            {tools}
        </div>
    </div>
    """
    return html