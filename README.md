# Pāli text replacements

Type Pāli terms in plain ASCII and get the diacritics automatically: `satipatthana` → satipaṭṭhāna, `samsara` → saṃsāra, `Anguttara` → Aṅguttara.

400 terms covering doctrine, text titles, people and places, and common chanting vocabulary, in two formats:

| File | For | Entries |
|---|---|---|
| [Pali.alfredsnippets](dist/Pali.alfredsnippets) | Alfred 5 on Mac (Powerpack) | 860 snippets |
| [Pali Text Replacements.plist](dist/Pali%20Text%20Replacements.plist) | Apple Text Replacement on iPhone, iPad and Mac | 429 replacements |

The full list of what you type and what you get is in [pali-snippets-list.md](pali-snippets-list.md).

## Install

**Alfred.** Download `Pali.alfredsnippets` and double-click it to import the collection. Turn on "Automatically expand snippets by keyword" in Alfred Preferences → Features → Snippets.

**iPhone / iPad / Mac.** iOS has no import of its own, so add the list on a Mac: open System Settings → Keyboard → Text Replacements…, then drag `Pali Text Replacements.plist` into the list. The entries sync to your iPhone and iPad through iCloud.

## How it behaves

- Common nouns follow the case you type (`jhana` → jhāna, `Jhana` → Jhāna). Proper names and text titles are always capitalised.
- Words that are also English words, or the start of one, would misfire in Alfred, which expands a keyword the moment it is typed. Those 30 need a `!` prefix there: `!pali` → Pāli, `!sila` → sīla, `!dana` → dāna.
- Text Replacement only fires on whole words, so in the iOS list the same words are plain shortcuts with no `!`. Delete any you would rather keep as English (`dana`, `maya`, `papa`, …).
- In Alfred a short keyword fires before a longer compound can be typed, so a few compounds are entered as separate words or with a hyphen: `samma ditthi` → sammā diṭṭhi. The list file has the full table of these.

## Adding terms

Both lists are generated from [terms.txt](terms.txt), one `category|term` per line with the diacritics in place; the ASCII keyword is derived by stripping them. Edit it, then rebuild `dist/` and the list file:

```bash
python3 gen.py
```

The exclusion tables (English clashes, unreachable compounds) live at the top of [gen.py](gen.py).
