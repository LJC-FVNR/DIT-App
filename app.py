# -*- coding: utf-8 -*-
from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_session import Session
from flask import g
import pandas as pd
from werkzeug.utils import secure_filename
import os
from Processing import Processor
from file_ops import USER, file_name_listdir, TemplateExternalReader
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
import collections

app = Flask(__name__)
app._static_folder = "static"
'''
response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
response.headers['X-Content-Type-Options'] = 'nosniff'
'''
pd.set_option('display.max_rows', None)

app.config['SECRET_KEY'] = "*(%-4pqnn(^(#$#8173"
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_PERMANENT'] = False 
app.config['SESSION_USE_SIGNER'] = True
app.config['SESSION_KEY_PREFIX'] = 'session:'
# app.config['SESSION_FILE_THRESHOLD'] = 500
app.config['SESSION_PERMANENT'] = True


Session = Session()
Session.init_app(app=app)
from flask import session

# ----------Global Variables----------
'''
script, content: for current using elements
	-> session['current_script'] & session ['current_content']
SCRIPT, CONTENT: for getting saved elements and rendering template
	-> session['SCRIPT'] & session['CONTENT']
CONTENT_CACHE, SCIPRT_CACHE: for saving elements
	-> session['cached_content'] & session['cached_script']
'''

TOOLS = ['close', 'hide', 'show', 'reset', 'info']

GLOBAL_SENDING = {} # use a global sending dict to store the status update info for each requirement
std_temp = sys.stdout
class Send_MSG:
    def __init__(self, global_sending_id):
        sys.stdout=self
        GLOBAL_SENDING[global_sending_id] = []
        self.global_sending_id = global_sending_id
    def write(self, content):
        GLOBAL_SENDING[self.global_sending_id].append(content)
    def flush(self):
        self.buff=''
    def reset(self):
        sys.stdout = std_temp
'''
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def catch_all(path):
    return redirect(url_for('login'))
'''

@app.route('/')
def login():
    session.clear()
    session["DATA_LOADED"] = False
    session["DATA_REGISTRATED"] = False
    session["WARNING"] = []
    session["PHASE"] = 0
    session['RESULT_INDEX_ID'] = 0 # Set a individual id for each output result
    session['RELOADED'] = False # for the reloading action of DA_Core.combinatorial_query_by
    session['current_script']  = ''
    session ['current_content'] = ''
    session['SCRIPT'] = ''
    session['CONTENT'] = ''
    session['cached_content'] = {}
    session['cached_script'] = {}
    session['cached_tempform'] = collections.OrderedDict()     # [step1(form1), step2, step3, ...]
    session['cached_style'] = None
    return render_template('Login.html')

@app.route('/panel-file', methods=['POST', 'GET'])
def login_username():
    session['username'] = request.form['username']
    session['user'] = USER(session['username'])
    user = session['user']
    session['UPLOAD_FOLDER'] = f'static/user/{user.username}/data/'
    gsid = session['username']
    GLOBAL_SENDING[gsid] = []
    session['APP_PRINT'] = Send_MSG(gsid)
    SCRIPT, CONTENT = session.get('SCRIPT'), session.get('CONTENT')
    return render_template('Template.html', TITLE="Panel", session=session, data=user.data, 
                           current_func=user.get_func_settings(session['PHASE']), form_func_input_html=form_func_input_html,
                           username=session['username'], script=SCRIPT, content=CONTENT, get_panel=get_panel)

# -------------------------------- Main Panel -----------------------------------

@app.route("/panel-upload/<username>/", methods=['POST', 'GET'])
def upload_excel(username):
    if request.method == 'POST':
        file = request.files['file']
        path = os.path.join(session['UPLOAD_FOLDER'], secure_filename(file.filename))
        file.save(path)
        session['cached_tempform']['data_path'] = path
        session['cached_tempform']['data_name'] = file.filename
        user = session['user']
        user.update_info_file()    # update file info of user
        data = pd.read_excel(file)
        session['data'] = data
        session['DATA_NAME'] = secure_filename(file.filename)
        session["DATA_LOADED"] = True
        session["PHASE"] = 1
        current_func = user.get_func_settings(session['PHASE'])
        SCRIPT, CONTENT = session.get('SCRIPT'), session.get('CONTENT')
        return render_template('Template.html', TITLE="Processing", 
                               session=session,
                               current_func=current_func,
                               username=username,
                               form_func_input_html=form_func_input_html, script=SCRIPT, content=CONTENT, get_panel=get_panel)

