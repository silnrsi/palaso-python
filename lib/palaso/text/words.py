#!/usr/bin/python

from itertools import groupby, ifilter, imap
import unicodedata, operator

word_cat = set(['Lu','Ll','Lt','Lm','Lo','Mn','Mc','Me','Pd','Cs','Co','Cn'])
'''Define a word character as being one of:
     Letter
     Mark
     Punctuation,Dash  
     Other,{Surrogate,Private Use,Not Assigned}'''


nonword_cat = set(['Nd','Nl','No','Pc','Ps','Pe','Pi','Pf','Po','Sm','Sc','Sk','So','Zs','Zl','Zp','Cc','Cf'])
'''Define a word character as not being any of:
         Number
         Punctuation (all except Dash)
         Symbol
         Separator
         Other,{Control,Format}'''

def word_char(char, words, nonwords, category=word_cat, __ucd_category=unicodedata.category):
    '''Test character for membership in word_cat set where characters in 
       opts.word are considered to be Letter,Other and characters in 
       opts.nonword are considered to be Punctuation,Other.'''
    cat = (char in words and 'Lo' 
        or char in nonwords and 'Po' 
        or __ucd_category(char))
    return cat in category


def words(text, words=[], nonwords=[], category=word_cat):
    '''Split a text string into words.
       Words are defined as groups of characters that satisfy word_char'''
    joiner = unicode().join
    return imap(joiner, 
                imap(operator.itemgetter(1),
                     ifilter(operator.itemgetter(0),
                             groupby(text, lambda x: word_char(x, words, nonwords, category)))))


