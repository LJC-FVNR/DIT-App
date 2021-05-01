import re
from sparklines import sparklines
from matplotlib import colors
import seaborn as sns
import numpy as np
import copy
import pandas as pd
from HTML_HeatMap import HStyler
import holoviews as hv



class PB_Data:
    default_classification = ['reporting_year','reporting_qtr', 'regiond_id',
               'marketplace_id', 'marketplace', 'asin', 'item_name', 'launch_bucket',
               'is_deprecated',
               'wbr_division', 'hdl_classification', 'gl_product_group',
               'gl_product_group_desc', 'category_code', 'category_desc',
               'subcategory_code', 'subcategory_desc', 'primary_vendor',
               'primary_vendor_name', 'preferred_vendor_name', 'preferred_vendor', 'vendor']
    default_performance = ['ops', 'list_price', 'total_gv', 'product_site_launch_day', 'asin_launch_day',
               'ordered_units', 'net_ordered_gms', 'on_hand_quantity', 'on_hand_cost',
               'quantity_shipped', 'contribution_profit_amt', 'revenue_share_amt',
               'product_cogs_amt', 'net_ppm_amt', 'ppm_amt', 'ship_profit_amt',
               'sales_discounts_amt', 'product_gms', 'shipping_revenue_amt',
               'subscription_revenue_amt', 'shipping_cost_amt', 'display_ads_amt',
               'vendor_profit_amt', 'one_star', 'two_star', 'three_star', 'four_star',
               'five_star', 'total_reviews', 'total_stars', 'returned_units',
               'refunded_units', 'refunded_amt', 'andon_count']
    key_attribute_set = ['ordered_units', 'ASIN', 'item_name', 'vendor_name', 'vendor_code',
                     'reporting_year', 'marketplace_id', 'marketplace', 'hdl_classification']
    
    def __init__(self, processor, classification:list, performance:list, 
                 name='unnamed', universal_label="Full Data", time_series=None, **kwargs):
        '''
        data: raw data
        classification: slice of classification columns (
               'reporting_year','reporting_qtr', 'regiond_id',
               'marketplace_id', 'marketplace', 'asin', 'item_name', 'launch_bucket',
               'product_site_launch_day', 'asin_launch_day', 'is_deprecated',
               'wbr_division', 'hdl_classification', 'gl_product_group',
               'gl_product_group_desc', 'category_code', 'category_desc',
               'subcategory_code', 'subcategory_desc', 'primary_vendor',
               'primary_vendor_name', 'preferred_vendor_name', 'preferred_vendor')
        performance:    slice of performance columns (
               'ops', 'list_price', 'total_gv',
               'ordered_units', 'net_ordered_gms', 'on_hand_quantity', 'on_hand_cost',
               'quantity_shipped', 'contribution_profit_amt', 'revenue_share_amt',
               'product_cogs_amt', 'net_ppm_amt', 'ppm_amt', 'ship_profit_amt',
               'sales_discounts_amt', 'product_gms', 'shipping_revenue_amt',
               'subscription_revenue_amt', 'shipping_cost_amt', 'display_ads_amt',
               'vendor_profit_amt', 'one_star', 'two_star', 'three_star', 'four_star',
               'five_star', 'total_reviews', 'total_stars', 'returned_units',
               'refunded_units', 'refunded_amt', 'andon_count')
        name: data name
        **kwargs: positioning the columns of key requirements
        '''
        self.processor = processor
        data = processor.data
        self.reset_data = copy.deepcopy(data)
        self.default_cmap = [sns.light_palette("green", as_cmap=True), sns.light_palette("purple", as_cmap=True)]
        self.attribute = {}
        self.config_currency = ['list_price', 'preferred_vendor_cost', 'ops', 'net_ordered_gms', 'on_hand_cost', 'contribution_profit_amt', 'revenue_share_amt',
                               'product_cogs_amt', 'ship_profit_amt',
                               'sales_discounts_amt', 'product_gms', 'shipping_revenue_amt',
                               'subscription_revenue_amt', 'shipping_cost_amt', 'display_ads_amt',
                               'vendor_profit_amt', 'refunded_amt']
        self.set_attribute(kwargs) # self.attribute: key features utilized in search section
        self.set_label(classification, performance)
        self.set_data(data, universal_label)
        self.set_time(time_series)
        self.set_category()
        
    def reset(self):
        self.data = self.reset_data
    
    def set_config_currency(self, config_currency:list):
        self.config_currency = config_currency
        
    def set_time(self, time_series=None):
        if time_series is None:
            time_series = ['reporting_year','reporting_qtr']
        time_series = self.uniform_feature(time_series)
        self.data['Time_Series'] = eval("+".join([f'self.data["{i}"].astype("str")' for i in time_series]))
        self.classification.append('Time_Series')
        
    def set_type(self, type_map):
        for column in type_map:
            try:
                self.data[column] = self.data[column].astype(type_map[column])
            except:
                pass
            
    def set_category(self):
        for c in self.classification:
            if c not in self.performance:
                self.data[c] = self.data[c].astype('object')


    def set_attribute(self, kwargs):
        # initialize key features / uniform attr name
        # self.attribute['year'] = 'reporting_year'
        self.attribute['ordered_units'] = 'ordered_units'
        self.attribute['ASIN'] = 'asin'
        self.attribute['item_name'] = 'item_name'
        self.attribute['vendor_name'] = 'preferred_vendor_name'
        self.attribute['vendor_code'] = 'preferred_vendor'
        self.attribute['reporting_year'] = 'reporting_year'
        self.attribute['marketplace_id'] = 'marketplace_id'
        self.attribute['marketplace'] = 'marketplace'
        self.attribute['hdl_classification'] = 'hdl_classification'
        for i in kwargs:
            self.attribute[i] = kwargs[i]

    def set_data(self, data, universal_label):
        # initialize / manipulate data
        data['records'] = data.iloc[:, 0].map(lambda x: 1)
        self.data = data
        self.data['combinatorial_queries'] = self.data.iloc[:, 0].map(lambda x: '')
        self.classification.append('combinatorial_queries')
        self.latest_query = copy.deepcopy(data)
        self.universal_label = universal_label
        return self
    
    def select_data(self, feature=['reporting_year', 'reporting_qtr'] , operator=['==', '=='], value=['2020', '1'], inheritance=False):
        left = feature if type(feature) is list else [feature]
        mid = operator if type(operator) is list else [operator]
        right = value if type(value) is list else [value]
        min_len = min([len(left), len(mid), len(right)])
        left, mid, right = left[0:min_len], mid[0:min_len], right[0:min_len]
        select = list(zip(left, mid, right))
        selected = []
        for s in select:
            selected += [f'(self.data["{s[0]}"]{s[1]}{s[2]})'] if inheritance==False else [f'(self.latest_query["{s[0]}"]{s[1]}{s[2]})']
        selected = "&".join(selected)
        self.latest_query = copy.deepcopy(self.data[eval(selected)]) if inheritance==False else copy.deepcopy(self.latest_query[eval(selected)])
        return self.latest_query
        
    def set_label(self, classification, performance):
        # initialize / manipulate feature labels
        self.classification = classification
        self.performance = performance
        return self
    
    def query_by(self, kw_and=None, kw_or=None, kw_not=None, attr=None, inheritance=False):
        q_data = self.data if inheritance==False else self.latest_query
        q_data_str = 'self.data' if inheritance==False else 'self.latest_query'
        extract_full = lambda s: re.findall('["](.*?)["]', s)
        extract_single = lambda s: [i for i in re.sub('\\".*?\\"', '', s).split(" ") if i != '']
        # search presents
        if kw_and is None or kw_and == '':
            crit_and = q_data[attr].astype('str').str.contains('', regex=True)
        else:
            kw_and_single = extract_single(kw_and)
            kw_and_full = [r'\\b'+i+r'\\b' for i in extract_full(kw_and)]
            kw_and = kw_and_single + kw_and_full
            form_and = [f"({q_data_str}[attr].astype('str').str.contains('(?i){iand}', regex=True))" for iand in kw_and]
            crit_and = eval("&".join(form_and))
        if kw_or is None or kw_or == '':
            crit_or = q_data[attr].astype('str').str.contains('', regex=True)
        else:
            kw_or_single = extract_single(kw_or)
            kw_or_full = ['\\b'+i+'\\b' for i in extract_full(kw_or)]
            kw_or = kw_or_single + kw_or_full
            form_or = "|".join([f'(?i){ior}' for ior in kw_or])
            crit_or = q_data[attr].astype('str').str.contains(form_or, regex=True)
        if kw_not is None or kw_not == '':
            crit_not = q_data[attr].astype('str').str.contains('', regex=True)
        else:
            kw_not_single = extract_single(kw_not)
            kw_not_full = ['\\b'+i+'\\b' for i in extract_full(kw_not)]
            kw_not = kw_not_single + kw_not_full
            form_not = "|".join([f'(?i){inot}' for inot in kw_not])
            crit_not = q_data[attr].astype('str').str.contains(form_not, regex=True).map(lambda x:not x)
        self.latest_query = copy.deepcopy(q_data[(crit_and)&(crit_or)&(crit_not)])
        return self.latest_query
        
    def regex_query_by(self, reg='', attr=None, inheritance=False):
        q_data = self.data if inheritance==False else self.latest_query
        # regex search
        self.latest_query = copy.deepcopy(q_data[(q_data[attr].str.contains(reg, regex=True)==True)])
        return self.latest_query
    
    def query_bulk(self, Q_List:str='', attr='', inheritance=False):
        q_data = self.data if inheritance==False else self.latest_query
        q = str(Q_List).replace("[", "").replace("]", "")
        sp = "," if q.count(",") > q.count('\n') else "\n"
        q = q.split(sp)
        q = [i.strip() for i in q]
        self.latest_query = copy.deepcopy(q_data[q_data.apply(lambda x: x[attr] in q, axis=1)])
        return self.latest_query

    def get_cl_set(self, cl:str='', inheritance=False)->list:
        q_data = self.data if inheritance==False else self.latest_query
        if cl in self.attribute:
            cl = self.attribute[cl]
        try:
            cl = list(set(q_data[cl].dropna().to_list()))
            cl.sort()
            return cl
        except:
            raise(f"Cannot Find {cl} in Data")

    def combinatorial_query_by(self, kw_and='', kw_or='', kw_not='', attr=None, show_overall=False, inheritance=False):
        print(kw_and, kw_or, kw_not, attr, show_overall, inheritance)
        left = kw_and if type(kw_and) is list else [kw_and]
        mid = kw_or if type(kw_or) is list else [kw_or]
        right = kw_not if type(kw_not) is list else [kw_not]
        max_len = max([len(left), len(mid), len(right)])
        diff = [max_len-len(left), max_len-len(mid), max_len-len(right)]
        left, mid, right = left+diff[0]*[''], mid+diff[1]*[''], right+diff[2]*[''],
        query_list = list(zip(left, mid, right))
        print(query_list)
        '''
        query_list: [[and, or, not], [and, or, not], ...]
        '''
        if type(attr) is list:
            for ql, at in zip(query_list, attr):
                query_name = " | ".join(ql)
                q_index = self.query_by(kw_and=ql[0], kw_or=ql[1], kw_not=ql[2], attr=attr).index
                self.data.loc[:, 'combinatorial_queries'] = self.data.apply(lambda x: x['combinatorial_queries']+query_name if x.name in q_index else x['combinatorial_queries'], axis=1)
        else:
            for ql in query_list:
                query_name = " | ".join(ql)
                q_index = self.query_by(kw_and=ql[0], kw_or=ql[1], kw_not=ql[2], attr=attr).index
                self.data.loc[:, 'combinatorial_queries'] = self.data.apply(lambda x: x['combinatorial_queries']+query_name if x.name in q_index else x['combinatorial_queries'], axis=1)
        self.latest_query = copy.deepcopy(self.data)
        if show_overall == False:
            self.latest_query = copy.deepcopy(self.data[self.data['combinatorial_queries'] != ''])
        self.data['combinatorial_queries'] = self.data.iloc[:, 0].map(lambda x: '')
        return self.latest_query
    
    # ----- feature pivot and visualize functions -----
    def distribution(self, x):
        bins=np.histogram(x)[0]
        sl = ''.join(sparklines(bins))
        return sl
    
    def counts(self, x):
        return x.nunique()
    
    def uniform_feature(self, feat_list:list):
        return [self.attribute[i] if i in self.attribute else i for i in feat_list]
            
    def feature_summary(self, feature:list, data=None, performance=['ASIN', 'ordered_units', 'ops', 'product_cogs_amt', 'contribution_profit_amt'],
                            agg=['count', 'sum', 'sum', 'sum', ['sum', 'mean']], distribution=True, 
                            percentage=True, color_map=None, color=True, grand_total=True):
        # initialize data and color map list
        if data is None:
            data = self.latest_query
        if color_map is None:
            color_map = self.default_cmap
        if type(color_map) is not list:
            color_map = [color_map]
        color_length = len(color_map)
        color_control = 0
        self.color_wait = True
        def color_on_change(cc): 
            if self.color_wait:
                self.color_wait = not self.color_wait
            else:
                cc = cc+1 if cc+1<color_length else 0
                self.color_wait = not self.color_wait
            return cc
        # read features
        feature = [feature] if type(feature) is str else feature
        performance = [performance] if type(performance) is str else performance
        feature_name = [i for i in feature]
        feature = self.uniform_feature(feature)
        performance = self.uniform_feature(performance)
        feature_len = len(feature)
        
        # handling data type
        data_type = {i:data[i].dtype.name for i in performance}
        
        # standardize function name for aggfunc
        agg = [agg] if type(agg) is str else agg
        agg = [self.counts if i=='count' else i for i in agg]
        agg = {p:a for p,a in zip(performance, agg)} if len(agg)==len(performance) else {p:a for p,a in zip(performance, [agg]*len(performance))}
        # correct agg based on dtype
        for i in agg:
            if data_type[i] == 'object':
                agg[i] = self.counts
        
        # generate column name tuple for existing features
        p_pp = performance
        p_index = []
        for p in agg:
            if type(agg[p]) is not list:
                a = agg[p] if type(agg[p]) is str else agg[p].__name__
                p_index.append((p, a))
            else:
                for a in agg[p]:
                    a = a if type(a) is str else a.__name__
                    p_index.append((p, a))
        
        # dropna from used features
        ci = data.dropna(axis=0, subset=performance, how='any', inplace=False)
        
        # generate percentage metrics
        drop_percentage = []
        if percentage:
            performance_f = [i for i in performance if data_type[i]!='object']
            performance_percentage = [i+'%' for i in performance if data_type[i]!='object']
            performance_object = [i for i in performance if data_type[i]=='object']
            for p, pp in zip(performance_f, performance_percentage):
                agg[pp] = agg[p]
            for p, pp in zip(performance_f, performance_percentage):
                su = ci[p].sum()
                ci.loc[:, pp] = ci[p].map(lambda x: x/su)
            p_pp += performance_percentage
            pp_index = []
            for p in agg:
                if p in performance_f:
                    pp = p+"%"
                    if type(agg[p]) is not list:
                        a = agg[p] if type(agg[p]) is str else agg[p].__name__
                        pp_index.append((pp, a))
                    else:
                        for a in agg[p]:
                            a = a if type(a) is str else a.__name__
                            pp_index.append((pp, a))
            if distribution:
                drop_percentage = [(pp, 'distribution') for pp in performance_percentage]
        
        # add distribution visualization function
        if distribution:
            for i in agg:
                if i[-1] != '%':
                    if data_type[i] != 'object':
                        if type(agg[i]) is str:
                            agg[i] = [agg[i]]+[self.distribution]
                        else:
                            agg[i] = agg[i]+[self.distribution]
        
        # get pivot table
        ci = ci.pivot_table(index=feature, values=p_pp, aggfunc=agg,
                            fill_value=0, dropna=False)
        ci = ci.drop(drop_percentage, axis=1)
        ci_dropzero = (ci.any()==0)[(ci.any()==0)==True].index
        ci = ci.drop(ci_dropzero, axis=1)
        
        def get_sub(x):
            if x.dtype.name != 'object':
                if x.name[0] in data.columns:
                    if data[x.name[0]].dtype.name == 'object':
                        return self.counts(data[x.name[0]])
                    else:
                        return data[x.name[0]].dropna().sum()
                elif x.name[0][:-1] in data.columns:
                    return 1
                else:
                    return 0
            else:
                return self.distribution(data[x.name[0]].dropna())

        
        if grand_total:
            def get_grand(x):
                if x.dtype.name != 'object':
                    if x.name[0] in self.data.columns:
                        if data[x.name[0]].dtype.name == 'object':
                            return self.counts(self.data[x.name[0]])
                        else:
                            return self.data[x.name[0]].dropna().sum()
                    elif x.name[0][:-1] in self.data.columns:
                        if data[x.name[0][:-1]].dtype.name == 'object':
                            return (self.counts(self.data[x.name[0][:-1]]))/(self.counts(data[x.name[0][:-1]]))
                        else:
                            return (self.data[x.name[0][:-1]].dropna().sum())/(data[x.name[0][:-1]].dropna().sum())
                    else:
                        return 0
                else:
                    return self.distribution(self.data[x.name[0]].dropna())

            if feature_len > 1:
                sub = ci.apply(get_sub).to_frame().transpose()
                if grand_total:
                    grand = ci.apply(get_grand).to_frame().transpose()
                sub.index = pd.MultiIndex.from_tuples([tuple([""]*(feature_len-2)+["Total"]+["Sub Total"])], names=ci.index.names)
                ci = pd.concat([ci, sub])
                if grand_total:
                    grand.index = pd.MultiIndex.from_tuples([tuple([""]*(feature_len-2)+["Total"]+["Grand Total"])], names=ci.index.names)
                    ci = pd.concat([ci, grand])
            else:
                ci.loc["Sub Total"] =ci.apply(get_sub)
                if grand_total:
                    ci.loc["Grand Total"] =ci.apply(get_grand) 
        
        # generate % for object columns after building of pivot table
        if percentage:
            for p in performance_object:
                current_columns = [i for i in ci.columns if i[0] == p]
                generate_columns = [(i[0]+'%', i[1]) for i in ci.columns if i[0] == p]
                for cc, gc in zip(current_columns, generate_columns):
                    ci[gc] = ci[cc].map(lambda x: x/ci[cc][-2])
                    pp_index.append(gc)
        
        # sort
        ci = ci.sort_index(axis=1)
        p_index.sort()
        if percentage:
            pp_index.sort()
        
        #ci.rename(index={i:" ".join([str(j) for j in i]) if type(i) == tuple else i for i in ci.index}, inplace=True)
        
        
        # format text 
        formatting = {}
        for pi in p_index:
            if pi[0] in self.config_currency and data[pi[0]].dtype.name!='object':
                formatting[pi] = '${0:,.0f}'
            else:
                formatting[pi] = '{:.2f}'
        if percentage:
            for ppi in pp_index:
                formatting[ppi] = '{:.2%}'
        
        title = f"Breakdown of {', '.join(feature_name)} | Current Data Range: {self.universal_label}"
        ex = f'HStyler(ci).format(formatting).set_caption("{title}")'
        
        if grand_total:
            grand_control = '[:-1]'
        else:
            grand_control = ""
        # colorize  
        if color:
            form = ""
            color_range = (0.25, 0.65)
            color_step = (color_range[1] - color_range[0])/len(ci.columns)
            for index, column in enumerate(ci.columns):
                if percentage:
                    if column in pp_index:
                        pp = column
                        color = colors.to_hex(color_map[color_control](color_range[0]+(index+1)*color_step))
                        align = 'left' if ci[pp].min()>=0 else 'mid'
                        form += f".bar(color='{color}', subset=(ci.index{grand_control}, [{pp}]), align='{align}')"
                        color_control = color_on_change(color_control)
                    elif column in p_index:
                        p = column
                        form += f".background_gradient(cmap=color_map[{color_control}], subset=(ci.index{grand_control}, [{p}]))"
                        color_control = color_on_change(color_control)
                    else:
                        pass
                else:
                    p = column
                    form += f".background_gradient(cmap=color_map[{color_control}], subset=(ci.index{grand_control}, [{p}]))"
                    color_control = color_on_change(color_control)
            ex += f'{form}'
        return eval(ex)
    
    def feature_summary_dual(self, data=None, index=['vendor_code'], columns=["marketplace"], 
                             values=['ops'], agg=['sum'], color=True, color_map=None, 
                             percentage=False, grand_total=True):
        # initialize data and color map list
        if data is None:
            data = self.latest_query
        if color_map is None:
            color_map = self.default_cmap
        if type(color_map) is not list:
            color_map = [color_map]
        color_length = len(color_map)
        color_control = 0
        def color_on_change(cc): 
            cc = cc+1 if cc+1<color_length else 0
            return cc
        
        # read features
        index = [index] if type(index) is str else index
        columns = [columns] if type(columns) is str else columns
        values = [values] if type(values) is str else values
        feature_name = index + columns
        index = self.uniform_feature(index)
        columns = self.uniform_feature(columns)
        values = self.uniform_feature(values)
        
        if data[values[0]].dtype.name == 'object':
            agg = [self.counts]
        ci = data.dropna(axis=0, subset=index+columns, how='any', inplace=False)
        ci = ci.pivot_table(index=index, columns=columns, values=values, aggfunc=agg, fill_value=0, dropna=False)
        ci_index = ci.index
        ci_columns = [i[2] for i in ci.columns]
        
        def get_sub(x, a=0):
            column = columns[0]
            i = index[0]
            v = values[0]
            if a==0:
                if x.name[1] in data.columns:
                    if data[x.name[1]].dtype.name == 'object':
                        return self.counts(data[data[column]==x.name[2]][x.name[1]])
                    else:
                        return data[data[column]==x.name[2]][x.name[1]].dropna().sum()
                else:
                    return 0
            else:
                if v in data.columns:
                    if data[v].dtype.name == 'object':
                        return self.counts(data[data[i]==x.name][v])
                    else:
                        return data[data[i]==x.name][v].dropna().sum()
                else:
                    return 0
        ci["Sub Total"] =ci.apply(get_sub, a=1, axis=1)
        ci.loc["Sub Total"] =ci.apply(get_sub)
        ci.iloc[-1, -1] = self.counts(data[values[0]]) if data[values[0]].dtype.name == 'object' else data[values[0]].sum
        
        if grand_total:
            def get_grand(x, a=0):
                column = columns[0]
                i = index[0]
                v = values[0]
                if a==0:
                    if x.name[1] in self.data.columns:
                        if self.data[x.name[1]].dtype.name == 'object':
                            return self.counts(self.data[self.data[column]==x.name[2]][x.name[1]])
                        else:
                            return self.data[self.data[column]==x.name[2]][x.name[1]].dropna().sum()
                    else:
                        return 0
                else:
                    if v in self.data.columns:
                        if self.data[v].dtype.name == 'object':
                            return self.counts(self.data[self.data[i]==x.name][v])
                        else:
                            return self.data[self.data[i]==x.name][v].dropna().sum()
                    else:
                        return 0
            ci["Grand Total"] =ci.apply(get_grand, a=1, axis=1)
            ci.loc["Grand Total"] =ci.apply(get_grand)
            ci.iloc[-1, -1] = self.counts(self.data[values[0]]) if self.data[values[0]].dtype.name == 'object' else self.data[values[0]].sum
            ci.loc["Grand Total", ("Sub Total",'','')] =  self.data[self.data[columns[0]].map(lambda x: x in ci_columns)][values[0]].sum() if self.data[columns[0]].dtype.name != 'object' else self.counts(self.data[self.data[columns[0]].map(lambda x: x in ci_columns)][values[0]])
            ci.loc["Sub Total", ("Grand Total",'','')] = self.data[self.data[index[0]].map(lambda x: x in ci_index)][values[0]].sum() if self.data[index[0]].dtype.name != 'object' else self.counts(self.data[self.data[index[0]].map(lambda x: x in ci_index)][values[0]])
            
        if percentage:
            ci = ci/ci.loc["Sub Total", ("Sub Total",'','')]
        
        if color:
            stci = HStyler(ci)
            # inner
            stci.get_heatmap(cmap=color_map[color_control], sub=(ci.index[0:-2], ci.columns[0:-2]))
            color_control = color_on_change(color_control)
            # margins-1
            stci.get_heatmap(cmap=color_map[color_control], sub=(ci.index[0:-1], ci.columns[-2]))
            stci.get_heatmap(cmap=color_map[color_control], sub=(ci.index[-2], ci.columns[0:-1]))
            color_control = color_on_change(color_control)
            # margins-1
            stci.get_heatmap(cmap=color_map[color_control], sub=(ci.index[:], ci.columns[-1]))
            stci.get_heatmap(cmap=color_map[color_control], sub=(ci.index[-1], ci.columns[:]))
            color_control = color_on_change(color_control)
        
        # format text 
        formatting = self.get_format(values[0], percentage)
        
        title = f"Breakdown of {', '.join(feature_name)} | Current Data Range: {self.universal_label}"
        ex = f'stci.format(formatting).set_caption("{title}")'
        exec(ex)
        return stci
    
    def get_format(self, feature, percentage=False, brace=True):
        formatting = ""
        if feature in self.config_currency:
            formatting = '{$0:,f}' if brace else '$0:,f'
        else:
            formatting = '{:.2f}' if brace else ':.2f'
        if percentage:
            formatting = '{:.2%}' if brace else ':.2%'
        return formatting
    
    def draw_feature_distribution_scatter(self, feature:str, performance='product_cogs_amt', ddata=None):
        from bokeh.models import ColumnDataSource
        from bokeh.plotting import figure
        from bokeh.transform import jitter
        from bokeh.models import NumeralTickFormatter
        
        if ddata is None:
            ddata = copy.deepcopy(self.latest_query)
        
        feature = self.uniform_feature([feature])[0]
        ddata[feature] = ddata[feature].astype('object')
        ddata = ddata.dropna(how='any', subset=[feature])
        ddata[feature] = ddata[feature].astype(np.str)
        source = ColumnDataSource(ddata)

        yr = [i for i in set(ddata[feature])]
        
        length_feature = len(yr)

        p = figure(plot_width=800, plot_height=80*length_feature, y_range=yr,
                   title=f"Distribution Figure: {performance} of {feature}", tools = "pan,xwheel_zoom,box_zoom,reset", active_scroll = "xwheel_zoom")

        p.circle(x=performance, y=jitter(feature, width=0.3, range=p.y_range),  
                 source=source, alpha=0.2)
        
        p.xaxis[0].formatter = NumeralTickFormatter(format=self.get_format(performance, brace=False))
        p.x_range.range_padding = 0
        p.ygrid.grid_line_color = None

        return p
    
    def draw_feature_time_seires_heatmap(self, feature:str, time_series=['Time_Series'], performance='product_cogs_amt', data=None, cmap=["#75968f", "#a5bab7", "#c9d9d3", "#e2e2e2", "#dfccce", "#ddb7b1", "#cc7878", "#933b41", "#550b1d"]):
        from holoviews import opts
        from random import choice
        from bokeh.models import NumeralTickFormatter
        from bokeh.models import HoverTool
        hv.extension('bokeh')
        if data is None:
            data = copy.deepcopy(self.latest_query)
        if cmap is None:
            cmap = choice(self.default_cmap)
        feature = self.uniform_feature([feature])[0]
        data[feature] = data[feature].astype('object')
        data = data.dropna(how='any', subset=[feature])
        time_series = self.uniform_feature(time_series)

        data = copy.deepcopy(data[time_series+[performance]+[feature]])
        data.replace([np.inf, -np.inf], np.nan, inplace=True)
        data.dropna(inplace=True)
        draw = data[['Time_Series', feature, performance]].groupby(by=['Time_Series', feature]).agg('sum').reset_index()

        formatting = self.get_format(performance, brace=False)
        formatting_b = self.get_format(performance, brace=True)
        formatter = NumeralTickFormatter(format=formatting)
        hover = HoverTool(tooltips=[(f"{feature}",f"@{feature}"),
                                    ('Time_Series', '@Time_Series'),
                                    (f"{performance}", f"@{performance}{formatting_b}")])
        hover_a = HoverTool(tooltips=[('Time_Series', '@Time_Series'),
                                      (f"{performance}", f"@{performance}{formatting_b}")])
        
        ag = []
        heatmap = hv.HeatMap(draw, label='Total')
        aggregate = hv.Dataset(heatmap).aggregate('Time_Series', np.sum, np.std)

        features = list(set(draw[feature]))
        feature_length = len(features)
        for i in range(feature_length):
            hm_temp = hv.HeatMap(draw[draw[feature] == features[i]], label=str(features[i]))
            ag += [hv.Dataset(hm_temp).aggregate('Time_Series', np.sum, np.std)]
        
        line = "hv.Curve(aggregate)"+"*"+ "*".join([f'hv.Curve(ag[{i}])' for i in range(feature_length)])
        point = "hv.Scatter(aggregate)"+"*"+ "*".join([f'hv.Scatter(ag[{i}])' for i in range(feature_length)])
        draw_agg = "*".join([line, point])
        agg = eval(draw_agg) 
        overlay = (heatmap + agg).cols(1)
        width = 760+max(data[feature].map(lambda x: len(str(x))))*7
        overlay.opts(
            opts.HeatMap(width=width, height=40*len(list(set(data[feature]))), tools=[hover], logz=True, 
                         invert_yaxis=True, labelled=[], toolbar='above',
                         xaxis=None, colorbar=True, clim=(1, np.nan), cformatter=formatter, cmap=cmap, 
                         title=f'Time Series - Heatmap: {performance} / {feature}'),
            opts.Curve(tools=[hover_a], show_grid=True, alpha=0.8),
            opts.Scatter(size=6, line_color='grey'),
            opts.Overlay(width=width, height=300, xrotation=90, yformatter=formatter, 
                         show_legend=True, show_title=False, legend_position='right',
                         legend_opts={'background_fill_alpha': 0}, legend_spacing=-2, fontsize={'legend':7.5}))

        return hv.render(overlay)
    
    def draw_feature_scatter(self, data=None, x:str='marketplace', y:str='ops', cate:str='hdl_classification'):
        from holoviews import dim, opts
        import holoviews as hv
        from bokeh.models import NumeralTickFormatter
        from bokeh.models import HoverTool
        hv.extension('bokeh')
        data = self.latest_query if data==None else data
        x = self.uniform_feature([x])[0]
        y = self.uniform_feature([y])[0]
        cate = self.uniform_feature([cate])[0]
        asin = self.attribute['ASIN']

        type_list = [(y, data[y].dtype.name), (x, data[x].dtype.name), (cate, data[cate].dtype.name)]
        by = [i[0] for i in type_list if i[1] == 'object']
        ext = [i[0] for i in type_list if i[1] != 'object']

        def asin_counter(x):
            select = []
            for i in by:
                select += [f'(data["{i}"]=="{x[i]}")']
            select = "&".join(select)
            return data[eval(select)][asin].nunique()

        data_draw = data.groupby(by=by)[ext].agg('sum').reset_index()
        data_draw['asin_counter'] = data_draw.apply(asin_counter, axis=1)
        key_dimensions   = [(y, y), (cate, cate)]
        value_dimensions = [(x, x), ('asin_counter', 'asin_counter')]
        macro = hv.Table(data_draw, key_dimensions, value_dimensions)
        dfs = macro.to.scatter(x, [y, 'asin_counter'])
        overlay_scatter = dfs.overlay(cate)
        
        formatting_x = self.get_format(x, brace=False) if x in ext else ""
        formatting_xb = self.get_format(x, brace=True) if x in ext else ""
        xformatter = NumeralTickFormatter(format=formatting_x) if x in ext else ""
        formatting_y = self.get_format(y, brace=False) if y in ext else ""
        formatting_yb = self.get_format(y, brace=True) if y in ext else ""
        yformatter = NumeralTickFormatter(format=formatting_y) if y in ext else ""
        
        hover = HoverTool(tooltips=[(f'{cate}', f'@{cate}'),
                                    (f"{x}",f"@{x}{formatting_xb}"),
                                    (f"{y}", f"@{y}{formatting_yb}")])
        
        overlay_scatter.opts(
            opts.Scatter(color=hv.Cycle('Category20'), line_color='grey', size=(dim('asin_counter').lognorm()+0.3)*11,
                         show_grid=True, width=760+max(data_draw[cate].map(lambda x: len(x)))*5, height=400, tools=[hover], alpha=0.8),
            opts.NdOverlay(legend_position='right', show_frame=False, xformatter=xformatter, yformatter=yformatter, 
                           fontsize={'legend':7.5}))
        return hv.render(overlay_scatter)
    
    def full_describe(self, fdata=None):
        d = ''
        if fdata is None:
            fdata = self.latest_query
        try:
            num = fdata.describe(include=[np.number])
            num_len = len(num.columns)
            num_caption = f"Numeric: {num_len} columns"
            num = num.style.format("{:.2f}").set_caption(num_caption).render()
            d += num
        except:pass
        try:
            obj = fdata.describe(include=[object])
            obj_len = len(obj.columns)
            obj_caption = f"String: {obj_len} columns"
            obj = obj.style.set_caption(obj_caption).render()
            d += obj
        except:pass
        try:
            cate = fdata.describe(include=['category']).style
            cate_len = len(cate.columns)
            cate_caption = f"Categorical: {cate_len} columns"
            cate = cate.style.set_caption(cate_caption).render()
            d += cate
        except:pass
        return d
    
    def show_details(self, sdata=None):
        if sdata is None:
            sdata = self.latest_query
        d = sdata.head(100).style.render()
        return d
    
    def generate_topic_model(self, word_scale=100, n_topics=10, vis_type='PCA'):
        from sklearn.decomposition import PCA
        from sklearn.manifold import TSNE
        from sklearn.decomposition import NMF
        import networkx as nx
        from bokeh.models import HoverTool
        
        # get data
        a, b= self.processor.co_occurence(scale=word_scale)
        word_set = set([i for i in np.array(a)[:, 0]])
        count = pd.DataFrame(a)
        
        # identify topics and corresponding colors
        print('\n>> Identifying Topics...')
        N = n_topics
        colors = hv.Cycle('Category20').values
        if N < 20:
            colors = colors[0:N]
        else:
            colors = int(N/20) * colors + colors[0:(N%20)]
        model = NMF(n_components=N, init='random', random_state=0)
        X = self.processor.data["BaggingVector"].to_list()
        W = model.fit_transform(X)
        H = model.components_
        self.processor.data['Topic'] = pd.Series(np.argmin(W, axis=1))
        word_topic = np.argmin(H, axis=0)
        word_index = [i for i in word_set]
        
        # generate position (x,y) of nodes
        print('\n>> Generating Position of each node...')
        if vis_type == 'PCA':
            X = np.array(self.processor.data["BaggingVector"].to_list()).T
            pca = PCA(n_components=2)
            pca.fit(X)
            P = pca.transform(X).T
        elif vis_type == 'NMF':
            model = NMF(n_components=2, init='random', random_state=0)
            X = self.processor.data["BaggingVector"].to_list()
            W = model.fit_transform(X)
            P = model.components_
        elif vis_type == 'tSNE':
            X = np.array(self.processor.data["BaggingVector"].to_list()).T
            pca = PCA(n_components=int(X.shape[0]/20))
            pca.fit(X)
            P = pca.transform(X)
            P = TSNE(n_components=2).fit_transform(P).T
        else:
            func = eval(vis_type)
            G = nx.Graph()
            G.add_weighted_edges_from(b)
            nodes = pd.DataFrame(func(G), index=['x', 'y']).transpose().reset_index()
            P = [nodes.x.to_list(), nodes.y.to_list()]
        
        # form features of nodes for visualization
        print('\n>> Generating Visualized Graph...')
        word_de = pd.DataFrame({'x':P[0], 'y':P[1], 'index':word_index, 'word':word_index, 'topic':word_topic, 'color':[colors[i] for i in word_topic]})
        nodes = word_de[word_de['word'].isin(word_set)]
        nodes['counter'] = nodes['word'].map(lambda x: int(count[count[0]==x][1]))
        nodes['size'] = ((nodes['counter']-nodes['counter'].min())/(nodes['counter'].max()-nodes['counter'].min()))*20 + 20
        
        # generathe map
        edges = b
        main_graph = hv.Graph((edges, nodes))
        labels = hv.Labels(main_graph.nodes.data, ['x', 'y'], "word")
        labels.opts(xoffset=0, yoffset=0, text_font_size='9pt', text_alpha=0.7)
        hover = HoverTool(tooltips=[("word", "@word"), ("counter", "@counter"), ("topic", "@topic")])
        main_graph.opts(tools=[hover], inspection_policy='nodes', edge_line_alpha=0.01, node_color='color', 
                        edge_hover_alpha=0.4, node_size='size', node_alpha=0.5, node_line_alpha=0.2, active_tools=['wheel_zoom'])
        fig = main_graph * labels
        fig.opts(width=1000, height=1000)
        return hv.render(fig)
                