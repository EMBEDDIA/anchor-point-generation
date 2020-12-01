import argparse
import os

import lxml.etree as lxml
from lxml import etree

def create_alignment_from_link(link, lang1_c, lang2_c, pc_mpc_mapper=None, lang1_file_id=None, lang2_file_id=None):
    if pc_mpc_mapper is None:
        split_lang = link.split(';')
        sent_ids_lang1 = list(map(int, split_lang[0].split(' ')))
        sent_ids_lang2 = list(map(int, split_lang[1].split(' ')))
        lang1_res = ' '.join([lang1_c[i - 1] for i in sent_ids_lang1]) + '\n'
        lang2_res = ' '.join([lang2_c[i - 1] for i in sent_ids_lang2]) + '\n'
        return lang1_res, lang2_res

    lang1_c_temp = lang1_c[lang1_file_id]
    split_lang = link.split(';')
    sent_ids_lang1 = list(map(int, split_lang[0].split(' ')))
    sent_ids_lang2 = list(map(int, split_lang[1].split(' ')))
    lang1_res = ' '.join([lang1_c_temp[i - 1] for i in sent_ids_lang1]) + '\n'
    lang2_res = ' '.join([lang2_c[int(pc_mpc_mapper[lang2_file_id][str(i)]) - 1] for i in sent_ids_lang2]) + '\n'

    return lang1_res, lang2_res


def read_mpc_pc_mapper(mpc_pc_mapper_path):
    with open(mpc_pc_mapper_path, 'r') as p:
        mapper = {}
        for line in p:
            mpc, pc = line[:-1].split('-')
            sent_mpc_id = mpc.split(' ')[0].split('/')[1]
            for el in pc.split(' '):
                file_pc_id = el.split('/')[0]
                sent_pc_id = el.split('/')[1]
                if file_pc_id not in mapper:
                    mapper[file_pc_id] = {}
                if sent_pc_id not in mapper[file_pc_id]:
                    mapper[file_pc_id][sent_pc_id] = {}
                mapper[file_pc_id][sent_pc_id] = sent_mpc_id

    return mapper


def main(args):
    parser = argparse.ArgumentParser(
        description='Find words from languages L1 and L2 in same context, output dictionaries and embeddings for those words.')
    parser.add_argument('-i', '--input1', help='L1 corpus in .vert format (or already pre-processed .ali format)')
    parser.add_argument('-j', '--input2', help='L2 corpus in .vert format (or already pre-processed .ali format)')
    parser.add_argument('-a', '--mapper_file', help='path to mapper file')
    parser.add_argument('-o', '--output1', help='path to output1 file')
    parser.add_argument('-p', '--output2', help='path to output2 file')
    parser.add_argument('--file_extension', help='extention to read in multiple files')
    parser.add_argument('--mpc-pc_mapper', default=None, help='tell whether we have paracrawl corpus on input1 (not multiparacrawl) - multiple files on input')
    args = parser.parse_args(args)

    pc_mpc_mapper = read_mpc_pc_mapper(args.mpc_pc_mapper)



    lang1 = {}
    lang2 = []
    if os.path.isdir(args.input1):
        if args.file_extension == 'tsv':
            loc = -3
        else:
            loc = -4
        paths_to_files = [(str(int(filename.split('.')[loc])), os.path.join(args.input1, filename)) for filename in os.listdir(args.input1) if filename.split('.')[-1] == args.file_extension]
    else:
        paths_to_files = [('1', args.input1)]
    for f_id, path in paths_to_files:
        with open(path, 'r') as corpus:
            for line in corpus:
                lang1.setdefault(f_id, []).append(line[:-1])

    with open(args.input2, 'r') as lang2_corpus:
        for line in lang2_corpus:
            lang2.append(line[:-1])
            # break


    with open(args.output1, 'w') as lang1_w, open(args.output2, 'w') as lang2_w:
        if args.mpc_pc_mapper is None:
            root = etree.parse(args.mapper_file)
            linkGrp = root.find('linkGrp')
            for link in linkGrp.findall('link'):
                lang1_sen, lang2_sen = create_alignment_from_link(link.attrib['xtargets'], lang1, lang2)
                lang1_w.write(lang1_sen)
                lang2_w.write(lang2_sen)

        else:
            root = etree.parse(args.mapper_file)
            linkGrps = root.findall('linkGrp')
            for linkGrp in linkGrps:
                fromDoc = str(int(linkGrp.attrib['fromDoc'].split('.')[-3]))
                toDoc = str(int(linkGrp.attrib['toDoc'].split('.')[-3]))
                for link in linkGrp.findall('link'):
                    lang1_sen, lang2_sen = create_alignment_from_link(link.attrib['xtargets'], lang1, lang2, pc_mpc_mapper,
                                                                      fromDoc, toDoc)
                    lang1_w.write(lang1_sen)
                    lang2_w.write(lang2_sen)

if __name__ == '__main__':
    import sys
    main(sys.argv[1:])
