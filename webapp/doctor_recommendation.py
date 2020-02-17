import pandas as pd
import numpy as np
import os
import pickle
from sklearn.metrics.pairwise import cosine_similarity
from collections import defaultdict
from ast import literal_eval
from transformers import BertTokenizer
from transformers import BertModel
import torch

class Oncomatch_model():
    def __init__(self,cancer_type):
        self.base_dir='/Volumes/Yuchen_Drive/Insight/OncoMatch'
        self.cancer_type=cancer_type
        self.prefix="_".join(i.lower() for i in cancer_type.split())
        self.bert_df=pd.read_csv(os.path.join(self.base_dir,'bert_data/{}_abstract_bert_df.csv'.format(self.prefix)),index_col='pmid')
        self.model=BertModel.from_pretrained(os.path.join(self.base_dir, 'bert/biobert_v1.1_pubmed'))
        self.tokenizer = BertTokenizer.from_pretrained(os.path.join(self.base_dir, 'bert/biobert_v1.1_pubmed'), do_lower_case=True)

        self.onco_df=pd.read_csv(os.path.join(self.base_dir, "data/Oncologist_info_clinicaltrial_1470.csv"))
        self.onco_df.index=self.onco_df.name
        self.cancerclinical2doctor_dict_df=pd.read_csv(os.path.join(self.base_dir, 'data/cancerclinical2doctor_dict_df.csv'),converters={"doctor":literal_eval},index_col='cancer_type')
        self.doctor2clinical_dict2_df=pd.read_csv(os.path.join(self.base_dir, 'data/doctor2clinical_dict2_df.csv'),index_col='name')
        self.pmid2doctor_dict_df=pd.read_csv(os.path.join(self.base_dir, 'data/pmid2doctor_dict_df.csv'),converters={"doctor":literal_eval},index_col='pmid')

    def prepare_input_seq(self, input_seq, tokenizer, max_len):
        # here prepare the input sequence for the Bert model
        tokens0 = tokenizer.tokenize(input_seq)
        for j,t in enumerate(tokens0):
            if t in [".","?","!"]:
                tokens0[j] = t+" [SEP]"
        tokens = []
        for t in tokens0:
            tokens+=t.split()
        if tokens[-1]!='[SEP]':
            tokens = ['[CLS]'] + tokens + ['[SEP]']
        else:
            tokens = ['[CLS]'] + tokens

        if len(tokens)>max_len:
            padded_tokens = tokens[:max_len]
        else:
            padded_tokens = tokens

        indexed_tokens = tokenizer.convert_tokens_to_ids(padded_tokens)
        tokens_tensor = torch.tensor([indexed_tokens])

        return tokens_tensor

    def embed_sents(self, sents,model,max_len):
        # LM is the language model to be loaded separately.
        id2sent = {j:sent for j,sent in enumerate(sents)}
        emb_mat = np.zeros([len(id2sent),768])
        for j,sent in enumerate(sents):
            input_seq = sent
            tokens_tensor = self.prepare_input_seq(input_seq,self.tokenizer,max_len)
            val, hidden = model(tokens_tensor)
            val = torch.squeeze(val).mean(axis=0).reshape(1,-1)
            emb_mat[j,:] = val.detach().numpy()

        return emb_mat

    def get_embedding_vector(self, text):
        text_bert = self.embed_sents([text], self.model,max_len=128)
        return text_bert

    def compute_similarity(self, embedding_matrix, text_vector):
        return cosine_similarity(X=embedding_matrix,Y=text_vector,dense_output=False)

    def get_similarity_scores(self, text):
        text_bert=self.get_embedding_vector(text)
        text_bert_sim=self.compute_similarity(self.bert_df,text_bert)
        similarity_df=pd.DataFrame({'pmid':self.bert_df.index, 'bert_similarity':text_bert_sim.squeeze()}).sort_values(by=['bert_similarity'],ascending=False).reset_index().drop(['index'],axis=1)
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

    def gene_to_pmid(self,gene,data):
        pmid_array = data.query('HGNC=="{}"'.format(gene)).pmid.unique()
        return pmid_array

    #def doctor_to_pmid(self,doctor):
    #    return self.doctor2pmid_dict[doctor]
