import pandas as pd
import nltk
from nltk.corpus import stopwords
from tqdm import tqdm
from nltk.text import TextCollection
import json
from collections import Iterable
from Translation import Translator
import datetime
from gensim.models.doc2vec import Doc2Vec, TaggedDocument
import numpy as np

class Processor:
    english_stopwords = stopwords.words('english')
    english_punctuations = [',', ':', ';', '?', '(', ')', '[', ']', '&', '!', '*', '@', '#', '$', '%', "、", "】", "【", "，", "`", "~"]
    html = {'&nbsp;': " ", "&quot;": '"', "&apos;": "'", "&amp;": "&", "&lt;": "<", "&gt;": ">", "&iexcl;": "¡",
           "&cent;": "¢",
           "&pound;": "£", "&curren;": "¤", "&yen;": "¥", "&brvbar;": "¦", "&sect;": "§", "&uml;": "¨", "&copy;": "",
           "&ordf;": "ª", "&laquo;": "«", "&not;": "¬", "&shy;": "­", "&reg;": "", "&macr;": "¯", "&deg;": "°",
           "&plusmn;": "±", "&sup2;": "²", "&sup3;": "³", "&acute;": "´", "&micro;": "µ", "&para;": "¶",
           "&middot;": "·", "&cedil;": "¸", "&sup1;": "¹", "&ordm;": "º", "&raquo;": "»", "&frac14;": "¼",
           "&frac12;": "½", "&frac34;": "¾", "&iquest;": "¿", "&times;": "×", "&divide;": "÷", "&Agrave;": "À",
           "&Aacute;": "Á", "&Acirc;": "Â", "&Atilde;": "Ã", "&Auml;": "Ä", "&Aring;": "Å", "&AElig;": "Æ",
           "&Ccedil;": "Ç", "&Egrave;": "È", "&Eacute;": "É", "&Ecirc;": "Ê", "&Euml;": "Ë", "&Igrave;": "Ì",
           "&Iacute;": "Í", "&Icirc;": "Î", "&Iuml;": "Ï", "&ETH;": "Ð", "&Ntilde;": "Ñ", "&Ograve;": "Ò",
           "&Oacute;": "Ó", "&Ocirc;": "Ô", "&Otilde;": "Õ", "&Ouml;": "Ö", "&Oslash;": "Ø", "&Ugrave;": "Ù",
           "&Uacute;": "Ú", "&Ucirc;": "Û", "&Uuml;": "Ü", "&Yacute;": "Ý", "&THORN;": "Þ", "&szlig;": "ß",
           "&agrave;": "à", "&aacute;": "á", "&acirc;": "â", "&atilde;": "ã", "&auml;": "ä", "&aring;": "å",
           "&aelig;": "æ", "&ccedil;": "ç", "&egrave;": "è", "&eacute;": "é", "&ecirc;": "ê", "&euml;": "ë",
           "&igrave;": "ì", "&iacute;": "í", "&icirc;": "î", "&iuml;": "ï", "&eth;": "ð", "&ntilde;": "ñ",
           "&ograve;": "ò", "&oacute;": "ó", "&ocirc;": "ô", "&otilde;": "õ", "&ouml;": "ö", "&oslash;": "ø",
           "&ugrave;": "ù", "&uacute;": "ú", "&ucirc;": "û", "&uuml;": "ü", "&yacute;": "ý", "&thorn;": "þ",
           "&yuml;": "ÿ", "&ndash;":""
           }

    def __init__(self, DATA, VENDORCODE_MAPPING=None, VENDORCODE_ORIGINAL=None, 
                 STOPWORDS=None, UNIT=None, COMBINE=None, MAPPING=None, USER_PATH='',
                 DICTIONARY=None, VENDORCODE=None, OUTPUT=None, 
                 do_doc2vec=False,
                 marketplace_id="marketplace_id", item_name="item_name"):
        def vendor_code_mapping():
            vendor_mapping = pd.read_excel(VENDORCODE_MAPPING)
            vendor_code_original = pd.read_excel(VENDORCODE_ORIGINAL)
            vendor_code_cleaned = {}
            for index, row in tqdm(vendor_mapping.iterrows()):
                vendor_code_cleaned[row["Vendor_Code"]] = row["Simplified_Vendor_Name"]
            vendor_code_10 = {}
            for index, row in tqdm(vendor_code_original.iterrows()):
                vendor_code_10[row["po_vendor_name"].replace(" ", "")[0:7]] = row["po_vendor_code"]
                
            self.data["vendor"] = self.data["preferred_vendor"].map(lambda x:"")
            mapped = 0
            for index in tqdm(range(len(self.data))):
                if str(self.data.loc[index, "preferred_vendor"]).strip() in vendor_code_cleaned:
                    self.data.loc[index, "vendor"] = vendor_code_cleaned[str(self.data.loc[index, "preferred_vendor"]).strip()]
                    mapped += 1
                elif str(self.data.loc[index, "primary_vendor"]).strip() in vendor_code_cleaned:
                    self.data.loc[index, "vendor"] = vendor_code_cleaned[str(self.data.loc[index, "primary_vendor"]).strip()]
                    mapped += 1
                elif str(self.data.loc[index, "preferred_vendor_name"]).replace(" ", "")[0:7] in vendor_code_10:
                    code = vendor_code_10[str(self.data.loc[index, "preferred_vendor_name"]).replace(" ", "")[0:7]]
                    self.data.loc[index, "vendor"] = vendor_code_cleaned[code]
                    mapped += 1
                elif str(self.data.loc[index, "primary_vendor_name"]).replace(" ", "")[0:7] in vendor_code_10:
                    code = vendor_code_10[str(self.data.loc[index, "primary_vendor_name"]).replace(" ", "")[0:7]]
                    self.data.loc[index, "vendor"] = vendor_code_cleaned[code]
                    mapped += 1
                elif type(self.data.loc[index, "preferred_vendor_name"]) == str:
                    self.data.loc[index, "vendor"] = self.data.loc[index, "preferred_vendor_name"]
                else:
                    self.data.loc[index, "vendor"] = self.data.loc[index, "preferred_vendor_name"]
            print(f"\n>> Vendor Code Mapping: {mapped+1} in {index+1} Mapped    ")
        
        def is_number(s):
            try:
                float(s)
                return True
            except ValueError:
                pass
         
            try:
                import unicodedata
                unicodedata.numeric(s)
                return True
            except (TypeError, ValueError):
                pass
            return False
        
        def simplify(str_list):
            for index, value in enumerate(str_list):
                try:
                    if is_number(value) and str_list[index+1] in unit:
                        str_list[index] = value + unit[str_list[index+1]]
                        str_list[index+1] = "Amazon"
                    if (value, str_list[index+1]) in combine:
                        str_list[index] = combine[(value, str_list[index+1])]
                        str_list[index+1] = "Amazon"
                    if (value, str_list[index+1], str_list[index+2]) in combine:
                        str_list[index] = combine[(value, str_list[index+1], str_list[index+2])]
                        str_list[index+1] = "Amazon"
                        str_list[index+2] = "Amazon"
                    if is_number(value) and str_list[index+1]=="x" and is_number(str_list[index+2]):
                        str_list[index] = value+str_list[index+1]+str_list[index+2]
                        str_list[index+1], str_list[index+2] = "Amazon", "Amazon"
                except:
                    pass
            return str_list
        
        def mapping(str_list):
            f = False
            for index, value in enumerate(str_list):
                if value in mapping_dict:
                    str_list[index] = mapping_dict[value]
                    f = True
            if f:
                str_list = flatten(str_list)
            return str_list
        
        # main cleaning function
        def gtk_simple(x_origin):
            x = str(x_origin)
            if x.strip() in self.dictionary:
                x = self.dictionary[x.strip()]
            try:
                x = nltk.word_tokenize(x.strip())
                x = [i.lower() for i in x if not i in Processor.english_stopwords]
                x = [i for i in x if not i in Processor.english_stopwords]
                x = [i for i in x if not '/' in i]
                x = simplify(x)
                x = mapping(x)
                x = [i for i in x if not i in technique_stopwords]
                x = [i for i in x if not i in Processor.english_punctuations]
                for punc in Processor.english_punctuations:
                    x = [i.replace(punc, "") for i in x]
                x = [i.replace('-', '') if i[0]=='-' or i[-1]=='-' else i for i in x]
                x = [i for i in x if i != '']
                return x
            except:
                return ""
        
        def flatten(items):
            for x in items:
                if isinstance(x, Iterable) and not isinstance(x, (str, bytes)):
                    yield from flatten(x)
                else:
                    yield x
            
        self.DICTIONARY = DICTIONARY
        self.VENDORCODE = VENDORCODE
        self.OUTPUT = OUTPUT
        self.USER_PATH = USER_PATH
        self.enable_topk = False
        print("\n>> Reading Data...    ")
        self.data = DATA
        print("\n>> Reading Data Finished    ")

        print("\n>> Translating...    ")

        if str(DICTIONARY) == 'None':
            translation_pos = [marketplace_id, item_name]
            self.dictionary = Translator(self.data, name=translation_pos).dictionary
        else:
            di = pd.read_excel("{}".format(DICTIONARY))
            self.dictionary = {}
            for index, row in di.iterrows():
                self.dictionary[str(row["item_name"]).strip()] = row["item_name_translate"]
        print("\n>> Translation Finished    ")
        # stopwords and cleaning strategy - implemented on translated data
        print("\n>> Tokenizing...    ")

        technique_stopwords = STOPWORDS
        unit = UNIT
        combine = COMBINE
        combine = {tuple(i.strip().split(",")):combine[i] for i in combine}
        mapping_dict = MAPPING
        for i in range(1000):
            mapping_dict[str(i)+"-"+"watt"] = str(i)+"w"
            mapping_dict[str(i)+"-"+"Watt"] = str(i)+"w"
        
        # -----------------------------Data Cleaning------------------------------ #
        tqdm.pandas(desc="processing")
        str_list = ["item_name", "gl_product_group_desc", "subcategory_desc", "primary_vendor_name", "preferred_vendor_name"]
        for i in str_list:
            for h in Processor.html:
                self.data.loc[:, i] = self.data.loc[:, i].str.replace(h, Processor.html[h])
        self.data["Tokenize"] = self.data.progress_apply(lambda x: gtk_simple(x["item_name"]), axis=1)
        self.data['item_name_original'] = self.data['item_name']
        self.data['item_name'] = self.data['Tokenize'].map(lambda x: " ".join(x))
        print("\n>> Tokenizing Finished    ")
        print("\n>> Vendor Code Mapping...    ")
        vendor_code_mapping()
        print("\n>> Vendor Code Mapping Finished    ")
        print("\n>> Extracting Keywords...    ")
        self.tfidf_extraction()
        print("\n>>Keywords Extraction Finished    ")
        if do_doc2vec:
            self.doc2vec()
        print(">> End")

    def save(self):
        curr_time = datetime.datetime.now()
        time_str = curr_time.strftime("%Y%m%d%H%M%S")
        if self.OUTPUT is None:
            output =  f'{self.USER_PATH}data/processed_data_{time_str}.xlsx'
            self.data.to_excel("{}".format(output), index=False)
        else:
            if '.' not in self.OUTPUT:
                OUTPUT = self.USER_PATH + str(self.OUTPUT) + '.xlsx'
            self.data.to_excel("{}".format(str(OUTPUT)), index=False)
            
    def save_dictionary(self, path=None):
        curr_time = datetime.datetime.now()
        time_str = curr_time.strftime("%Y%m%d%H%M%S")
        if path is None:
            output =  f'{self.USER_PATH}dictionary/translation_{time_str}.xlsx'
        keys = self.dictionary.keys()
        values = self.dictionary.values()
        df = pd.DataFrame({'item_name':keys,'item_name_translate':values})
        df.to_excel('{}'.format(output), index=False)
    
    def tfidf_extraction(self, subset=None):
        if subset is not None:
            data = self.data[subset]
        else:
            data = self.data
        get_idf = TextCollection(data.Tokenize.to_list())
        word_list = list(set([w for l in data.Tokenize.to_list() for w in l]))
        full_winfo = [[word, idf, tag[1]] for word, idf, tag in zip(word_list, [get_idf.idf(i) for i in word_list], nltk.pos_tag(word_list))]
        self.keywords = pd.DataFrame([i for i in full_winfo if i[2] in ["JJ", "NNP", "VBP", 'VBG', 'VBD', 'VBN', 'CD', 'NN', 'NNPS', 'RB', 'IN'] 
                                      and not is_number(i[0])], columns=["word", "idf", "tag"]).sort_values(by="idf", ascending=True).reset_index(drop=False)
        self.full_words = pd.DataFrame(full_winfo, columns=["word", "idf", "tag"]).sort_values(by="idf", ascending=True).reset_index(drop=False)
        self.enable_topk == True
        
    def topk(self, k):
        if self.enable_topk:
            return self.keywords.loc[0: k]['word'].to_list()
        else:
            return None
    def co_occurence(self, scale = 500):
        co_dict = {}
        top_list = self.keywords['word'].to_list()[0:scale]
        print(">> Start Building Co-occurence Matrix...")
        for item_doc in self.data.Tokenize.to_list():
            for first_word in item_doc:
                if first_word not in top_list:
                    continue
                for second_word in item_doc:
                    if second_word not in top_list:
                        continue
                    oc = (first_word, second_word)
                    co = (second_word, first_word)
                    if oc in co_dict:
                        co_dict[oc] += 1
                    elif co in co_dict:
                        co_dict[co] += 1
                    else:
                        co_dict[oc] = 1
        for dup in co_dict:
            if dup[0] != dup[1]:
                co_dict[dup] = int(co_dict[dup]/2)
        print(">> Finished Building Co Matrix")
        nodes, edges = [], []
        for co in co_dict:
            if co[0] == co[1]:
                nodes.append([co[0], co_dict[co]])
            else:
                edges.append([co[0], co[1], co_dict[co]])
        return nodes, edges
        
    def doc2vec(self):
        print("\n>> Training Document Vectors by Doc2Vec Model...")
        documents = [TaggedDocument(doc, [i]) for i, doc in enumerate(self.data.Tokenize.to_list())]
        self.d2v_model = Doc2Vec(documents, vector_size=7, window=2, min_count=1, workers=4)
        self.data['DocVector'] = self.data.index.map(lambda i: self.d2v_model.docvecs.vectors_docs[i])
        print("\n>> Training Finished    ")
        
    def bag_of_word(self):
        sub_cl = TextCollection(self.data["Tokenize"].to_list())
        sub_collection = list(set([word for text in self.data["Tokenize"].to_list() for word in text]))
        sub_dict = {}
        print("\n>> Extracting Bag-of-word Vector with TF-IDF...")
        for i in tqdm(sub_collection):
            sub_dict[i] = sub_cl.idf(i)
        sub_pos = {}
        index = 0
        for i in tqdm(sub_collection):
            sub_pos[i] = index
            index+=1
        sub_len = len(sub_collection)
        def d2v(word_list):
            v = np.zeros(sub_len)
            for i in word_list:
                v[sub_pos[i]] = sub_dict[i]
            return v
        tqdm.pandas(desc="Processing")
        self.sub_pos = sub_pos
        BaggingVector = self.data["Tokenize"].progress_apply(lambda x: d2v(x))
        print("\n>> Extracting Finished...")
        return BaggingVector, sub_pos
        
def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        pass
 
    try:
        import unicodedata
        unicodedata.numeric(s)
        return True
    except (TypeError, ValueError):
        pass
    return False
        
if __name__ == '__main__':
    # read data and dictionary
    init = dict(
    DATA=pd.read_excel("Backup/CE WA Sub.xlsx"),
    VENDORCODE_MAPPING="static/user/public/mapping/Vendor Code Mapping.xlsx",
    VENDORCODE_ORIGINAL="static/user/public/mapping/Vendor Code Mapping - Original.xlsx",
    STOPWORDS=json.load(open("static/user/public/settings/stopwords.json", 'r')),
    UNIT=json.load(open("static/user/public/settings/unit.json", 'r')),
    COMBINE=json.load(open("static/user/public/settings/combine.json", 'r')),
    MAPPING=json.load(open("static/user/public/settings/mapping.json", 'r')),
    do_doc2vec=True,
    do_clustering=True
    )
    
    #p_test = Processor(**init)




