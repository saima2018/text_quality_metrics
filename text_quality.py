# !/usr/bin/python3
# -*- coding: utf-8 -*-

import os
import sys
import copy
import traceback
from math import log10, log2, log
import time
import json
from read_clean import read_excel, clean_content
import stanza

from flask import Flask, make_response, request
from Utils.DataUtils import load_xml_conf
# 从配置文件中获取指定GPU序号的参数
conf = load_xml_conf()
# 标题类别词汇
categories = conf['categories']

app = Flask(__name__)
@app.route('/',methods=['POST'])
def article_vocab_and_clean_test():
    if request.method == 'POST':
        title = request.json.get('title')
        article = request.json.get('article')
    # print(title,article)
    vocab_score, in_count, out_count, in_word, out_word = article_vocab_test(title,article)
    print(vocab_score, in_count, out_count, in_word, out_word)
    # vocab_score = round(in_count/(in_count+out_count), 2)
    clean_score = article_clean_test(article)
    return '文章切题度得分{}，有效度得分{}'.format(vocab_score, clean_score)

def generate_category_vocab(article_file, vocab_file):
    """
    生成整容细分类别词汇
    :param article_file: 语料文件，第一列序号，第二列标题，第三列文章
    :param vocab_file: 词汇库文件，有初始格式，可新增
    :param vocab_file_new:
    :param title_column:
    :param content_column:
    :return:
    """

    # 读取现有类别词汇
    with open(vocab_file,'r', encoding='utf-8') as load_f:
        content = load_f.read()
        if content.startswith(u'\ufeff'):
            content = content.encode('utf8')[3:].decode('utf8')
        load_json = json.loads(content)
    category_vocab = load_json['category_vocab'] # 该类别名词词条个数
    category_vocab_title = load_json['category_vocab_title'] # 人工设定该类别标题词条列表
    category_count = load_json['category_count'] # 分词所得该类别名词词条个数

    # 读取待学习的标准文章excel文件
    title_list, title_content_list = read_excel(article_file, 1,2)

    article_counter = 0
    article_sum = len(title_content_list)
    for title_content in title_content_list:
        article_counter += 1
        print('\r正在处理第{:^5}篇文章，共{:^5}篇文章'.format(article_counter,article_sum),end='')

        title, content = title_content.split(';;;')

        # 根据标题判断每篇文章的类别，一篇文章可以属于多个类别
        for key, value in category_vocab_title.items():
            for n in value:
                # 如果类别关键词出现在标题中,则将文章中的实义名词加入类别词汇，同时将类别文章计数加1
                if n in title:
                    doc = nlp(content)
                    for sent in doc.sentences:
                        for word in sent.words:
                            if word.xpos in['NN']:
                                if word.text not in category_vocab[key]:
                                    category_vocab[key][word.text] = 1
                                else:
                                    category_vocab[key][word.text] += 1

                    break # 出现一个该类别关键词即可跳出

    print(category_vocab)
    # 找出同时出现在十个类别的词汇，再将它们去除
    # repeat_word_list = []
    # for key, vocab_list in category_vocab.items():
    #     for word in vocab_list:
    #         word_counter = 0
    #         for other_key, other_vocab_list in category_vocab.items():
    #             if word in other_vocab_list:
    #                 word_counter += 1
    #                 if word_counter >= 10: # 该词同时出现于五个及以上类别
    #                     repeat_word_list.append(word)
    # repeat_word_list = list(set(repeat_word_list))
    # print(repeat_word_list)
    # for key, value_list in category_vocab.items():
    #     value_list_catch = []
    #     for value in value_list:
    #         if value not in repeat_word_list:
    #             value_list_catch.append(value)
    #     category_vocab[key] = value_list_catch
    # 得出各类别词条个数
    for key,value in category_vocab.items():
        category_count[key] = len(value)
    # 按category_count各类别词条个数的格式初始化category_weight各类别权重
    category_weight = copy.deepcopy(category_count)
    total_categories = 0
    total_articles = 0
    for key, value in category_count.items():
        total_categories += 1
        total_articles += value
    average_articles = round(total_articles / total_categories, 2)
    for key, value in category_count.items():
        category_weight[key] = round(value / average_articles, 2)
    # print(category_weight)
    # 根据各类别词库和权重，计算各类别词条加权个数
    category_vocab_tfidf = tfidf(category_vocab, category_weight)
    # 将vocab写入json文件
    vocab = {}
    vocab['category_count'] = category_count
    vocab['category_vocab'] = category_vocab
    vocab['category_vocab_title'] = category_vocab_title
    vocab['category_vocab_tfidf'] = category_vocab_tfidf
    vocab['category_weight'] = category_weight
    # vocab['repeat_word_list'] = repeat_word_list

    # 将生成的无序词汇表写入json文件
    with open(vocab_file, 'w', encoding='utf-8') as f:
        json.dump(vocab, f, ensure_ascii=False)

    #
    # # 将排序的生成的词汇表写入新json文件
    # category_count = sorted(category_count.items(), key=lambda d: d[1], reverse=True)
    # for key, value in category_vocab.items():
    #     category_vocab[key] = sorted(value.items(), key=lambda d: d[1], reverse=True)
    # vocab_ordered = {}
    # vocab_ordered['category_count'] = category_count
    # vocab_ordered['category_vocab'] = category_vocab
    # vocab_ordered['category_vocab_title'] = category_vocab_title
    # with open(vocab_file_new, 'w', encoding='utf-8') as f:
    #     json.dump(vocab_ordered,f,ensure_ascii=False)

