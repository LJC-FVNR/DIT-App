# -*- coding: utf-8 -*-
from flask import Flask, render_template, request, redirect, url_for, jsonify
import pandas as pd
from werkzeug.utils import secure_filename
import os
from Processing import Processor
from file_ops import USER, file_name_listdir
import json
import sys
from fuzzywuzzy import fuzz
from DA_Core import PB_Data
from HTML_HeatMap import HStyler
import datetime
import time
import copy
from bokeh.embed import components
import traceback

app = Flask(__name__)
app.Debug = True
app.debug = True
app._static_folder = "static"

pd.set_option('display.max_rows', None)

# ---------Widgets Realization------------
WARNING = []
OUTPUT_RESULT = []  # [{title: "t", html: [script, div], tools: ['delete', 'download', ...]}, ...]
username = 'default'
# ----------Global Variables----------
GLOBAL_VARIABLES = {
    "DATA_LOADED":False,
    "DATA_REGISTRATED":False,
    "WARNING": [],
    "PHASE": 0,
    }
script = ''
content = ''
SCRIPT = ''
CONTENT = ''

RESULT_INDEX_ID = 1 # Set a individual id for each output result
RELOADED = False # for the reloading action of DA_Core.combinatorial_query_by
CONTENT_CACHE = []
SCRIPT_CACHE = []

temp = sys.stdout
SEND = []
class Send_MSG:
    def __init__(self):
        sys.stdout=self
    def write(self, content):
        global SEND
        SEND.append(content)
    def flush(self):
        self.buff=''
    def reset(self):
        sys.stdout = temp
APP_PRINT = Send_MSG()


@app.route('/')
def login():
    return render_template('Login.html')

@app.route('/panel-file', methods=['POST', 'GET'])
def login_username():
    global username
    username = request.form['username']
    global user
    user = USER(username)
    app.config['UPLOAD_FOLDER'] = f'static/user/{user.username}/data/'
    return render_template('Template.html', TITLE="Panel", GLOBAL_VARIABLES=GLOBAL_VARIABLES, data=user.data, 
                           current_func=user.get_func_settings(GLOBAL_VARIABLES['PHASE']), form_func_input_html=form_func_input_html,
                           username=username, script=SCRIPT, content=CONTENT)

@app.route("/panel-upload/<username>/", methods=['POST', 'GET'])
def upload_excel(username):
    if request.method == 'POST':
        file = request.files['file']
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(file.filename)))
        user.update_info_file()    # update file info of user
        global data
        data = pd.read_excel(file)
        GLOBAL_VARIABLES['DATA_NAME'] = secure_filename(file.filename)
        GLOBAL_VARIABLES["DATA_LOADED"] = True
        GLOBAL_VARIABLES["PHASE"] = 1
        current_func = user.get_func_settings(GLOBAL_VARIABLES['PHASE'])
        return render_template('Template.html', TITLE="Processing", 
                               GLOBAL_VARIABLES=GLOBAL_VARIABLES,
                               current_func=current_func,
                               username=username,
                               form_func_input_html=form_func_input_html, script=SCRIPT, content=CONTENT)

@app.route("/panel-data/<username>/", methods=['POST', 'GET'])
def choose_data(username):
    filelink, filename = request.form['filelink'].split("|")[0], request.form['filelink'].split("|")[1]
    global data
    data = pd.read_excel(filelink)
    GLOBAL_VARIABLES['DATA_NAME'] = filename
    GLOBAL_VARIABLES["DATA_LOADED"] = True
    GLOBAL_VARIABLES["PHASE"] = 1
    current_func = user.get_func_settings(GLOBAL_VARIABLES['PHASE'])
    return render_template('Template.html', TITLE="Processing", 
                       GLOBAL_VARIABLES=GLOBAL_VARIABLES,
                       current_func=current_func,
                       username=username, 
                       form_func_input_html=form_func_input_html, script=SCRIPT)

