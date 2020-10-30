import torch
import torch.utils.data as data
import random
import math
import os
# import sys
# sys.path.append('/apdcephfs/share_916081/qtli/install/ft_local/EmpDG')
# print(sys.path)
import logging 
from utils import config
import pickle
from tqdm import tqdm
import numpy as np
import pprint
pp = pprint.PrettyPrinter(indent=1)
from nltk.tokenize import word_tokenize
from nltk.corpus import wordnet
from nltk.corpus import stopwords
stop_words = stopwords.words('english')
import re
import time
import nltk
import json
import pdb
# nltk.download('punkt')
word_pairs = {"it's": "it is", "don't": "do not", "doesn't": "does not", "didn't": "did not", "you'd": "you would",
                  "you're": "you are", "you'll": "you will", "i'm": "i am", "they're": "they are", "that's": "that is",
                  "what's": "what is", "couldn't": "could not", "i've": "i have", "we've": "we have", "can't": "cannot",
                  "i'd": "i would", "i'd": "i would", "aren't": "are not", "isn't": "is not", "wasn't": "was not",
                  "weren't": "were not", "won't": "will not", "there's": "there is", "there're": "there are"}

class Lang:
    def __init__(self, init_index2word):
        self.word2index = {str(v): int(k) for k, v in init_index2word.items()}
        self.word2count = {str(v): 1 for k, v in init_index2word.items()}
        self.index2word = init_index2word 
        self.n_words = len(init_index2word)  # Count default tokens
      
    def index_words(self, sentence):
        for word in sentence:
            self.index_word(word.strip())

    def index_word(self, word):
        if word not in self.word2index:
            self.word2index[word] = self.n_words
            self.word2count[word] = 1
            self.index2word[self.n_words] = word
            self.n_words += 1
        else:
            self.word2count[word] += 1

def clean(sentence, word_pairs):
    sentence = sentence.lower()
    for k, v in word_pairs.items():
        sentence = sentence.replace(k,v)
    sentence = nltk.word_tokenize(sentence)
    return sentence


def get_wordnet_pos(tag):
    if tag.startswith('J'):
        return wordnet.ADJ
    elif tag.startswith('V'):
        return wordnet.VERB
    elif tag.startswith('N'):
        return wordnet.NOUN
    elif tag.startswith('R'):
        return wordnet.ADV
    else:
        return None


