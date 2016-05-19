#!/usr/bin/env python
#
# rank_terms.py - rank index terms by frequency

import sys
import xapian

from operator import itemgetter

if __name__ == '__main__':
    if "-h" in sys.argv or not len(sys.argv) == 4:
        print "\nUsage: rank_terms.py INDEX TERMS_FILE PREFIX\n"
    else:
        try:
            index = xapian.Database(sys.argv[1])
        except:
            print "Could no open xapian index at %s" % sys.argv[1]
        try:
            with open(sys.argv[2]) as terms_file:
                terms_list = [line.strip() for line in terms_file]
                print terms_list
                frequencies = {}
                for term in terms_list:
                    frequencies[term] = index.get_termfreq(sys.argv[3] + term)
            sorted_freqs = sorted(frequencies.items(), key=itemgetter(1))
        except:
            print "Could not extract terms list from %s" % sys.argv[2]
        for term, freq in sorted_freqs:
            print term, str(freq)
