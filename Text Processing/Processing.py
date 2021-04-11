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


class Processor:
    english_stopwords = stopwords.words('english')
    english_punctuations = [',', '.', ':', ';', '?', '(', ')', '[', ']', '&', '!', '*', '@', '#', '$', '%', "、", "】", "【", "，", "`", "~"]
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

    def __init__(self, CATEGORY, DICTIONARY=None, VENDORCODE=None, OUTPUT=None, translation_pos=["marketplace", "item_name"], do_doc2vec=False):
        def vendor_code_mapping():
            vendor_mapping = pd.read_excel("Vendor Code Mapping.xlsx")
            vendor_code_original = pd.read_excel("Vendor Code Mapping - Original.xlsx")
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
                    self.data.loc[index, "vendor"] = vendor_code_cleaned[self.data.loc[index, "preferred_vendor"]]
                    mapped += 1
                elif str(self.data.loc[index, "primary_vendor"]).strip() in vendor_code_cleaned:
                    self.data.loc[index, "vendor"] = vendor_code_cleaned[self.data.loc[index, "primary_vendor"]]
                    mapped += 1
                elif str(self.data.loc[index, "preferred_vendor_name"]).replace(" ", "")[0:7] in vendor_code_10:
                    code = vendor_code_10[self.data.loc[index, "preferred_vendor_name"].replace(" ", "")[0:7]]
                    self.data.loc[index, "vendor"] = vendor_code_cleaned[code]
                    mapped += 1
                elif str(self.data.loc[index, "primary_vendor_name"]).replace(" ", "")[0:7] in vendor_code_10:
                    code = vendor_code_10[self.data.loc[index, "primary_vendor_name"].replace(" ", "")[0:7]]
                    self.data.loc[index, "vendor"] = vendor_code_cleaned[code]
                    mapped += 1
                elif type(self.data.loc[index, "preferred_vendor_name"]) == str:
                    self.data.loc[index, "vendor"] = self.data.loc[index, "preferred_vendor_name"]
                else:
                    self.data.loc[index, "vendor"] = self.data.loc[index, "preferred_vendor_name"]
            print(f"\n>> Vendor Code Mapping: {mapped+1} in {index+1} Mapped")
        
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
        
        self.CATEGORY = CATEGORY
        self.DICTIONARY = DICTIONARY
        self.VENDORCODE = VENDORCODE
        self.OUTPUT = OUTPUT
        print("\n>> Reading Data...")
        self.data = pd.read_excel("{}".format(CATEGORY))
        print("\n>> Reading Data Finished")
        di = pd.read_excel("{}".format(DICTIONARY))
        print("\n>> Translating...")
        if DICTIONARY is None:
            self.dictionary = Translator(self.data, name=translation_pos).dictionary
        else:
            self.dictionary = {}
            for index, row in di.iterrows():
                self.dictionary[str(row["item_name"]).strip()] = row["item_name_translate"]
        print("\n>> Translation Finished")
        # stopwords and cleaning strategy - implemented on translated data
        print("\n>> Tokenizing...")
        with open('Processing/stopwords.json') as s:
            technique_stopwords = json.loads(s.read())
        with open('Processing/unit.json') as s:
            unit = json.loads(s.read())
        with open('Processing/combine.json') as s:
            combine = json.loads(s.read())
        combine = {tuple(i.strip().split(",")):combine[i] for i in combine}
        with open('Processing/mapping.json') as s:
            mapping_dict = json.loads(s.read())
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
        print("\n>> Tokenizing Finished")
        print("\n>> Vendor Code Mapping...")
        vendor_code_mapping()
        print("\n>> Vendor Code Mapping Finished")
        print("\n>> Extracting Keywords...")
        self.tfidf_extraction()
        print("\n>>Keywords Extraction Finished")
        if do_doc2vec:
            self.doc2vec()

    def save(self):
        curr_time = datetime.datetime.now()
        time_str = curr_time.strftime("%Y%m%d%H%M%S")
        if self.OUTPUT is None:
            output =  f'data_{time_str}.xlsx'
            self.data.to_excel("{}".format(output))
        else:
            if '.' not in self.OUTPUT:
                self.OUTPUT = str(self.OUTPUT) + '.xlsx'
            self.data.to_excel("{}".format(str(self.OUTPUT)))
            
    def save_dictionary(self, path=None):
        curr_time = datetime.datetime.now()
        time_str = curr_time.strftime("%Y%m%d%H%M%S")
        if path is None:
            output =  f'translation_{time_str}.xlsx'
            self.data.to_excel("{}".format(output))
        keys = self.dictionary.keys()
        values = self.dictionary.values()
        df = pd.DataFrame({'item_name':keys,'item_name_translate':values})
        if '.' not in path:
            path = str(path) + '.xlsx'
        df.to_excel('{}'.format(str(path)), index=False)
    
    def tfidf_extraction(self, subset=None):
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
        self.topk = lambda k: self.keywords.loc[0: k]['word'].to_list()
        
    def doc2vec(self):
        print("\n>> Training Document Vectors...")
        documents = [TaggedDocument(doc, [i]) for i, doc in enumerate(self.data.Tokenize.to_list())]
        self.d2v_model = Doc2Vec(documents, vector_size=10, window=2, min_count=1, workers=4)
        self.data['DocVector'] = self.data.index.map(lambda i: p_test.d2v_model.docvecs.vectors_docs[i])
        print("\n>> Training Finished")


if __name__ == '__main__':
    # read data and dictionary
    CATEGORY = "CE WA Sub.xlsx"
    DICTIONARY = "dict0408.xlsx"
    VENDORCODE = "Vendor Code Mapping.xlsx"
    OUTPUT= "raw_data_prepared.xlsx"
    p_test = Processor(CATEGORY, DICTIONARY, VENDORCODE, OUTPUT, do_doc2vec=True)




