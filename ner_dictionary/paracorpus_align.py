import argparse
import csv
import os
import pickle
import sys
from nltk.metrics import *

csv.field_size_limit(sys.maxsize)

from lxml import etree


def read_sentences(path, limit, links=None, file_extension=None):
    tsv_path = path
    if os.path.isdir(tsv_path):
        if file_extension is None:
            all_paths = [(str(int(f_name.split('.')[2])), os.path.join(tsv_path, f_name)) for f_name in os.listdir(tsv_path)]
        else:
            all_paths = [(str(int(f_name.split('.')[2])), os.path.join(tsv_path, f_name)) for f_name in os.listdir(tsv_path) if f_name.split('.')[-1] == file_extension]
    else:
        all_paths = [(-1, tsv_path)]

    i = 0
    sentences = {}
    for file_id, tsv_path in all_paths:
        with open(tsv_path) as tsvfile:
            reader = csv.reader(tsvfile, delimiter='\t', quoting=csv.QUOTE_NONE)
            sentence_id = -1
            new_sentence = []
            for row in reader:
                if sentence_id == -1:
                    sentence_id = int(row[2][1:].split('.')[0])
                    new_sentence.append([row[0], row[1], row[3]])
                elif len(row) == 0:
                    if links is not None:
                        file_id, new_sentence_id = links[str(sentence_id)].split('/')
                        if file_id not in sentences:
                            sentences[file_id] = {}
                        sentences[file_id][int(new_sentence_id)] = new_sentence
                    elif file_id == '-1':
                        sentences[sentence_id] = new_sentence
                    else:
                        if file_id not in sentences:
                            sentences[file_id] = {}
                        sentences[file_id][sentence_id] = new_sentence
                    if limit and i == limit:
                        break
                    sentence_id = -1
                    new_sentence = []
                    i += 1
                else:
                    new_sentence.append([row[0], row[1], row[3]])

    return sentences


def form_sentences(ids, dictionary, file_id=None, multifile=False):
    complete_sentence = []
    for id in ids:
        if multifile:
            if int(id) in dictionary[file_id]:
                complete_sentence.extend(dictionary[file_id][int(id)])
        else:
            if int(id) in dictionary:
                complete_sentence.extend(dictionary[int(id)])

    return complete_sentence




def get_named_entities(sentence):
    ne = []
    ne_type = None
    sentence_ne = {}
    for word in sentence:
        if word[2] != 'O':
            if word[2][0] == 'B' or word[2][0] == 'S':
                if ne != []:
                    if ne_type in sentence_ne:
                        sentence_ne[ne_type].append(ne)
                    else:
                        sentence_ne[ne_type] = []
                        sentence_ne[ne_type].append(ne)
                ne_type = word[2][2:]
                ne = [word[1]]
            else:
                ne.append(word[1])
        else:
            if ne != []:
                if ne_type in sentence_ne:
                    sentence_ne[ne_type].append(ne)
                else:
                    sentence_ne[ne_type] = []
                    sentence_ne[ne_type].append(ne)
            ne = []
    return sentence_ne


def read_links(mpc_pc_links):
    links = {}
    with open(mpc_pc_links, 'r') as the_file:
        for line in the_file.readlines():
            whole_ids, split_ids = line.split('-')
            split_id = split_ids[:-1].split()[0]
            for whole_id in whole_ids.split():
                links[whole_id.split('/')[1]] = split_id

    return links


