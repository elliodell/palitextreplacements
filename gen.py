import unicodedata, re, json, uuid, os, shutil, zipfile, collections
def ascii_of(s): return ''.join(c for c in unicodedata.normalize('NFD', s) if not unicodedata.combining(c))
def cap(s): return s[0].upper()+s[1:]
def nfc(s): return unicodedata.normalize('NFC', s)

# Excluded because the plain keyword is an English word, or the start of one (would fire while typing English)
ENGLISH = {
 'pali':'palindrome, palisade, palimpsest; "Pali" itself', 'nana':'nana (grandmother)', 'mana':'mana; manage, manacle, manatee',
 'raga':'raga (music); ragamuffin', 'papa':'papa; papal, papacy', 'dana':'Dana (common given name)', 'maya':'Maya, Mayan',
 'mara':'marathon, maraud, maraca', 'brahma':'Brahma; brahman', 'sona':'sonar, sonata', 'vaca':'vacancy, vacant, vacation',
 'sila':'silage, silane, Silas', 'piti':'pitiful, pitiable', 'vicara':'vicarage', 'appana':'appanage', 'nama':'namaste, namable',
 'kama':'Kamala, Kama Sutra', 'parami':'paramilitary', 'hina':'Hina (name), Hinayana', 'apo':'apocalypse, apology, apostle',
 'kalama':'Kalamazoo, kalamata', 'sikhi':'Sikhism', 'bhagava':'Bhagavad (Gita), Bhagavata', 'pava':'pavane, Pavarotti',
 'lanka':'Sri Lanka (English spelling)', 'maha':'maharaja, mahatma, Mahabharata (never added)', 'cula':'culinary (never added)',
 'kaya':'kayak (never added)', 'panca':'pancake, pancreas (never added)', 'ghana':'Ghana (never added)', 'etam':'etamine',
}
# Dropped for other reasons (collisions / ambiguity); value = note
DROPPED = {
 'majjhima':'majjhimā (in majjhimā paṭipadā) would also turn "Majjhima Nikāya" into "Majjhimā" – wrong there',
 'idam':'function word, only useful inside a chant line', 'satta':'ambiguous: satta (seven) has no diacritics, sattā (beings) does',
 'araha':'rare; arahaṃ is kept',
 'punna (Puṇṇa)':'Puṇṇa (the monk) shares keyword "punna" with puñña (merit); puñña kept',
}
# Compounds that can never fire because a shorter keyword fires first (and the diacritics differ in the compound)
UNREACHABLE = {
 'akasanancayatana':'akasa fires first', 'vinnanancayatana':'vinnana fires first', 'anagamiphala':'anagami fires first → type "anāgāmi-phala"',
 'anattalakkhana':'anatta fires first → type "anatta-lakkhana" (gives anattā-lakkhaṇa)', 'anattata':'anatta fires first',
 'arupajhana':'arupa fires first → type "arupa jhana"', 'rupajhana':'rupa fires first → type "rupa jhana"',
 'asavakkhayavaham':'asava fires first', 'caganussati':'caga fires first → type "caga-anussati"', 'dhatukatha':'dhatu fires first',
 'dhatuvibhanga':'dhatu fires first → type "Dhatu-vibhanga"', 'mahasihanada':'mahasi fires first', 'nibbanadhatu':'nibbana fires first → type "nibbana-dhatu"',
 'pannaparami':'panna fires first → type "panna-parami"… but parami is excluded (paramilitary)', 'pannatti':'panna fires first; paññatti cannot be typed in one word',
 'paticca':'dropped the short form so that paticcasamuppada fires as one word (paṭicca-samuppāda also works with a hyphen if you add paṭicca back)',
 'punnam':'punna fires first', 'salayatanavibhanga':'salayatana fires first → type "Salayatana-vibhanga"',
 'sammaajiva':'samma fires first → type "samma ajiva"', 'sammaditthi':'samma fires first → type "samma ditthi" / "samma-ditthi"',
 'sammasamadhi':'samma fires first → type "samma samadhi"', 'sammasankappa':'samma fires first → type "samma sankappa"',
 'sammavaca':'samma fires first; and vaca is excluded (vacancy) → sammā vācā has to be typed by hand',
 'sammavayama':'samma fires first → type "samma vayama"', 'micchaditthi':'miccha fires first → type "miccha ditthi"',
 'sanghadisesa':'sangha fires first', 'sangham':'sangha fires first', 'sanghanussati':'sangha fires first → type "sangha-anussati"',
 'saranam':'sarana fires first', 'sasanam':'sasana fires first', 'sikkhapadam':'sikkhapada fires first',
 'theri':'therī dropped so that Therīgāthā can fire as one word', 'vedananupassana':'vedana fires first → type "vedana-anupassana"',
 'yathabhutananadassana':'yathabhuta fires first → type "yathabhuta-nanadassana"', 'silabbataparamasa':'silabbata fires first → type "silabbata-paramasa"',
 'buddhana':'rare chant inflection', 'micchacara':'miccha fires first → type "miccha-cara" by hand',
}
# Keep, but flag: the plain keyword is in the English dictionary only because it is a Pali/Sanskrit loanword
LOANWORDS = ['samsara','nibbana','samadhi','panna','avijja','rupa','vedana','tanha','jati','jara','sangha','brahmana','arupa','nidana','devata','naga','kamaloka','akasa','suttapitaka','gatha','apadana','mahayana','vajrayana','theravada','ananda','bimbisara','magadhi','sadhu','puja','vihara','karuna','jataka','sakya','metta','marana','sanna','punna','caga','bhumi','vesali','avici','gaya','anapana','gotami','tika','pitaka','asava','ahara','tathata','aloka','alara','sukhita']

