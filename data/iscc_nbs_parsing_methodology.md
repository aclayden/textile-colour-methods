# ISCC-NBS Dictionary: Source, Transformation, and Parsing Methodology

**Prepared for:** DD4 pilot study — *Measuring colour for dress and archive specialists*  
**Artefact produced:** `iscc_nbs_dictionary.csv`  
**Date:** June 2026

---

## 1. Source document

The lookup table was derived from:

> Kelly, Kenneth L. and Deane B. Judd. *The ISCC-NBS Method of Designating Colors and a Dictionary of Color Names*. National Bureau of Standards Circular 553. Washington, DC: U.S. Government Printing Office, 1955.

A digitised copy is freely available via Internet Archive at `https://archive.org/details/u.-s.-department-of-commerce-pdf-a`. The plain-text OCR layer (`U.S._Department_of_CommercePDF-A_djvu.txt`) was used as the basis for parsing. This file is a public domain U.S. government publication.

The 1955 Circular contains two major sections relevant to this work:

- **Section 14** (*Synonymous and Near-Synonymous Color Names With Their Sample Identifications*): organised by ISCC-NBS block number (1–267), listing under each block all colour names from contributing sources that map to it. This is the section parsed.
- **Section 15** (*Dictionary of Color Names*): an alphabetical index of the same ~7,500 names with their ISCC-NBS designations. Section 15 was assessed but not used as the primary parsing source (see §3 below).

---

## 2. The ISCC-NBS system

The ISCC-NBS system divides colour space into 267 named blocks, each identified by a plain-English descriptor (e.g. "254. VIVID PURPLISH RED") and anchored to a Munsell centroid. Block descriptors are composed systematically from 12 basic hue terms and a fixed set of lightness/chroma modifiers. The blocks are non-uniform in perceptual size and were designed for human interpretation rather than computational precision; Munsell centroid values, which can be converted to CIELAB, provide the quantitative grounding.

The dictionary component of Circular 553 maps approximately 7,500 colour names drawn from nine contributing source vocabularies — including the Textile Color Card Association and the American Association of Textile Chemists and Colorists — onto these 267 blocks. It was explicitly designed to bridge vernacular, trade, and scientific colour vocabularies, which is why it is appropriate as the lookup layer in this pipeline.

---

## 3. Parsing strategy: why Section 14 rather than Section 15

Both sections contain equivalent information but are organised differently:

- Section 14 is organised **block-first**: each block header (e.g. `254. VIVID PURPLISH RED`) is followed by synonym entries listed under source subheadings.
- Section 15 is organised **name-first**: alphabetical entries each bearing a source code and ISCC-NBS designation.

Section 15 was initially assessed for parsing. However, examination of the OCR output revealed that the djvu text layer reproduces the printed three-column layout (colour name | source | ISCC-NBS designation) as column-batched text rather than row-sequential text: within each page spread, the OCR reads all names in the left column first, then all source codes, then all designations. This produces batches of names followed by batches of sources followed by batches of block codes, separated by repeated column headers. The batching is inconsistent across page spreads and incompatible with a sequential row parser without significant additional structural inference.

Section 14, by contrast, has a consistent and machine-readable structure:

```
N. BLOCK NAME
Source subheading
Colour name . source_reference
Colour name . source_reference
...
N+1. BLOCK NAME
...
```

The source reference at the end of each entry is the contributing source's own internal code (e.g. a Maerz & Paul grid reference, a Plochere catalogue number, or a Ridgway plate citation) — not the ISCC-NBS serial number, which is carried by the block header. This means the parser need only identify block headers and extract name tokens; source references are present but not needed for the output.

---

## 4. Parsing procedure

The OCR text was loaded and the section 14 range (lines 7,242–54,982 of the first document copy) was extracted. The file contains two complete copies of the document; only the first was used.

**Step 1: Block header detection**  
Lines matching the pattern `^\d{1,3}\.\s+[A-Z ]+$` were identified as block headers. The integer prefix was extracted as the ISCC-NBS serial number; the remainder as the block name.

**Step 2: Source subheading filtering**  
Lines matching a fixed set of known source subheadings (Maerz and Paul, Plochere, Ridgway, Taylor Knoche Granville, Textile Color Card Association, Other Sources) were skipped.