@app.route("/panel-data/<username>/", methods=['POST', 'GET'])
def choose_data(username):
    user = session['user']
    filelink, filename = request.form['filelink'].split("|")[0], request.form['filelink'].split("|")[1]
    session['cached_tempform']['data_path'] = filelink
    session['cached_tempform']['data_name'] = filename
    data = pd.read_excel(filelink)
    session['data'] = data
    session['DATA_NAME'] = filename
    session["DATA_LOADED"] = True
    session["PHASE"] = 1
    current_func = user.get_func_settings(session['PHASE'])
    SCRIPT = session.get('SCRIPT')
    return render_template('Template.html', TITLE="Processing", 
                       session=session,
                       current_func=current_func,
                       username=username, 
                       form_func_input_html=form_func_input_html, script=SCRIPT, get_panel=get_panel)

@app.route("/status/<username>/",methods=["GET"])
def sending(username):
    while len(GLOBAL_SENDING[username]) == 0:
        time.sleep(1)
    current = GLOBAL_SENDING[username]
    GLOBAL_SENDING[username] = []
    return jsonify(current)

@app.route("/panel-func/<username>/", methods=['POST', 'GET'])
def use_function(username):
    if session.get("PHASE") == 0:
        if session.get("username") is not None:
            redirect(url_for('login_username'))
        else:
            redirect(url_for('login'))
    processor = session.get('processor')
    pb_data = session.get('pb_data')
    if session.get("PHASE") == 1:
        data = session.get('data')
    user = session['user']
    form = request.form
    func_class, func_name = form['func-name'].split(".")
    para_list = [p for p in user.info['settings']['func_settings'][func_class][func_name]['parameters']]
    parameters = {}
    parameters_presave = {}
    for p in para_list:
        # p: current_parameter_key
        if str(form[p]).strip() == 'None':
            parameters[p] = None
            parameters_presave[p] = 'None'
        else:
            current_input_type = user.info['settings']['func_settings'][func_class][func_name]['parameters'][p][2][0]
            if current_input_type == 'immutable':
                if user.info['settings']['func_settings'][func_class][func_name]['parameters'][p][2][1] == 'eval':
                    parameters[p] = eval(form[p])
                    parameters_presave[p] = form[p]
                elif user.info['settings']['func_settings'][func_class][func_name]['parameters'][p][2][1] == 'text':
                    parameters[p] = str(form[p])
                    parameters_presave[p] = str(form[p])
            elif current_input_type == 'choose_dir':
                    parameters[p] = str(form[p])
                    parameters_presave[p] = str(form[p])
            elif current_input_type == 'json_edible':
                    parameters[p] = json.loads(form[p])
                    parameters_presave[p] = form[p]
            elif current_input_type == 'text_edible':
                if user.info['settings']['func_settings'][func_class][func_name]['parameters'][p][2][2] == 'eval':
                    parameters[p] = eval(form[p])
                    parameters_presave[p] = form[p]
                elif user.info['settings']['func_settings'][func_class][func_name]['parameters'][p][2][2] in ('text', 'eval_pre'):
                    parameters[p] = str(form[p])
                    parameters_presave[p] = str(form[p])
            elif current_input_type == 'choose':
                parameters[p] = eval(form[p])
                parameters_presave[p] = form[p]
            elif current_input_type == "checks":
                parameters[p] = form.getlist(p)
                parameters_presave[p] = form.getlist(p)
            elif current_input_type == "choose_append":
                parameters[p] = form.getlist(p)
                parameters_presave[p] = form.getlist(p)
            elif current_input_type == "floating_choose":
                key_value = form.getlist(p)
                parameters_presave[p] = form.getlist(p)
                for kv in key_value:
                    k, v = kv.split(":")
                    parameters[k] = v
            elif current_input_type == "text_append":
                parameters[p] = form.getlist(p)
                parameters_presave[p] = form.getlist(p)
            elif current_input_type == "choose_eval":
                if user.info['settings']['func_settings'][func_class][func_name]['parameters'][p][2][1] == 'eval':
                    parameters[p] = eval(form[p])
                    parameters_presave[p] = form[p]
                elif user.info['settings']['func_settings'][func_class][func_name]['parameters'][p][2][1] in ('text', 'eval_pre'):
                    parameters[p] = str(form[p])
                    parameters_presave[p] = str(form[p])
    session['RESULT_INDEX_ID'] = session['RESULT_INDEX_ID']+1             # increase global result index here to record not only the results with returning divs
    session['cached_tempform'][session['RESULT_INDEX_ID']] = [func_class, func_name, para_list, parameters_presave]
    try:
        # registrate the processor
        call = user.info['settings']['func_settings'][func_class][func_name]["call"]
        session['current_info'] = user.info['settings']['func_settings'][func_class][func_name]["info"]
        exec(call)
        # execute after
        operate = user.info['settings']['func_settings'][func_class][func_name]["after"]["exec"]
        session['operate'] = operate
        script = user.info['settings']['func_settings'][func_class][func_name]["after"]["script"]
        session['current_script'] = script
        finish = user.info['settings']['func_settings'][func_class][func_name]["after"]["finish"]
        session['finish'] = finish
        if user.info['settings']['func_settings'][func_class][func_name]["type"] == "submit":
            exec(operate)
            return redirect(url_for('render_panel_func', username=username))
            # return eval(user.info['settings']['func_settings'][func_class][func_name]["after"]["finish"])
        else:
            exec(operate)
            current_id = session['RESULT_INDEX_ID']
            content = session['current_content']
            script = session['current_script']
            session['cached_content'][current_id] = content
            if 'location.reload()' in script:
                script = ''
            session['cached_script'][current_id] = script
            return eval(finish)
    except Exception as e:
        print('>> End')
        session['RESULT_INDEX_ID'] = session['RESULT_INDEX_ID'] - 1             # increase global result index here to record not only the results with returning divs
        traceback.print_exc()
        return jsonify({'error': 'Error occured'})
    # APP_PRINT.reset()

