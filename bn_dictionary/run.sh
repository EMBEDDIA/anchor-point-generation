java LanguageWordsObtainer HR "data/hr_bn.txt"
java LanguageWordsObtainer SL "data/sl_bn.txt"
python generate_dictionary_babelnet_lucene.py --input_path "babelnet/BabelNet-4.0.1" --lang1 SL --lang2 HR --results_path "data/internal_data" --internal_data_path "data/internal_data" --lang1_wordlist_path "data/sl.txt" --lang2_wordlist_path "data/hr.txt" --raw_output
java DictionaryCreator SL HR "data/internal_data/sl_bn_checked.txt" "data/internal_data/sl_hr_dict.txt"
python modify_dictionary_babelnet_api.py --input_path "data/internal_data/sl_hr_dict.txt" --lang1 SL --lang2 EN --results_path "data/output/hr-sl.dict" --lang1_wordlist_path "data/sl.txt" --lang2_wordlist_path "data/hr.txt" --reverse_lang