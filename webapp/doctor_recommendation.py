import pandas as pd
import numpy as np
import os
import gensim
from nltk.stem import WordNetLemmatizer
import pickle
from sklearn.metrics.pairwise import cosine_similarity
from collections import defaultdict
from ast import literal_eval

class Oncomatch_model():
    def __init__(self,cancer_type):
        self.base_dir='/Volumes/Yuchen_Drive/Insight/OncoMatch'
        self.cancer_type=cancer_type
        self.prefix="_".join(i.lower() for i in cancer_type.split())
        self.bow_dict=gensim.corpora.Dictionary.load(os.path.join(self.base_dir,'models_lda/{}_abstract_bow_dict.dict'.format(self.prefix)))
        self.tfidf=gensim.models.TfidfModel.load(os.path.join(self.base_dir,'models_lda/{}_abstract_tfidf.tfidf'.format(self.prefix)))
        self.lda_model=gensim.models.LdaMulticore.load(os.path.join(self.base_dir,'models_lda/{}_abstract_lda.lda'.format(self.prefix)))
        self.lda_df=pd.read_csv(os.path.join(self.base_dir, "models_lda/{}_abstract_ldavector_df.csv".format(self.prefix)), index_col='pmid').drop(['pred'],axis=1)
        self.stop_words=pickle.load(open(os.path.join(self.base_dir, "data/stop_words_lda.set"),"rb"))

        self.onco_df=pd.read_csv(os.path.join(self.base_dir, "data/Oncologist_info_clinicaltrial_1470.csv"))
        self.onco_df.index=self.onco_df.name
        self.cancerclinical2doctor_dict_df=pd.read_csv(os.path.join(self.base_dir, 'data/cancerclinical2doctor_dict_df.csv'),converters={"doctor":literal_eval},index_col='cancer_type')
        self.doctor2clinical_dict2_df=pd.read_csv(os.path.join(self.base_dir, 'data/doctor2clinical_dict2_df.csv'),index_col='name')
        self.pmid2doctor_dict_df=pd.read_csv(os.path.join(self.base_dir, 'data/pmid2doctor_dict_df.csv'),converters={"doctor":literal_eval},index_col='pmid')

    def preprocess(self, text):
        result = []
        for token in gensim.utils.simple_preprocess(text):
            temp=WordNetLemmatizer().lemmatize(token).lower()
            if len(temp)>1 and temp not in self.stop_words:
                result.append(temp)
        return result

    def get_embedding_vector(self, text):
        text_corpus=[self.bow_dict.doc2bow(text)]
        text_tfidf=self.tfidf[text_corpus]

        #text_lsa=self.lsa_model[text_tfidf]
        #text_lsa=gensim.matutils.corpus2csc(text_lsa)
        #text_lsa=text_lsa.T.toarray()

        text_lda=self.lda_model[text_tfidf]
        text_lda = gensim.matutils.corpus2csc(text_lda)
        text_lda = text_lda.T.toarray()

        #text_doc2vec=self.doc2vec.infer_vector(text, alpha=0.001, min_alpha=0.001, steps=10000)
        #text_doc2vec=text_doc2vec.reshape(1,-1)

        return text_lda

    def compute_similarity(self, embedding_matrix, text_vector):
        return cosine_similarity(X=embedding_matrix,Y=text_vector,dense_output=False)

    def get_similarity_scores(self, text):
        text_preprocess=self.preprocess(text)
        text_lda=self.get_embedding_vector(text_preprocess)

        #text_lsa_sim=self.compute_similarity(self.lsa_df,text_lsa)
        text_lda_sim=self.compute_similarity(self.lda_df,text_lda)
        #text_doc2vec_sim=self.compute_similarity(self.doctovec_df,text_doc2vec)

        similarity_df=pd.DataFrame({'pmid':self.lda_df.index, 'lda_similarity':text_lda_sim.squeeze()}).sort_values(by=['lda_similarity'],ascending=False).reset_index().drop(['index'],axis=1)
        return similarity_df

    def get_onco_info(self, pmid_list,clinical_trial):
        """
        Input: cancer_type and a list of pmid
        Output: DataFrame containing information for oncologists that publish the articles
        """
        onco2pmid=defaultdict(list)
        onco2rank=defaultdict(list)
        for i,pmid in enumerate(pmid_list):
            for doctor in self.pmid2doctor_dict_df.loc[pmid,'doctor']:
                onco2pmid[doctor].append(pmid)
                onco2rank[doctor].append(i)
        temp_df = self.onco_df.loc[np.array(list(onco2pmid.keys()))]
        temp_df['query_pmid'] = temp_df.name.apply(lambda x:onco2pmid[x])
        temp_df['query_pmid_num'] = temp_df.name.apply(lambda x:len(onco2pmid[x]))
        temp_df['pmid_rank'] = temp_df.name.apply(lambda x:onco2rank[x])
        temp_df['pmid_rank_10th_percentile'] = temp_df.pmid_rank.apply(lambda x: sum(np.array(x)<=int(np.ceil(temp_df.shape[0]/10))))
        temp_df['clinical_trial_num2']='NA'

        if clinical_trial and self.cancer_type in self.cancerclinical2doctor_dict_df.index:
            doctor_clin = np.intersect1d(np.array(self.cancerclinical2doctor_dict_df.loc[self.cancer_type,'doctor']), temp_df.name.values)
            temp_df = temp_df.loc[np.array(doctor_clin)].sort_values(by=['pmid_rank_10th_percentile'],ascending=False)
            temp_df['clinical_trial_num2']=temp_df.name.apply(lambda x: int(self.doctor2clinical_dict2_df.loc[x, self.cancer_type]))

        return temp_df

    def get_clinical_data(self, onco_name):
        cancer_prefix="_".join(i.lower() for i in self.cancer_type.split())
        temp_df = pd.read_csv(os.path.join(self.base_dir, 'clinical_trial/{}_clinical_trial_info.csv'.format(cancer_prefix)))
        temp_df_onco=temp_df.query('name=="{}"'.format(onco_name))
        return temp_df_onco

class Get_info():
    def __init__(self):
        self.base_dir='/Volumes/Yuchen_Drive/Insight/OncoMatch'
        #self.doctor2pmid_dict=pickle.load(open(os.path.join(self.base_dir, "data/doctor2pmid_1153_dict.pkl"),"rb"))
        #self.cancer2pmid_dict=pickle.load(open(os.path.join(self.base_dir, "data/cancer2pmid_dict.pkl"),"rb"))
        #self.cancer2doctor_dict=pickle.load(open(os.path.join(self.base_dir, "data/cancer2doctor_dict.pkl"),"rb"))
        #self.pmid2doctor_dict=pickle.load(open(os.path.join(self.base_dir, "data/pmid2doctor_dict.pkl"),"rb"))
        #self.pmid2cancer_dict=pickle.load(open(os.path.join(self.base_dir, "data/pmid2doctor_dict.pkl"),"rb"))
        #self.doctor2cancer_dict=pickle.load(open(os.path.join(self.base_dir, "data/doctor2cancer_dict.pkl"),"rb"))
    def gene_to_pmid(self,gene,data):
        pmid_array = data.query('HGNC=="{}"'.format(gene)).pmid.unique()
        return pmid_array

    #def doctor_to_pmid(self,doctor):
    #    return self.doctor2pmid_dict[doctor]
