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
    parser.add_argument('notocjk', help='Noto CJK fonts repo')
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
    broken = []
    for font_name in read_scriptfont(args.scriptfont):
        if font_name in ('Noto Sans', 'Noto Sans SC'):
            font_names.insert(0, font_name)
        elif font_name in broken:
            pass
        else:
            font_names.append(font_name)

    needed_codepoints = read_langtags(args.langtags)

    # subset the fonts
    needed_codepoints = make_font(needed_codepoints, font_names, args.noto, args.fontname)
    needed_codepoints = make_font(needed_codepoints, font_names, args.notocjk, args.fontname, True)


def make_font(needed_codepoints, font_names, noto_repo, fontname, CJK=False):

    subset_fonts = dict()
    subset_options = fontTools.subset.Options()
    for font_name in font_names:
        script_name = font_name.split(' ')[-1]
        font_path = find_font(font_name, script_name, CJK)
        font_file = os.path.join(noto_repo, font_path)
        if os.path.exists(font_file):
            needed_codepoints, subset_font = subset(needed_codepoints, font_file, subset_options)
            if subset_font:
                extension = os.path.splitext(font_file)[1]
                subset_fonts[script_name] = subset_font

    # report what codepoints could not be found
    for missing_codepoint in sorted(needed_codepoints):
        script = fontTools.unicodedata.script(missing_codepoint)
        print(f'missing U+{missing_codepoint:04X} {script}')

    # output the subseted fonts
    if CJK:
        for script_code, subset_font in subset_fonts.items():
            outfile = f'{fontname}{script_code}-Regular{extension}'
            fontTools.subset.save_font(subset_font, outfile, subset_options)
    else:
        subset_fontfiles = list()
        for script_code, subset_font in subset_fonts.items():
            subset_fontfile = io.BytesIO()
            fontTools.subset.save_font(subset_font, subset_fontfile, subset_options)
            subset_fontfiles.append(subset_fontfile)
        merge_options = fontTools.merge.Options(drop_tables=["vmtx", "vhea", "MATH"])
        merger = fontTools.merge.Merger(options=merge_options)
        autonym_font = merger.merge(subset_fontfiles)
        outfile = f'{fontname}-Regular{extension}'
        fontTools.subset.save_font(autonym_font, outfile, subset_options)

    return needed_codepoints


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


def find_font(noto_name, script_name, CJK=False):
    notoname = noto_name.replace(' ', '')
    if CJK:
        return f'Sans/SubsetOTF/{script_name}/{notoname}-Regular.otf'
    else:
        return f'fonts/{notoname}/unhinted/ttf/{notoname}-Regular.ttf'


def subset(needed_codepoints, font_file, options):
    # subset font if the font has needed codepoints
    codepoints_in_font = read_font(font_file)
    codepoints_from_font = needed_codepoints & codepoints_in_font
    if not codepoints_from_font:
        return needed_codepoints, None
    subsetter = fontTools.subset.Subsetter(options=options)
    subset_font = fontTools.subset.load_font(font_file, options)
    subsetter.populate(unicodes=codepoints_from_font)
    subsetter.subset(subset_font)
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
