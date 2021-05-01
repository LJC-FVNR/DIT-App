# -*- coding: utf-8 -*-
import json
import os
import datetime


class USER:
    def __init__(self, username):
        self.username = username
        self.path = f'static/user/{username}/'
        self.public_path = 'static/user/public/'
        self.calling_parameters = {}
        if not os.path.exists(self.path):
            self._generate_user()
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
        self.update_info_file()
    
    def update_info_file(self):
        current_path = self.path + 'data/'
        file_list = file_name_listdir(current_path)
        for i in file_list:
            if i not in self.data:
                self.data[i] = [current_path+i, get_now()]
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
            self.data[i] = [current_path+i, get_now()]
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
        return available_func
        
            

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