**Step 3: Name extraction and cleaning (first pass)**  
All remaining non-blank lines within a block context were treated as colour name entries. Each entry line carries a trailing source reference which was stripped via iterative regex substitution covering the following reference formats:

| Source | Format | Example |
|---|---|---|
| Maerz & Paul | Alphanumeric grid: digit + letter + digit | `42K12` |
| Plochere | Number + letter code + hyphen code | `358 R 3-f` |
| Ridgway | Roman numeral + alphanumeric ref | `XXVI 71'b` |
| Taylor, Knoche & Granville | Digit + letter pair | `9 pa` |
| Textile Color Card Association | 5-digit number | `70213` |
| Other sources | Letter code with optional number | `H 27`, `S`, `A` |

Stripping was applied iteratively until the line stabilised. Trailing fill characters (`_`, `.`, `-`, whitespace) were removed before and after reference stripping. The cleaned name was validated by requiring: minimum length of 2 characters, an alphabetic starting character, and presence of at least one letter.

**Step 4: Validity filtering**  
Entries that, after cleaning, consisted only of source reference fragments (e.g. pure digit strings, single uppercase letter codes, alphanumeric grid patterns) were discarded.

**Step 5: Second and third pass cleaning**  
Inspection of the first-pass output revealed two residual noise categories requiring targeted treatment.

*Second pass — OCR garbage and unstripped reference codes (366 entries discarded).* A subset of entries retained 4+ digit Plochere catalogue numbers, Roman numeral Ridgway plate references, and OCR symbol substitutions (`$`, `#`, `/`, `»`) that the first-pass regex had not reached. These were identified via a targeted pattern (`\d{4,}`, `[IVX]{3,}\s*[\d\w#/]`, `[$#/\\»¥£¢*]`) and discarded entirely, as no colour name information was recoverable from them.

*Third pass — Taylor system modifier suffixes (1,423 entries cleaned; 74 further discarded).* Taylor, Knoche & Granville's *Descriptive Color Names Dictionary* appends chroma and lightness qualifier codes directly to colour names using a suffix notation: `m` (medium), `g` (greyed), `gm` (greyed medium). These appear in the source as entries such as `Baby Pink m`, `Cherry Rose g`, `Blossom Pink gm`. These suffixes are not part of the colour name as a rater would use it; a rater will say "baby pink", not "baby pink m". Trailing `m`, `g`, and `gm` suffixes were stripped, collapsing variant forms of the same name to a single entry. A further 74 entries where the Taylor chroma suffix had been OCR-rendered as symbol garbage (`^`, `\`, `|`, `*` — e.g. `Tomato Red m..6^ pc`) were discarded as unrecoverable.

The Taylor suffix stripping reduced unique name count relative to the first-pass output, as intended: `Baby Pink m` and `Baby Pink g` both collapse to `Baby Pink`, which maps to the same block. No block assignment information is lost by this collapse.

---

## 5. Output

The resulting CSV (`iscc_nbs_dictionary.csv`) has three columns:

| Column | Description |
|---|---|
| `name` | Colour name as it appears in the source dictionary, after cleaning |
| `serial_number` | ISCC-NBS block number (1–267) |
| `block_name` | ISCC-NBS block descriptor (e.g. `VIVID PURPLISH RED`) |

**Summary statistics:**

| Metric | Value |
|---|---|
| Total entries (after all cleaning passes) | 12,350 |
| Unique names (case-insensitive) | 6,435 |
| ISCC-NBS blocks covered | 263 of 267 |
| Names mapping to more than one block | 2,398 |
| Entries discarded across all passes | 440 (3.4% of first-pass output) |

**Missing blocks:** 3 (Deep Pink), 5 (Moderate Pink), 65 (Brownish Black), 111 (Grayish Olive Green). These blocks may be absent from section 14 of this edition or may have been lost to OCR failure.

---

## 6. Known limitations

**Residual OCR noise (~0.6% of entries).** Following three cleaning passes, approximately 74 entries with unrecoverable OCR symbol substitutions remain in the discard set. No such entries are present in the final CSV. The cleaning passes are documented in §4 (steps 5a and 5b) and reproducible from the parsing script.

