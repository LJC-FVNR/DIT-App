# -*- coding: utf-8 -*-
"""
Created on Wed Apr 14 10:31:40 2021

@author: ljiechen
"""
import json

form = \
{
    "UserManagement":{},

    "DataProcessing":{
                    "Initialize": {"call":"session['PHASE']=2;session['DATA_REGISTRATED'] = True;processor=Processor(**parameters);session['processor']=processor", 
                                   'tab': 'Data', 
                                  "info":               "To initialize the text data processor of item name and implement the translator",
                                  "available_phase":    [1],
                                  "type": "submit", 
                                  "parameters": {
                                                 "DATA":                ["Data", "data", ["immutable", "eval"], 1, "data", "None"],
                                                 "VENDORCODE_MAPPING":  ["Vendor Code Mapping File", "Vendor Code Mapping.xlsx", ["choose_dir", "mapping/"], 1, "choose the vendor code mapping file with uniform vendor name"],
                                                 "VENDORCODE_ORIGINAL": ["Vendor Code Original File (No need to change)", "Vendor Code Mapping - Original.xlsx", ["choose_dir", "mapping/"], 1, "choose the vendor code mapping file with original vendor name"],
                                                 "STOPWORDS":           ["Stopwords", "user.settings['stopwords']", ["json_edible"], 3, "edit stopwords"],
                                                 "UNIT":                ["Unit of Quanitity", "user.settings['unit']", ["json_edible"], 3, "edit unit of quantity"],
                                                 "COMBINE":             ["Word Combining", "user.settings['combine']", ["json_edible"], 3, "edit words that need combinations"],
                                                 "MAPPING":             ["Word Mapping", "user.settings['mapping']", ["json_edible"], 3, "edit to map words to there correct formats"],
                                                 "USER_PATH":           ["USER_PATH", "user.path", ["immutable", "eval"], 1, "path of the user", "None"],
                                                 "DICTIONARY":          ["Dictionary File", "None", ["choose_dir", "dictionary/"], 1, "choose a prepared translation mapping file or leave it as None"],
                                                 "OUTPUT":              ["Output Filename", "None", ["text_edible", 'small', 'text'], 3, "provide a filename of output data or leave it as None"],
                                                 "translation_pos":     ["Columns Mapping for Translation", "list(data.columns)", ["floating_choose", "['marketplace_id', 'item_name']"], 5, "write the column names which represent the marketplace id and item name"],
                                                 "do_doc2vec":          ["Doc2Vec", "False", ["choose", "False", "True"], 1, "whether to build the Doc2Vec model based on this data"]
                                                },
                                  "after":{"exec":"""print('>> End');session['data'] = [];
                                           """,
                                           "script":"",
                                           "finish":""
                                           }
                                    },
                                 
                    "Save Data":{ "call":            "session.get('processor').save()",
                                 'tab': 'Data', 
                                 "info":                "To save the processed data",
                                 "available_phase":     [2, 3],
                                 "type": "ajax", 
                                 "parameters": {},
                                 "after":{"exec":"print('>> End')",
                                          "script":"",
                                          "finish":"jsonify({'success': 'Data Saved'})"
                                          }
                               },
             "Save Translation":{ "call":            "session.get('processor').save_dictionary()",
                                 'tab': 'Data', 
                                 "info":                "To save the translation dictionary as a file",
                                 "available_phase":     [2, 3],
                                 "type": "ajax", 
                                 "parameters": {},
                                 "after":{"exec":"print('>> End')",
                                          "script":"",
                                          "finish":"jsonify({'success': 'Dictionary Saved'})"
                                          }
                               },


             },
    
    "DA":{"Initialize": {"call": "session['PHASE']=3;pb_data=PB_Data(**parameters);session['pb_data']=pb_data", 
                         'tab': 'Data', 
                                  "info":               "To initialize the Visualization Toolkits",
                                  "available_phase":    [2],
                                  "type": "submit", 
                                  "parameters": {"processor": ["Text Processor", "session.get('processor')", ["immutable", "eval"], 1, "Pre-built Text Processor"],
                                                 "auto_labeling":["Auto Labeling", "False", ["choose", "False", "True"], 1, "Auto labeling the feature with categorical or numerical variables"],
                                                 "classification": ["Categorical Features", "list(session.get('processor').data.columns)", ["checks", "PB_Data.default_classification"], 4, "Check all categorical columns"],
                                                 "performance": ["Numerical Features", "list(session.get('processor').data.columns)", ["checks", "PB_Data.default_performance"], 4, "Check all numerical columns"],
                                                 "name":["Data Label", "'data'+'_'+datetime.datetime.now().strftime('%Y%m%d')", ["text_edible", "small", 'eval_pre'], 2, "Edit the name of the data"],
                                                 "universal_label": ["Label of Overall Data", "Overall Data", ["text_edible", 'small', 'text'], 2, "Edit the label to represent the overall data in visualization"],
                                                 "time_series": ["Time Series Formatting", "list(session.get('processor').data.columns)", ["choose_append"], 5, "Format the time series feature"],
                                                 "key_feature_matching":["Key Feature Matching", "list(session.get('processor').data.columns)", ["floating_choose", "PB_Data.key_attribute_set"], 3, "Match these default key features"]
                                                },
                                  "after":{"exec":"session['PHASE']=3;print('>> End')",
                                           "script":"",
                                           "finish":""
                                           }
                                    },
          "Select Data": {"call": "session['pb_data'].select_data(**parameters)", 
                          'tab': 'Select', 
                                  "info":               "The numeric way to get a subset of data",
                                  "available_phase":    [3],
                                  "type": "ajax", 
                                  "parameters": {"feature": ["Columns", "list(session['pb_data'].data.columns)", ["choose_append"], 5, "Select columns"],
                                                 "operator": ["Operators", "['==', '!=', '>', '<', '>=', '<=']", ["choose_append"], 5, "Select numeric operators"],
                                                 "value": ["Values", "", ["text_append", "None"], 5, "Write values"],
                                                 "inheritance": ["Inheritance", "False", ["choose", "False", "True"], 3, "whether to query on the basis of the latest selected data (True) or the overall data (False)"]
                                                },
                                  "after":{"exec":"div=session['pb_data'].full_describe();title='Data Selected';content=format_result(title, '', div, TOOLS, session.get('current_info'));session['current_content']=content;print('>> End')",
                                           "script":"",
                                           "finish":"jsonify({'content':content})"
                                           }
                                    },
        "Query by Keywords": {"call": "session['pb_data'].query_by(**parameters)", 
                              'tab': 'Select', 
                      "info":               'Select data by searching keywords in a column with logical operators: and, or, not. Use "" to specify the exact spelling of a keyword',
                      "available_phase":    [3],
                      "type": "ajax", 
                      "parameters": { "attr": ["Column to Search in", "list(session['pb_data'].data.columns)", ["choose_eval", "text"], 5, "Select columns to apply the search"],
                                      "kw_and": ["Keywords: And", "", ["text_edible", 'small', 'text'], 4, "All of the keywords must appear"],
                                     "kw_or": ["Keywords: Or", "", ["text_edible", 'small', 'text'], 4, "At least one of the keywords must appear"],
                                     "kw_not": ["Keywords: Not", "", ["text_edible", 'small', 'text'], 4, "None of these keywords should appear"],
                                     "inheritance": ["Inheritance", "False", ["choose", "False", "True"], 3, "whether to query on the basis of the latest selected data (True) or the overall data (False)"]
                                    },
                      "after":{"exec":"div=session['pb_data'].full_describe();title='Data Selected';content=format_result(title, '', div, TOOLS, session.get('current_info'));session['current_content']=content;print('>> End')",
                               "script":"",
                               "finish":"jsonify({'content':content})"
                               }
                        },
        "Query by Bulk Keywords": {"call": "session['pb_data'].query_bulk(**parameters)", 
                                   'tab': 'Select', 
              "info":               'Select data by positioning bulk input that contained in a feature',
              "available_phase":    [3],
              "type": "ajax", 
              "parameters": {"attr": ["Column to Search in", "list(session['pb_data'].data.columns)", ["choose_eval", "text"], 5, "Select columns to apply the search"],
                             "Q_List": ["Bulk List", "", ["text_edible", 'large', 'text'], 5, "Use ',' or line breaks to split each element"],
                             "inheritance": ["Inheritance", "False", ["choose", "False", "True"], 3, "whether to query on the basis of the latest selected data (True) or the overall data (False)"]
                            },
              "after":{"exec":"div=session['pb_data'].full_describe();title='Data Selected';content=format_result(title, '', div, TOOLS, session.get('current_info'));session['current_content']=content;print('>> End')",
                       "script":"",
                       "finish":"jsonify({'content':content})"
                       }
                },
        "Combinatorial Query": {"call": "session['pb_data'].combinatorial_query_by(**parameters)", 
                                'tab': 'Select', 
              "info":               'Classifying and selecting data by multiple keyword rules and form a new categorical feature based on this for further analysis',
              "available_phase":    [3],
              "type": "ajax", 
              "parameters": {"attr": ["Column to Apply to", "list(session['pb_data'].data.columns)", ["choose_eval", "text"], 5, "Select columns to apply the search"],
                             "kw_and": ["Keywords: And", "", ["text_append", "None"], 4, "All of the keywords must appear"],
                             "kw_or": ["Keywords: Or", "", ["text_append", "None"], 4, "At least one of the keywords must appear"],
                             "kw_not": ["Keywords: Not", "", ["text_append", "None"], 4, "None of these keywords should appear"],
                             "show_overall": ["Show Overall", "False", ["choose", "False", "True"], 5, "whether to contain the data that do not conform to any of the rules listed above"],
                             "inheritance": ["Inheritance", "False", ["choose", "False", "True"], 3, "whether to query on the basis of the latest selected data (True) or the overall data (False)"]
                            },
              "after":{"exec":"""div=session['pb_data'].full_describe() 
                       \ntitle='Data Selected' 
                       \ncontent=format_result(title, '', div, TOOLS, session.get('current_info')) 
                       \nsession['current_content']=content
                       \nprint('>> End')
                       \nif session.get('RELOADED') == False:
                       \n    script = 'location.reload()'
                       \n    session['current_script'] = script
                       \n""",
                       "script":"",
                       "finish":"jsonify({'content':content, 'script':script})"
                       }
                },
        "Feature Pivot": {"call": "result = session['pb_data'].feature_summary(**parameters)", 
                          'tab': 'Feature', 
              "info":               'Summarize and aggregate performance data with breakdown of categorical features',
              "available_phase":    [3],
              "type": "ajax", 
              "parameters": {"feature": ["Breakdown Features", "list(session['pb_data'].classification)", ["choose_append"], 5, "Select categorical features to process the breakdown summary"],
                             "performance": ["Value Contents", "list(session['pb_data'].data.columns)", ["choose_append"], 5, "Select features as columns to be presented in summary"],
                             "agg": ["Aggregation Methods", "['count', 'sum', 'mean']", ["choose_append"], 5, "Select the method to aggregate the feature above"],
                             "distribution": ["Show Distribution", "False", ["choose", "False", "True"], 3, "whether to show distribution summary of each numerical column"],
                             "percentage": ["Show Percentage", "True", ["choose", "False", "True"], 3, "whether to show percentage column of each numerical feature"],
                             "color": ["Show Color", "True", ["choose", "False", "True"], 3, "whether to colorize the summary"],
                             "grand_total": ["Show Grand Total", "True", ["choose", "False", "True"], 3, "whether showing grand_total for numerical features"],
                             "color_map": ["Color Map", "['None']", ["choose_eval", "eval"], 1, "Choose a theme of color"]
                            },
              "after":{"exec":"div=result.render();title='Feature Breakdown';content=format_result(title, '', div, TOOLS, session.get('current_info'));session['current_content']=content;print('>> End')",
                       "script":"",
                       "finish":"jsonify({'content':content})"
                       }
                },
        "Feature Pivot - Dual": {"call": "result = session['pb_data'].feature_summary_dual(**parameters)", 
                                 'tab': 'Feature', 
              "info":               'Summarize and aggregate performance data with breakdown of two categorical features',
              "available_phase":    [3],
              "type": "ajax", 
              "parameters": {"index": ["Feature of Row Index","list(session['pb_data'].classification)", ["choose_eval", "text"], 5, "Select a categorical feature to process the breakdown summary"],
                             "columns": ["Feature of Columns", "list(session['pb_data'].classification)", ["choose_eval", "text"], 5, "Select another categorical features to process the breakdown summary"],
                             "values": ["Value Contents", "list(session['pb_data'].data.columns)", ["choose_append"], 5, "Select features as columns to be presented in summary"],
                             "agg": ["Aggregation Methods", "['count', 'sum', 'mean']", ["choose_append"], 5, "Select the method to aggregate the feature above"],
                             "percentage": ["Show Percentage", "True", ["choose", "False", "True"], 3, "whether to show percentage column of each numerical feature"],
                             "grand_total": ["Show Grand Total", "True", ["choose", "False", "True"], 3, "whether showing grand_total for numerical features"],
                             "color": ["Show Color", "True", ["choose", "False", "True"], 3, "whether to colorize the summary"],
                             "color_map": ["Color Map", "['None']", ["choose_eval", "eval"], 1, "Choose a theme of color"],
                            },
              "after":{"exec":"div=result.render();title='Feature Breakdown';content=format_result(title, '', div, TOOLS, session.get('current_info'));session['current_content']=content;print('>> End')",
                       "script":"",
                       "finish":"jsonify({'content':content})"
                       }
                },
        "Distribution Scatter Plot": {"call": "result = session['pb_data'].draw_feature_distribution_scatter(**parameters)", 
                                      'tab': 'Visualization', 
              "info":               'Draw the jitter distribution plot of a feature',
              "available_phase":    [3],
              "type": "ajax", 
              "parameters": {"feature": ["Breakdown Feature", "list(session['pb_data'].classification)", ["choose_eval", "text"], 5, "Select a categorical feature draw its breakdown distribution plot"],
                             "performance": ["Feature Distribution", "list(session['pb_data'].performance)", ["choose_eval", "text"], 5, "Select a numeric feature to show its distribution"]
                            },
              "after":{"exec":"""script, div = components(result);title='Distribution Scatter Plot';content=format_result(title, '', div, TOOLS, session.get('current_info'));session['current_content']=content;script = script.replace('<script type="text/javascript">', '').replace('</script>', '');session['current_script'] = script;print('>> End')""",
                       "script":"",
                       "finish":"jsonify({'content':content, 'script':script})"
                       }
                },
        "Time Series / Heatmap Plot": {"call": "result = session['pb_data'].draw_feature_time_seires_heatmap(**parameters)", 
                                       'tab': 'Visualization', 
              "info":               'Draw the line plot and heatmap based on the preset time series',
              "available_phase":    [3],
              "type": "ajax", 
              "parameters": {"feature": ["Breakdown Feature", "list(session['pb_data'].classification)", ["choose_eval", "text"], 5, "Select a categorical feature draw its breakdown distribution plot"],
                             "performance": ["Feature to Display", "list(session['pb_data'].performance)", ["choose_eval", "text"], 5, "Select a numeric feature to show its distribution"]
                            },
              "after":{"exec":"""script, div = components(result);title='Time Series Plot';content=format_result(title, '', div, TOOLS, session.get('current_info'));session['current_content']=content;script = script.replace('<script type="text/javascript">', '').replace('</script>', '');session['current_script'] = script;print('>> End')""",
                       "script":"",
                       "finish":"jsonify({'content':content, 'script':script})"
                       }
                },
        "Custom Feature Relationship Plot": {"call": "result = session['pb_data'].draw_feature_scatter(**parameters);", 
                                             'tab': 'Visualization', 
              "info":               'Draw scatter plot with the selected axes and a categorical breakdown',
              "available_phase":    [3],
              "type": "ajax", 
              "parameters": {"x": ["Axis X", "list(session['pb_data'].data.columns)", ["choose_eval", "text"], 5, "Select a categorical feature draw its breakdown distribution plot"],
                             "y": ["Axis Y", "list(session['pb_data'].data.columns)", ["choose_eval", "text"], 5, "Select a numeric feature to show its distribution"],
                             "cate": ["Hue with Feature", "list(session['pb_data'].classification)", ["choose_eval", "text"], 5, "Select a categorical feature draw its breakdown distribution plot"],
                            },
              "after":{"exec":"""script, div = components(result);title='Feature Scatter Plot';content=format_result(title, '', div, TOOLS, session.get('current_info'));session['current_content']=content;script = script.replace('<script type="text/javascript">', '').replace('</script>', '');session['current_script'] = script;print('>> End')""",
                       "script":"",
                       "finish":"jsonify({'content':content, 'script':script})"
                       }
                },
        "Generate Topic Model - Plot": {"call": "result = session['pb_data'].generate_topic_model(**parameters)", 
                        'tab':'Models',
              "info":               'Generate co-occurence mapping of keywords with specific strategy based on processed name feature',
              "available_phase":    [3],
              "type": "ajax", 
              "parameters": {
                  "word_scale": ["Scale of Word", "100", ["text_edible", 'small', 'text'], 5, "Scale of top importance keywords included"],
                  "n_topics": ["Extracted Topic #", "10", ["text_edible", 'small', 'text'], 5, "How much topics extracted from original feature"],
                  "vis_type": ["Visualization Type", "['PCA', 'NMF', 'tSNE', 'nx.layout.fruchterman_reingold_layout', 'nx.spring_layout']", ["choose_eval", "text"], 5, "Select a categorical feature draw its breakdown distribution plot"]},
              "after":{"exec":"""\nscript, div = components(result);
                                 \ntitle='Keyword Extraction and Topic Clustering';
                                 \ncontent=format_result(title, '', div, TOOLS, session.get('current_info'));
                                 \nsession['current_content']=content;
                                 \nscript = script.replace('<script type="text/javascript">', '').replace('</script>', '');
                                 \nsession['current_script'] = script;
                                 \nprint('>> End')""",
                       "script":"",
                       "finish":"jsonify({'content':content, 'script':script})"
                       }
                },
        
        "Generate Topic Model - Table": {"call": "result = session['pb_data'].generate_topic_model_table(**parameters)", 
                        'tab':'Models',
              "info":               'Generate topic clustering of top keywords to demonstrate the composition of a category',
              "available_phase":    [3],
              "type": "ajax", 
              "parameters": {
                  "word_scale": ["Scale of Word", "100", ["text_edible", 'small', 'text'], 5, "Scale of top importance keywords included"],
                  "bridge": ["Bridge Vector Length", "5", ["text_edible", 'small', 'text'], 5, "The longer the bridge vector length set, the more the model focus on outlier keywords"],
                  "clusters": ["Extracted Topic #", "10", ["text_edible", 'small', 'text'], 5, "How much topics extracted from original feature"],
                  "limit": ["Max Display Rows", "100", ["text_edible", 'small', 'text'], 3, "Max rows to display in the keyword clustering table"],
                  "soft_clustering": ["Soft Clustering", "True", ["choose", "False", "True"], 5, "whether to deploy soft clustering strategy"],
                  "topic_dist_matrix": ["Show Topic Distance Matrix", "False", ["choose", "False", "True"], 4, "whether to show distance matrix of topics"],
                  "keyword_dist_matrix": ["Show Keyword Distance Matrix", "False", ["choose", "False", "True"], 4, "whether to show distance matrix of keywords"],
                  },
              "after":{"exec":"""\ndiv = result;
                                 \ntitle='Keyword Extraction and Topic Clustering';
                                 \ncontent=format_result(title, '', div, TOOLS, session.get('current_info'));
                                 \nsession['current_content']=content;
                                 \nprint('>> End')""",
                       "script":"",
                       "finish":"jsonify({'content':content})"
                       }
                },
        
        "Note": {"call": "title, note, h_tools = session['pb_data'].note(**parameters);", 
                         'tab':"Tools",
              "info":               'Write a comment in this dashboard',
              "available_phase":    [3],
              "type": "ajax", 
              "parameters": {"title": ["Title", "", ["text_edible", 'small', 'text'], 5, "Title of this note"],
                             "note": ["Content", "", ["text_edible", 'large', 'text'], 5, "Content of this note"],
                             "tools": ["Show Tools", "True", ["choose", "False", "True"], 3, "whether to use result tools"],
                             },
              "after":{"exec":"""tools=TOOLS if h_tools else [];content=format_result(title, '', note, tools, session.get('current_info'), outerClass='noteResult');session['current_content']=content;print('>> End')""",
                       "script":"",
                       "finish":"jsonify({'content':content})"
                       }
                },
        
        "Show Details": {"call": "result = session['pb_data'].show_details(**parameters)", 
                         'tab':"Tools",
              "info":               'Show top 100 rows of the latest queried data',
              "available_phase":    [3],
              "type": "ajax", 
              "parameters": {"scale": ["Scale of Rows", "100", ["text_edible", 'small', 'text'], 3, "scale of rows to display"]},
              "after":{"exec":"""div=result;title='Data Details (top 100 rows)';content=format_result(title, '', div, TOOLS, session.get('current_info'));session['current_content']=content;print('>> End')""",
                       "script":"",
                       "finish":"jsonify({'content':content})"
                       }
                },
        "Reset Data": {"call": "result = '';session['pb_data'].reset();", 
                         'tab':"Tools",
              "info":               'Restore the manipulated data',
              "available_phase":    [3],
              "type": "ajax", 
              "parameters": {},
              "after":{"exec":"""div=result;title='Data Reset';content=format_result(title, '', div, ['close'], session.get('current_info'));session['current_content']=content;print('>> End')""",
                       "script":"",
                       "finish":"jsonify({'content':content})"
                       }
                },
          }
}

js = json.dumps(form)
f = open('static/user/public/settings/func_settings.json', 'w')
f.write(js)
f.close()