@app.route("/panel/<username>/", methods=['GET'])
def render_panel_func(username):
    user = session['user']
    current_func = user.get_func_settings(session['PHASE'])
    CONTENT, SCRIPT = get_cache()
    SCRIPT += get_cached_layout()
    return render_template('Template.html', TITLE="Processing", session=session, 
                           current_func=current_func,username=username,form_func_input_html=form_func_input_html, 
                           script=SCRIPT, content=CONTENT, get_panel=get_panel)

@app.route("/save-template/<username>/", methods=['POST'])
def save_template(username):
    form = request.form
    template_name = form['template_name']
    content, script = get_cache()
    view = {"content":content, "script":script}
    model = session.get('cached_tempform')        # model: [step1(form1), step2, step3...]
    user = session['user']
    layout = get_cached_layout()
    layout_dict = session['cached_style']
    user.save_template(view, model, layout, template_name, layout_dict)
    return jsonify({'success': 'Template Saved'})

@app.route("/template-close/<username>/", methods=['POST'])
def close_div(username):
    po = request.get_json()
    result_id = po['result_id']
    session['cached_tempform'].pop(result_id, None)
    session['cached_content'].pop(result_id, None)
    session['cached_script'].pop(result_id, None)
    return jsonify({'success': 'Division Closed'})

@app.route("/save-style/<username>/", methods=['POST'])
def save_style(username):
    style = request.get_json()
    session['cached_style'] = style
    return jsonify({'success': 'Layout Saved'})
    
@app.route("/view/<username>/<template_name>/", methods=['GET'])
def use_view(username, template_name):
    uv = TemplateExternalReader(username)
    view, layout, t, layout_dict = uv.get_template_view(template_name)
    title_dict = {result_id: layout_dict[result_id][1] for result_id in layout_dict}
    CONTENT, SCRIPT = view['content'], view['script']
    SCRIPT += layout
    return render_template('TemplateView.html', TITLE=template_name,
                           script=SCRIPT, content=CONTENT, username=username,
                           t=t, title_dict=title_dict)

@app.route("/model/<username>/<template_name>/", methods=['GET'])
def use_model(username, template_name):
    session.clear()
    initialize_model(username)
    uv = TemplateExternalReader(username)
    model, layout, t, layout_dict = uv.get_template_model(template_name)
    session['cached_style'] = layout_dict
    filelink, filename = model['data_path'], model['data_name']
    data = pd.read_excel(filelink)
    session['data'] = data
    session['DATA_NAME'] = filename
    session["DATA_LOADED"] = True
    session["PHASE"] = 1
    model.pop('data_path', None)
    model.pop('data_name', None)
    for result_id in model:
        use_func(model[result_id])
    print('>> End')
    return redirect(url_for('render_panel_func', username=username))

