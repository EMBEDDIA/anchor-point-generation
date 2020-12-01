package babelnet;

import it.uniroma1.lcl.babelnet.BabelNet;
import it.uniroma1.lcl.babelnet.BabelNetQuery;
import it.uniroma1.lcl.babelnet.BabelSense;
import it.uniroma1.lcl.babelnet.BabelSynset;
import it.uniroma1.lcl.jlt.util.Language;

import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.IOException;
import java.nio.charset.Charset;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.LinkedList;
import java.util.List;
import java.util.Optional;
import java.util.Scanner;
import java.util.stream.Stream;

public class DictionaryCreator {
	/*
	 * Args:
	 * 0: Language from which to translate
	 * 1: Language to which we translate
	 * 2: Input file (wordlist with words in lang_from) destination
	 * 3: Output file destination
	 */
	private static List<String> getWordTranslation(String keyword, Language lang_from, Language lang_to, BabelNet bn, FileOutputStream fos) {
		List<BabelSense> translations_bs = new ArrayList<BabelSense>();
		BabelNetQuery query = new BabelNetQuery.Builder(keyword)
    			.from(lang_from)
    			.to(Arrays.asList(lang_to))
    			.build();
        for (BabelSynset synset : bn.getSynsets(query)) {
            List<BabelSense> senses = synset.getSenses();
            translations_bs.addAll(senses);
        }
        
        List<String> translations = new ArrayList<String>();
        for (BabelSense sense : translations_bs) {
        	translations.add(sense.getFullLemma());
        }
        
		for (String translation : translations) {
			try {
				String res = keyword + "\t" + translation + "\n";
				fos.write(res.getBytes(Charset.forName("UTF-8")));
			} catch (IOException e) {
				e.printStackTrace();
			}
        }
        		
		return translations;
	}
	
	
    public static void main(String[] args) throws IOException {
    	Language lang_from = Language.fromISO(args[0]);
    	Language lang_to = Language.fromISO(args[1]);
    	File input_file = new File(args[2]);
    	File output_file = new File(args[3]);

    	BabelNet bn = BabelNet.getInstance();

    	FileOutputStream fos = new FileOutputStream(output_file);
    	
    	
    	FileInputStream fis = new FileInputStream(input_file);
    	Scanner sc = new Scanner(fis);

    	int i = 0;
    	while (sc.hasNext()) {
    		List<String> a = getWordTranslation(sc.nextLine(), lang_from, lang_to, bn, fos);
    		i++;
    		if (i % 1000 == 0)
    			System.out.println(i);
    	}
    	
        
    	fis.close();
    	fos.close();
    	
    	System.out.println("DONE");
    }
}
