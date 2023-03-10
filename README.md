# text_quality_metrics

How to use：

1. Start service python3.7 text_quality.py，default http://localhost:19092

2. Enter the title and content of the article to be evaluated in json format {"title":"xxxx","article":"yyyyyyyy"}


Metrics explanation:


  With reference to the HUSE index, a 100-point quantitative index is designed to judge whether the model is good or bad.


Readability: Manually judge the readability and convert it into a score

a. Randomly sample sentences
b. Manual scoring standard


Topic relevance: compare the benchmark corpus of the generated topic, and use statistical means to obtain the topic relevance score

Preparation of subject benchmark corpus:

Using the title as the topic, eg, the existing more than 4,000 topics are classified into less than 100 topics.

Segment the articles on each topic to get vocabulary with real meaning (mainly verbs, nouns, adjectives), such as: filling, fullness, hyaluronic acid, etc.

Use the resulting vocabulary as a benchmark reference corpus for a specific topic

Comparison of model generated articles and benchmark corpus:

Determine the category of the generated article, and perform word segmentation to obtain the vocabulary of real meaning.
Detect the proportion of substantive vocabulary in generated articles belonging to various subject benchmark corpora. 
The higher the proportion belonging to its own category, the higher the degree of relevance.


Repetition degree: 
    It is divided into repetition degree within the article, repetition degree between articles generated by the same model and the same topic, and repetition degree between generated articles and corpus articles
    a. The degree of repetition in the article, the ratio of the number of words left in the article after N-gram de-duplication processing to the number of required words
    b. The N-gram between articles generated by the same model, the longest common sequence LCS, the longer the more points will be deducted
    c. N-gram between model articles and corpus, LCS

Combining manual and statistical scores, debug their respective weight parameters, and obtain a general scoring standard