@app.route("/template_management/<username>/", methods=['GET'])
def template_management(username):
    user = session['user']
    temp_collection = user.user_template_management()
    title = f"User Management - {username}"
    return render_template('TempMgt.html', TITLE=title, temp_collection=temp_collection, username=username)

@app.route("/template_rename/<username>/<template_name>/<template_new_name>/", methods=['GET'])
def template_rename(username, template_name, template_new_name):
    user = session['user']
    user.template_rename(template_name, template_new_name)
    return jsonify({'success': 'Template Renamed'})

@app.route("/template_delete/<username>/<template_name>/", methods=['GET'])
def template_delete(username, template_name):
    user = session['user']
    user.template_delete(template_name)
    return jsonify({'success': 'Template Deleted'})

@app.route("/session-clear/<username>/", methods=['GET'])
def clear_session(username):
    session.clear()
    return jsonify({'success': 'Session Closed'})


# ----------------------------- User Management ----------------------------

def initialize_model(username):
    session["DATA_LOADED"] = False
    session["DATA_REGISTRATED"] = False
    session["WARNING"] = []
    session["PHASE"] = 0
    session['RESULT_INDEX_ID'] = 0 # Set a individual id for each output result
    session['RELOADED'] = False # for the reloading action of DA_Core.combinatorial_query_by
    session['current_script']  = ''
    session ['current_content'] = ''
    session['SCRIPT'] = ''
    session['CONTENT'] = ''
    session['cached_content'] = {}
    session['cached_script'] = {}
    session['cached_tempform'] = collections.OrderedDict()     # [step1(form1), step2, step3, ...]
    session['cached_style'] = None
    session['username'] = username
    session['user'] = USER(session['username'])
    user = session['user']
    session['UPLOAD_FOLDER'] = f'static/user/{user.username}/data/'
    GLOBAL_SENDING[username] = []
    session['APP_PRINT'] = Send_MSG(username)

def use_func(parameter_presaved):
    processor = session.get('processor')
    pb_data = session.get('pb_data')
    if session["PHASE"] == 1:
        data = session.get('data')
    if session["PHASE"] == 3:
        processor = session.get('pb_data').processor
    user = session['user']
    func_class, func_name, para_list, form = parameter_presaved[0], parameter_presaved[1], parameter_presaved[2], parameter_presaved[3]
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
                parameters[p] = form.get(p)
            elif current_input_type == "choose_append":
                parameters[p] = form.get(p)
            elif current_input_type == "floating_choose":
                key_value = form.get(p)
                for kv in key_value:
                    k, v = kv.split(":")
                    parameters[k] = v
            elif current_input_type == "text_append":
                parameters[p] = form.get(p)
            elif current_input_type == "choose_eval":
                if user.info['settings']['func_settings'][func_class][func_name]['parameters'][p][2][1] == 'eval':
                    parameters[p] = eval(form[p])
                elif user.info['settings']['func_settings'][func_class][func_name]['parameters'][p][2][1] in ('text', 'eval_pre'):
                    parameters[p] = str(form[p])
    session['RESULT_INDEX_ID'] = session['RESULT_INDEX_ID'] + 1             # increase global result index here to record not only the results with returning divs
    session['cached_tempform'][session['RESULT_INDEX_ID']] = [func_class, func_name, para_list, parameters]
    try:
        # registrate the processor
        call = user.info['settings']['func_settings'][func_class][func_name]["call"]
        session['current_info'] = user.info['settings']['func_settings'][func_class][func_name]["info"]
        exec(call)
        # execute after
        operate = user.info['settings']['func_settings'][func_class][func_name]["after"]["exec"]
        if "print('>> End');" in operate: 
            operate.replace("print('>> End');", '')
        if "print('>> End')" in operate: 
            operate.replace("print('>> End')", '')
        session['operate'] = operate
        script = user.info['settings']['func_settings'][func_class][func_name]["after"]["script"]
        session['current_script'] = script
        finish = user.info['settings']['func_settings'][func_class][func_name]["after"]["finish"]
        session['finish'] = finish
        if user.info['settings']['func_settings'][func_class][func_name]["type"] == "submit":
            exec(operate)
        else:
            exec(operate)
            current_id = session['RESULT_INDEX_ID']
            content = session['current_content']
            script = session['current_script']
            session['cached_content'][current_id] = content
            if 'location.reload()' in script:
                script = ''
            session['cached_script'][current_id] = script
    except Exception as e:
        print('>> End')
        session['RESULT_INDEX_ID'] -= 1             # increase global result index here to record not only the results with returning divs
        traceback.print_exc()
        return jsonify({'error': 'Error occured'})

