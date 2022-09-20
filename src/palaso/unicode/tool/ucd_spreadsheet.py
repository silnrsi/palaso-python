#!/usr/bin/python3

"""ucd_spreadsheet

To create an updated spreadsheet for new versions of Unicode, run

./ucd_spreadsheet -a PropertyAliases.txt ucd.nounihan.flat.zip ucd-14.0.0.csv

Then with LibreOffice Calc, do the following:

- Import CSV file, with following columns as Text
- USV
- Decomposition Mapping
- Numeric Value
- Bidi Mirroring Glyph
- Uppercase Mapping
- Lowercase Mapping
- Titlecase Mapping

- Left justify all columns headers
- Left justify age column
- Auto filter headings
- Freeze columns (USV, Glyph, and Name) and row (headings)
- Change font to Arial
- Change language to US English
"""

from palaso.unicode.ucd import UCD
import csv
import sys
import argparse


def main():
    parser = argparse.ArgumentParser(description='Create CSV of Unicode data')
    parser.add_argument('-a', '--alias', help='List of header names')
    parser.add_argument('ucd', help='UCD XML file to get (beta) data from')
    parser.add_argument('csv', help='Spreadsheet to create')
    args = parser.parse_args()

    fields = [
        'gc',
        'ccc',
        'bc',
        'dt',
        'dm',
        'nv',
        'Bidi_M',
        'bmg',
        'uc',
        'lc',
        'tc',
        'sc',
        'scx',
        'InSC',
        'InPC',
        'jt',
        'jg',
        'CE',
        'Comp_Ex',
        'lb',
        'age',
        'blk',
        ]

    ucd = UCD(localfile=args.ucd)

    header_names = dict()
    if args.alias:
        read_header_names(args.alias, header_names)

    header = list()
    header.append('USV')
    header.append('Glyph')
    header.append('Name')
    for field in fields:
        header_name = header_names.get(field, field)
        header_words = header_name.split(' ')
        header_string = '\n'.join(header_words)
        header.append(header_string)

    with open(args.csv, 'w', newline='') as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(header)
        write_data(writer, ucd, fields)


def read_header_names(alias_filename, names):
    with open(alias_filename) as alias_file:
        for line in alias_file:
            # Ignore comments
            line = line.partition('#')[0]
            line = line.strip()

            # Ignore blank lines
            if line == '':
                continue

            # Parse names
            alias = line.split(';')
            short = alias[0].strip()
            long = alias[1].strip()
            names[short] = long.replace('_', ' ')


def write_data(writer, ucd, fields):
    for codepoint in range(sys.maxunicode-1):
        # Get the character name if the character exists
        try:
            name = ucd.get(codepoint, 'na')
        except KeyError:
            continue

        # Omit algorithmically derived CJK names
        if 'CJK UNIFIED IDEOGRAPH-' in name:
            continue

        # Omit PUA characters
        script = ucd.get(codepoint, 'sc')
        if script == 'Zzzz':
            continue

        # Record data obtained so far
        row = list()
        row.append(f'{codepoint:04X}')
        char = '  ' + chr(codepoint) + ' '
        # Some format or control characters should not be
        # actually present in the spreadsheet. This includes
        # the control characters in ASCII and
        # LINE SEPARATOR and PARAGRAPH SEPARATOR
        if codepoint < 0x20 or 0x2028 <= codepoint <= 0x2029:
            char = ''
        row.append(char)
        row.append(name)

        script_names = {
            'Zyyy': 'Common',
            'Zinh': 'Inherited'
        }
        # Get all other needed character properties
        for field in fields:
            data = ucd.get(codepoint, field)
            if field == 'dt':
                if data == 'none':
                    data = ''
            if field in ('dm', 'uc', 'lc', 'tc', 'bmg'):
                # Some fields returns the actual characters,
                # for the spreadsheet, we want to display the USV
                mapping = list()
                for char in data:
                    usv = ord(char)
                    mapping.append(f'{usv:04X}')
                data = ' '.join(mapping)
            if field == 'nv':
                if data == 'NaN':
                    data = ''
            if field == 'scx':
                if data == script:
                    data = ''
            if field in ('sc', 'scx'):
                data = script_names.get(data, data)
            row.append(data)

        # Write data to CSV file
        writer.writerow(row)


if __name__ == '__main__':
    main()
