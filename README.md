# OncoMatch
-- Find the expert oncologist for personalized cancer therapies
http://52.90.79.42

# Project Aim:
### Match the needs of patients to abstracts published by oncologists based on similarity in semantic meanings which are encoded by word embedding.

<img src='https://github.com/xiey1/OncoMatch/blob/master/images/OncoMatch_model.png' width=600px>

# Data Source:
1. **Cancer.Net**: https://www.cancer.net/
2. **Pubmed**: https://www.ncbi.nlm.nih.gov/pubmed/
3. **ClinicalTrial**: https://clinicaltrials.gov/
<img src='https://github.com/xiey1/OncoMatch/blob/master/images/web_scraping.png' width=600px>

Here is a summary of some statistics of the data for this project:
| Data type  | Number of data |
| ------------- | ------------- |
| Abstracts  | 50930  |
| Oncologists  |  1470 |
| Cancer types  |  55 |
| Genes  |  206 |
| Cancer Centers  |  48 |

# Approach:
## Step 1 -- Annotate abstracts by cancer type
Around 83.4% of abstracts are annotated with cancer type by searching for cancer-related information and the remaining 16.6% are unlabeled.
<br><img src='https://github.com/xiey1/OncoMatch/blob/master/images/abstract_annotation_piechart.png' width=300px>

### Model -- LSTM
To annotate the unlabeled 16.6% abstracts, an **LSTM** model is built and trained on the labeled abstracts.
<br><img src='https://github.com/xiey1/OncoMatch/blob/master/images/lstm_model.png' width=600px>
<br>For each cancer type, an LSTM model is trained separately as a binary classification problem. **Class_0** suggests the abstract doesn't contain information about the specific cancer type and **Class_1** suggests that the abstract contains information about this cancer type.

### Classification results
<br>Here is the overall training performance for the top 29 most frequent cancer types

<br><img src='https://github.com/xiey1/OncoMatch/blob/master/images/dl_summary.png' width=400px>

Here is the detailed training and prediction results for Breast Cancer:

<br><img src='https://github.com/xiey1/OncoMatch/blob/master/images/Breast_Cancer_LSTM.png' width=800px>

After annotating the unlabeled abstracts, here is the overall cancer type information for the abstracts:

<br><img src='https://github.com/xiey1/OncoMatch/blob/master/images/LSTM_prediction.png' width=600px>

## Step 2 -- Word Embedding
Each abstract will be converted to a numeric vector that represents its semantic meanings. 
### Validation
To evaluate the word embedding performance, article titles are also converted to numeric vectors. The consine similarity scores between each pair of abstract and title are calculated and ranked. The better embedding performance suggests that the consine similarity score between each abstract and its corresponding title should have the highest ranking (percentile close to 0).

<br><img src='https://github.com/xiey1/OncoMatch/blob/master/images/validation.png' width=200px>

### Embedding results
<br>Here I tested **Word2Vec**, **Latent Dirichlet Allocation (LAD)** and **BioBERT** three models. The embedding performance is plotted as the distribution of cosine similarity score rankings between each abstract and its corresponding title (better performance corresponds to higher ranking and percentile closer to 0).

<br><img src='https://github.com/xiey1/OncoMatch/blob/master/images/Word_embedding.png' width=800px>

<br>To better visualize the embedding results from BioBERT, here I generated TSNE plots of the embedded vectors of abstracts converted by BioBERT colored based on cancer types or gene mutation information.

<br><img src='https://github.com/xiey1/OncoMatch/blob/master/images/BioBERT_TSNE.png' width=800px>

### Conclusion
**BioBERT** significantly outperforms **Word2Vec** and **LDA** models and I chose **BioBERT** to embed abstracts as well as the free-form text input from users.

# Application
**OncoMatch** http://52.90.79.42
<br><img src='https://github.com/xiey1/OncoMatch/blob/master/images/OncoMatch_webpage1.png' width=800px>
<br>Users will provide information about **Cancer type**, **Gene mutation** (optional), **Clinical Trials** and a detailed description about the disease including medical records, family history and specific therapies, etc.

For example, a user is looking for oncologists specialized in melanoma treatment. Here if we entered the biography from a famous melanoma oncologist Dr. Jedd D. Wolchok. The number one ranked oncologist from OncoMatch is Dr. Jedd D. Wolchok.

<br><img src='https://github.com/xiey1/OncoMatch/blob/master/images/OncoMatch_webpage2.png' width=800px>

<br>OncoMatch will provide information about the oncologist's affiliation, location, a list of clinical trials and a list of most relevant publications based on the search record. OncoMatch will also give a list of top ranked oncoligsts that users can take a lookt at.

For visualization, the localization of abstracts about melanoma, abstracts published by Dr. Jedd D. Wolchok about melanoma and the text input are plotted in TSNE plot.

<br><img src='https://github.com/xiey1/OncoMatch/blob/master/images/BioBERT_TSNE3.png' width=800px>