def tfidf(category_vocab, category_weight):
    # 读取现有词汇权重
    category_weight = category_weight
    # 读取现有类别词汇
    category_vocab = copy.deepcopy(category_vocab)  # 各类别名词词条个数
    category_vocab_tfidf = category_vocab # 按category_vocab的格式初始化category_vocab_tfidf
    for category, value_dict in category_vocab.items():
        for term, frequency in value_dict.items():
            term = term
            tf = frequency / category_weight[category]  # 计算词频时，除以该词所属类别文章的权重
            df = 1
            for _, other_value_dict in category_vocab.items():
                if term in other_value_dict:
                    df += 1
            idf = log2(len(category_vocab)/(df+1))
            # print(term, tf,df,idf, tf*idf)
            try:
                category_vocab_tfidf[category][term] = round(tf*idf,2)
            except:
                traceback.print_exc()
                pass
    # print(category_vocab_tfidf)
    return category_vocab_tfidf

def article_vocab_test(title, content):
    # 清洗标题和文章
    title = clean_content(title)
    content = clean_content(content)
    # 读取现有类别词汇
    vocab_file = r'conf/vocab.json'

    with open(vocab_file,'r', encoding='utf-8') as load_f:
        load_json = json.load(load_f)
    category_vocab = load_json['category_vocab']
    category_vocab_tfidf = load_json['category_vocab_tfidf'] # 词汇加权个数
    # 读取标题类别词汇
    category_vocab_title = copy.deepcopy(categories)

    all_key_list = [] #全部类别列表
    article_key_list = []     # 文章所属类别列表
    non_article_key_list = []     # 非文章所属类别列表
    # 遍历各类别标题词库中的每一个词，如果它出现在待评测文章的标题中，则将该文章归为此类别
    for key, value_list in category_vocab_title.items():
        for value in value_list:
            if value in title:
                if key not in article_key_list: # 如果没有已经归到某类，则将匹配到的类别加入列表
                    article_key_list.append(key)
            elif (key not in non_article_key_list):
                non_article_key_list.append(key)
    if len(article_key_list) == 0:
        return '未能归类标题'
    # 去除 non_article_key_list 里面同时出现在 article_key_list里的key
    non_article_key_list_catch = []
    for key in non_article_key_list:
        if key not in article_key_list:
            non_article_key_list_catch.append(key)
    non_article_key_list = non_article_key_list_catch

    # nlp = stanza.Pipeline('zh')
    doc = nlp(content)
    # 统计文章词汇在所属类别词汇的次数in_counter，存入列表in_word，与在非所属类别词汇的次数out_counter，存入out_word
    in_word = []
    out_word = []
    # 待评估文章中的NN词列表
    noun_in_article_list = []
    for sent in doc.sentences:
        for word in sent.words:
            if word.xpos in ['NN']:
                noun_in_article_list.append(word.text)
    noun_in_article_list = list(set(noun_in_article_list))
    for word in noun_in_article_list:
        for key in article_key_list:
            if word in category_vocab[key]:
                in_word.append(word)
                # in_word.append(key)

        for key in non_article_key_list:
            if word in category_vocab[key]:
                out_word.append(word)
                # out_word.append(key)
    in_word = list(set(in_word))
    out_word = list(set(out_word))
    out_word_catch = []
    for word in out_word:
        if word not in in_word:
            out_word_catch.append(word)
    out_word = out_word_catch
    # 读取词汇加权个数
    in_word_weighted_score = 0
    out_word_weighted_score = 0
    # 计算正确类别词汇加权个数
    for _, vocab_list in category_vocab_tfidf.items():
        for word in in_word:
            if word in vocab_list:
                in_word_weighted_score += vocab_list[word]
    # 计算错误类别词汇加权个数
    for _, vocab_list in category_vocab_tfidf.items():
        for word in out_word:
            if word in vocab_list:
                out_word_weighted_score += vocab_list[word]

    vocab_score = round(in_word_weighted_score/(in_word_weighted_score+out_word_weighted_score), 2)

    return vocab_score, round(in_word_weighted_score,2), round(out_word_weighted_score,2), in_word, out_word