def get_cache():
    return "".join(list(session['cached_content'].values())), "".join(list(session['cached_script'].values()))

def get_cached_layout():
    if session['cached_style'] is not None:
        style_script = ""
        for i in session['cached_style']:
            result_id = str(i)
            outerStyle = session['cached_style'][i][0]
            changedTitle = session['cached_style'][i][1]
            displayContent = session['cached_style'][i][2]
            style_script += f"$('#{result_id}').attr('style', '{outerStyle}');"
            style_script += f"$($('#{result_id}').children()[0]).children()[0].innerHTML = '{changedTitle}';"
            style_script += f"$($('#{result_id}').children()[1]).attr('style', '{displayContent}');"
        return style_script
    else:
        return ""
    

def get_panel(session):
    user = session['user']
    current_func_all = user.get_func_settings(session['PHASE'])
    tab_output_before = ""
    tab_output_after = ""
    index = 1
    activate = "Select" if "Select" in current_func_all else "Data"
    for tab in current_func_all:
        is_active = " active" if  tab == activate else ""
        is_show = " show" if  tab == activate else ""
        tab_element = f"""
                  <li class="nav-item" role="presentation">
                    <a class="nav-link{is_active}" id="home-tab" data-toggle="tab" href="#{tab}" role="tab" aria-controls="home" aria-selected="true">{tab}</a>
                  </li>
                     """
        tab_output_before += tab_element
        
        inner_choose = ""
        func_all = current_func_all[tab]
        for func in func_all:
            inner_choose += f'<option value="FUNC{index}">{func}</option>'
            index += 1
        after_content = f"""
            <div class="tab-pane fade{is_show}{is_active}" id="{tab}" role="tabpanel" aria-labelledby="{tab}-tab">
                <div class="input-group mb-3 intro" stype="margin-top:0">
                  <div class="input-group-prepend">
                    <label class="input-group-text" for="inputGroupSelect01">Function</label>
                  </div>
                  <select class="custom-select funcSelector">
                    <option selected>Select A Method...</option>
                        {inner_choose}
                  </select>
                </div>
            </div>
                """
        tab_output_after += after_content
    before = f"""
             <ul class="nav nav-tabs intro" id="panelTab" role="tablist">
                 {tab_output_before}
             </ul>
            """
    after = f"""
            <div class="tab-content" id="myTabContent">
                {tab_output_after}
            </div>
            """
    output = before+after
    outer_loop_index = 1
    outer = ""
    for tab in current_func_all:
        current_func = current_func_all[tab]
        for index, func in enumerate(current_func):
            inner = ""
            for i, name in enumerate(current_func[func]['parameters']):
                para_index = i + 1
                inner += form_func_input_html(current_func[func]['parameters'], name, para_index, outer_loop_index)
            outer += f"""
                    <form method="post" id="FUNC{outer_loop_index}" action="panel-func/{user.username}/">
                        <div class="alert alert-dark error col-lg-9" role="alert">
                        <p class="h6 func-title">Method: {func}</p>
                        <p class="func-title-info">{current_func[func]['info']}</p>
                        <input type="text" class="form-control" name="func-name" value="{func}" form="FUNC{outer_loop_index}" style="display:None">
                        {inner}
                        <button type="button" class="btn btn-secondary btn-lg btn-block" style="border-radius: .1rem;" onclick={current_func[func]["type"]}Method("FUNC{outer_loop_index}");>RUN</button>
                        </div>
                    </form>
                    """
            outer_loop_index += 1
    output += outer
    return output
    

