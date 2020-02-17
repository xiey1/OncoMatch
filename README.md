# OncoMatch
-- Find the expert oncologist for personalized cancer therapies

# Project Aim:
### Match the needs of patients to abstracts published by oncologists based on similarity in semantic meanings which are encoded by word embedding.

# Data Source:
1. **Cancer.Net**: https://www.cancer.net/
2. **Pubmed**: https://www.ncbi.nlm.nih.gov/pubmed/
3. **ClinicalTrial**: https://clinicaltrials.gov/
<img src='https://github.com/xiey1/OncoMatch/blob/master/images/web_scraping.png' width=600px>

Here is a summary of some statistics of the data for this project:
| Information type  | Number of data |
| ------------- | ------------- |
| Abstracts  | 50930  |
| Oncologists  |  1470 |
| Cancer types  |  55 |
| Genes  |  206 |
| Cancer Centers  |  48 |

# Approach:
## Step 1 -- Annotate abstract by cancer type
Around 83.4% of abstracts are annotated with cancer type by searching for cancer-related information and the remaining 16.6% are unlabeled.
<br><img src='https://github.com/xiey1/OncoMatch/blob/master/images/abstract_annotation_piechart.png' width=300px>

To annotate the unlabeled 16.6% abstracts, an **LSTM** model is built.
<br><img src='https://github.com/xiey1/OncoMatch/blob/master/images/lstm_model.png' width=600px>
<br>For each cancer type, an LSTM model is trained separately as a binary classification problem. **Class_0** suggests the abstract doesn't contain information about the specific cancer type and **Class_1** suggests that the abstract contains information about this cancer type.

<br>Here is the overall training performance for the top 29 most frequent cancer types
<br><img src='https://github.com/xiey1/OncoMatch/blob/master/images/dl_summary.png' width=300px>