@app.route("/panel-func/<username>/", methods=['POST', 'GET'])
def use_function(username):
    form = request.form
    func_class, func_name = form['func-name'].split(".")
    para_list = [p for p in user.info['settings']['func_settings'][func_class][func_name]['parameters']]
    parameters = {}
    for p in para_list:
        # p: current_parameter_key
        if str(form[p]).strip() == 'None':
            parameters[p] = None
        else:
            current_input_type = user.info['settings']['func_settings'][func_class][func_name]['parameters'][p][2][0]
            if current_input_type == 'immutable':
                if user.info['settings']['func_settings'][func_class][func_name]['parameters'][p][2][1] == 'eval':
                    parameters[p] = eval(form[p])
                elif user.info['settings']['func_settings'][func_class][func_name]['parameters'][p][2][1] == 'text':
                    parameters[p] = str(form[p])
            elif current_input_type == 'choose_dir':
                    parameters[p] = str(form[p])
            elif current_input_type == 'json_edible':
                    parameters[p] = json.loads(form[p])
            elif current_input_type == 'text_edible':
                if user.info['settings']['func_settings'][func_class][func_name]['parameters'][p][2][2] == 'eval':
                    parameters[p] = eval(form[p])
                elif user.info['settings']['func_settings'][func_class][func_name]['parameters'][p][2][2] in ('text', 'eval_pre'):
                    parameters[p] = str(form[p])
            elif current_input_type == 'choose':
                parameters[p] = eval(form[p])
            elif current_input_type == "checks":
                parameters[p] = form.getlist(p)
            elif current_input_type == "choose_append":
                parameters[p] = form.getlist(p)
            elif current_input_type == "floating_choose":
                key_value = form.getlist(p)
                for kv in key_value:
                    k, v = kv.split(":")
                    parameters[k] = v
            elif current_input_type == "text_append":
                parameters[p] = form.getlist(p)
            elif current_input_type == "choose_eval":
                if user.info['settings']['func_settings'][func_class][func_name]['parameters'][p][2][1] == 'eval':
                    parameters[p] = eval(form[p])
                elif user.info['settings']['func_settings'][func_class][func_name]['parameters'][p][2][1] in ('text', 'eval_pre'):
                    parameters[p] = str(form[p])
    # registrate the processor
    call = user.info['settings']['func_settings'][func_class][func_name]["call"]
    try:
        exec(call)
        # execute after
        global operate
        operate = user.info['settings']['func_settings'][func_class][func_name]["after"]["exec"]
        # exec(user.info['settings']['func_settings'][func_class][func_name]["after"]["exec"])
        global script
        script = user.info['settings']['func_settings'][func_class][func_name]["after"]["script"]
        global finish
        finish = user.info['settings']['func_settings'][func_class][func_name]["after"]["finish"]
        #return eval(user.info['settings']['func_settings'][func_class][func_name]["after"]["finish"])
        if user.info['settings']['func_settings'][func_class][func_name]["type"] == "submit":
            exec(operate)
            return redirect(url_for('render_panel_func', username=username))
            # return eval(user.info['settings']['func_settings'][func_class][func_name]["after"]["finish"])
        else:
            exec(operate)
            global CONTENT_CACHE
            CONTENT_CACHE.append(content)
            if 'location.reload()' in script:
                script = ''
            global SCRIPT_CACHE
            SCRIPT_CACHE.append(script)
            return eval(finish)
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': 'Error occured'})
    # APP_PRINT.reset()


@app.route("/panel/<username>/", methods=['GET'])
def render_panel_func(username):
    global script
    current_func = user.get_func_settings(GLOBAL_VARIABLES['PHASE'])
    global finish
    CONTENT, SCRIPT = get_cache()
    return render_template('Template.html', TITLE="Processing", GLOBAL_VARIABLES=GLOBAL_VARIABLES, current_func=current_func,username=username,form_func_input_html=form_func_input_html, script=SCRIPT, content=CONTENT)


