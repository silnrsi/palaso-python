# -*- coding: utf-8 -*-
# Author:  Tim Eves (tim_eves@sil.org)
# Version: 20090525

import codecs, csv

from csv import QUOTE_MINIMAL, QUOTE_ALL, QUOTE_NONNUMERIC, QUOTE_NONE, \
                Error, Dialect, excel, excel_tab, field_size_limit, \
                register_dialect, get_dialect, list_dialects, \
                unregister_dialect, __version__, __doc__


__all__ = [ "QUOTE_MINIMAL", "QUOTE_ALL", "QUOTE_NONNUMERIC", "QUOTE_NONE",
            "Error", "Dialect", "Sniffer", "excel", "excel_tab", "reader", "writer",
            "register_dialect", "get_dialect", "list_dialects",
            "unregister_dialect", "__version__", "DictReader", "DictWriter" ]


def _utf8_recoder(f,enc):
    return (f if enc in ('utf_8','U8','UTF','utf8') 
              else codecs.EncodedFile(f,'utf_8',enc))

class reader:
    def __init__(self, f, dialect=excel, encoding='utf-8', *args, **kwds):
        self.__reader = csv.reader(_utf8_recoder(f,encoding), dialect, *args, **kwds)
    
    def next(self):
        return tuple(unicode(cell,'utf-8') for cell in self.__reader.next())
    
    def __iter__(self):
        return self
    
    @property
    def dialect(self): return self.__reader.dialect
    
    @property
    def line_num(self): return self.__reader.line_num


class writer:
    def __init__(self, f, dialect=excel, encoding='utf-8', *args, **kwds):
        self.__writer = csv.writer(_utf8_recoder(f,encoding), dialect, *args, **kwds)
    
    def writerow(self,row):
        self.__writer.writerow(cell.encode('utf-8') for cell in row)
    
    def writerows(self,rows):
        self.__writer.writerows([cell.encode('utf-8') for cell in row] for row in rows)
    
    @property
    def dialect(self): return self.__writer.dialect



class DictReader:
    def __init__(self, f, fieldnames=None, restkey=None, restval=None, dialect=excel, encoding='utf-8', *args, **kwds):
        self.__reader=csv.DictReader(_utf8_recoder(f,encoding), dialect=dialect, *args, **kwds)
    
    def __iter__(self): return self
    
    def next(self):
        return dict((unicode(k,'utf-8'),unicode(v,'utf-8')) for k,v in self.__reader.next().iteritems())
    
    @property
    def dialect(self): return self.__reader.dialect
    
    @property
    def line_num(self): return self.__reader.line_num
    
    @property
    def fieldnames(self): return self.__reader.fieldnames


class DictWriter:
    def __init__(self, f, fieldnames, restval='', extrasaction='raise', dialect=excel, encoding='utf-8', *args, **kwds):
        self.__writer=csv.DictWriter(_utf8_recoder(f,encoding), fieldnames, dialect=dialect, *args, **kwds)
    
    @staticmethod
    def __make_row(row):
        return dict((k.encode('utf-8'),v.encode('utf-8')) for k,v in row.iteritems())
    
    def writerow(self,row):
        self.__writer.writerow(self.__make_row(row))
    
    def writerows(self,rows):
        self.__writer.writerows(self.__make_row(row) for row in rows)
    
    @property
    def dialect(self): return self.__writer.dialect


class Sniffer(csv.Sniffer):
    def sniff(self, sample, delimiters=None, encoding='utf-8'):
        """
        Returns a dialect (or None) corresponding to the sample
        """
        csv.Sniffer.sniff(self, sample.decode(encoding).encode('utf-8') if encoding != 'utf-8' else sample)
    
    def has_header(self, sample, encoding='utf-8'):
        csv.Sniffer.has_header(self, sample.decode(encoding).encode('utf-8') if encoding != 'utf-8' else sample)

