# ====================================================================
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
# ====================================================================
import argparse
import pickle
import string
import sys

import lucene
import os

from java.nio.file import Path, Paths
from org.apache.lucene.analysis.standard import StandardAnalyzer
from org.apache.lucene.index import \
    IndexOptions, IndexWriter, IndexWriterConfig, DirectoryReader, \
    FieldInfos, MultiFields, MultiTerms, Term
from org.apache.lucene.queryparser.classic import \
    MultiFieldQueryParser, QueryParser
from org.apache.lucene.search import BooleanClause, IndexSearcher, TermQuery
from org.apache.lucene.store import MMapDirectory, SimpleFSDirectory, FSDirectory, NIOFSDirectory


def create_translation_mapping(translation_mappings, all_senses, all_translation_mappings, languages):
    for translation_mapping in translation_mappings:
        tran_split = translation_mapping.split('_')
        if tran_split[0] in all_senses[languages[0]] and tran_split[1] in all_senses[
            languages[1]]:
            all_translation_mappings.append((all_senses[languages[0]][tran_split[0]],
                                             all_senses[languages[1]][tran_split[1]]))

        if tran_split[0] in all_senses[languages[1]] and tran_split[1] in all_senses[
            languages[0]]:
            all_translation_mappings.append((all_senses[languages[0]][tran_split[1]],
                                             all_senses[languages[1]][tran_split[0]]))


def populate_data(path, args):
    name = path.split('/')[-1]
    print(f"Processing {name}")
    all_senses = {}

    all_senses[args.lang1] = {}
    all_senses[args.lang2] = {}

    if args.pivot_lang is not None:
        all_senses[args.pivot_lang] = {}

    all_translation_mappings = []
    if args.pivot_lang is not None:
        all_translation_pivot1_mappings = []
        all_translation_pivot2_mappings = []

    store = SimpleFSDirectory(Paths.get(path))
    dr = DirectoryReader.open(store)
    searcher = IndexSearcher(dr)
    analyzer = StandardAnalyzer()
    query = QueryParser("title", analyzer).parse("*:*")
    topDocs = searcher.search(query, 1000000000)
    for scoreDoc in topDocs.scoreDocs:
        doc = scoreDoc.doc
        language_lemmas = searcher.doc(doc).getValues("LANGUAGE_LEMMA")
        sense_ids = searcher.doc(doc).getValues("ID_SENSE")
        for language_lemma, sense_id in zip(language_lemmas, sense_ids):
            lang = language_lemma[:2]
            lemma = language_lemma[3:]
            if language_lemma[:2] in LANGUAGES_OF_INTEREST:
                all_senses[lang] = {sense_id: lemma}
            if args.pivot_lang is not None and language_lemma[:2] == args.pivot_lang:
                all_senses[args.pivot_lang] = {sense_id: lemma}
        translation_mappings = searcher.doc(doc).getValues("TRANSLATION_MAPPING")
        create_translation_mapping(translation_mappings, all_senses, all_translation_mappings, LANGUAGES_OF_INTEREST)
        if args.pivot_lang is not None:
            create_translation_mapping(translation_mappings, all_senses, all_translation_pivot1_mappings, [args.lang1, args.pivot_lang])
            create_translation_mapping(translation_mappings, all_senses, all_translation_pivot2_mappings, [args.lang2, args.pivot_lang])

    output = open(f'{args.internal_data_path}/{name}.pkl', 'wb')
    pickle.dump(all_translation_mappings, output)
    output.close()
    if args.pivot_lang is not None:
        output = open(f'{args.internal_data_path}/{name}_{args.lang1}-{args.pivot_lang}.pkl', 'wb')
        pickle.dump(all_translation_pivot1_mappings, output)
        output.close()
        output = open(f'{args.internal_data_path}/{name}_{args.lang2}-{args.pivot_lang}.pkl', 'wb')
        pickle.dump(all_translation_pivot2_mappings, output)
        output.close()

LANGUAGES_OF_INTEREST = []


