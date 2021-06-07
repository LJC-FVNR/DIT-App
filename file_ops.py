# -*- coding: utf-8 -*-
import json
import os
import datetime
import pickledb
from urllib.parse import quote, unquote


class USER:
    
    def __init__(self, username):
        self.username = username
        self.path = f'static/user/{username}/'
        self.public_path = 'static/user/public/'
        self.calling_parameters = {}
        if not os.path.exists(self.path):
            self._generate_user()
            self._generate_global_sending_id()
        else:
            self.get_user()
            
            
    def _generate_user(self):
        mkdir(self.path)
        folders = ['data', 'dictionary', 'mapping']
        for f in folders:
            mkdir(self.path+f)
        self.update_public(refresh=True)        # initialize user info and settings
        self.form_info()
        self.save_info()
        self._generate_db()
        self._generate_global_sending_id()
            
    def _generate_db(self):
        template_db = pickledb.load('static/user/public/template_view/template_view.db', False, sig=False)
        if template_db.db.get(self.username) is None:
            template_db.dcreate(self.username)
            template_db.dump()
    
    def _generate_global_sending_id(self):
        gsid_db = pickledb.load('static/user/public/template_view/gsid.db', False, sig=False)
        if gsid_db.db.get(self.username) is None:
            import random
            import string
            global_sending_id = ''.join(random.sample(string.ascii_letters + string.digits, 12))
            gsid_db.set(self.username, global_sending_id)
            gsid_db.dump()
            
    def get_global_sending_id(self):
        gsid_db = pickledb.load('static/user/public/template_view/gsid.db', False, sig=False)
        return gsid_db.get(self.username)
        
    def form_info(self):
        self.info = {'data':self.data, 'dictionary':self.dictionary, 
             'mapping':self.mapping, 'settings':self.settings}
    
    def save_info(self):
        save_file(self.path, 'info.json', self.info)
    
    def get_user(self):
        with open(self.path+'info.json', 'r') as f:
            self.info = json.load(f)
        self.data = self.info['data']
        self.dictionary = self.info['dictionary']
        self.mapping = self.info['mapping']
        self.settings = self.info['settings']
        self.update_public(refresh=False)
        self.update_info_file()
        template_db = pickledb.load('static/user/public/template_view/template_view.db', False, sig=False)
        if template_db.db.get(self.username) is None:
            template_db.dcreate(self.username)
            template_db.dump()
    
    def update_info_file(self):
        current_path = self.path + 'data/'
        file_list = file_name_listdir(current_path)
        for i in file_list:
            if i not in self.data:
                self.data[i] = [quote(current_path+i), get_now()]
        current_path = self.path + 'dictionary/'
        file_list = file_name_listdir(current_path)
        for i in file_list:
            if i not in self.dictionary:
                self.dictionary[i] = [current_path+i, get_now()]
        current_path = self.path + 'mapping/'
        file_list = file_name_listdir(current_path)
        for i in file_list:
            if i not in self.mapping:
                self.mapping[i] = [current_path+i, get_now()]
        pop_list = []
        for check in self.data:
            if not os.path.exists(unquote(self.data[check][0])):
                pop_list.append(check)
        [self.data.pop(i) for i in pop_list]
        pop_list = []
        for check in self.dictionary:
            if not os.path.exists(self.dictionary[check][0]):
                pop_list.append(check)
        [self.dictionary.pop(i) for i in pop_list]
        pop_list = []
        for check in self.mapping:
            if not os.path.exists(self.mapping[check][0]):
                pop_list.append(check)
        [self.mapping.pop(i) for i in pop_list]
        self.form_info()

    def update_public(self, refresh=False):
        if refresh:
            self.data = {}              # {'default':['static/user/public/1.xlsx', ‘2021-04-12 13:52’], }
            self.dictionary = {}
            self.mapping = {}
            self.settings = {}          # {'combine':content, mapping:content, ...}
        current_path = self.public_path + 'data/'
        file_list = file_name_listdir(current_path)
        for i in file_list:
            self.data[i] = [quote(current_path+i), get_now()]
        current_path = self.public_path + 'dictionary/'
        file_list = file_name_listdir(current_path)
        for i in file_list:
            self.dictionary[i] = [current_path+i, get_now()]
        current_path = self.public_path + 'mapping/'
        file_list = file_name_listdir(current_path)
        for i in file_list:
            self.mapping[i] = [current_path+i, get_now()]
        current_path = self.public_path + 'settings/'
        file_list = file_name_listdir(current_path)
        for u_settings in file_list:
            name = u_settings.split('.')[0]
            with open(current_path+u_settings, 'r') as f:
                self.settings[name] = json.load(f)
                
    def refresh_user_info(self):
        self.update_public(refresh=True)
        self.get_user()
                
    def drop_file(self, filelink):
        if os.path.exists(filelink):
            os.remove(filelink)
        self.update_info_file()
    
    def change_settings(self, name, content):
        try:
            self.info['settings'][name] = content
            self.save_info()
        except:
            print('failed on updating settings')
            
            
    # -------------------- html interaction ---------------------
    def get_func_settings(self, phase):
        # 1. get all available functions during this phase
        fs = self.info['settings']['func_settings']
        available_func = {}
        for module in fs:
            for func in fs[module]:
                if 'available_phase' in fs[module][func]:
                    if phase in fs[module][func]['available_phase']:
                        available_func[module+"."+func] = fs[module][func]
        available_func_class = {}
        for i in available_func:
            if available_func[i]['tab'] in available_func_class:
                available_func_class[available_func[i]['tab']][i] = available_func[i]
            else:
                available_func_class[available_func[i]['tab']] = {i: available_func[i]}
        return available_func_class
    
    # ------------------- view ops --------------------------------
    def save_template(self, view, model, layout, template_name, layout_dict):
        t = get_now()
        template_db = pickledb.load('static/user/public/template_view/template_view.db', False, sig=False)
        temp = {'view':view, 'model':model, 'layout':layout, 'time':t, 'layout_dict':layout_dict}
        template_db.dadd(self.username, (template_name, temp))
        template_db.dump()
        
    def user_template_management(self):
        template_db = pickledb.load('static/user/public/template_view/template_view.db', False, sig=False)
        temp_collection = template_db.get(self.username)
        if temp_collection is None:
            temp_collection = {}
        return temp_collection
    
    def template_rename(self, template_name, template_new_name):
        template_db = pickledb.load('static/user/public/template_view/template_view.db', False, sig=False)
        temp_content = template_db.dget(self.username, template_name)
        template_db.dpop(self.username, template_name)
        template_db.dadd(self.username, (template_new_name, temp_content))
        template_db.dump()
        
    def template_delete(self, template_name):
        template_db = pickledb.load('static/user/public/template_view/template_view.db', False, sig=False)
        template_db.dpop(self.username, template_name)
        template_db.dump()
        
        
