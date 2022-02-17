#!/usr/bin/env python3
'''
Count the words in a USFM file skipping punctuation and non-publication
markers updating a master concordance CSV file with any new references
to existing words and append any words not already found in it to it's
end.
'''
__version__ = '0.1'
__date__ = '29 October 2009'
__author__ = 'Tim Eves <tim_eves@sil.org>'
__credits__ = '''
Dennis Drescher for having done something very similar and showing how it
can be done.
'''

from argparse import ArgumentParser
from functools import reduce
from itertools import chain, groupby, starmap
from palaso.sfm import usfm, style
from pathlib import Path
from typing import (
    Callable,
    Iterable,
    Iterator,
    MutableMapping,
    Sequence,
    Set,
    Union,
    cast)
import csv
import palaso.sfm as sfm
import collections
import warnings
import shutil
import sys
import tempfile
import unicodedata


class References(Set[str]):
    '''Represent a set of biblical references.
       This class is really a typed parser and pretty printer for a set
       of strings.'''
    def __init__(self, sequence: Union[Iterable[str], str] = []) -> None:
        if isinstance(sequence, str):
            sequence = sequence.split(', ')
        super().__init__(filter(None, (r.strip() for r in sequence)))

    def __str__(self) -> str:
        return ', '.join(sorted(self))


Concordance = MutableMapping[str, References]


word_cat: set = {
    'Lu', 'Ll', 'Lt', 'Lm', 'Lo',
    'Mn', 'Mc', 'Me',
    'Pd',
    'Cs', 'Co', 'Cn'
}
'''Define a word character as being one of:
     Letter
     Mark
     Punctuation, Dash
     Other, {Surrogate, Private Use, Not Assigned}'''


nonword_cat: set = {
    'Nd', 'Nl', 'No',
    'Pc', 'Ps', 'Pe', 'Pi', 'Pf', 'Po',
    'Sm', 'Sc', 'Sk', 'So',
    'Zs', 'Zl', 'Zp',
    'Cc', 'Cf'
}
'''Define a word character as not being any of:
         Number
         Punctuation (all except Dash)
         Symbol
         Separator
         Other, {Control, Format}'''


def word_char(char: str) -> bool:
    '''Test character for membership in word_cat set where characters in
       opts.word are considered to be Letter, Other and characters in
       opts.nonword are considered to be Punctuation, Other.'''
    cat = (char in args.word and 'Lo'
           or char in args.nonword and 'Po'
           or unicodedata.category(char))
    return cat in word_cat


def words(text: str) -> Iterator[str]:
    '''Split a text string into words.
       Words are defined as groups of characters that satisfy word_char'''
    return (''.join(g[1]) for g in groupby(text, word_char) if g[0])


def _flatten(doc: Iterable[sfm.Element]) -> Sequence[sfm.Text]:
    def _t(e, ts):
        t, *_ = e.split('|')
        ts.append(t)
        return ts

    return sfm.sreduce(lambda e, ts, _: ts,
                       _t,
                       doc, [])


def concordance(refs: Concordance, source_path: Path) -> Concordance:
    if args.verbose:
        sys.stdout.write(f'processing file: {str(source_path)!r}\n')
    try:
        with source_path.open('r', encoding='utf_8_sig') as source:
            doc = sfm.sfilter(
                    sfm.text_properties('publishable', 'vernacular'),
                    usfm.decorate_references(
                        usfm.parser(source,
                                    stylesheet=args.stylesheet,
                                    error_level=args.error_level)))
    except SyntaxError as err:
        sys.stderr.write(f'{parser.prog}: failed to parse USFM: {err!s}\n')
        return refs

    for txt in _flatten(doc):
        for word in words(txt):
            assert '\n' not in word, 'carriage return in word'
            refs[word].add(f'{txt.pos.book} {txt.pos.chapter}:{txt.pos.verse}')
    return refs


Row = MutableMapping[str, Union[str, References]]


def update_row(wordrefs: Concordance) -> Callable[[int, Row], Row]:
    wordlog = {}

    def _g(ln: int, row: Row) -> Row:
        word = cast(str, row['Word'])
        if word in wordlog:
            raise ValueError(f'duplicates: Word {word.encode("utf-8")!r}'
                             f' at row {wordlog[word]+2} is repeated'
                             f' at row {ln+2} of master file')
        wordlog[word] = ln
        try:
            newrefs = wordrefs.pop(word)
        except KeyError:
            if args.unused_warning:
                sys.stderr.write(
                    f'{parser.prog}: CSV merge warning:'
                    f' possible unused word {word.encode("utf_8")!r}'
                    f' at row {ln+2} of master file\n')
            newrefs = References()
        oldrefs = References(row['References'])
        if newrefs - oldrefs:
            row['References'] = References(oldrefs | newrefs)
        return row
    return _g


def merge_master_file_with_book(infile, outfile, refs):
    try:
        infile.seek(0)
        outfile.seek(0)
        reader = csv.DictReader(infile)
        fieldnames = reader.fieldnames or ['Word', 'References']
        writer = csv.DictWriter(outfile, fieldnames)

        # write out the header row
        writer.writerow(dict(zip(fieldnames, fieldnames)))
        # write out an updated list
        writer.writerows(starmap(update_row(refs), enumerate(iter(reader))))
        # write out any new words
        writer.writerows({'Word': w, 'References': r}
                         for (w, r) in refs.items())

        infile.flush()
        outfile.flush()
    except ValueError as err:
        sys.stderr.write(f'{parser.prog}: CSV parse error: {err!s}\n')
        sys.exit(3)


