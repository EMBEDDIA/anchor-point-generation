package babelnet;


import it.uniroma1.lcl.babelnet.BabelNet;
import it.uniroma1.lcl.babelnet.BabelSynset;
import it.uniroma1.lcl.jlt.util.Language;

import java.io.File;
import java.io.FileOutputStream;
import java.io.IOException;
import java.nio.charset.Charset;
import java.util.stream.Stream;

public class LanguageWordsObtainer {
	/*
	 * Args:
	 * 0: Language to extract
	 * 1: Output file destination
	 */
    public static void main(String[] args) throws IOException {
    	Language lang = Language.fromISO(args[0]);
    	File outputFile = new File(args[1]);
    	
    	BabelNet bn = BabelNet.getInstance();
    	Stream<BabelSynset> bn_stream = bn.stream();
    	FileOutputStream fos = new FileOutputStream(outputFile);
    	bn_stream.forEach(s -> s.getLemmas(lang).forEach(w -> {
			try {
				String res = w.getLemma() + "\n";
				fos.write(res.getBytes(Charset.forName("UTF-8")));
			} catch (IOException e) {
				e.printStackTrace();
			}
		}));
    	fos.close();
    }
}