def read_langs_for_G(vocab):
    emotion_lexicon = json.load(open('empathetic-dialogue/NRCDict.json'))[0]

    train_context = np.load('empathetic-dialogue/sys_dialog_texts.train.npy', allow_pickle=True)
    train_target = np.load('empathetic-dialogue/sys_target_texts.train.npy', allow_pickle=True)
    train_emotion = np.load('empathetic-dialogue/sys_emotion_texts.train.npy', allow_pickle=True)
    train_situation = np.load('empathetic-dialogue/sys_situation_texts.train.npy', allow_pickle=True)

    dev_context = np.load('empathetic-dialogue/sys_dialog_texts.dev.npy', allow_pickle=True)
    dev_target = np.load('empathetic-dialogue/sys_target_texts.dev.npy', allow_pickle=True)
    dev_emotion = np.load('empathetic-dialogue/sys_emotion_texts.dev.npy', allow_pickle=True)
    dev_situation = np.load('empathetic-dialogue/sys_situation_texts.dev.npy', allow_pickle=True)

    test_context = np.load('empathetic-dialogue/sys_dialog_texts.test.npy', allow_pickle=True)
    test_target = np.load('empathetic-dialogue/sys_target_texts.test.npy', allow_pickle=True)
    test_emotion = np.load('empathetic-dialogue/sys_emotion_texts.test.npy', allow_pickle=True)
    test_situation = np.load('empathetic-dialogue/sys_situation_texts.test.npy', allow_pickle=True)

    data_train = {'context': [], 'emotion_context': [], 'target': [], 'emotion': [], 'situation': []}
    data_dev = {'context': [], 'emotion_context': [], 'target': [], 'emotion': [], 'situation': []}
    data_test = {'context': [], 'emotion_context': [], 'target': [], 'emotion': [], 'situation': []}

    # train
    for context in train_context:
        u_list = []
        e_list = []
        for u in context:
            u = clean(u, word_pairs)  # have been tokenized
            u_list.append(u)
            vocab.index_words(u)
            # for emotion context
            ws_pos = nltk.pos_tag(u)  # pos
            for w in ws_pos:
                w_p = get_wordnet_pos(w[1])
                if w[0] not in stop_words and (w_p == wordnet.ADJ or w[0] in emotion_lexicon):
                    e_list.append(w[0])
        data_train['context'].append(u_list)
        data_train['emotion_context'].append(e_list)
    for target in train_target:
        target = clean(target, word_pairs)
        data_train['target'].append(target)
        vocab.index_words(target)
    for situation in train_situation:
        situation = clean(situation, word_pairs)
        data_train['situation'].append(situation)
        vocab.index_words(situation)
    for emotion in train_emotion:
        data_train['emotion'].append(emotion)
    assert len(data_train['context']) == len(data_train['target']) == len(data_train['emotion']) == len(
        data_train['situation'])

    # valid
    for context in dev_context:
        u_list = []
        e_list = []
        for u in context:
            u = clean(u, word_pairs)
            u_list.append(u)
            vocab.index_words(u)
            # for emotion context
            ws_pos = nltk.pos_tag(u)  # pos
            for w in ws_pos:
                w_p = get_wordnet_pos(w[1])
                if w[0] not in stop_words and (w_p == wordnet.ADJ or w[0] in emotion_lexicon):
                    e_list.append(w[0])
        data_dev['context'].append(u_list)
        data_dev['emotion_context'].append(e_list)
    for target in dev_target:
        target = clean(target, word_pairs)
        data_dev['target'].append(target)
        vocab.index_words(target)
    for situation in dev_situation:
        situation = clean(situation, word_pairs)
        data_dev['situation'].append(situation)
        vocab.index_words(situation)
    for emotion in dev_emotion:
        data_dev['emotion'].append(emotion)
    assert len(data_dev['context']) == len(data_dev['target']) == len(data_dev['emotion']) == len(data_dev['situation'])

    # test
    for context in test_context:
        u_list = []
        e_list = []
        for u in context:
            u = clean(u, word_pairs)
            u_list.append(u)
            vocab.index_words(u)
            # for emotion context
            ws_pos = nltk.pos_tag(u)  # pos
            for w in ws_pos:
                w_p = get_wordnet_pos(w[1])
                if w[0] not in stop_words and (w_p == wordnet.ADJ or w[0] in emotion_lexicon):
                    e_list.append(w[0])
        data_test['context'].append(u_list)
        data_test['emotion_context'].append(e_list)
    for target in test_target:
        target = clean(target, word_pairs)
        data_test['target'].append(target)
        vocab.index_words(target)
    for situation in test_situation:
        situation = clean(situation, word_pairs)
        data_test['situation'].append(situation)
        vocab.index_words(situation)
    for emotion in test_emotion:
        data_test['emotion'].append(emotion)
    assert len(data_test['context']) == len(data_test['target']) == len(data_test['emotion']) == len(
        data_test['situation'])
    return data_train, data_dev, data_test, vocab


