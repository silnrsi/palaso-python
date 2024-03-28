#!/usr/bin/python3

import argparse
import csv
import io
import json
import os.path

import fontTools.merge
import fontTools.subset
import fontTools.unicodedata
from fontTools.ttLib import TTFont


def main():
    parser = argparse.ArgumentParser(description='Build an autonym font')
    parser.add_argument('langtags', help='Langtags JSON file')
    parser.add_argument('scriptfont', help='Script2Font CSV file')
    parser.add_argument('noto', help='Noto fonts repo')
    parser.add_argument('fontname', help='Name for autonym font')
    args = parser.parse_args()

    # list of fonts to subset
    font_names = list()
    broken = [
        'Noto Sans Canadian Aboriginal',
        'Noto Sans Ethiopic',
        'Noto Sans Sora Sompeng',
        'Noto Serif Tangut',
        'Noto Sans Thaana'
    ]
    for font_name in read_scriptfont(args.scriptfont):
        if font_name == 'Noto Sans':
            font_names.insert(0, font_name)
        elif font_name in broken:
            pass
        else:
            font_names.append(font_name)

    # subset the fonts
    needed_codepoints = read_langtags(args.langtags)
    subset_fonts = list()
    subset_options = fontTools.subset.Options()
    for font_name in font_names:
        font_path = find_font(font_name)
        font_file = os.path.join(args.noto, font_path)
        if os.path.exists(font_file):
            needed_codepoints, subset_font = subset(needed_codepoints, font_file, subset_options)
            if subset_font:
                subset_fonts.append(subset_font)

    # report what codepoints could not be found
    for missing_codepoint in sorted(needed_codepoints):
        script = fontTools.unicodedata.script(missing_codepoint)
        print(f'missing U+{missing_codepoint:04X} {script}')

    # merge the subseted fonts
    merge_options = fontTools.merge.Options()
    merger = fontTools.merge.Merger(options=merge_options)
    autonym_font = merger.merge(subset_fonts)
    outfile = f'{args.fontname}-Regular.ttf'
    fontTools.subset.save_font(autonym_font, outfile, subset_options)


def read_langtags(filename):
    codepoints = set()
    with open(filename) as langtags_file:
        langtags = json.load(langtags_file)
        for language in langtags:
            if 'localname' in language:
                for char in language['localname']:
                    codepoints.add(ord(char))
            if 'localnames' in language:
                for localname in language['localnames']:
                    for char in localname:
                        codepoints.add(ord(char))
    return codepoints


def read_scriptfont(filename):
    with open(filename, newline='') as scriptfont_file:
        scriptfont = csv.DictReader(scriptfont_file)
        for fonts in scriptfont:
            for style in ['Sans', 'Serif']:
                noto_style = f'Noto {style}'
                if fonts[noto_style]:
                    font_name = fonts[noto_style]
                    yield font_name
                    break


def find_font(noto_name):
    notoname = noto_name.replace(' ', '')
    fontpath = f'fonts/{notoname}/unhinted/ttf/{notoname}-Regular.ttf'
    return fontpath


def subset(needed_codepoints, font_file, options):
    # subset font if the font has needed codepoints
    codepoints_in_font = read_font(font_file)
    codepoints_from_font = needed_codepoints & codepoints_in_font
    if not codepoints_from_font:
        return needed_codepoints, None
    subsetter = fontTools.subset.Subsetter(options=options)
    font = fontTools.subset.load_font(font_file, options)
    subsetter.populate(unicodes=codepoints_from_font)
    subsetter.subset(font)
    subset_font = io.BytesIO()
    fontTools.subset.save_font(font, subset_font, options)
    needed_codepoints = needed_codepoints - codepoints_from_font
    return needed_codepoints, subset_font


def read_font(font_file):
    # load cmap from the font
    font = TTFont(font_file)
    cmap = font.getBestCmap()
    codepoints = set(cmap.keys())
    return codepoints


if __name__ == '__main__':
    main()