**Multi-block ambiguity.** 2,398 names map to more than one ISCC-NBS block. This reflects genuine disagreement between contributing sources about where a colour name falls — "magenta" is assigned to 9 different blocks across sources, ranging from block 205 (Vivid Violet) to block 262 (Grayish Purplish Red). This is not an error in the lookup table; it is a finding about the imprecision of vernacular colour naming, which is precisely what the study aims to document. The pipeline should record all matching blocks and apply a disambiguation rule (e.g. modal block, or block from the textile-specific sources — Textile Color Card Association, AATCC — where available).

**Orthographic variants.** The dictionary uses 1955 American English spellings and two-word forms for some terms in common use today as single words (e.g. "Terra Cotta" not "terracotta", "Raw Sienna" not "sienna"). A small normalisation layer — lowercasing, stripping trailing whitespace, and a curated list of common variant mappings — is required before lookup. This normalisation layer should be documented and version-controlled alongside the CSV.

**Four uncovered blocks.** Blocks 3, 5, 65, and 111 have no entries in the parsed output. Rater terms that would naturally fall in these ranges (certain pinks and olive greys) will not be matchable via this table. The four missing blocks should be noted in the limitations section of any publication using this pipeline.

**Source bias.** The nine contributing vocabularies are predominantly mid-twentieth-century American and British trade and scientific sources. The resulting name coverage reflects that cultural and linguistic context. Terms from non-Anglophone textile traditions are absent.

---

## 7. Intended use in the DD4 pipeline

In the DD4 study, raters at the Falmouth conference inter-rater activity will provide free-form colour names for KMeans-defined colour regions displayed on screen. These names will be lowercased, whitespace-normalised, and looked up against this CSV. Matched names will return an ISCC-NBS serial number, which will then be joined to Munsell centroid data (sourced from bstreiff's CC0 machine-readable transcription of NBS Special Publication 440) and converted to CIELAB for delta-E comparison against spectrophotometer ground truth.

Names with no match will be recorded as unmappable. The proportion of unmappable terms is a study finding about the limits of vernacular colour vocabulary for standardisation purposes, and is only interpretable as such because the lookup table was derived from the full published dictionary rather than a curated subset. A curated subset would predetermine which terms are "acceptable", conflating lookup table gaps with genuine vocabulary limits.

---

## 8. AI tool use

All parsing scripts were developed with the assistance of Claude Sonnet 4.6 (model string `claude-sonnet-4-6`), Anthropic, in an interactive session on 4 June 2026 via claude.ai. Claude is acknowledged as a code development collaborator in this study and will be attributed in any resulting publication, consistent with the study's broader methodology for crediting AI tool contributions.

The following aspects of the pipeline were produced in whole or in part through this session:

- Structural analysis of the OCR text file to determine that Section 14 was preferable to Section 15 for parsing (§3)
- All regex patterns in the first-pass parser (`parse_iscc_final2.py`), including source reference detection and iterative stripping logic
- Diagnosis of the Taylor modifier suffix issue and the decision to strip rather than discard (§4, step 5)
- Both cleaning scripts and their inline documentation
- This methodology document

The source data (Kelly & Judd 1955), parsing decisions, methodological framing, and all research judgements are the author's own. Outputs were reviewed and verified before use.

**Model:** Claude Sonnet 4.6 (`claude-sonnet-4-6`)  
**Provider:** Anthropic (claude.ai)  
**Session date:** 4 June 2026  
**Knowledge cutoff of model:** August 2025

---

## 9. Files

| File | Description |
|---|---|
| `iscc_nbs_dictionary.csv` | Parsed and cleaned lookup table (this artefact) |
| `parse_iscc_final2.py` | First-pass parsing script |
| `parse_iscc_clean.py` | Second and third pass cleaning script |
| `dictionary-iscc.txt` | Source OCR text (Internet Archive) |

**Cite as:** Kelly, K. L. and Judd, D. B. (1955), parsed by [Author] with code developed using Claude Sonnet 4.6 (Anthropic), `parse_iscc_final2.py` and `parse_iscc_clean.py`, June 2026.
