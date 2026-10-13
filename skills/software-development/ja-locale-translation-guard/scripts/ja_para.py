#!/usr/bin/env python3
"""Append one paragraph to a markdown file.

Each argument is ONE short sentence; they are joined with no space into a single
paragraph line, then the corruption scan runs. Keeps generation short enough to
stay clean while still producing normal paragraphs.

Usage: ja_para.py <file> "sentence one。" "sentence two。" ...
       ja_para.py <file> --h2 "Heading"
       ja_para.py <file> --h3 "Heading"
       ja_para.py <file> --img "/essay/06-09/IMG_X.jpg"
       ja_para.py <file> --blank
       ja_para.py <file> scan
"""
import sys
from ja_append import scan, report

def main():
    path = sys.argv[1]
    args = sys.argv[2:]
    if args == ['scan']:
        p = scan(path); report(path, p); sys.exit(1 if p else 0)

    out = []
    if args and args[0].startswith('--'):
        kind = args[0][2:]
        rest = args[1:]
        if kind in ('h2', 'h3'):
            out.append('#' * int(kind[1]) + ' ' + rest[0])
        elif kind == 'img':
            out.append('![](' + rest[0] + ')')
        elif kind == 'blank':
            out.append('')
        else:
            raise SystemExit('bad kind ' + kind)
    else:
        out.append(''.join(args))

    with open(path, 'a', encoding='utf-8') as f:
        for line in out:
            f.write('\n' + line)
        f.write('\n')
    p = scan(path)
    report(path, p)
    sys.exit(1 if p else 0)

if __name__ == '__main__':
    main()
