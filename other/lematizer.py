# /media/luka/Portable Disk/Datasets/embeddings_alignment/hr-sl.txt/OpenSubtitles.hr-sl.hr.lemmatized
import argparse
import os

import stanfordnlp


def match_pars_opensubtitles(ali1):
    # matches paragraphs from file ali1 with those from ali2, based on alignfile and outputs them
    # as generator, tab separated. sentences within paragraphs are </s> separated.
    with open(ali1, 'r') as leftpars:
        for line in leftpars:
            lpar = line.strip()
            yield lpar


def match_pars_iob(input):
    with open(input, 'r') as leftpars:
        sentence = []
        sentence_raw = []
        for line in leftpars:
            if len(line) == 1:
                continue
            lpar = line.split()
            if lpar[0] == '1' and sentence:
                yield ' '.join(sentence), sentence_raw
                sentence = []
                sentence_raw = []
            sentence.append(lpar[1])
            sentence_raw.append(lpar)

        yield ' '.join(sentence), sentence_raw


def multipara_corpus_lemmatizer(matchingpars, nlp1, args, input):
    if os.path.exists(input + '.lemmatized'):
        sent_num = 0
        with open(input + '.lemmatized', 'r') as r:
            for _ in r:
                sent_num += 1
    else:
        sent_num = 0
    i = 0
    sentence_count_ok = False
    with open(input + '.unlemmatized', 'a') as w_u:
        with open(input + '.lemmatized', 'a') as w_l:
            for lpar in matchingpars:
                if i < sent_num and not sentence_count_ok:
                    i += 1
                    continue
                else:
                    sentence_count_ok = True
                doc1 = nlp1(lpar[0])
                lem1 = [word.lemma if word.lemma is not None else '_' for sent in doc1.sentences for word in sent.words]
                ulem1 = [word.text if word.text is not None else '_' for sent in doc1.sentences for word in sent.words]
                w_u.write(' '.join(ulem1) + '\n')
                w_l.write(' '.join(lem1) + '\n')
                if args.use_prelemmatized is not None:
                    with open(input + '.lemmatized_iob', 'a') as w_l_i:
                        assert len(lem1) == len(lpar[1]), 'Incorrect length - number of lemmas not equal to num of lines in input file.'
                        for line_i, line in enumerate(lpar[1]):
                            line[1] = lem1[line_i]
                            w_l_i.write('\t'.join(line) + '\n')
                        w_l_i.write('\n')
                if sent_num % 10000 == 0:
                    print('%d sentences processed' % sent_num)
                sent_num += 1


def dict_lemmatizer(text, nlp1):
    doc1 = nlp1(text)
    lem1 = [word.lemma if word.lemma is not None else '_' for sent in doc1.sentences for word in sent.words]
    return ' '.join(lem1)


def read_part(path, nlp1):
    res = []
    with open(path, 'r') as read_file:
        for line in read_file:
            if len(line) == 1:
                continue
            split = line.split('\t')
            res.append((split[0], split[1]))


def main(args):
    parser = argparse.ArgumentParser(
        description='Find words from languages L1 and L2 in same context, output dictionaries and embeddings for those words.')
    parser.add_argument('--input', help='Path to document')
    parser.add_argument('--lang', help='Language of document')
    parser.add_argument('--lang2', default=None, help='Language of document')
    parser.add_argument('--nlpbatch', default=5000, type=int, help='Language of document')
    parser.add_argument('--format', default='openSubtitles', help='Format of processed input file')
    parser.add_argument('--dict_input', action='store_true', help='If format is not multipara_crawl_like')
    # parser.add_argument('--use_prelemmatized', default=None, help='Path to prelematized file not in iob_format')
    parser.add_argument('--use_prelemmatized', action='store_true', help='Whether to save lemmatized file in iob_format')
    args = parser.parse_args(args)

    os.environ["CUDA_VISIBLE_DEVICES"]="0"
    processors = 'tokenize,lemma'
    try:
        nlp1 = stanfordnlp.Pipeline(lang=args.lang, processors=processors, lemma_batch_size=args.nlpbatch, tokenize_batch_size=args.nlpbatch, use_gpu=True, tokenize_pretokenized=True)
        if args.lang2 is not None:
            nlp2 = stanfordnlp.Pipeline(lang=args.lang2, processors=processors, lemma_batch_size=args.nlpbatch, tokenize_batch_size=args.nlpbatch, use_gpu=True, tokenize_pretokenized=True)
    except:
        stanfordnlp.download(args.lang)
        nlp1 = stanfordnlp.Pipeline(lang=args.lang, processors=processors, lemma_batch_size=args.nlpbatch, tokenize_batch_size=args.nlpbatch, use_gpu=True, tokenize_pretokenized=True)
        if args.lang2 is not None:
            nlp2 = stanfordnlp.Pipeline(lang=args.lang2, processors=processors, lemma_batch_size=args.nlpbatch, tokenize_batch_size=args.nlpbatch, use_gpu=True, tokenize_pretokenized=True)

    if args.dict_input:
        with open(args.input, 'r') as read_file:
            with open(args.input + '.lemmatized', 'w') as write_file:
                for line in read_file:
                    split_line = line.split('\t')
                    l1 = dict_lemmatizer(split_line[0], nlp1)
                    l2 = dict_lemmatizer(split_line[1][:-1], nlp2)
                    write_file.write(l1 + '\t' + l2 + '\n')
        dict_lemmatizer(args.input, nlp1)
    else:
        if os.path.isdir(args.input):
            input_files = [os.path.join(args.input, filename) for filename in os.listdir(args.input) if filename.split('.')[-1] == 'tsv' and not os.path.exists(os.path.join(args.input, filename + '.lemmatized'))]
        else:
            input_files = [args.input]
        for input in input_files:
            if args.format == 'openSubtitles':
                matchingpars = match_pars_opensubtitles(input)
            elif args.format == 'iob':
                matchingpars = match_pars_iob(input)
            else:
                raise Exception('Corpus format not supported!')
            multipara_corpus_lemmatizer(matchingpars, nlp1, args, input)


if __name__ == '__main__':
    import sys
    main(sys.argv[1:])
