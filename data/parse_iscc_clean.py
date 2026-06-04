#!/usr/bin/env python3
"""
parse_iscc_clean.py
Second and third pass cleaning of iscc_nbs_dictionary.csv.

Produced with Claude Sonnet 4.6 (claude-sonnet-4-6), June 2026.
Part of the DD4 pilot study: Measuring colour for dress and archive specialists.
"""

import re
import csv
from pathlib import Path

INPUT  = Path('iscc_nbs_dictionary_firstpass.csv')   # output of parse_iscc_final2.py
OUTPUT = Path('iscc_nbs_dictionary.csv')

# ---------------------------------------------------------------------------
# Second pass: discard entries containing OCR garbage and unstripped source
# reference codes that survived the first pass.
#
# Targets:
#   - 4+ digit numbers (Plochere catalogue numbers, Maerz & Paul grid refs
#     where digit sequence ran together: e.g. "1110", "2110")
#   - Roman numeral source refs: e.g. "XXVII 3 #/ f"
#   - OCR symbol substitutions: $  #  /  \  »  ¥  £  ¢  *  !  @  ^  ~  `
# ---------------------------------------------------------------------------
TRUE_NOISE_RE = re.compile(
    r'\d{4,}'                           # 4+ digit run
    r'|[IVX]{3,}\s*[\d\w#/\\\'\"*$!]'  # Roman numeral + ref token
    r'|[$#/\\»¥£¢*!@^~`]'              # OCR symbol garbage
    r'|\d+\}\$|\d+\*'                   # "7}$", "7*" specific OCR failures
    r'|\bMUP\d|\bPSP\d'                # Plastic standard codes
)

# ---------------------------------------------------------------------------
# Third pass: strip trailing Taylor, Knoche & Granville modifier suffixes.
#
# Taylor's system appends lightness/chroma qualifiers to colour names:
#   m  = medium chroma
#   g  = greyed (reduced chroma)
#   gm = greyed medium
#
# These are source-system notation, not part of the colour name as a rater
# would use it. "Baby Pink m" and "Baby Pink g" both collapse to "Baby Pink"
# and map to the same ISCC-NBS block; no block assignment information is lost.
#
# Entries where the suffix was OCR-rendered as symbol garbage
# (e.g. "Tomato Red m..6^ pc") are caught and discarded by the second pass.
# ---------------------------------------------------------------------------
TAYLOR_SUFFIX_RE = re.compile(r'\s+[gm]{1,2}\s*$')
FILL_RE          = re.compile(r'[\s._\-]+$')


def clean_taylor(name: str) -> str:
    name = TAYLOR_SUFFIX_RE.sub('', name).strip()
    name = FILL_RE.sub('', name)
    return name


def main():
    entries = list(csv.DictReader(open(INPUT, encoding='utf-8')))

    results   = []
    discarded = []

    for e in entries:
        name = e['name']

        # Second pass: discard true noise
        if TRUE_NOISE_RE.search(name):
            discarded.append(e)
            continue

        # Third pass: strip Taylor suffix
        cleaned = clean_taylor(name)

        if len(cleaned) >= 2:
            results.append({
                'name':          cleaned,
                'serial_number': e['serial_number'],
                'block_name':    e['block_name'],
            })

    with open(OUTPUT, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['name', 'serial_number', 'block_name'])
        writer.writeheader()
        writer.writerows(results)

    unique = len(set(e['name'].lower() for e in results))
    print(f"Input entries:    {len(entries)}")
    print(f"Discarded:        {len(discarded)}")
    print(f"Output entries:   {len(results)}")
    print(f"Unique names:     {unique}")
    print(f"Written to:       {OUTPUT}")


if __name__ == '__main__':
    main()
