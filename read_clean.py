# !/usr/bin/python3
# -*- coding: utf-8 -*-

import csv
import json
import os
import sys
import re
root_path = os.path.dirname(os.path.abspath(__file__))
sys.path.append(root_path)
import xlrd
from tqdm import tqdm

regex = re.compile('<p>|</p>|<br>|</br>|<br/>|<br />|<strong>|</strong>|<blockquote>|</blockquote>|<ul>|</ul>'
                   '|<li>|</li>|<ol>|</ol>|<h2>|</h2>|<table.*?>|</table>|<tbody>|</tbody>|<tr>|</tr>|<td.*?>|</td>'
                   '|<p .*?>|<iframe .*?</iframe>|<img .*?>|<pstyle.*?>|<a .*?</a>|\t|\\.{7,}|【em55317ig】'
                   '|<file .*?</file>|<ikvideo .*?</ikvideo>|<div .*?>|</div>|<span.*?>|</span>'
                   '|<video .*?</video>|<vvideo .*?</vvideo>|<em>.*?</em>|www.*?com|http.*?com|www.*?cn|http.*?cn'
                   '|◆|�|&quot|&shy|[你您]好[,:!，： ！]|&#[0-9]+[;；]?|&nbsp[;；]+|O(∩_∩)O|~~', re.I)

# 去除汉字间的空格，而不去除英文间的空格
space_regex = re.compile(u'[\u4e00-\u9fa5。\.,，:：《》、\(\)（）]{1} +(?<![a-zA-Z])|\d+ +| +\d+|[a-z A-Z]+')


def read_csv(file_in, out_list):
    all_count = 0
    success_count = 0

    with open(file_in, 'r', encoding='utf-8') as f:
        csv_reader = csv.reader(f)
        for i, row in enumerate(csv_reader):
            if i == 0:
                continue
            all_count += 1
            # if (all_count%1000) == 0:
            #     print(content)
            content = clean_content(row[1])
            if content:
                out_list.append(content)
                success_count += 1
    return all_count, success_count


def read_excel(file_in, title_column:int, content_column:int):
    "column为读取的列"
    title_list = []
    title_content_list = []
    workbook = xlrd.open_workbook(file_in)
    sheet = workbook.sheet_by_index(0)

    for i in range(sheet.nrows):
        title = clean_content(sheet.row_values(i,title_column)[0])
        content = clean_content(sheet.row_values(i, content_column)[0])
        if title:
            title_list.append(title)
        if content:
            # 连续三个英文分号连接标题和内容
            title_content_list.append(title+';;;'+content)
    # for n in out_list:
    #     print('文章：',n)
    return title_list, title_content_list


def clean_content(text_in):
    """
    处理内容
    :param text_in:
    :return:
    """
    # 如果没有一篇文章中没有中文，则不要这篇文章返回空
    if not re.search('[\u4e00-\u9fa5]', text_in):
        return ''
    # 大于小于转换
    out_text = text_in.replace('&lt;', '<').replace('&gt;', '>').replace('大于大于', '大于')
    # 通过正则去除掉相关标签
    out_text = re.sub(regex, '', out_text)
    # 全角转半角
    out_text = full_to_half(out_text)
    # 英文标点转中文标点
    out_text = eng_trans_to_chi(out_text)
    # 去除重复的字符
    if out_text:
        out_text = remove_dump_char(out_text)
    # 替换文本中部分.为句号
    if out_text:
        out_text = replace_dot(out_text)
    # 去除多余的空格
    out_text = remove_space(out_text)
    # 去除重复
    out_text = remove_repeat(out_text)
    # 去除连续标点符号
    out_text = remove_continuous_punctuations(out_text)

    return out_text


def full_to_half(ustring):
    """
    全角转半角
    :param ustring:
    :return:
    """
    ss = []
    for s in ustring:
        inside_code = ord(s)
        if inside_code == 12288:
            # 空格直接转换
            inside_code = 32
        elif 65281 <= inside_code <= 65374:
            # 其它按公式进行转换
            inside_code -= 65248
        ss.append(chr(inside_code))
    return ''.join(ss)


def eng_trans_to_chi(string):
    """
    将英文标点符号转换为中文标点符号
    :param string:
    :return:
    """
    E_pun = u',!?;'
    C_pun = u'，！？；'
    table = {ord(f): ord(t) for f, t in zip(E_pun, C_pun)}
    return string.translate(table)


def remove_dump_char(in_text):
    """
    去除文本中的重复字符
    :param in_text:输入的字符串，in_text='-----::普通'
    :return:
    """
    # 统计每个字符连续出现的次数,[{'-': 5}, {':': 2}, {'普': 1}, {'通': 1}]
    count_list = []
    count_char = in_text[0]
    count_json = {count_char: 1}
    for i in range(1, len(in_text)):
        if in_text[i] == count_char:
            count_json[count_char] += 1
        else:
            count_list.append(count_json)
            count_char = in_text[i]
            count_json = {count_char: 1}
    count_list.append(count_json)

    # 输出的字符列表
    out_list = []
    for tmp_jsoin in count_list:
        for k, v in tmp_jsoin.items():
            if v == 1:
                out_list.append(k)
            elif k in ['.'] or re.findall('[a-zA-Z]|[0-9]', k):
                out_list.append(k * v)
            elif k in ['。', '？', '—', '！', '，', '*', '；']:
                out_list.append(k)
            elif re.findall('[\u4e00-\u9fa5]', k):
                if v > 3:
                    out_list.append(k)
                else:
                    out_list.append(k * v)
            elif k in ['-']:
                out_list.append(k * 2)
            else:
                out_list.append(k)
    return ''.join(out_list)