def check_multiple_words(words, c_set):
    for word in words:
        if word not in c_set:
            return False
    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Find words from languages L1 and L2 in same context, output dictionaries and embeddings for those words.')
    parser.add_argument('--input_path', help='Path to language of difference')
    parser.add_argument('--lang1', help='First language')
    parser.add_argument('--lang2', default=None, help='Second language')
    # TODO
    parser.add_argument('--pivot_lang', default=None, help='(Optional) use pivot language for extended dictionaries')
    parser.add_argument('--internal_data_path', default=None, help='Path to folder for internal processing')
    parser.add_argument('--results_path', help='Path to result folder')
    parser.add_argument('--read_directories', action='store_true', help='Read directories when already preprocessed (otherwise only read already processed data)')
    parser.add_argument('--lang1_wordlist_path', default=None, help='Path to lang1 wordlist, to filter incorrect words.')
    parser.add_argument('--lang2_wordlist_path', default=None, help='Path to lang2 wordlist, to filter incorrect words.')
    parser.add_argument('--raw_output', action='store_true',
                        help='Save raw output to result folder')
    args = parser.parse_args()

    LANGUAGES_OF_INTEREST = [args.lang1, args.lang2]

    if args.lang2 is not None:
        if args.read_directories:
            lucene.initVM(vmargs=['-Djava.awt.headless=true'])
            all_directories = [x[0] for x in os.walk(args.input_path)][1:]
            for path in all_directories:
                populate_data(path, args)

        all_data = []
        for filename in os.listdir(args.internal_data_path):
            if filename.endswith(".pkl"):
                file_path = os.path.join(args.internal_data_path, filename)
                pkl_file = open(file_path, 'rb')
                raw_dict = pickle.load(pkl_file)
                pkl_file.close()
                all_data += raw_dict
        sorted_dedup_data = set()
        for el in all_data:
            sorted_dedup_data.add(el)
        sorted_dedup_data = sorted(list(sorted_dedup_data), key=lambda x: x[1])
        sorted_dedup_data = list(sorted_dedup_data)

    lang1_set = set()
    lang1_wl_set = set()
    lang2_wl_set = set()

    with open(args.lang1_wordlist_path, 'r') as read_file:
        for line in read_file:
            lang1_wl_set.add(line[:-1])

    if args.lang2 is None:
        with open(args.input_path, 'r') as read_file:
            for line in read_file:
                words = line[:-1].replace('-', '_').split('_')
                if check_multiple_words(words, lang1_wl_set):
                    lang1_set.add(line)
        res = sorted(list(lang1_set))

        with open(args.results_path, 'w') as write_file:
            for word in res:
                write_file.write(word)

        sys.exit(0)

    with open(args.lang2_wordlist_path, 'r') as read_file:
        for line in read_file:
            lang2_wl_set.add(line[:-1])

    slo_checked_cro_checked_data = []
    for tup in sorted_dedup_data:
        if tup[0] in lang1_wl_set and tup[1] in lang2_wl_set:
            slo_checked_cro_checked_data.append(tup)

    slo_checked_cro_checked_mw_data = []
    for tup in sorted_dedup_data:
        words0 = tup[0].replace('-', '_').split('_')
        words1 = tup[1].replace('-', '_').split('_')
        if check_multiple_words(words0, lang1_wl_set) and check_multiple_words(words1, lang2_wl_set):
            slo_checked_cro_checked_mw_data.append((' '.join(words0), ' '.join(words1)))

    if args.raw_output:
        with open(os.path.join(args.results_path, args.lang1 + '-' + args.lang2 + '_raw_dictionary.txt'), 'w') as write_file:
            for data in all_data:
                write_file.write(data[0] + '\t' + data[1]+'\n')

        with open(os.path.join(args.results_path, args.lang1 + '-' + args.lang2 + '_sorted_dedup_dictionary.txt'), 'w') as write_file:
            for data in sorted_dedup_data:
                write_file.write(data[0] + '\t' + data[1]+'\n')

    with open(os.path.join(args.results_path, args.lang1 + '-' + args.lang2 + '_dictionary.txt'), 'w') as write_file:
        for data in slo_checked_cro_checked_data:
            write_file.write(data[0] + '\t' + data[1]+'\n')

    with open(os.path.join(args.results_path, args.lang1 + '-' + args.lang2 + '_mw_dictionary.txt'), 'w') as write_file:
        for data in slo_checked_cro_checked_mw_data:
            write_file.write(data[0] + '\t' + data[1]+'\n')
