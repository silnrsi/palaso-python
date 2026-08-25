#!/usr/bin/python3
"""
Apply Arabic Mark Transient Reordering Algorithm (AMTRA) to a sequence of characters codes.

AMTRA is described in Unicode Standard Annex #53 (UAX#53) and, as named and described, is
intended to be used in a transient manor during text rendering. However, for testing purposes
it can be helpful to see what the algorithm would do with a given sequence of characters. 

The uax53() function accepts a list of integers representing Unicode Scalar Values and
applies the AMTRA algorithm to any sequences of Arabic marks with the list. The function
returns the resulting now-reordered list of integers.

Caveat: This is not intended as a reference implementation for UAX53, and there may be bugs. 

SYNOPSIS:

    from palaso.unicode.uax53 import uax53
    from palaso.unicode.ucd import get_ucd

    testInput = [0x0628, 0x064E, 0x0654, 0x0651]
    output = uax53(testInput, get_ucd)
    print(' '.join(f'0x{u:04X}' for u in output))

Note that the second argument is the function imported from palaso.unicode.ucd.

If needed, properties for characters in Unicode's character pipeline can be added using
the loadxml function prior to calling uax53:

    from palaso.unicode.ucd import get_ucd, loadxml
    loadxml('additional_ucd.xml')
    ...

See palaso.unicode.ucd for more details on the loadxml interface.

"""

import unicodedata
from collections.abc import Callable

# Set of non-zero combining class values for Arabic script characters
arabMarksCCC = {str(ccc) for ccc in (*range(27, 34), 220, 230)}


def uax53(uids: list[int], get_ucd: Callable[[int, str], str | bool]) -> list[int]:
    # Apply UAX#53 to a list of Unicode Scalar Values expressed as ints

    def reorder(uids: list[int]) -> list[int]:
        # Given a maximal-length subset of non-Starters (assumed to be Arabic marks)
        # apply AMTRA reordering and return resulting list.

        # Step 1: order by ascending ccc
        # (This handles the case that there were pipeline diacritics)
        # sorted() is _stable_ so items of the same key value will retain original order
        myiter = iter(sorted(uids, key=lambda x: int(get_ucd(x, 'ccc'))))

        shaddas = []
        mcm220 = []
        mcm230 = []
        others = []

        try:
            ccc = int(get_ucd(uid := next(myiter), 'ccc'))
            while ccc < 220:
                if ccc == 33:
                    shaddas.append(uid)
                else:
                    others.append(uid)
                ccc = int(get_ucd(uid := next(myiter), 'ccc'))
            while ccc == 220 and get_ucd(uid, 'MCM'):
                mcm220.append(uid)
                ccc = int(get_ucd(uid := next(myiter), 'ccc'))
            while ccc == 220:
                others.append(uid)
                ccc = int(get_ucd(uid := next(myiter), 'ccc'))
            while ccc == 230 and get_ucd(uid, 'MCM'):
                mcm230.append(uid)
                ccc = int(get_ucd(uid := next(myiter), 'ccc'))
            while ccc == 230:
                others.append(uid)
                ccc = int(get_ucd(uid := next(myiter), 'ccc'))
        except StopIteration:
            pass
        result = mcm220 + mcm230 + shaddas + others
        assert len(uids) == len(result), 'Unexpected length difference in uax53.reorder()'
        return result

    output = []
    subseq = []

    # First step: NFD the entire list of uids
    nfd = map(ord, unicodedata.normalize('NFD', "".join(map(chr, uids))))

    # If there were pipeline chars in s, we'll have to reorder diacritics again anyway.
    # So we'll plan to do a further sort of just the diacritics in a minute, but at least
    # we got all the decompositions done.

    for uid in nfd:
        if get_ucd(uid, 'ccc') in arabMarksCCC:
            # We're in a subsequence of arabic marks... accumulate it.
            subseq.append(uid)
        else:
            if len(subseq):
                if len(subseq) > 1:
                    # okay, we need to AMTRA to the accumulated subsequence of marks
                    subseq = reorder(subseq)
                # append to output
                output.extend(subseq)
                # clear subseq
                subseq = []

            # Now process the character which is not an arabic mark
            output.append(uid)

    if len(subseq):
        # One final subsequence of marks to process
        if len(subseq) > 1:
            subseq = reorder(subseq)
        output.extend(subseq)

    # Done!
    return output


if __name__ == '__main__':
    import sys
    import re
    from palaso.unicode.ucd import get_ucd, loadxml
    from palaso.unicode.uax53 import uax53

    if len(sys.argv) > 1:
        loadxml(sys.argv[1])

    testInput = [0x0628, 0x064E, 0x0654, 0x0651]
    print(f""" Apply UAX53 to a sequence of characters identified by their USVs

    Example: 
        desired input: beh fatha hamza shadda
        USV input list:  {' '.join(f'{uid:04X}' for uid in testInput)}
        USV output list: {' '.join(f'{uid:04X}' for uid in uax53(testInput, get_ucd))}
""")

    # Let the user enter USVs:
    try:
        while i := input("USV sequence (blank to stop): "):
            if re.match(r'q?\s*$', i):
                break
            # Convert USVs to ints:
            try:
                iuids = [int(usv, 16) for usv in re.split(r'[,\s]+', i)]
            except ValueError:
                print('Invalid input: must be comma- or space-separated hex numbers')
                continue
            try:
                ouids = uax53(iuids, get_ucd)
                print(' '.join(f'{uid:04X}' for uid in ouids))
            except ValueError as e:
                print(f'Invalid input: {e}')

    except KeyboardInterrupt:
        pass