def read_langs_for_D(vocab):
    train_context = np.load('empathetic-dialogue/sys_dialog_texts.train.npy', allow_pickle=True)
    train_feedback = np.load('empathetic-dialogue/sys_target_texts.train.npy', allow_pickle=True)
    train_emotion = np.load('empathetic-dialogue/sys_emotion_texts.train.npy', allow_pickle=True)
    train_situation = np.load('empathetic-dialogue/sys_situation_texts.train.npy', allow_pickle=True)

    dev_context = np.load('empathetic-dialogue/sys_dialog_texts.dev.npy', allow_pickle=True)
    dev_feedback = np.load('empathetic-dialogue/sys_target_texts.dev.npy', allow_pickle=True)
    dev_emotion = np.load('empathetic-dialogue/sys_emotion_texts.dev.npy', allow_pickle=True)
    dev_situation = np.load('empathetic-dialogue/sys_situation_texts.dev.npy', allow_pickle=True)

    test_context = np.load('empathetic-dialogue/sys_dialog_texts.test.npy', allow_pickle=True)
    test_feedback = np.load('empathetic-dialogue/sys_target_texts.test.npy', allow_pickle=True)
    test_emotion = np.load('empathetic-dialogue/sys_emotion_texts.test.npy', allow_pickle=True)
    test_situation = np.load('empathetic-dialogue/sys_situation_texts.test.npy', allow_pickle=True)

    data_train = {'context':[],'emotion_context':[],'target':[],'target_emotion':[],'feedback':[],'feedback_emotion':[],'emotion':[],'situation': []}
    data_dev = {'context':[],'emotion_context':[],'target':[],'target_emotion':[],'feedback':[],'feedback_emotion':[],'emotion':[],'situation': []}
    data_test = {'context':[],'emotion_context':[],'target':[],'target_emotion':[],'feedback':[],'feedback_emotion':[],'emotion':[],'situation': []}

    emotion_lexicon = json.load(open('empathetic-dialogue/NRCDict.json'))[0]

    # train
    for context in train_context:
        if len(context) < 2:
            continue
        u_list = []
        e_list = []
        t_list = []
        for i, u in enumerate(context):
            u = clean(u, word_pairs)
            if i == len(context)-1:  # target in adversarial training
                data_train['target'].append(u)
                vocab.index_words(u)
                # for target emotional words
                ws_pos = nltk.pos_tag(u)  # pos
                for w in ws_pos:
                    w_p = get_wordnet_pos(w[1])
                    if w[0] not in stop_words and (w_p == wordnet.ADJ or w[0] in emotion_lexicon):
                        t_list.append(w[0])
                data_train['target_emotion'].append(t_list)
            else:
                u_list.append(u)
                vocab.index_words(u)
                # for emotion context
                ws_pos = nltk.pos_tag(u)  # pos
                for w in ws_pos:
                    w_p = get_wordnet_pos(w[1])
                    if w[0] not in stop_words and (w_p == wordnet.ADJ or w[0] in emotion_lexicon):
                        e_list.append(w[0])
        data_train['context'].append(u_list)
        data_train['emotion_context'].append(e_list)
    for idx, feedback in enumerate(train_feedback):
        if len(train_context[idx]) < 2:
            continue
        feedback = clean(feedback, word_pairs)
        data_train['feedback'].append(feedback)
        vocab.index_words(feedback)
        # for feedback emotional words
        f_list = []
        ws_pos = nltk.pos_tag(feedback)  # pos
        for w in ws_pos:
            w_p = get_wordnet_pos(w[1])
            if w[0] not in stop_words and (w_p == wordnet.ADJ or w[0] in emotion_lexicon):
                f_list.append(w[0])
        data_train['feedback_emotion'].append(f_list)
    for idx, situation in enumerate(train_situation):
        if len(train_context[idx]) < 2:
            continue
        situation = clean(situation, word_pairs)
        data_train['situation'].append(situation)
        vocab.index_words(situation)
    for idx, emotion in enumerate(train_emotion):
        if len(train_context[idx]) < 2:
            continue
        data_train['emotion'].append(emotion)
    assert len(data_train['context']) == len(data_train['target']) == len(data_train['emotion']) == len(data_train['situation'])

    # valid
    for context in dev_context:
        if len(context) < 2:
            continue
        u_list = []
        e_list = []
        t_list = []
        for i, u in enumerate(context):
            u = clean(u, word_pairs)
            if i == len(context) - 1:  # target in adversarial training
                data_dev['target'].append(u)
                vocab.index_words(u)
                # for target emotional words
                ws_pos = nltk.pos_tag(u)  # pos
                for w in ws_pos:
                    w_p = get_wordnet_pos(w[1])
                    if w[0] not in stop_words and (w_p == wordnet.ADJ or w[0] in emotion_lexicon):
                        t_list.append(w[0])
                data_dev['target_emotion'].append(t_list)
            else:
                u_list.append(u)
                vocab.index_words(u)
                # for emotion context
                ws_pos = nltk.pos_tag(u)  # pos
                for w in ws_pos:
                    w_p = get_wordnet_pos(w[1])
                    if w[0] not in stop_words and (w_p == wordnet.ADJ or w[0] in emotion_lexicon):
                        e_list.append(w[0])
        data_dev['context'].append(u_list)
        data_dev['emotion_context'].append(e_list)
    for idx, feedback in enumerate(dev_feedback):
        if len(dev_context[idx]) < 2:
            continue
        feedback = clean(feedback, word_pairs)
        data_dev['feedback'].append(feedback)
        vocab.index_words(feedback)
        # for feedback emotional words
        f_list = []
        ws_pos = nltk.pos_tag(feedback)  # pos
        for w in ws_pos:
            w_p = get_wordnet_pos(w[1])
            if w[0] not in stop_words and (w_p == wordnet.ADJ or w[0] in emotion_lexicon):
                f_list.append(w[0])
        data_dev['feedback_emotion'].append(f_list)
    for idx, situation in enumerate(dev_situation):
        if len(dev_context[idx]) < 2:
            continue
        situation = clean(situation, word_pairs)
        data_dev['situation'].append(situation)
        vocab.index_words(situation)
    for idx, emotion in enumerate(dev_emotion):
        if len(dev_context[idx]) < 2:
            continue
        data_dev['emotion'].append(emotion)
    assert len(data_dev['context']) == len(data_dev['target']) == len(data_dev['emotion']) == len(data_dev['situation'])

    # test
    for context in test_context:
        if len(context) < 2:
            continue
        u_list = []
        e_list = []
        t_list = []
        for i, u in enumerate(context):
            u = clean(u, word_pairs)
            if i == len(context) - 1:  # target in adversarial training
                data_test['target'].append(u)
                vocab.index_words(u)
                # for target emotional words
                ws_pos = nltk.pos_tag(u)  # pos
                for w in ws_pos:
                    w_p = get_wordnet_pos(w[1])
                    if w[0] not in stop_words and (w_p == wordnet.ADJ or w[0] in emotion_lexicon):
                        t_list.append(w[0])
                data_test['target_emotion'].append(t_list)
            else:
                u_list.append(u)
                vocab.index_words(u)
                # for emotion context
                ws_pos = nltk.pos_tag(u)  # pos
                for w in ws_pos:
                    w_p = get_wordnet_pos(w[1])
                    if w[0] not in stop_words and (w_p == wordnet.ADJ or w[0] in emotion_lexicon):
                        e_list.append(w[0])
        data_test['context'].append(u_list)
        data_test['emotion_context'].append(e_list)
    for idx, feedback in enumerate(test_feedback):
        if len(test_context[idx]) < 2:
            continue
        feedback = clean(feedback, word_pairs)
        data_test['feedback'].append(feedback)
        vocab.index_words(feedback)
        # for feedback emotional words
        f_list = []
        ws_pos = nltk.pos_tag(feedback)  # pos
        for w in ws_pos:
            w_p = get_wordnet_pos(w[1])
            if w[0] not in stop_words and (w_p == wordnet.ADJ or w[0] in emotion_lexicon):
                f_list.append(w[0])
        data_test['feedback_emotion'].append(f_list)
    for idx, situation in enumerate(test_situation):
        if len(test_context[idx]) < 2:
            continue
        situation = clean(situation, word_pairs)
        data_test['situation'].append(situation)
        vocab.index_words(situation)
    for idx, emotion in enumerate(test_emotion):
        if len(test_context[idx]) < 2:
            continue
        data_test['emotion'].append(emotion)
    assert len(data_test['context']) == len(data_test['target']) == len(data_test['emotion']) == len(
        data_test['situation'])
    return data_train, data_dev, data_test, vocab