SECTION = {'doctrine':'Doctrine','texts':'Texts','people':'People & Places','places':'People & Places','chanting':'Chanting'}
terms = collections.OrderedDict()  # keyword(lower) -> (cat, expansion)
# Validate every source line before replacing any previously generated exports.
with open('terms.txt', encoding='utf-8') as source:
    for line_number, line in enumerate(source, 1):
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        if line.count('|') != 1:
            raise ValueError(f'terms.txt:{line_number}: expected category|term')
        cat, word = (part.strip() for part in line.split('|'))
        if cat not in SECTION:
            raise ValueError(f'terms.txt:{line_number}: unknown category {cat!r}')
        if not word:
            raise ValueError(f'terms.txt:{line_number}: term must not be empty')
        for p in re.split(r'[ \-]+', nfc(word)):
            a = ascii_of(p)
            if a == p:
                continue
            terms.setdefault(a.lower(), (cat, p))
BANG_EXTRA = {'maha':'mahā','cula':'cūḷa','kaya':'kāya','panca':'pañca','ghana':'ghāna'}
bang = {}  # English-clash words, reachable with a "!" prefix
for k in list(terms):
    if k in ENGLISH: bang[k]=terms[k][1]
    if k in ENGLISH or k in DROPPED or k in UNREACHABLE: del terms[k]
bang.update(BANG_EXTRA)

# sanity: remaining prefix collisions with differing diacritics
ks=sorted(terms)
for k in ks:
    for l in ks:
        if l!=k and l.startswith(k):
            rest=terms[l][1][len(terms[k][1]):]
            if not terms[l][1].lower().startswith(terms[k][1].lower()) or ascii_of(rest)!=rest:
                print('STILL BAD', k, l)

COLLECTION='Pali'
PLIST='''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
\t<key>snippetkeywordprefix</key>
\t<string></string>
\t<key>snippetkeywordsuffix</key>
\t<string></string>
</dict>
</plist>
'''
out='dist'; shutil.rmtree(out, ignore_errors=True); os.makedirs(out)
build='build'; shutil.rmtree(build, ignore_errors=True)
count=0; rows=collections.defaultdict(list)
for k,(cat,exp) in terms.items():
    d=os.path.join(build, COLLECTION); os.makedirs(d, exist_ok=True)
    variants=[(k, cap(exp) if exp[0].isupper() else exp[0].lower()+exp[1:]), (k[0].upper()+k[1:], cap(exp))]
    for kw,ex in variants:
        uid=str(uuid.uuid4()).upper()
        obj={"alfredsnippet":{"snippet":ex,"uid":uid,"name":ex,"keyword":kw}}
        with open(os.path.join(d, f'{kw} [{uid}].json'),'w',encoding='utf-8') as f:
            json.dump(obj,f,ensure_ascii=False,indent=2)
        count+=1
    rows[SECTION[cat]].append((k, exp))