def main(args):
    parser = argparse.ArgumentParser(
        description='Find words from languages L1 and L2 in same context, output dictionaries and embeddings for those words.')
    parser.add_argument('--corpus_lang1', help='Path to MultiParaCrawl corpus file or ParaCrawl folder in first language language')
    parser.add_argument('--corpus_lang2', help='Path to MultiParaCrawl corpus in second language language (If you have ParaCrawl it should passed in first parameter)')
    parser.add_argument('--align_file', help='Path to xml file that contains sentence alignments')
    parser.add_argument('--output_folder', help='Path to output folder')
    parser.add_argument('--mpc_pc_links', default=None, help='File that links MultiparaCrawl ids to ParaCrawl ids - created by align_sentences.py script.')
    parser.add_argument('--file_extension', default=None, help='File extensions of interest in corpus_lang1')
    args = parser.parse_args(args)

    limit = False

    hr_sl_path = args.align_file

    print('Reading data...')

    if args.mpc_pc_links is not None:
        links = read_links(args.mpc_pc_links)
    else:
        links = None

    hr_sentences = read_sentences(args.corpus_lang1, limit, file_extension=args.file_extension)
    print('L1 data read.')
    sl_sentences = read_sentences(args.corpus_lang2, limit, links=links)
    print('L2 data read.')


    print('Formatting data...')

    context = etree.iterparse(hr_sl_path, tag="linkGrp")
    sl_saved_sentences = []
    hr_saved_sentences = []
    i = 0
    for _, links_grouped in context:
        lang1_file_id = str(int(links_grouped.attrib['fromDoc'].split('.')[2]))
        lang2_file_id = str(int(links_grouped.attrib['toDoc'].split('.')[2]))
        for elem in links_grouped.iter(tag="link"):
            links = elem.attrib['xtargets'].split(';')
            hr = links[0].split(' ')
            sl = links[1].split(' ')

            if limit and (any(int(el) > limit for el in hr) or any(int(el) > limit for el in sl)):
                continue

            hr_saved_sentences.append(form_sentences(hr, hr_sentences, lang1_file_id, args.mpc_pc_links is not None))
            sl_saved_sentences.append(form_sentences(sl, sl_sentences, lang2_file_id, args.mpc_pc_links is not None))
            if limit:
                if i == limit:
                    break
                i += 1


    print('Writing results...')

    path = args.output_folder
    final_results = set()
    aligned_nes = []
    with open(path + 'results.txt', 'w') as the_file:
        with open(path + 'results_dist0.txt', 'w') as the_file0:
            with open(path + 'results_dist2.txt', 'w') as the_file2:
                with open(path + 'results_dist4.txt', 'w') as the_file4:
                    with open(path + 'results_sim9.txt', 'w') as the_files9:
                        with open(path + 'results_sim8.txt', 'w') as the_files8:
                            with open(path + 'results_sim7.txt', 'w') as the_files7:
                                for hr, sl in zip(hr_saved_sentences, sl_saved_sentences):
                                    hr_nes = get_named_entities(hr)

                                    sl_nes = get_named_entities(sl)
                                    for key in hr_nes:
                                        # check if size of SLO entities is equal to CRO
                                        if key in sl_nes and len(hr_nes[key]) == len(sl_nes[key]):
                                            correct = True
                                            for i in range(len(hr_nes[key])):
                                                if len(hr_nes[key][i]) != len(sl_nes[key][i]):
                                                    correct = False
                                                    break
                                            if correct:
                                                for h_w, s_w in zip(hr_nes[key], sl_nes[key]):
                                                    final_results.add((' '.join(h_w), ' '.join(s_w)))
                                                aligned_nes.append([hr_nes[key], sl_nes[key]])

                                for h_w, s_w in final_results:
                                    edit_dist = edit_distance(h_w, s_w)
                                    jaro_dist = distance.jaro_similarity(h_w, s_w)
                                    the_file.write(h_w + '\t' + s_w + '\n')
                                    if edit_dist == 0:
                                        the_file0.write(h_w + '\t' + s_w + '\n')
                                    if edit_dist <= 2:
                                        the_file2.write(h_w + '\t' + s_w + '\n')
                                    if edit_dist <= 4:
                                        the_file4.write(h_w + '\t' + s_w + '\n')
                                    if jaro_dist >= 0.9:
                                        the_files9.write(h_w + '\t' + s_w + '\n')
                                    if jaro_dist >= 0.8:
                                        the_files8.write(h_w + '\t' + s_w + '\n')
                                    if jaro_dist >= 0.7:
                                        the_files7.write(h_w + '\t' + s_w + '\n')


if __name__ == '__main__':
    import sys
    main(sys.argv[1:])
