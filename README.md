# Anchor point generation

This repository is split into two parts, part with creation code for anchor points from named entity recognition (NER) task, and part with BabelNet extraction code.

## NER anchor points

To obtain NER anchor points you need to have data in appropriate format. Use the tab separated values (tsv) format, where first column should contain word position in sentence, second actual word, third should be word id (sentence id and word position separated with '.'), and last named entity column. After each sentence there should be an empty line. Example:

```bash
1	The	w33134.1	O
2	diameter	w33134.2	O
3	of	w33134.3	O
4	the	w33134.4	O
5	wheels	w33134.5	O
6	is	w33134.6	O
7	20	w33134.7	O
8	cm	w33134.8	O
9	.	w33134.9	O

1	The	w33135.1	O
2	weight	w33135.2	O
3	of	w33135.3	O
4	the	w33135.4	O
5	stroller	w33135.5	O
6	is	w33135.6	O
7	9.2	w33135.7	O
8	kg	w33135.8	O
9	.	w33135.9	O
```

Afterwards run scripts `paracorpus_align.py` to generate dictionary and `filter_single_word_ners.py` to filter out one word named entities. Examples of this are provided in `ner_dictionary/run.sh`.

## BabelNet anchor points

If you want to obtain dictionary from BabelNet you have to obtain data from https://babelnet.org/ . Afterwards, you need to get Java API code, that they provide on website.

You also have to obtain a wordlist of desired languages, with one word in one line of a file and name them as `data/sl.txt`.

Run `bn_dictionary/run.sh`.

## Other

Other folder contains useful scripts with purpose to prepare data for vecmap alignment over anchor points.

`lemmatizer.py` script lemmatizes text and puts tabular NER text in apropriate format for further processing. `aligning_two_corpuses.py` aligns sentences as instructed in appropriate linking file. These files may then be further processed by other projects, namely https://github.com/EMBEDDIA/vecmap-changes.  