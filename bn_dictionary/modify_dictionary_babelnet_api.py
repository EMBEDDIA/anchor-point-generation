import argparse
import pickle

import sys





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


def find_language_treshold(lang2_dict):
    max_occ = 1
    for lang2_v, occurences in lang2_dict.items():
        if occurences > max_occ:
            max_occ = occurences

    return max_occ



if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Find words from languages L1 and L2 in same context, output dictionaries and embeddings for those words.')
    parser.add_argument('--input_path', help='Path to language of difference')
    parser.add_argument('--lang1', help='First language')
    parser.add_argument('--lang2', default=None, help='Second language')
    parser.add_argument('--results_path', help='Path to result folder')
    parser.add_argument('--lang1_wordlist_path', default=None, help='Path to lang1 wordlist, to filter incorrect words.')
    parser.add_argument('--lang2_wordlist_path', default=None, help='Path to lang2 wordlist, to filter incorrect words.')
    parser.add_argument('--filter_wordlist', action='store_true', help='Filters wordlist to words that are in dictionary')
    parser.add_argument('--reverse_lang', action='store_true', help='Filters wordlist to words that are in dictionary')
    args = parser.parse_args()

    LANGUAGES_OF_INTEREST = [args.lang1, args.lang2]

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

    keyword_dict = {}
    with open(args.input_path, 'r') as read_file:
        for line in read_file:
            con_split = line.split('\t')
            word_lang1 = con_split[0]
            word_lang2 = con_split[1][:-1]
            word_lang1_split = word_lang1.replace('-', '_').split('_')
            word_lang2_split = word_lang2.replace('-', '_').split('_')
            if check_multiple_words(word_lang1_split, lang1_wl_set) and check_multiple_words(word_lang2_split, lang2_wl_set):
                if word_lang1 not in keyword_dict:
                    keyword_dict[word_lang1] = {}
                if word_lang2 in keyword_dict[word_lang1]:
                    keyword_dict[word_lang1][word_lang2] += 1
                else:
                    keyword_dict[word_lang1][word_lang2] = 1

    new_keyword_dict = {}
    if args.reverse_lang:
        for lang1_v, v in keyword_dict.items():
            for lang2_v, lang2_v_num in v.items():
                if lang2_v not in new_keyword_dict:
                    new_keyword_dict[lang2_v] = {}
                if lang1_v not in new_keyword_dict[lang2_v]:
                    new_keyword_dict[lang2_v][lang1_v] = lang2_v_num
                else:
                    new_keyword_dict[lang2_v][lang1_v] += lang2_v_num
        keyword_dict = new_keyword_dict

    unfiltered_dict = []
    filtered_dict = []
    for lang1_v, lang2_dict in keyword_dict.items():
        threshold = find_language_treshold(lang2_dict)
        for lang2_v, occurences in lang2_dict.items():
            unfiltered_dict.append((lang1_v, lang2_v))
            if threshold > 1 and len(lang2_dict) > 1 and occurences == 1:
                continue
            filtered_dict.append((lang1_v, lang2_v))

    unfiltered_dict = sorted(unfiltered_dict, key=lambda x: x[0])
    filtered_dict = sorted(filtered_dict, key=lambda x: x[0])
    with open(args.results_path + '.unfiltered', 'w') as write_file:
        for w1, w2 in unfiltered_dict:
            write_file.write(w1 + '\t' + w2 + '\n')

    with open(args.results_path + '.split_words', 'w') as write_file:
        for w1, w2 in filtered_dict:
            write_file.write(w1 + '\t' + w2 + '\n')

    with open(args.results_path, 'w') as write_file:
        for w1, w2 in filtered_dict:
            if '-' not in w1 and '_' not in w1 and '-' not in w2 and '_' not in w2:
                write_file.write(w1 + '\t' + w2 + '\n')