BANGCOLL='! prefixed (English-word clashes)'
d=os.path.join(build,COLLECTION)
# A custom term list may contain no unprefixed snippets.
os.makedirs(d, exist_ok=True)
for k,exp in sorted(bang.items()):
    for kw,ex in [('!'+k, cap(exp) if exp[0].isupper() else exp[0].lower()+exp[1:]), ('!'+k[0].upper()+k[1:], cap(exp))]:
        uid=str(uuid.uuid4()).upper()
        json.dump({"alfredsnippet":{"snippet":ex,"uid":uid,"name":ex,"keyword":kw}}, open(os.path.join(d,f'{kw} [{uid}].json'),'w',encoding='utf-8'), ensure_ascii=False, indent=2)
        count+=1
    rows[BANGCOLL].append(('!'+k, exp))
for name in [COLLECTION]:
    d=os.path.join(build,name)
    open(os.path.join(d,'info.plist'),'w').write(PLIST)
    with zipfile.ZipFile(os.path.join(out, name+'.alfredsnippets'),'w',zipfile.ZIP_DEFLATED) as z:
        for fn in sorted(os.listdir(d)): z.write(os.path.join(d,fn), fn)
print('snippets written:', count, 'terms:', len(terms))

with open('pali-snippets-list.md','w',encoding='utf-8') as f:
    f.write('# Pali diacritic snippets\n\nOne Alfred collection: `Pali.alfredsnippets`.\n\nEach term exists twice: lowercase keyword and Capitalised keyword. Common nouns follow the case you type; proper names (people, places, text titles) are always Capitalised.\n\n')
    for name in ['Doctrine','Texts','People & Places','Chanting',BANGCOLL]:
        f.write(f'## {name} ({len(rows[name])} terms)\n\n| type | get |\n|---|---|\n')
        for k,e in sorted(rows[name]): f.write(f'| {k} | {e} |\n')
        f.write('\n')
    f.write('## English-word clashes: only available with the ! prefix (see section above)\n\n| keyword | clashes with |\n|---|---|\n')
    for k,v in sorted(ENGLISH.items()): f.write(f'| {k} | {v} |\n')
    f.write('\n## Not created: a shorter snippet would always fire first\n\n| keyword | why / workaround |\n|---|---|\n')
    for k,v in sorted(UNREACHABLE.items()): f.write(f'| {k} | {v} |\n')
    f.write('\n## Not created: other\n\n| keyword | why |\n|---|---|\n')
    for k,v in sorted(DROPPED.items()): f.write(f'| {k} | {v} |\n')
    f.write('\n## Created but worth knowing: in the English dictionary only as a Pali/Sanskrit loanword\n\n' + ', '.join(sorted(set(LOANWORDS)&set(terms))) + '\n')

# ---- Apple Text Replacement export (macOS/iOS, syncs via iCloud) ----
# Text Replacement only fires on a whole word (after space/punctuation), and shortcuts are matched
# case-insensitively, so one entry per term is enough.
from xml.sax.saxutils import escape
entries = []
for k,(cat,exp) in sorted(terms.items()):
    entries.append((k, exp))                      # proper names already Capitalised in exp
# English-clash words go in plain (no '!'): Text Replacement only matches whole words, so prefixes are safe.
for k,exp in sorted(bang.items()):
    if k in ('ghana',): continue   # would rewrite the country name
    entries.append((k, exp))
with open(os.path.join(out,'Pali Text Replacements.plist'),'w',encoding='utf-8') as f:
    f.write('<?xml version="1.0" encoding="UTF-8"?>\n<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">\n<plist version="1.0">\n<array>\n')
    for sc,ph in entries:
        f.write(f'\t<dict>\n\t\t<key>phrase</key>\n\t\t<string>{escape(ph)}</string>\n\t\t<key>shortcut</key>\n\t\t<string>{escape(sc)}</string>\n\t</dict>\n')
    f.write('</array>\n</plist>\n')
print('text replacements written:', len(entries))
