import pandas as pd
import requests
from tqdm import tqdm
from google_trans_new import google_translator

class Translator:
    '''
       initialization input: data, name:[mp_id, item_name] (column names in data)
       result variable: self.dictionary
       method: self.save(path)
    
    '''
    mpid_mapping = {
        1:"US",3:"UK",4:"Germany",5:"France",35691:"Italy",101611:"Italy",
        44551:"Spain",123311:"Spain",623225021:"Egypt",63384901:"Egypt",
        44571:"India",123591:"India",6:"Japan",7:"Canada",3240:"China",
        3240:"China",526970:"Brazil",142980:"Brazil",771770:"Mexico",
        181720:"Mexico",111172:"Australia",12542:"Australia",111162:"Russia",
        12532:"Russia",328451:"Netherlands",260281:"Netherlands",
        338801:"United Arab Emirates",314421:"United Arab Emirates",
        338811:"Saudi Arabia",314691:"Saudi Arabia",44561:"India",
        243811:"India",218691:"India",338851:"Turkey",318651:"Turkey",
        104444012:"Singapore",114978812:"Singapore",712115121:"Poland",
        154936711:"Poland",704403121:"Sweden",161450861:"Sweden",
        1338980:"US",1398340:"Canada",330551:"UK",330871:"Germany",
        330921:"France",330711:"Italy",330731:"Spain",151302:"Singapore",
        121322:"Japan",264730:"US",903668:"Canada",279841:"UK",
        289371:"Germany",300671:"France",287991:"Italy",288961:"Spain",
        13152:"Japan",50462:"Singapore",1367890:"N/A",316340:"N/A",
        331021:"N/A",305631:"N/A",151232:"N/A",40232:"N/A",331051:"N/A",
        306801:"N/A",138103361:"UK",386046051:"UK",139629011:"Germany",
        386046061:"Germany",330961:"UK",1368230:"US",329821:"IN",
        1367840:"US",298901900:"BR",1531427160:"BR",298909900:"ZA",
        1645489180:"ZA",298837240:"KR",1618151160:"KR",199920:"US",
        1071810:"US",181352260:"US",884070040:"US"}
    mapping = {'&nbsp;': ' ', '&quot;': '"', '&apos;': "'", '&amp;': '&',
             '&lt;': '<', '&gt;': '>', '&iexcl;': '¡', '&cent;': '¢', '&pound;': '£',
             '&curren;': '¤', '&yen;': '¥', '&brvbar;': '¦', '&sect;': '§', '&uml;': '¨',
             '&copy;': '', '&ordf;': 'ª', '&laquo;': '«', '&not;': '¬', '&shy;': '\xad',
             '&reg;': '', '&macr;': '¯', '&deg;': '°', '&plusmn;': '±', '&sup2;': '²',
             '&sup3;': '³', '&acute;': '´', '&micro;': 'µ', '&para;': '¶', '&middot;': '·',
             '&cedil;': '¸', '&sup1;': '¹', '&ordm;': 'º', '&raquo;': '»', '&frac14;': '¼',
             '&frac12;': '½', '&frac34;': '¾', '&iquest;': '¿', '&times;': '×', '&divide;': '÷',
             '&Agrave;': 'À', '&Aacute;': 'Á', '&Acirc;': 'Â', '&Atilde;': 'Ã', '&Auml;': 'Ä',
             '&Aring;': 'Å', '&AElig;': 'Æ', '&Ccedil;': 'Ç', '&Egrave;': 'È', '&Eacute;': 'É',
             '&Ecirc;': 'Ê', '&Euml;': 'Ë', '&Igrave;': 'Ì', '&Iacute;': 'Í', '&Icirc;': 'Î',
             '&Iuml;': 'Ï', '&ETH;': 'Ð', '&Ntilde;': 'Ñ', '&Ograve;': 'Ò', '&Oacute;': 'Ó',
             '&Ocirc;': 'Ô', '&Otilde;': 'Õ', '&Ouml;': 'Ö', '&Oslash;': 'Ø', '&Ugrave;': 'Ù',
             '&Uacute;': 'Ú', '&Ucirc;': 'Û', '&Uuml;': 'Ü', '&Yacute;': 'Ý', '&THORN;': 'Þ',
             '&szlig;': 'ß', '&agrave;': 'à', '&aacute;': 'á', '&acirc;': 'â', '&atilde;': 'ã',
             '&auml;': 'ä', '&aring;': 'å', '&aelig;': 'æ', '&ccedil;': 'ç', '&egrave;': 'è',
             '&eacute;': 'é', '&ecirc;': 'ê', '&euml;': 'ë', '&igrave;': 'ì', '&iacute;': 'í',
             '&icirc;': 'î', '&iuml;': 'ï', '&eth;': 'ð', '&ntilde;': 'ñ', '&ograve;': 'ò',
             '&oacute;': 'ó', '&ocirc;': 'ô', '&otilde;': 'õ', '&ouml;': 'ö', '&oslash;': 'ø',
             '&ugrave;': 'ù', '&uacute;': 'ú', '&ucirc;': 'û', '&uuml;': 'ü', '&yacute;': 'ý',
             '&thorn;': 'þ', '&yuml;': 'ÿ', '&ndash;': ''}
    EN_list = ["US", "UK", "Canada", 'Australia', "United Arab Emirates", 'Singapore', 'India', "Saudi Arabia"]
    Latin = ['Germany', 'France', 'Italy', 'Spain', 'Egypt', 'Egypt', 
             'Brazil', 'Mexico', 'Russia', 'Netherlands', "United Arab Emirates", 
             "Turkey", "Poland", "Sweden", "BR"]
    english_punctuations = [',', '.', ':', ';', '?', '(', ')', '[', ']', '&', '!', '*', '@', '#', '$', "、", "】", "【", "，"]

    def __init__(self, dataT:'pd.DataFrame', name=None):
        s = requests.session()
        s.keep_alive = False
        group = ["marketplace_id", "item_name"]
        if name is not None:
            group = [name[0], name[1]]
        
        self.data = dataT[group]
        self.data['marketplace'] = self.data[group[0]].map(lambda x: Translator.mpid_mapping[int(x)] if int(x) in Translator.mpid_mapping else x)
        group = ['marketplace', 'item_name']
        self.mp_itnm = self.data.groupby(group).groups
        self.translator = google_translator()
        self.dictionary = {}
        self.dictionary_failed = []
        print("\n>> Start Translation")
        self.translate()
        print("\n>> Translation Finished")

    def trans(self, word, mp):
        if mp == 'France':
            return self.translator.translate(word, lang_src='fr', lang_tgt='en')
        if mp in Translator.Latin:
            return self.translator.translate(word,lang_tgt='en')
        else:
            if mp=='Japan':
                return self.translator.translate(word.replace(" ", ","), lang_src='jp', lang_tgt='en').replace(",", " ")
            if mp=='China':
                return self.translator.translate(word.replace(" ", ","), lang_src='cn', lang_tgt='en').replace(",", " ")
            return self.translator.translate(word.replace(" ", ","), lang_tgt='en').replace(",", " ")

    def translate(self):
        data_hash = self.mp_itnm
        wait = [i for i in data_hash if i[0] not in Translator.EN_list]
        self.gtk_join(wait)
        
    def gtk_join(self, wait):
        mp_dict = {}
        for w in wait:
            if w[0] not in mp_dict:
                mp_dict[w[0]] = [str(w[1])]
            else:
                if len(mp_dict[w[0]][-1]) >=4000:
                    mp_dict[w[0]].append(str(w[1]))
                else:
                    mp_dict[w[0]][-1] += " \r\n\r\n "+str(w[1])
        for mp in mp_dict:
            for h in Translator.mapping:
                mp_dict[mp] = [i.replace(h, Translator.mapping[h]) for i in mp_dict[mp]]
        mp_trans = {}
        for mp in tqdm(mp_dict):
            for mp_list_inner in tqdm(mp_dict[mp]):
                if mp not in mp_trans:
                    mp_trans[mp] = [self.trans(mp_list_inner, mp)]
                else:
                    mp_trans[mp].append(self.trans(mp_list_inner, mp))
        temp = {}
        tid = 0
        alignment = {}
        for mp in mp_trans:
            for index, value in enumerate(mp_trans[mp]):
                mp_trans[mp][index] = mp_trans[mp][index]
                temp[tid] = [mp_trans[mp][index], mp_dict[mp][index]]
                alignment[tid] = [len(mp_trans[mp][index].split("\r\n")) == len(mp_dict[mp][index].split("\r\n")), 
                                  mp_dict[mp][index].split("\r\n"), mp_trans[mp][index].split("\r\n")]
                tid+=1
        for i in alignment:
            if alignment[i][0] == True:
                for mpd, mpt in zip(alignment[i][1], alignment[i][2]):
                    self.dictionary[mpd.strip()] = mpt.strip()
            else:
                self.dictionary_failed.append(alignment[i][1])
        
        return self.dictionary 
        
    def save(self, path):
        keys = self.dictionary.keys()
        values = self.dictionary.values()
        df = pd.DataFrame({'item_name':keys,'item_name_translate':values})
        if '.' not in path:
            path = str(path) + '.xlsx'
        df.to_excel('{}'.format(str(path)), index=False)


if __name__ == '__main__':
    CATEGORY = "CE WA Sub.xlsx"
    print("\n>> Reading Data")
    dataT = pd.read_excel("C:/Users/ljiechen/Documents/20210128 Business Overview/CE WA Sub.xlsx")
    print("\n>> Data Loaded")
    t = Translator(dataT)