def replace_dot(in_text):
    """
    替换句子中部分'.'为句号,英文和数字间的不替换
    :param in_text:
    :return:
    """
    # 判断文本结尾是否是一个汉字，如果是汉字则在末尾加上句号
    if re.search('[\u4e00-\u9fa5]', in_text[-1]):
        in_text += '。'
    txt_list = list(in_text)
    while True:
        tmp_match = re.search('[\u4e00-\u9fa5]\.[\u4e00-\u9fa5]|[\u4e00-\u9fa5]\.$', in_text)
        if tmp_match:
            txt_list[tmp_match.start() + 1] = '。'
            in_text = ''.join(txt_list)
        else:
            return in_text

def remove_continuous_punctuations(text):
    duels = [x+y for x in list('。，；！？、：') for y in list('。，；！？、：')]
    for d in duels:
        while d in text:
            text = text.replace(d,'')
    return text

def remove_space(text):
    """"
    处理中文之间的空格与换行符，不去除英文之间的空格
    """
    should_replace_list = space_regex.findall(text)
    order_replace_list = sorted(should_replace_list, key=lambda i: len(i), reverse=True)
    for i in order_replace_list:
        if i == u' ':
            continue
        new_i = i.strip()
        text = text.replace(i, new_i)
        text = text.replace('\n','')
    return text.strip()

# 文章循环重复检测，如果文本中有任意连续四个字出现了四次及以上，则从文本中去除该字符串
# def remove_repeat(text):
#     quartet_list = []
#     for n in range(len(text)-4):
#         quartet_list.append(text[n:n + 4])
#     for quartet in quartet_list:
#         count = quartet_list.count(quartet)
#         if count >= 4:
#             print(quartet)
#             text = text.replace(quartet,'')
#     return text

def remove_repeat(article_in):
    """
    以句号为单位，删除文章中重复的句子,如果最后一句没有写完，则删除最后一句
    :param article_in:
    :return:
    """
    sent_list = list(filter(None, re.split('。|！|？', article_in)))
    # 如果最后一个字符不是句号，则说明句子不完整，将列表的最后一个元素设置为空
    if article_in[-1] != '。':
        sent_list[-1] = ''
    # 因为去空函数将最后一个表示句号的空值去掉了，所以要在最后加一个空值
    if sent_list[-1]:
        sent_list.append('')
    if len(sent_list) <= 1:
        return article_in
    out_list = []
    for i in sent_list:
        if i not in out_list:
            out_list.append(i)
        elif len(i) < 10:
            out_list.append(i)
    return '。'.join(out_list)


def clean_corpus(filename):
    dir_name = os.path.join(root_path, 'data')
    # files = os.listdir(dir_name)
    result_list = []
    # for tmp_file in tqdm(files):
    # file_dir = os.path.join(dir_name, tmp_file)
    # print('处理文件：', file_dir)
    if filename[-3:] == 'csv':
        all_count, success_count = read_csv(os.path.join(dir_name, filename), result_list)
    else:
        all_count, success_count = read_excel(os.path.join(dir_name, filename), result_list)
    logger.debug('文件语料条数：{}，有效条数：{}，无效条数：{}\n'.format(all_count, success_count, all_count - success_count))
    logger.debug('=' * 50)
    logger.debug('语料长度'+str(len(result_list)))
    logger.debug('去重前语料条数；{}'.format(len(result_list)))
    result_list = list(set(result_list))
    logger.debug('去重后语料条数；{}'.format(len(result_list)))
    filename = filename[:-5]+'.json'
    with open(os.path.join(dir_name,filename), 'w', encoding='utf-8') as f:
        return json.dump(result_list, f, ensure_ascii=False, indent=2)


def analysis(in_file):
    """
    分析语料中不同长度的文章各有多少篇
    :param in_file:
    :return:
    """
    count_json = {
        'first': 0,
        'second': 0,
        'third': 0,
        'fourth': 0,
        'fifth': 0
    }
    corpus_list = json.load(open(in_file, 'r', encoding='utf-8'))
    print('语料长度')
    for i in corpus_list:
        length = len(i)
        if length <= 50:
            count_json['first'] += 1
        elif 50 < length <= 100:
            count_json['second'] += 1
        elif 100 < length <= 250:
            count_json['third'] += 1
        elif 250 < length <= 800:
            count_json['fourth'] += 1
        else:
            count_json['fifth'] += 1
    print(count_json)


if __name__ == '__main__':
    # clean_corpus('shazi.xlsx')
    # analysis('train_all_0416.json')
    # tmp_txt = '1.细胞自行收紧，推移脂肪，填补凹陷，收粗大毛孔，只需一次，只需两个小时.既安心无痛苦，又可以提升.瘦脸.紧肤.除皱同时完成.'

    a=clean_content("""或外观感觉不自然。的。、。，。，。；。；。，。；。，；，。，；
""")
    print(a)