class TemplateExternalReader:
    def __init__(self, username):
        self.username = username
    
    def get_template_name(self):
        template_db = pickledb.load('static/user/public/template_view/template_view.db', False, sig=False)
        return template_db.dkeys(self.username)
        
    def get_template_view(self, template_name):
        template_db = pickledb.load('static/user/public/template_view/template_view.db', False, sig=False)
        view, layout, t, layout_dict = template_db.dget(self.username, template_name)['view'], template_db.dget(self.username, template_name)['layout'], template_db.dget(self.username, template_name)['time'], template_db.dget(self.username, template_name)['layout_dict']
        return view, layout, t, layout_dict
    
    def get_template_model(self, template_name):
        template_db = pickledb.load('static/user/public/template_view/template_view.db', False, sig=False)
        model, layout, t, layout_dict = template_db.dget(self.username, template_name)['model'], template_db.dget(self.username, template_name)['layout'], template_db.dget(self.username, template_name)['time'], template_db.dget(self.username, template_name)['layout_dict']
        return model, layout, t, layout_dict
    

# ----------------- external functions ---------------------                
    
def get_now():
    curr_time = datetime.datetime.now()
    time_str = curr_time.strftime("%Y-%m-%d %H:%M")
    return time_str
    
def file_name_listdir(file_dir):
    filel = []
    for files in os.listdir(file_dir):
        filel.append(files)
    return filel

def mkdir(path):
	folder = os.path.exists(path)
	if not folder:
		os.makedirs(path)   
		

def save_file(path, name, content, filetype='.json'):
    if filetype=='.json':
        content = json.dumps(content)
        mkdir(path)
        if path[-1] != '/':
            path += '/'
        if name[-5:] != filetype:
            name += filetype
        f = open(path+name, 'w')
        f.write(content)
        f.close()

def getFileSize(filePath):

    fsize = os.path.getsize(filePath)
    if fsize < 1024:
    	return f"{round(fsize,2)}Byte"
    else: 
    	KBX = fsize/1024
    	if KBX < 1024:
    		return f"{round(KBX,2)}K"
    	else:
    		MBX = KBX /1024
    		if MBX < 1024:
    			return f'{round(MBX,2)}M'
    		else:
    			return f'{round(MBX/1024)}G'