@app.route("/status/<username>/",methods=["GET"])
def sending(username):
    current = []
    current = get_send()
    return jsonify(current)
    
def get_send():
    global SEND
    while len(SEND) == 0:
        time.sleep(0.5)
    current = SEND
    SEND = []
    return current

def get_cache():
    global CONTENT_CACHE
    global SCRIPT_CACHE
    return "".join(CONTENT_CACHE), "".join(SCRIPT_CACHE)

def form_func_input_html(parameters, name, index, outer_index):
    current_parameter = parameters[name]
    display_name = current_parameter[0]        # name to display
    input_content = current_parameter[1]        # default content
    type_input = current_parameter[2][0]
    type_input_parameters = current_parameter[2][1:] if len(current_parameter[2])>1 else None
    input_level = current_parameter[3]
    input_desc = current_parameter[4]
    try:
        if current_parameter[5] == 'None':
            display = 'visibility:hidden; position:absolute;'
    except:
        display = ''
    level = f"Parameter Importance: Lv. {input_level}"
    border_level = ['DarkSlateGray', 'SeaGreen', 'SteelBlue', 'Gold', 'OrangeRed']
    current_border = border_level[input_level-1]
    output_html = ''
    if type_input == 'immutable':
        output_html = f"""
                        <div class="input-group func-input-list parameters" style="border-left: 5px {current_border} solid; border-radius: 0.15rem; {display}">
                          <div class="input-group-append">
                            <span class="input-group-text" style="border-left: 0px solid" data-toggle="popover" data-trigger="hover" data-placement="top" data-content="{level}">{index}</span>
                            <span class="input-group-text" data-toggle="popover" data-trigger="hover" data-placement="top" data-content="{input_desc}">{display_name}</span>
                          </div>
                            <input type="text" class="form-control" name="{name}" value="{input_content}" form="FUNC{outer_index}" readonly>
                        </div>
                        """
    elif type_input == 'choose_dir':
        path = user.path + type_input_parameters[0]
        public_path = 'static/user/public/' + type_input_parameters[0]
        file_list = {}
        if input_content != 'None':
            file_list[input_content] = input_content
        file_user = file_name_listdir(path)
        for i in file_user:
            if i in file_list:
                continue
            else:
                file_list[i] = path + i

        file_public = file_name_listdir(public_path)
        for i in file_public:
            if i not in file_list:
                file_list[i] = public_path + i

        if input_content in file_user:
            input_content = path + input_content
        elif input_content in file_public:
            input_content = public_path + input_content
        else:
            pass
        options = "".join([f"<option value='{file_list[i]}'>{i}</option>" for i in file_list if i != input_content])
        output_html = f"""
                        <div class="input-group func-input-list parameters" style="border-left: 5px {current_border} solid; border-radius: 0.15rem; {display}">
                          <div class="input-group-append">
                            <span class="input-group-text" style="border-left: 0px solid" data-toggle="popover" data-trigger="hover" data-placement="top" data-content="{level}">{index}</span>
                            <span class="input-group-text" data-toggle="popover" data-trigger="hover" data-placement="top" data-content="{input_desc}">{display_name}</span>
                          </div>
                            <select class="custom-select" name="{name}" form="FUNC{outer_index}">
                                <option selected="selected" value="{input_content}">{input_content}</option>
                                {options}
                            </select>
                        </div>
                      """
    elif type_input == 'json_edible':
        content = json.dumps(eval(input_content))
        output_html = f"""
                        <div class="input-group func-input-list parameters" style="border-left: 5px {current_border} solid; border-radius: 0.15rem; {display}">
                          <div class="input-group-append">
                            <span class="input-group-text" style="border-left: 0px solid" data-toggle="popover" data-trigger="hover" data-placement="top" data-content="{level}">{index}</span>
                            <span class="input-group-text" data-toggle="popover" data-trigger="hover" data-placement="top" data-content="{input_desc}">{display_name}</span>
                          </div>
                            <textarea class="form-control func-json-area" aria-label="With textarea" name="{name}" form="FUNC{outer_index}">{content}</textarea>
                        </div>
                        """
    elif type_input == 'text_edible':
        if type_input_parameters[1] == 'eval_pre':
            input_content = eval(input_content)
        if type_input_parameters[0] == 'small':
            output_html = f"""
                            <div class="input-group func-input-list parameters" style="border-left: 5px {current_border} solid; border-radius: 0.15rem; {display}">
                              <div class="input-group-append">
                                <span class="input-group-text" style="border-left: 0px solid" data-toggle="popover" data-trigger="hover" data-placement="top" data-content="{level}">{index}</span>
                                <span class="input-group-text" data-toggle="popover" data-trigger="hover" data-placement="top" data-content="{input_desc}">{display_name}</span>
                              </div>
                                <input type="text" class="form-control" name="{name}" value="{input_content}" form="FUNC{outer_index}">
                            </div>
                        """
        if type_input_parameters[0] == 'large':
            output_html = f"""
                <div class="input-group func-input-list parameters" style="border-left: 5px {current_border} solid; border-radius: 0.15rem; {display}">
                  <div class="input-group-append">
                    <span class="input-group-text" style="border-left: 0px solid" data-toggle="popover" data-trigger="hover" data-placement="top" data-content="{level}">{index}</span>
                    <span class="input-group-text" data-toggle="popover" data-trigger="hover" data-placement="top" data-content="{input_desc}">{display_name}</span>
                  </div>
                    <textarea class="form-control func-json-area" aria-label="With textarea" name="{name}" form="FUNC{outer_index}">{input_content}</textarea>
                </div>
            """
    elif type_input == 'choose':
        if hasattr(eval(type_input_parameters[0]), '__iter__'):
            type_input_parameters = eval(type_input_parameters[0])
        select = []
        for i in type_input_parameters:
            if i != input_content:
                select.append(i)
        options = "".join([f"<option value='{i}'>{i}</option>" for i in select])
        output_html = f"""
                        <div class="input-group func-input-list parameters" style="border-left: 5px {current_border} solid; border-radius: 0.15rem; {display}">
                          <div class="input-group-append">
                            <span class="input-group-text" style="border-left: 0px solid" data-toggle="popover" data-trigger="hover" data-placement="top" data-content="{level}">{index}</span>
                            <span class="input-group-text" data-toggle="popover" data-trigger="hover" data-placement="top" data-content="{input_desc}">{display_name}</span>
                          </div>
                            <select class="custom-select" name="{name}" form="FUNC{outer_index}">
                                <option selected="selected" value="{input_content}">{input_content}</option>
                                {options}
                            </select>
                        </div>
                      """
    elif type_input == "checks":
        pool = eval(input_content)
        # prepare matching score with default feature for each column
        match = {i:'' for i in pool}
        if type_input_parameters[0] != 'None':
            default_pool = eval(type_input_parameters[0])
            for s1 in match:
                matching_score = [fuzz.token_set_ratio(str(s1), str(s2)) for s2 in default_pool]
                if max(matching_score) > 70:
                    match[s1] = 'checked'
        template = """
                    <div class="form-check form-check-inline">
                      <input class="form-check-input" type="checkbox" name="{name}" value="{pool}" {is_checked}>
                      <label class="form-check-label" for="inlineCheckbox1">{pool}</label>
                    </div>
                    """
        checks = "".join([template.format(pool=p, is_checked=match[p], name=name) for p in match])
        output_html = f"""
                        <div class="input-group func-input-list parameters" style="border-left: 5px {current_border} solid; border-radius: 0.15rem; {display}">
                        <div class="input-group-append">
                            <span class="input-group-text" style="border-left: 0px solid" data-toggle="popover" data-trigger="hover" data-placement="top" data-content="{level}">{index}</span>
                            <span class="input-group-text" data-toggle="popover" data-trigger="hover" data-placement="top" data-content="{input_desc}">{display_name}</span>
                            <div class="checks">{checks}</div>
                          </div>
                        </div>
                        """
    elif type_input == "choose_append":
        pool = eval(input_content)
        options = "".join([f"<option value='{i}'>{i}</option>" for i in pool])
        output_html = f"""
                    <div class="input-group func-input-list parameters" style="border-left: 5px {current_border} solid; border-radius: 0.15rem;">
                        <div class="input-group-append">
                            <span class="input-group-text" style="border-left: 0px solid" data-toggle="popover" data-trigger="hover" data-placement="top" data-content="{level}">{index}</span>
                            <span class="input-group-text" data-toggle="popover" data-trigger="hover" data-placement="top" data-content="{input_desc}">{display_name}</span>
                        </div>
                        <select class="custom-select" name="{name}" form="FUNC{outer_index}" id="{name}{outer_index}">
                            {options}
                        </select>
                        <button class="btn btn-outline-secondary" id="btn_{name}{outer_index}" type="button" onclick="$($('#{name}{outer_index}').prop('outerHTML')).insertBefore('#btn_{name}{outer_index}');">Append</button>
                        <button class="btn btn-outline-secondary" id="btn_del_{name}{outer_index}" type="button" onclick="deleteElement('btn_{name}{outer_index}')">Delete</button>
                    </div>
                """
    elif type_input == "choose_eval":
        pool = eval(input_content)
        options = "".join([f"<option value='{i}'>{i}</option>" for i in pool])
        output_html = f"""
                    <div class="input-group func-input-list parameters" style="border-left: 5px {current_border} solid; border-radius: 0.15rem;">
                        <div class="input-group-append">
                            <span class="input-group-text" style="border-left: 0px solid" data-toggle="popover" data-trigger="hover" data-placement="top" data-content="{level}">{index}</span>
                            <span class="input-group-text" data-toggle="popover" data-trigger="hover" data-placement="top" data-content="{input_desc}">{display_name}</span>
                        </div>
                        <select class="custom-select" name="{name}" form="FUNC{outer_index}" id="{name}{outer_index}">
                            {options}
                        </select>
                    </div>
                """
    elif type_input == "floating_choose":
        if hasattr(eval(type_input_parameters[0]), '__iter__'):
            type_input_parameters = eval(type_input_parameters[0])
        pool = eval(input_content)
        options = "".join([f"<option value='{i}'>{i}</option>" for i in pool])
        floating_labels = type_input_parameters
        fc_len = len(floating_labels) 
        margin = '0' if fc_len <= 2 else '0.25'
        # change
        floating = """
            <label class="border-lable-flt" style="margin-bottom: {margin}rem;">
              <select class="form-select form-control custom-select" id="floatingSelectGrid{fid}" name="{name}">
                  {options}
              </select>
              <span>{fl}</span>
            </label>
        """
        match = {fl:False for fl in floating_labels}
        for fl in floating_labels:
            # for subsequent optimization
            matching_score = {fuzz.token_set_ratio(fl, p):[] for p in pool}
            for p in pool:
                matching_score[fuzz.token_set_ratio(fl, p)].append([fl, p])
            if max(matching_score)>60:
                for m in matching_score[max(matching_score)]:
                    match[m[0]] = m[1]
        content = []
        for index, fl in enumerate(match):
            if match[fl] == False:
                options = "".join([f'<option value="{fl}:{p}">{p}</option>' for p in pool])
            else:
                temp_pool = copy.deepcopy(pool)
                temp_pool.remove(match[fl])
                options = f'<option value="{fl}:{match[fl]}" selected>{match[fl]}</option>' + "".join([f'<option value="{fl}:{p}">{p}</option>' for p in temp_pool])
            content.append(floating.format(margin=margin, options=options, fl=fl, name=name, fid=index))
        content = "".join(content)
        output_html = f"""
                        <div class="input-group func-input-list parameters" style="border-left: 5px {current_border} solid; border-radius: 0.15rem;">
                            <div class="input-group-append" style="margin-bottom: {margin}rem;">
                                <span class="input-group-text" style="border-left: 0px solid" data-toggle="popover" data-trigger="hover" data-placement="top" data-content="{level}">{index}</span>
                                <span class="input-group-text" data-toggle="popover" data-trigger="hover" data-placement="top" data-content="{input_desc}">{display_name}</span>
                            </div>
                            {content}
                        </div>
                        """
    elif type_input == "text_append":
        if 'eval_pre' in type_input_parameters:
            input_content = eval(input_content)
        output_html = f"""
                <div class="input-group func-input-list parameters" style="border-left: 5px {current_border} solid; border-radius: 0.15rem; {display}">
                  <div class="input-group-append">
                    <span class="input-group-text" style="border-left: 0px solid" data-toggle="popover" data-trigger="hover" data-placement="top" data-content="{level}">{index}</span>
                    <span class="input-group-text" data-toggle="popover" data-trigger="hover" data-placement="top" data-content="{input_desc}">{display_name}</span>
                  </div>
                    <input type="text" class="form-control" id="{name}{outer_index}" name="{name}" value="{input_content}" form="FUNC{outer_index}">
                    <button class="btn btn-outline-secondary" id="btn_{name}{outer_index}" type="button" onclick="$($('#{name}{outer_index}').prop('outerHTML')).insertBefore('#btn_{name}{outer_index}');">Append</button>
                    <button class="btn btn-outline-secondary" id="btn_del_{name}{outer_index}" type="button" onclick="deleteElement('btn_{name}{outer_index}')">Delete</button>
                </div>
            """
    return output_html