def load_dataset():
    if config.model == "adver_train":  # contains prediction and its emotional words for adversarial training
        print("LOADING empathetic_dialogue for adversarial training")
        with open('empathetic-dialogue/disc_data.p', "rb") as f:
            [data_tra, data_val, data_tst, _] = pickle.load(f)
    else:
        print("LOADING empathetic_dialogue for EmpDG_woG")
        with open('empathetic-dialogue/my_D_dataset_preproc.p', "rb") as f:
            [data_tra, data_val, data_tst, vocab] = pickle.load(f)

    for i in range(20,23):
        print('[situation]:', ' '.join(data_tra['situation'][i]))
        print('[emotion]:', data_tra['emotion'][i])
        print('[context]:', [' '.join(u) for u in data_tra['context'][i]])
        print('[emotion context]:', ' '.join(data_tra['emotion_context'][i]))
        print('[target]:', ' '.join(data_tra['target'][i]))
        print('[feedback]:', ' '.join(data_tra['feedback'][i]))
        print(" ")

    print("train length: ", len(data_tra['situation']))
    print("valid length: ", len(data_val['situation']))
    print("test length: ", len(data_tst['situation']))
    return data_tra, data_val, data_tst, vocab


# if __name__ == '__main__':
    # dataset for pre-train Empathetic Generator
    print("Building dataset...")  # train: 40250; valid: 5734; test: 5255.
    data_tra, data_val, data_tst, vocab = read_langs_for_G(vocab=Lang({config.UNK_idx: "UNK", config.PAD_idx: "PAD", config.EOS_idx: "EOS", config.SOS_idx: "SOS", config.USR_idx:"USR", config.SYS_idx:"SYS", config.CLS_idx:"CLS", config.LAB_idx:"LAB"}))
    with open('empathetic-dialogue/my_G_dataset_preproc.p', "wb") as f:
        pickle.dump([data_tra, data_val, data_tst, vocab], f)
        print("Saved PICKLE")


    # dataset for fine-tune Empathetic Generator with Interactive Discriminators
    # print("Building dataset...")
    # data_tra, data_val, data_tst, vocab = read_langs_for_D(vocab=Lang(
    #     {config.UNK_idx: "UNK", config.PAD_idx: "PAD", config.EOS_idx: "EOS", config.SOS_idx: "SOS",
    #      config.USR_idx: "USR", config.SYS_idx: "SYS", config.CLS_idx: "CLS", config.LAB_idx: "LAB"}))
    # with open('empathetic-dialogue/my_D_dataset_preproc.p', "wb") as f:
    #     pickle.dump([data_tra, data_val, data_tst, vocab], f)
    #     print("Saved PICKLE")

    # with open('empathetic-dialogue/my_G_dataset_preproc.p', "rb") as f:
    #     [data_tra, data_val, data_tst, vocab] = pickle.load(f)


    # for i in range(3):
    #     print('[emotion]:', data_tra['emotion'][i])
    #     print('[context]:', [' '.join(u) for u in data_tra['context'][i]])
    #     print('[emotion context]:', data_tra['emotion_context'][i])
    #     # print(len(data_tra['context'][i][0].split(' ')))
    #     print('[target]:', ' '.join(data_tra['target'][i]))
    #     print(" ")

    # context = ['i remember going to see the fireworks with my best friend . it was the first time we ever spent time alone together . although there was a lot of people , we felt like the only people in the world .',
    #     'was this a friend you were in love with , or just a best friend ?', 'this was a best friend . i miss her .',
    #     'where has she gone ?', 'we no longer talk .']
    # emotion_lexicon = json.load(open('empathetic-dialogue/NRCDict.json'))[0]
    #
    # for u in context:
    #     u = clean(u, word_pairs)
    #     # for emotion context
    #     e_list = []
    #     ws_pos = nltk.pos_tag(u)  # pos
    #     for w in ws_pos:
    #         w_p = get_wordnet_pos(w[1])
    #         if w[0] not in stop_words and (w_p == wordnet.ADJ or w[0] in emotion_lexicon):
    #             e_list.append(w[0])
    #     print(e_list)