def form_func_input_html(parameters, name, index, outer_index):
    processor = session.get('processor')
    pb_data = session.get('pb_data')
    if session["PHASE"] == 1:
        data = session['data']
    user = session['user']
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
        content_inner = []
        for index, fl in enumerate(match):
            if match[fl] == False:
                options = "".join([f'<option value="{fl}:{p}">{p}</option>' for p in pool])
            else:
                temp_pool = copy.deepcopy(pool)
                temp_pool.remove(match[fl])
                options = f'<option value="{fl}:{match[fl]}" selected>{match[fl]}</option>' + "".join([f'<option value="{fl}:{p}">{p}</option>' for p in temp_pool])
            content_inner.append(floating.format(margin=margin, options=options, fl=fl, name=name, fid=index))
        content_inner = "".join(content_inner)
        output_html = f"""
                        <div class="input-group func-input-list parameters" style="border-left: 5px {current_border} solid; border-radius: 0.15rem;">
                            <div class="input-group-append" style="margin-bottom: {margin}rem;">
                                <span class="input-group-text" style="border-left: 0px solid" data-toggle="popover" data-trigger="hover" data-placement="top" data-content="{level}">{index}</span>
                                <span class="input-group-text" data-toggle="popover" data-trigger="hover" data-placement="top" data-content="{input_desc}">{display_name}</span>
                            </div>
                            {content_inner}
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
    if session.get("PHASE") == 2:
        session.pop('data', None)
    if session.get("PHASE") == 3:
        session.pop('processor', None)
    return output_html

def format_result(title, script, div, tools:list, popover="", outerStyle="", changedTitle="", displayContent=""):
    title = "■ " + title + " "
    div_id = 'result'+str(session['RESULT_INDEX_ID'])
    # title: "t", script, div, tools: ['delete', 'download', 'funcinfo']}
    close = f"""
            <button type="button" class="btn btn-sm btn-outline-secondary" id="btn_result_close_{session['RESULT_INDEX_ID']}" onclick="$(this).parent().parent().remove();closeDiv({session['RESULT_INDEX_ID']});">
               <i class="bi bi-x-circle"><span class="icon-text">Close</span> </i>
            </button>
            """ if 'close' in tools else ""
            
    hide = f"""
                <button type="button" class="btn btn-sm btn-outline-secondary" id="btn_result_hide_{session['RESULT_INDEX_ID']}" onclick="$(this).parent().prev().hide()">
                <i class="bi bi-dash-circle"><span class="icon-text">Hide</span></i>
                </button>
            """ if 'hide' in tools else ""
            
    show = f"""
            <button type="button" class="btn btn-sm btn-outline-secondary" id="btn_result_show_{session['RESULT_INDEX_ID']}"  onclick="$(this).parent().prev().show()">
                <i class="bi bi-plus-circle">  <span class="icon-text">Show</span></i>
            </button>
        """ if 'show' in tools else ""
        
    reset = f"""
            <button type="button" class="btn btn-sm btn-outline-secondary" id="btn_result_reset_{session['RESULT_INDEX_ID']}"  onclick="$(this).parent().parent().removeAttr('style');">
                <i class="bi bi-arrow-counterclockwise"> <span class="icon-text">Reset</span></i>
            </button>
        """ if 'reset' in tools else ""
        
    info = f"""
            <button type="button" class="btn btn-sm btn-outline-secondary" id="btn_result_info_{session['RESULT_INDEX_ID']}"  data-container="body" data-toggle="popover" data-placement="top" data-content="{popover}" onclick="$(this).popover('show')">
                <i class="bi bi-info-circle">  <span class="icon-text">Info</span></i>
            </button>
        """ if 'info' in tools else ""

    tools=f'''
            {close}{hide}{show}{reset}{info}
    '''
    
    if outerStyle != "":
        outerStyle = 'style="' + outerStyle + '"'
    if changedTitle != "":
        title = changedTitle
    if displayContent != "":
        displayContent = 'style="' + displayContent + '"'
        
    title_head = f"""<div class="DITWidget-Title">
                <b contenteditable="true">{title}</b>
        </div>""" if title != "" else ""
    
    html = f"""
    <div class="DITWidget" id="{div_id}" {outerStyle}>
        {title_head}
        <!-- Main Content Here -->
        <div class="main-content m-auto" {displayContent}>
                {script}
                {div}
        </div>
        <div class="DITWidget-Tools btn-group">
            {tools}
        </div>
    </div>
    """
    return html

