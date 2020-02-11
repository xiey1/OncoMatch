from flask import render_template
from flask import request
from webapp import app
import pandas as pd
import numpy as np
import os
import gensim
from nltk.stem import WordNetLemmatizer
import pickle
from sklearn.metrics.pairwise import cosine_similarity
from webapp.doctor_recommendation import Oncomatch_model
from webapp.doctor_recommendation import Get_info
from ast import literal_eval

# here's the homepage
@app.route('/')
def homepage():
    base_dir='/Volumes/Yuchen_Drive/Insight/OncoMatch'
    abstract_catalog=pd.read_csv(os.path.join(base_dir,'data/abstract_citation_annot_df_50930_aws.csv'),index_col='pmid')
    cancertype_df=pd.read_csv(os.path.join(base_dir, "data/cancertype_df2.csv"))
    cancertype_list=list(cancertype_df.cancer_type.sort_values().unique())
    gene_df=pd.read_csv(os.path.join(base_dir, "data/HGNC_df2.csv"))
    gene_list=['NA']+list(gene_df.HGNC.unique())
    return render_template("webapp_input.html",cancertype_list=cancertype_list,gene_list=gene_list)

@app.route('/webapp_output')
def onco_output():
    cancer_type = request.args.get('cancer_type')
    gene_name = request.args.get('gene_name')
    original_text = request.args.get('original_text')
    clinical_trial_checked = (request.args.get('clinical_trial') != None)

    base_dir='/Volumes/Yuchen_Drive/Insight/OncoMatch'
    abstract_catalog=pd.read_csv(os.path.join(base_dir,'data/abstract_citation_annot_df_50930_aws.csv'),index_col='pmid')
    cancertype_df=pd.read_csv(os.path.join(base_dir, "data/cancertype_df2.csv"))
    cancertype_list=list(cancertype_df.cancer_type.sort_values().unique())
    gene_df=pd.read_csv(os.path.join(base_dir, "data/HGNC_df2.csv"))
    gene_list=['NA']+list(gene_df.HGNC.unique())
    img_df=pd.read_csv(os.path.join(base_dir, "data/img_dict_df.csv"),index_col='name',encoding='latin-1')

    err_message1 = "Cancer type cannot be found. Please try again."
    if cancer_type not in cancertype_list:
        return render_template("webapp_input.html",cancertype_list=cancertype_list,gene_list=gene_list,error_message1=err_message1)

    err_message2 = "Gene cannot be found. Please try again or select 'NA'."
    if gene_name not in gene_list:
        return render_template("webapp_input.html",cancertype_list=cancertype_list,gene_list=gene_list,error_message2=err_message2)

    err_message3 = "Disease description is important to find the matched oncologist. Please tell me about your disease."
    if len(original_text.strip())==0:
        return render_template("webapp_input.html",cancertype_list=cancertype_list,gene_list=gene_list,error_message3=err_message3)


    onco=Oncomatch_model(cancer_type)
    similarity_df=onco.get_similarity_scores(original_text)

    if gene_name != 'NA':
        pmid_gene=Get_info().gene_to_pmid(gene_name, gene_df)
        pmid_list=[]
        for i in similarity_df.pmid:
            if i in pmid_gene:
                pmid_list.append(i)
    else:
        pmid_list=list(similarity_df.pmid)

    if len(pmid_list) != 0:
        test_df = onco.get_onco_info(pmid_list,clinical_trial_checked)
        if test_df.shape[0] != 0:
            test_df.to_csv(os.path.join(base_dir,'temp/temp.csv'),index=False)
            onco_list = test_df.name
            onco_name = test_df.name.iloc[0]
            if onco_name in img_df.index:
                onco_img_path = '../static/images/'+img_df.loc[onco_name].img_name
            else:
                onco_img_path = '../static/images/smile_face_img.jpg'
            onco_center = test_df.center_name.iloc[0]
            center_img_path = '../static/images/'+"_".join([i.lower() for i in onco_center.split()])+".png"
            clin_num = test_df.loc[onco_name, 'clinical_trial_num2']
            location = test_df.loc[onco_name, 'city_state']
            pub_num = test_df.loc[onco_name, 'query_pmid_num']

            onco_clinical_df = onco.get_clinical_data(onco_name)
            pmid_list=test_df.loc[onco_name,'query_pmid'][:test_df.loc[onco_name,'pmid_rank_10th_percentile']]
            pmid_df=abstract_catalog.loc[np.array(pmid_list)]
            pmid_df['citation'] = pmid_df['citation'].astype('Int64')
            with open(os.path.join(base_dir, 'temp/temp.text'), 'w') as f:
                f.write(cancer_type)
            return render_template("webapp_output.html", onco_df=test_df.head(10), onco_list=onco_list, onco_name=onco_name, onco_clinical_df=onco_clinical_df, pmid_df=pmid_df, onco_img_path=onco_img_path, center_img_path=center_img_path, onco_center=onco_center, clin_num=clin_num, location=location, pub_num=pub_num)
        else:
            return render_template("error.html")
    else:
        return render_template("error.html")

@app.route('/webapp_output/webapp_clinical')
def clinical_output():
    onco_name = request.args.get('onco_name')
    base_dir='/Volumes/Yuchen_Drive/Insight/OncoMatch'
    img_df=pd.read_csv(os.path.join(base_dir, "data/img_dict_df.csv"),index_col='name',encoding='latin-1')
    if onco_name in img_df.index:
        onco_img_path = '../static/images/'+img_df.loc[onco_name].img_name
    else:
        onco_img_path = '../static/images/smile_face_img.jpg'
    with open(os.path.join(base_dir, 'temp/temp.text'), 'r') as f:
        cancer_type=f.read()

    test_df = pd.read_csv(os.path.join(base_dir,'temp/temp.csv'),index_col='name',converters={"query_pmid":literal_eval, "pmid_rank":literal_eval})
    abstract_catalog=pd.read_csv(os.path.join(base_dir,'data/abstract_citation_annot_df_50930_aws.csv'),index_col='pmid')
    onco_center = test_df.loc[onco_name, 'center_name']
    center_img_path = '../static/images/'+"_".join([i.lower() for i in onco_center.split()])+".png"
    clin_num = test_df.loc[onco_name, 'clinical_trial_num2']
    location = test_df.loc[onco_name, 'city_state']
    pub_num = test_df.loc[onco_name, 'query_pmid_num']

    onco=Oncomatch_model(cancer_type)
    onco_clinical_df = onco.get_clinical_data(onco_name)

    pmid_list=test_df.loc[onco_name,'query_pmid'][:test_df.loc[onco_name,'pmid_rank_10th_percentile']]
    pmid_df=abstract_catalog.loc[np.array(pmid_list)]
    pmid_df['citation'] = pmid_df['citation'].astype('Int64')
    return render_template("webapp_clinical.html", onco_name=onco_name, onco_clinical_df=onco_clinical_df, pmid_df=pmid_df, onco_img_path=onco_img_path, center_img_path=center_img_path, onco_center=onco_center, clin_num=clin_num, location=location, pub_num=pub_num)