# def load_dataset():
#     with open('empathetic-dialogue/my_G_dataset_preproc.p', "rb") as f:
#         [a,b,c,vocab] = pickle.load(f)
#     if config.model == "wo_D":  # train: 40250; valid: 5734; test: 5255.
#         print("LOADING empathetic_dialogue for EmpDG_woD")
#         with open('empathetic-dialogue/my_G_dataset_preproc.p', "rb") as f:
#             [data_tra, data_val, data_tst, _] = pickle.load(f)
#     elif config.model == "wo_G":
#         print("LOADING empathetic_dialogue for EmpDG_woG")
#         with open('empathetic-dialogue/my_D_dataset_preproc.p', "rb") as f:
#             [data_tra, data_val, data_tst, _] = pickle.load(f)
#     elif config.model == "adver_train":
#         print("LOADING empathetic_dialogue for adversarial training")
#         with open('empathetic-dialogue/disc_data.p', "rb") as f:
#             [data_tra, data_val, data_tst, _] = pickle.load(f)
#     elif config.model == "EmpDG":
#         print("LOADING empathetic_dialogue for EmpDG_woG")
#         with open('empathetic-dialogue/my_D_dataset_preproc.p', "rb") as f:
#             [data_tra, data_val, data_tst, _] = pickle.load(f)
#     elif config.model == "EmoPrepend" or "Transformer":
#         print("LOADING empathetic_dialogue for baseline model")
#         with open('empathetic-dialogue/my_G_dataset_preproc.p', "rb") as f:
#             [data_tra, data_val, data_tst, _] = pickle.load(f)
#     else:
#         data_tra, data_val, data_tst, vocab = None, None, None, None
#         print("data file not exists !!")
#         exit(0)
#     for i in range(20,23):
#         print('[situation]:', ' '.join(data_tra['situation'][i]))
#         print('[emotion]:', data_tra['emotion'][i])
#         print('[context]:', [' '.join(u) for u in data_tra['context'][i]])
#         print('[emotion context]:', ' '.join(data_tra['emotion_context'][i]))
#         print('[target]:', ' '.join(data_tra['target'][i]))
#         print(" ")
#
#     print("train length: ", len(data_tra['situation']))
#     print("valid length: ", len(data_val['situation']))
#     print("test length: ", len(data_tst['situation']))
#     return data_tra, data_val, data_tst, vocab
#
#
# # if __name__ == '__main__':
#     # dataset for pre-train Empathetic Generator
#     print("Building dataset...")  # train: 40250; valid: 5734; test: 5255.
#     data_tra, data_val, data_tst, vocab = read_langs_for_G(vocab=Lang({config.UNK_idx: "UNK", config.PAD_idx: "PAD", config.EOS_idx: "EOS", config.SOS_idx: "SOS", config.USR_idx:"USR", config.SYS_idx:"SYS", config.CLS_idx:"CLS", config.LAB_idx:"LAB"}))
#     with open('empathetic-dialogue/my_G_dataset_preproc.p', "wb") as f:
#         pickle.dump([data_tra, data_val, data_tst, vocab], f)
#         print("Saved PICKLE")
#
#
#     # dataset for fine-tune Empathetic Generator with Interactive Discriminators
#     # print("Building dataset...")
#     # data_tra, data_val, data_tst, vocab = read_langs_for_D(vocab=Lang(
#     #     {config.UNK_idx: "UNK", config.PAD_idx: "PAD", config.EOS_idx: "EOS", config.SOS_idx: "SOS",
#     #      config.USR_idx: "USR", config.SYS_idx: "SYS", config.CLS_idx: "CLS", config.LAB_idx: "LAB"}))
#     # with open('empathetic-dialogue/my_D_dataset_preproc.p', "wb") as f:
#     #     pickle.dump([data_tra, data_val, data_tst, vocab], f)
#     #     print("Saved PICKLE")
#
#     # with open('empathetic-dialogue/my_G_dataset_preproc.p', "rb") as f:
#     #     [data_tra, data_val, data_tst, vocab] = pickle.load(f)
#
#
#     # for i in range(3):
#     #     print('[emotion]:', data_tra['emotion'][i])
#     #     print('[context]:', [' '.join(u) for u in data_tra['context'][i]])
#     #     print('[emotion context]:', data_tra['emotion_context'][i])
#     #     # print(len(data_tra['context'][i][0].split(' ')))
#     #     print('[target]:', ' '.join(data_tra['target'][i]))
#     #     print(" ")
#
#     # context = ['i remember going to see the fireworks with my best friend . it was the first time we ever spent time alone together . although there was a lot of people , we felt like the only people in the world .',
#     #     'was this a friend you were in love with , or just a best friend ?', 'this was a best friend . i miss her .',
#     #     'where has she gone ?', 'we no longer talk .']
#     # emotion_lexicon = json.load(open('empathetic-dialogue/NRCDict.json'))[0]
#     #
#     # for u in context:
#     #     u = clean(u, word_pairs)
#     #     # for emotion context
#     #     e_list = []
#     #     ws_pos = nltk.pos_tag(u)  # pos
#     #     for w in ws_pos:
#     #         w_p = get_wordnet_pos(w[1])
#     #         if w[0] not in stop_words and (w_p == wordnet.ADJ or w[0] in emotion_lexicon):
#     #             e_list.append(w[0])
#     #     print(e_list)


