# -*- coding: utf-8 -*-
"""
Created on Wed Apr 14 10:31:40 2021

@author: ljiechen
"""
import json

form = \
{
    "User_Management":{},

    "Data_Processing":{
                    "Initialize": {"call":"global processor; processor=Processor(**parameters)", 
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
                                  "after":{"exec":"""\nGLOBAL_VARIABLES['PHASE'] = 2\nGLOBAL_VARIABLES["DATA_REGISTRATED"] = True\ncurrent_func = user.get_func_settings(GLOBAL_VARIABLES['PHASE'])\nprint('>> End')
                                           """,
                                           "script":"",
                                           "finish":"""render_template('Template.html', TITLE="Processing", GLOBAL_VARIABLES=GLOBAL_VARIABLES, current_func=current_func,username=username,form_func_input_html=form_func_input_html, script=SCRIPT, content=CONTENT)"""
                                           }
                                    },
                                 
                    "Save Data":{ "call":            "processor.save()",
                                 "info":                "To save the processed data",
                                 "available_phase":     [2, 3],
                                 "type": "ajax", 
                                 "parameters": {},
                                 "after":{"exec":"print('>> End')",
                                          "script":"",
                                          "finish":"jsonify({'success': 'Data Saved'})"
                                          }
                               },
             "Save Translation":{ "call":            "processor.save_dictionary()",
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
    
    "DA":{"Initialize": {"call": "global pb_data \npb_data = PB_Data(**parameters)", 
                                  "info":               "To initialize the Visualization Toolkits",
                                  "available_phase":    [2],
                                  "type": "submit", 
                                  "parameters": {"processor": ["Text Processor", "processor", ["immutable", "eval"], 1, "Pre-built Text Processor"],
                                                 "classification": ["Categorical Features", "list(processor.data.columns)", ["checks", "PB_Data.default_classification"], 4, "Please check all categorical columns"],
                                                 "performance": ["Numerical Features", "list(processor.data.columns)", ["checks", "PB_Data.default_performance"], 4, "Please check all numerical columns"],
                                                 "name":["Data Label", "'data'+'_'+datetime.datetime.now().strftime('%Y%m%d%H%M%S')", ["text_edible", "small", 'eval_pre'], 2, "Edit the name of the data"],
                                                 "universal_label": ["Label of Overall Data", "Overall Data", ["text_edible", 'small', 'text'], 2, "Edit the label to represent the overall data in visualization"],
                                                 "time_series": ["Time Series Formatting", "list(processor.data.columns)", ["choose_append"], 5, "Format the time series feature"],
                                                 "key_feature_matching":["Key Feature Matching", "list(processor.data.columns)", ["floating_choose", "PB_Data.key_attribute_set"], 3, "Match these default key features"]
                                                },
                                  "after":{"exec":"GLOBAL_VARIABLES['PHASE'] = 3 \nprint('>> End')",
                                           "script":"",
                                           "finish":"""render_template('Template.html', TITLE="Processing", GLOBAL_VARIABLES=GLOBAL_VARIABLES, current_func=current_func,username=username,form_func_input_html=form_func_input_html, script=SCRIPT, content=CONTENT)"""
                                           }
                                    },
          "select_data": {"call": "pb_data.select_data(**parameters)", 
                                  "info":               "The numeric way to get a subset of data",
                                  "available_phase":    [3],
                                  "type": "ajax", 
                                  "parameters": {"feature": ["Columns", "list(pb_data.data.columns)", ["choose_append"], 5, "Select columns"],
                                                 "operator": ["Operators", "['==', '!=', '>', '<', '>=', '<=']", ["choose_append"], 5, "Select numeric operators"],
                                                 "value": ["Values", "", ["text_append", "None"], 5, "Write values"],
                                                 "inheritance": ["Inheritance", "False", ["choose", "False", "True"], 3, "whether to query based on the latest selected data (False) or the overall data (True)"]
                                                },
                                  "after":{"exec":"div=pb_data.full_describe();title='Data Selected';global content;content=format_result(title, '', div, ['delete', 'download', 'funcinfo']);print('>> End')",
                                           "script":"",
                                           "finish":"jsonify({'content':content})"
                                           }
                                    },
        "query_by": {"call": "pb_data.query_by(**parameters)", 
                      "info":               'Select data by searching keywords in a column with logical operators: and, or, not. Use "" to specify the exact spelling of a keyword',
                      "available_phase":    [3],
                      "type": "ajax", 
                      "parameters": { "attr": ["Column to Search in", "list(pb_data.data.columns)", ["choose_eval", "text"], 5, "Select columns to apply the search"],
                                      "kw_and": ["Keywords: And", "", ["text_edible", 'small', 'text'], 4, "All of the keywords must appear"],
                                     "kw_or": ["Keywords: Or", "", ["text_edible", 'small', 'text'], 4, "At least one of the keywords must appear"],
                                     "kw_not": ["Keywords: Not", "", ["text_edible", 'small', 'text'], 4, "None of these keywords should appear"],
                                     "inheritance": ["Inheritance", "False", ["choose", "False", "True"], 3, "whether to query based on the latest selected data (False) or the overall data (True)"]
                                    },
                      "after":{"exec":"div=pb_data.full_describe();title='Data Selected';global content;content=format_result(title, '', div, ['delete', 'download', 'funcinfo']);print('>> End')",
                               "script":"",
                               "finish":"jsonify({'content':content})"
                               }
                        },
        "query_bulk": {"call": "pb_data.query_bulk(**parameters)", 
              "info":               'Select data by positioning bulk input that contained in a feature',
              "available_phase":    [3],
              "type": "ajax", 
              "parameters": {"attr": ["Column to Search in", "list(pb_data.data.columns)", ["choose_eval", "text"], 5, "Select columns to apply the search"],
                             "Q_List": ["Bulk List", "", ["text_edible", 'large', 'text'], 5, "Use ',' or line breaks to split each element"],
                             "inheritance": ["Inheritance", "False", ["choose", "False", "True"], 3, "whether to query based on the latest selected data (False) or the overall data (True)"]
                            },
              "after":{"exec":"div=pb_data.full_describe();title='Data Selected';global content;content=format_result(title, '', div, ['delete', 'download', 'funcinfo']);print('>> End')",
                       "script":"",
                       "finish":"jsonify({'content':content})"
                       }
                },
        "combinatorial_query_by": {"call": "pb_data.combinatorial_query_by(**parameters)", 
              "info":               'Classifying and selecting data by multiple keyword rules and form a new categorical feature based on this for further analysis',
              "available_phase":    [3],
              "type": "ajax", 
              "parameters": {"attr": ["Column to Apply to", "list(pb_data.data.columns)", ["choose_eval", "text"], 5, "Select columns to apply the search"],
                             "kw_and": ["Keywords: And", "", ["text_append", "None"], 4, "All of the keywords must appear"],
                             "kw_or": ["Keywords: Or", "", ["text_append", "None"], 4, "At least one of the keywords must appear"],
                             "kw_not": ["Keywords: Not", "", ["text_append", "None"], 4, "None of these keywords should appear"],
                             "show_overall": ["Show Overall", "False", ["choose", "False", "True"], 5, "whether to contain the data that do not conform to any of the rules listed above"]
                            },
              "after":{"exec":"""div=pb_data.full_describe() 
                       \ntitle='Data Selected' 
                       \nglobal content
                       \ncontent=format_result(title, '', div, ['delete', 'download', 'funcinfo']) 
                       \nprint('>> End')
                       \nglobal RELOADED
                       \nglobal script
                       \nif RELOADED == False:
                       \n    script = 'location.reload()'
                       \n    RELOADED == True
                       \nelse:
                       \n    RELOADED == False
                       \n    script = ''""",
                       "script":"",
                       "finish":"jsonify({'content':content, 'script':script})"
                       }
                },
        "feature_summary": {"call": "result = pb_data.feature_summary(**parameters)", 
              "info":               'Summarize and aggregate performance data with breakdown of categorical features',
              "available_phase":    [3],
              "type": "ajax", 
              "parameters": {"feature": ["Breakdown Features", "list(pb_data.classification)", ["choose_append"], 5, "Select categorical features to process the breakdown summary"],
                             "performance": ["Value Contents", "list(pb_data.data.columns)", ["choose_append"], 5, "Select features as columns to be presented in summary"],
                             "agg": ["Aggregation Methods", "['count', 'sum', 'mean']", ["choose_append"], 5, "Select the method to aggregate the feature above"],
                             "distribution": ["Show Distribution", "True", ["choose", "False", "True"], 3, "whether to show distribution summary of each numerical column"],
                             "percentage": ["Show Percentage", "True", ["choose", "False", "True"], 3, "whether to show percentage column of each numerical feature"],
                             "color": ["Show Color", "True", ["choose", "False", "True"], 3, "whether to colorize the summary"],
                             "grand_total": ["Show Grand Total", "True", ["choose", "False", "True"], 3, "whether showing grand_total for numerical features"],
                             "color_map": ["Color Map", "['None']", ["choose_eval", "eval"], 1, "Choose a theme of color"]
                            },
              "after":{"exec":"div=result.render();title='Feature Breakdown';global content;content=format_result(title, '', div, ['delete', 'download', 'funcinfo']);print('>> End')",
                       "script":"",
                       "finish":"jsonify({'content':content})"
                       }
                },
        "feature_summary_dual": {"call": "global result;result = pb_data.feature_summary_dual(**parameters)", 
              "info":               'Summarize and aggregate performance data with breakdown of two categorical features',
              "available_phase":    [3],
              "type": "ajax", 
              "parameters": {"index": ["Feature of Row Index","list(pb_data.classification)", ["choose_eval", "text"], 5, "Select a categorical feature to process the breakdown summary"],
                             "columns": ["Feature of Columns", "list(pb_data.classification)", ["choose_eval", "text"], 5, "Select another categorical features to process the breakdown summary"],
                             "values": ["Value Contents", "list(pb_data.data.columns)", ["choose_append"], 5, "Select features as columns to be presented in summary"],
                             "agg": ["Aggregation Methods", "['count', 'sum', 'mean']", ["choose_append"], 5, "Select the method to aggregate the feature above"],
                             "percentage": ["Show Percentage", "True", ["choose", "False", "True"], 3, "whether to show percentage column of each numerical feature"],
                             "grand_total": ["Show Grand Total", "True", ["choose", "False", "True"], 3, "whether showing grand_total for numerical features"],
                             "color": ["Show Color", "True", ["choose", "False", "True"], 3, "whether to colorize the summary"],
                             "color_map": ["Color Map", "['None']", ["choose_eval", "eval"], 1, "Choose a theme of color"],
                            },
              "after":{"exec":"div=result.render();title='Feature Breakdown';global content;content=format_result(title, '', div, ['delete', 'download', 'funcinfo']);print('>> End')",
                       "script":"",
                       "finish":"jsonify({'content':content})"
                       }
                },
        "draw_feature_distribution_scatter": {"call": "global result;result = pb_data.draw_feature_distribution_scatter(**parameters)", 
              "info":               'Draw the jitter distribution plot of a feature',
              "available_phase":    [3],
              "type": "ajax", 
              "parameters": {"feature": ["Breakdown Feature", "list(pb_data.classification)", ["choose_eval", "text"], 5, "Select a categorical feature draw its breakdown distribution plot"],
                             "performance": ["Feature Distribution", "list(pb_data.performance)", ["choose_eval", "text"], 5, "Select a numeric feature to show its distribution"]
                            },
              "after":{"exec":"""global script;global content;script, div = components(result);title='Distribution Scatter Plot';content=format_result(title, '', div, ['delete', 'download', 'funcinfo']);script = script.replace('<script type="text/javascript">', '').replace('</script>', '');print('>> End')""",
                       "script":"",
                       "finish":"jsonify({'content':content, 'script':script})"
                       }
                },
        "draw_feature_time_seires_heatmap": {"call": "global result;result = pb_data.draw_feature_time_seires_heatmap(**parameters)", 
              "info":               'Draw the line plot and heatmap based on the preset time series',
              "available_phase":    [3],
              "type": "ajax", 
              "parameters": {"feature": ["Breakdown Feature", "list(pb_data.classification)", ["choose_eval", "text"], 5, "Select a categorical feature draw its breakdown distribution plot"],
                             "performance": ["Time Series of Feature", "list(pb_data.performance)", ["choose_eval", "text"], 5, "Select a numeric feature to show its distribution"]
                            },
              "after":{"exec":"""global script;global content;script, div = components(result);title='Time Series Plot';content=format_result(title, '', div, ['delete', 'download', 'funcinfo']);script = script.replace('<script type="text/javascript">', '').replace('</script>', '');print('>> End')""",
                       "script":"",
                       "finish":"jsonify({'content':content, 'script':script})"
                       }
                },
        "draw_feature_scatter": {"call": "global result;result = pb_data.draw_feature_scatter(**parameters)", 
              "info":               'Draw scatter plot with the selected axes and a categorical breakdown',
              "available_phase":    [3],
              "type": "ajax", 
              "parameters": {"x": ["Axis X", "list(pb_data.data.columns)", ["choose_eval", "text"], 5, "Select a categorical feature draw its breakdown distribution plot"],
                             "y": ["Axis Y", "list(pb_data.data.columns)", ["choose_eval", "text"], 5, "Select a numeric feature to show its distribution"],
                             "cate": ["Hue with Feature", "list(pb_data.classification)", ["choose_eval", "text"], 5, "Select a categorical feature draw its breakdown distribution plot"],
                            },
              "after":{"exec":"""global script;global content;script, div = components(result);title='Feature Scatter Plot';content=format_result(title, '', div, ['delete', 'download', 'funcinfo']);script = script.replace('<script type="text/javascript">', '').replace('</script>', '');print('>> End')""",
                       "script":"",
                       "finish":"jsonify({'content':content, 'script':script})"
                       }
                },
        "show_details": {"call": "global result;result = pb_data.show_details(**parameters)", 
              "info":               'Show top 100 rows of the latest queried data',
              "available_phase":    [3],
              "type": "ajax", 
              "parameters": {},
              "after":{"exec":"""div=result;title='Data Details (top 100 rows)';global content;content=format_result(title, '', div, ['delete', 'download', 'funcinfo']);print('>> End')""",
                       "script":"",
                       "finish":"jsonify({'content':content})"
                       }
                },
        "generate_topic_model": {"call": "global result;result = pb_data.generate_topic_model(**parameters)", 
              "info":               'Generate co-occurence mapping with specific strategy based on processed name feature',
              "available_phase":    [3],
              "type": "ajax", 
              "parameters": {
                  "word_scale": ["Scale of Word", "100", ["text_edible", 'small', 'text'], 5, "scale of words to show"],
                  "n_topics": ["Extracted Topic #", "10", ["text_edible", 'small', 'text'], 5, "How much topics extracted from original feature"],
                  "decomposition_type": ["Visualization Type", "['PCA', 'NMF', 'tSNE', 'nx.layout.fruchterman_reingold_layout', 'nx.spring_layout']", ["choose_eval", "text"], 5, "Select a categorical feature draw its breakdown distribution plot"]},
              "after":{"exec":"""global script;global content;
                                 \nscript, div = components(result);
                                 \ntitle='Feature Scatter Plot';
                                 \ncontent=format_result(title, '', div, ['delete', 'download', 'funcinfo']);
                                 \nscript = script.replace('<script type="text/javascript">', '').replace('</script>', '');
                                 \nprint('>> End')""",
                       "script":"",
                       "finish":"jsonify({'content':content, 'script':script})"
                       }
                },
          }
}

js = json.dumps(form)
f = open('static/user/public/settings/func_settings.json', 'w')
f.write(js)
f.close()