def characterset(chars: str) -> set[str]:
    return set(chars.encode('ascii').decode('unicode_escape'))


def merged_stylesheet(path):
    stylesheet = usfm.default_stylesheet.copy()
    stylesheet.update(style.parse(Path(path).expanduser().open('r')))
    return stylesheet


if __name__ == '__main__':
    parser = ArgumentParser(description=__doc__)
    parser.add_argument(
        "sfms", metavar="<SFM FILE>", type=str, nargs='+',
        help='SFM file(s) to extract words from.')
    parser.add_argument(
        "db_path", metavar="<MASTER CSV FILE>",
        type=Path,
        help="Path to the master CSV database.")
    parser.add_argument("-v", "--verbose", action='store_true', default=False,
                        help='Print out statistics and progress info')
    parser.add_argument(
        "--no-warnings", action='store_false', dest='warnings',
        default=True,
        help='Silence syntax warnings discovered during SFM parsing')
    parser.add_argument(
        "-u", "--unused-warning", action='store_true',
        default=False,
        help='Print out warnings when possibly unsused words are found.')
    parser.add_argument(
        "-s", "--strict", action='store_const', dest='error_level',
        const=usfm.ErrorLevel.Marker,
        default=usfm.ErrorLevel.Content,
        help='Turn on strict parsing mode. Markers not in the stylesheet or'
             ' private name space will cause an error')
    parser.add_argument(
        "-l", "--loose", action='store_const', dest='error_level',
        const=usfm.ErrorLevel.Unrecoverable,
        default=usfm.ErrorLevel.Content,
        help='Turn on loose parsing mode. Nothing short of orphan markers or'
             ' unterminated inlines will halt the parser.')
    parser.add_argument(
        "-S", "--stylesheet", action='store', type=merged_stylesheet,
        metavar='PATH',
        default=usfm.default_stylesheet,
        help='User stylesheet to add/override marker definitions to the'
             ' default USFM stylesheet')
    charset = parser.add_argument_group(
        'Word definition',
        'By default the Unicode category type is used to decide what'
        ' characters are or are not word forming. The options below allow you'
        ' to override this for sets of characters. The default classifier'
        ' considers Unicode categories: all Letters and Marks,'
        ' Punctuation-Dash (for hyphenated words and non-break hyphens) and'
        ' Surrogate, Private-Use and Non-Assinged to be word forming.'
        '  WARNING: It is an error for the set of word forming characters to'
        ' intersect with the set of non-word characters.')
    charset.add_argument(
        "-W", "--word", action='store', type=characterset,
        metavar='WORD', default=set(),
        help='Extra word forming characters. Unicode codepoints may be'
             ' escaped \\uXXXX')
    charset.add_argument(
        "-n", "--nonword", action='store', type=characterset,
        metavar='NONWORD', default=set(),
        help='Extra non-word characters. Unicode codepoints may be'
             ' escaped \\uXXXX')

    args = parser.parse_args()
    args.sfms = chain.from_iterable(Path('.').glob(pat) for pat in args.sfms)

    if args.word & args.nonword:
        intersection = args.word & args.nonword
        sys.stderr.write(
            f'{parser.prog}: overlapping word/non-word characters'
            f' {"".join(intersection).encode("unicode_escape")!r}\n')
        sys.exit(1)

    try:
        with warnings.catch_warnings():
            warnings.simplefilter(
                "always" if args.warnings else "ignore",
                SyntaxWarning)
            words_refs = reduce(
                concordance,
                args.sfms,
                collections.defaultdict(References))

        # Open the master file if it exists and a temp output file.
        # copying metadata to the output file.
        with args.db_path.open('a+t',
                               newline='',
                               encoding='utf_8_sig') as db_src, \
            tempfile.NamedTemporaryFile("w+t",
                                        newline='',
                                        encoding="utf_8_sig") as db_new:
            # merge in the word referneces into the new master.
            prev_num_words = args.verbose and len(words_refs)
            prev_num_refs = args.verbose and sum(map(len, words_refs.values()))
            merge_master_file_with_book(db_src, db_new, words_refs)
            # Replace the original with the new version.
            # We need to use this verbose way rather than shutil.copy2 because
            #  Windows will not allow the NamedTemporaryFile object to be
            #  opened a second time and closing it deletes the temporary.
            db_new.seek(0)
            db_src.seek(0)
            db_src.truncate()
            shutil.copyfileobj(db_new, db_src)
    except IOError as err:
        sys.stderr.write(f'{parser.prog!s}: IO error: {err!s}\n')
        sys.exit(2)

    if args.verbose:
        num_words = len(words_refs)
        num_refs = sum(map(len, words_refs.values()))
        sys.stdout.write(
            f'{prev_num_refs - num_refs} references to'
            f' {prev_num_words - num_words} existing words updated\n'
            f'{num_refs} references to {num_words} new words added\n')