def format_result(title, script, div, tools:list):
    global RESULT_INDEX_ID
    div_id = 'result'+str(RESULT_INDEX_ID)
    # title: "t", script, div, tools: ['delete', 'download', 'funcinfo']}
    close = f"""
            <button type="button" class="btn btn-sm btn-outline-secondary" id="btn_result_close_{RESULT_INDEX_ID}" onclick="$('#btn_result_{RESULT_INDEX_ID}').parent().parent().remove()">
               <i class="bi bi-x-circle"><span class="icon-text">Close</span> </i>
            </button>
            """ if 'delete' in tools else ""
            
    hide = f"""
                <button type="button" class="btn btn-sm btn-outline-secondary" id="btn_result_hide_{RESULT_INDEX_ID}" onclick="$(this).parent().prev().hide()">
                <i class="bi bi-dash-circle"><span class="icon-text">Hide</span></i>
                </button>
            """ if 'hide' in tools else ""
            
    show = f"""
            <button type="button" class="btn btn-sm btn-outline-secondary" id="btn_result_show_{RESULT_INDEX_ID}"  onclick="$(this).parent().prev().show()">
                <i class="bi bi-plus-circle">  <span class="icon-text">Show</span></i>
            </button>
        """ if 'show' in tools else ""
    info = f"""
            <button type="button" class="btn btn-sm btn-outline-secondary" id="btn_result_info_{RESULT_INDEX_ID}">
                <i class="bi bi-info-circle">  <span class="icon-text">Info</span></i>
            </button>
        """ if 'info' in tools else ""
    
    tools=f'''
            {close}{hide}{show}{info}
    '''
    html = f"""
    <div class="DITWidget" id="{div_id}">
        <div class="DITWidget-Title">
                <b contenteditable="true">■ {title} </b>
        </div>
        <!-- Main Content Here -->
        <div class="main-content d-flex justify-content-center">
                {script}
                {div}
        </div>
        <div class="DITWidget-Tools btn-group">
            {tools}
        </div>
    </div>
    """
    RESULT_INDEX_ID += 1
    return html

