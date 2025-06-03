#!/usr/bin/python3

import uharfbuzz as uhb


def shape(text, script=None, direction=None):
    blob = uhb.Blob.from_file_path('Harmattan-Regular.ttf')
    face = uhb.Face(blob)
    font = uhb.Font(face)

    buf = uhb.Buffer()
    buf.add_str(text)
    escaped_text = text.encode('unicode_escape')
    print(f'text: {escaped_text}')
    if script is None or direction is None:
        buf.guess_segment_properties()
    else:
        buf.script = script
        buf.direction = direction
    print(f'script: {buf.script} direction: {buf.direction}')

    features = {}
    uhb.shape(font, buf, features)

    infos = buf.glyph_infos
    positions = buf.glyph_positions

    for info, pos in zip(infos, positions):
        gid = info.codepoint
        glyph_name = font.glyph_to_string(gid)
        cluster = info.cluster
        x_advance = pos.x_advance
        print(f"{glyph_name}={cluster}+{x_advance}")
    print()


texts = [
    '\u0628\u0644\u0645',
    '\u06f1\u06f2\u06f3',
    'Blm',
    '123',
]

bookends = (False, True)

for text in texts:
    for bookend in bookends:
        if bookend:
            text = '(' + text + ']'
        shape(text)

shape(texts[0], script='Arab', direction='ltr')
shape(texts[2], script='Arab', direction='rtl')