def article_clean_test(article):
    """计算文章去除重复、无效字符后的长度与初始长度的比例"""
    original_len = len(article)
    clean_article = clean_content(article)
    # print(clean_article)
    clean_len = len(clean_article)
    return round(clean_len/original_len, 2)

# 将现有词汇表全部清零，从头学习生成
def re_initialise():
    vocab_file = r'conf/vocab.json'
    with open(vocab_file, 'r', encoding='utf-8') as load_f:
        load_json = json.load(load_f)
    category_vocab = load_json['category_vocab'] # 各类别词汇及个数
    category_vocab_tfidf = load_json['category_vocab_tfidf']  # 各类别词汇及加权个数
    category_weight = load_json['category_weight'] # 各类别权重
    category_count = load_json['category_count'] # 各类别词条数
    category_vocab_title = load_json['category_vocab_title'] # 各类别标题词汇
    for category, count in category_count.items():
        category_count[category] = 0
    for category, weight in category_weight.items():
        category_weight[category] = 0
    for category, vocab_dict in category_vocab.items():
        for word, count in vocab_dict.items():
            category_vocab[category][word] = 0
    for category, vocab_dict in category_vocab_tfidf.items():
        for word, count in vocab_dict.items():
            category_vocab_tfidf[category][word] = 0

    # 将vocab写入json文件
    vocab = {}
    vocab['category_count'] = category_count
    vocab['category_vocab'] = category_vocab
    vocab['category_vocab_title'] = category_vocab_title
    vocab['category_vocab_tfidf'] = category_vocab_tfidf
    vocab['category_weight'] = category_weight

    # 将生成的无序词汇表写入json文件
    with open(vocab_file, 'w', encoding='utf-8') as f:
        json.dump(vocab, f, ensure_ascii=False)

if __name__ == '__main__':
    nlp = stanza.Pipeline('zh')
    vocab_file = r'conf/vocab.json'
    article_file = r'conf/test.xlsx'
    # title = r'开眼角手术花多少钱？'
    #
    # article = r"""<p>眼部整形手术大体分为两种，单开眼角和开内眼角。单开眼角的花费，一般在4000-15000。开眼角的花费，一般在4000-15000。不过开眼角的效果也并不是永久的，一般不会再有长的效果，所以求美者还是要到正规的美容机构接受手术。开眼角的花费。希望以上信息可以帮到您。希望能帮到您。望采纳。开眼角的花费。希望能帮到您。望采纳。希望能帮到您。望采纳。开眼角的花费。希望能帮到您。</p><p>望采纳。希望能帮到您。望采纳。开眼角的花费。望采纳。希望能帮到您。望采纳。希望能帮到您。望采纳。开眼角的花费。望采纳。希望能帮到您。望采纳。希望能帮到您。可以采纳。开眼角的花费。望采纳。望采纳。希望能帮到您。希望能帮到您。可以采纳。</p><p>开眼角的花费。望采纳。希望能帮到您。希望能帮到您。可以采纳。开眼角的花费。望采纳。希望能帮到您。希望能帮到您。可以采纳。开眼角的花费。望采纳。希望能帮到您。可以采纳。开眼角的花费。望采纳。希望能帮到您。可以采纳。开眼角的花费。望采纳。可以采纳。</p>
  # """
    # generate_category_vocab(article_file,vocab_file)
    # tfidf(vocab_file)
    # a = article_vocab_test(title,article)
    # a = article_vocab_and_clean_test(title, article)
    # print(a)
    app.debug = True
    app.run(host='0.0.0.0', port='19092')
#     b = article_clean_test(article)
#     print(b)
#     re_initialise()
