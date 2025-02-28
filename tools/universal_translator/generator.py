import random
import json

# Säännöt conlang-generaattorista
custom_consonants = "p b t d k ɡ f v s z ʃ ʒ h l r j w m n ɲ ŋ".split()
custom_vowels = "a e i o u y æ ø ɑ ɛ ɔ aː eː iː oː uː yː æː øː ɑː ɛː ɔː".split()
word_initial_consonants = "m k p ɢ w t n h ɲ ʃ d b v ʄ z ɗ g x ɓ f r ʤ ʧ ʒ".split()
mid_word_consonants = "p w t tn j ʤ m k kʃ b ɗ dʒ g s ŋ ɲ ɢ l d ʧ z n f ʒ nt h x rd r ŋk mp mb rt v ɣ gb ɓ ʄ ng lt tʃ ʃ q ʃt sk nf bl nj ts rm nv nʧ pl rg nʃ nm gj rs pt br nn gz mj tj tt lw kn mt vn pʃ gl ɲj vl sm kr rj mm mg nb pr xj rr tw ŋn mf rf rɣ vj xw ŋm ɲʤ hk mz rʃ sw xn zv dw gr hd jj nx zj fj gw pʧ rw sʧ bn ff mʧ rh tv ʧn gt mr rʤ wv zl ŋx mv nr ws zb ɣr ʧm bb mh np pn zg ŋh ŋw bm kɲ px tʧ vd vw wk xg bv zt bd db fh fn jg jv jʒ km kv wp ɣm ʃb ʤm bʒ fd fx gf jf js kz lz lɣ dx nʒ pz qq rʒ sz sɲ td tɲ wg wl wʤ xr ŋz ɣj ɣn ɲb ɲz ʃr ʃs ʒj ʒl ʤt ʧɲ bw bʃ fr fw fɣ fʃ hr lʧ qt tp vb vg wb wm xf xh xl xm xs xz ŋp ɣw ɲt ɲʧ ʃɲ ʒn ʧg ʧl".split()
word_final_consonants = "m k g z nz f n s ʧ t ɲ ɢ b ld ɣ ʒ ɓ dʒ nt d ŋ ʃ nd rt q ʄ ns ʤ ɗ mp bz ts rm lt dz ʃt ps ft md sk gz nʃ jj rd js lp rn mʧ jt nk lʃ ms ŋd kʃ zt gʧ lʒ lʧ nx ɲv dv gs jl nw pʃ rp rv rɲ sg tm ʃd".split()
# illegal_combinations = "".split()  # Ei sääntöjä tässä tapauksessa
bws_vowels = "a i u o e ə y æ ø ɑ ɛ ɔ aː eː iː oː uː yː æː øː ɑː ɛː ɔː".split()
bws_2nd_vowels = "aː eː iː oː uː yː æː øː ɑː ɛː ɔː".split()
phoneme_classes = {
    "C": "p t k b d ɡ f v s z ʃ ʒ h".split(),
    "L": "l r j w".split(),
    "N": "m n ɲ ŋ".split(),
    "V": "a e i o u y æ ø ɑ ɛ ɔ".split(),
    "S": ["CV", "CVL", "CVC", "CVL"] # Huom: Nämä ovat esimerkkejä, eivät sääntöjä
}
word_patterns = ["S", "SS", "SSS", "SSSS"] # Huom: Nämä ovat esimerkkejä, eivät sääntöjä
# article_patterns = ["S", "V"] # Ei käytössä tässä esimerkissä
# pronoun_patterns = ["S", "SS"] # Ei käytössä tässä esimerkissä
# determiner_patterns = ["S"] # Ei käytössä tässä esimerkissä
affix_patterns = ["-VC", "CV-", "-CVL", "-LVC", "-VCL"]
max_onset = None  # Ei rajoitusta tässä tapauksessa
max_coda = None  # Ei rajoitusta tässä tapauksessa
vowel_start_prob = 40
vowel_end_prob = 70
vowel_tones = "a¹ a² a³ a⁴e¹ e² e³ e⁴i¹ i² i³ i⁴o¹ o² o³ o⁴u¹ u² u³ u⁴y¹ y² y³ y⁴æ¹ æ² æ³ æ⁴ø¹ ø² ø³ ø⁴ɑ¹ ɑ² ɑ³ ɑ⁴ɛ¹ ɛ² ɛ³ ɛ⁴ɔ¹ ɔ² ɔ³ ɔ⁴".split()
spelling_rules = {
    "ɔː": "oooo", "ɛː": "eeee", "ɑː": "aaaa", "ʃ": "sh", "ʒ": "zh",
    "ɲ": "nj", "ŋ": "ng", "æː": "aee", "æ": "ae", "øː": "oee",
    "ø": "oe", "ɑ": "aa", "ɛ": "eh", "ɔ": "oh", "aː": "aa",
    "eː": "ee", "iː": "ii", "oː": "oo", "uː": "uu", "yː": "yy",
    "ɛ": "é", "ɑ": "á", "ə": "â", "ɔ": "aw", "y": "ú", "ɗ": "d’",
    "ʒ": "zh", "j": "y", "ʃ": "sh", "ŋ": "ng", "ʤ": "j", "ʄ": "j’",
    "ʧ": "ch", "ɓ": "b’", "ɢ": "ǵ", "ɲ": "ny", "x": "kh", "ɣ": "gh",
    "Vː": "VV" # Tämä sääntö korvataan alempana tarkemmilla säännöillä
}
# Lisätään Vː säännöt jokaiselle vokaalille erikseen
for vowel in custom_vowels:
    if "ː" in vowel:
        spelling_rules[vowel] = vowel.replace("ː", "") * 2
second_spelling_rules = {
    "ʃ": "sh", "ʒ": "zh", "ɲ": "nj", "ŋ": "ng", "æ": "ae",
    "ø": "oe", "ɑ": "aa", "ɛ": "eh", "ɔ": "oh", "aː": "aa",
    "eː": "ee", "iː": "ii", "oː": "oo", "uː": "uu", "yː": "yy",
    "æː": "aee", "øː": "oee", "ɑː": "aaaa", "ɛː": "eeee", "ɔː": "oooo"
}
custom_alphabet_order = "" # Ei käytössä tässä esimerkissä

def build_markov_chain(names, order=2):
    chain = {}
    for name in names:
        name = '^' * order + name + '$'
        for i in range(len(name) - order):
            context = name[i:i + order]
            next_char = name[i + order]
            if context not in chain:
                chain[context] = {}
            if next_char not in chain[context]:
                chain[context][next_char] = 0
            chain[context][next_char] += 1
    return chain

def generate_name(chain, order=4, min_length=4, max_length=8):
    while True:
        name = ''
        context = '^' * order

        # Todennäköisyys aloittaa vokaalilla
        if random.randint(1, 100) <= vowel_start_prob:
            context = random.choice(custom_vowels)
            name += context
            
        
        while True:
            if context not in chain:
                break

            possible_chars = chain[context]
            
            # Suodatetaan mahdolliset seuraavat merkit sääntöjen mukaan
            
            
            filtered_chars = {}
            
            # Jos nimi alkaa konsonantilla, lisää vokaali
            if len(name) > 0 and name[0] in custom_consonants:
                 for char, count in possible_chars.items():
                    if char in custom_vowels:
                        filtered_chars[char] = count

            #Jos nimi alkaa vokaalilla, lisää konsonantti
            if len(name) > 0 and name[0] in custom_vowels:
                 for char, count in possible_chars.items():
                    if char in custom_consonants:
                        filtered_chars[char] = count
            
            #Sanan keskellä:
            if '^' not in context and '$' not in context:
                for char, count in possible_chars.items():
                    if char in mid_word_consonants or char in custom_vowels:
                        filtered_chars[char] = count
                        
            
            # Sanan lopussa (viimeinen merkki)
            if len(name) > 0 and name[-1] in custom_consonants:
                for char, count in possible_chars.items():
                    if char == '$' or char in word_final_consonants:
                        filtered_chars[char] = count
            
            # Sanan alussa
            if '^' in context:
                for char, count in possible_chars.items():
                    if char in word_initial_consonants or char in custom_vowels:
                        filtered_chars[char] = count

            # Jos ei ole laillisia vaihtoehtoja, lopeta
            if not filtered_chars:
                break

            next_char = random.choices(list(filtered_chars.keys()), weights=list(filtered_chars.values()))[0]
            
            if next_char == '$':
                # Todennäköisyys lopettaa vokaaliin
                if name[-1] in custom_vowels and random.randint(1, 100) <= vowel_end_prob:
                    break
                elif name[-1] not in custom_vowels:
                    break
                else:
                    continue

            
            name += next_char
            context = context[1:] + next_char

        if min_length <= len(name) <= max_length:
            # Tarkistetaan vielä lopullinen nimi
            if (name[0] in word_initial_consonants or name[0] in custom_vowels) and (name[-1] in word_final_consonants or name[-1] in custom_vowels):
              
              return name

def apply_spelling_rules(name, rules):
    """
    Sovelletaan kirjoitussääntöjä nimeen.

    Args:
        name: Nimi, johon sääntöjä sovelletaan.
        rules: Sanakirja, joka sisältää kirjoitussäännöt.

    Returns:
        Nimi, johon säännöt on sovellettu.
    """
    for before, after in rules.items():
        name = name.replace(before, after)
    return name

# Esimerkkinimet (korvaa tähän omat nimesi)
example_names = [
    "furˈvodaj", "ʒal", "pɛˈtɑse", "patˈpøbʃe", "ˈsiwpɑj", "giʒ", "ʒɔj",
    "ˌʒypørˈdalkæ", "zɑˈsoker", "ˌpytpuˈvuldyj", "darˈfylke", "ʒawˈʃittud",
    "ˈgoge", "sɑr", "piˈtøtor", "se", "vɔʃ", "ha", "ty", "til",
    "ˌdyzuˈkɛldøl", "ˌbɔjfahˈkagu", "bɑv", "ˈdukbær", "pawˈpuwpi", "daj",
    "ˈbɔpfɛ", "vɑ", "feˈfopæv", "ˈseʒtoj", "ˌkɑsaˈkylbø", "ˈtɔwzi", "kor",
    "zɛjˈtorfa", "pøpˈgɔkod", "ˌsattɑʃˈpɔʃke", "zyj", "ɲoːp", "fuː", "jeːs",
    "ˈnɑːwpɛ", "wɑː", "vunˈtamlyᵑg", "sas", "bøː", "pɔ", "job", "ˈɲiwvi",
    "ᵑguː", "mɑːɣ", "ɲøːɲ", "teː", "ˈbɔːŋy", "voː", "niː", "ˈulke", "ɔː",
    "ˈgoːmyː", "ˈniːvom", "ˈjaːlø", "møm", "dɑːm", "nem", "ˈøːʒnɔ", "tæʃ",
    "fonˈʒæmwɑŋ", "ɣot", "ta", "ɲuː", "mɛːv", "ᵑgɛː", "zun", "ˈliʃkɔ", "vu",
    "ɬøɲ", "mæʃ", "bø", "zyːn", "gæm", "peː", "ˈvuyːm", "toː", "wo", "ken",
    "baː", "mɛᵑg", "nɑːt", "ˈɑmsu", "nɑː", "tu", "ˈøːɣjɑt", "ˈᵑgɔgne", "ˈnue",
    "ˈmɛrgi", "ɲøᵑg", "git", "ɬæ", "ɣa", "lim", "fi", "ˈjunly", "ɲal", "ʒøː",
    "pøː", "siː", "ɲo", "ˈpoːgøːm", "nohˈmærkaː", "aˈpɛːmwof", "weː",
    "ʃɑːˈʒoːgwiː", "faː", "ˈløːwgoː", "ɔ", "mɔ", "ᵐbaːn", "noːm", "ˈlavviː",
    "ˈguwpæ", "ʒygˈmyʃviː", "ɣeː", "ʒeːŋ", "ʃeɲ", "gæː", "ɣi", "nu", "peːp",
    "ˈaːdfyː", "ˈpætmuz", "ˈʃerpum", "ɬæː", "od", "ˈguʒɲyː", "ʒaː",
    "ˈɬømpɔː", "lo", "ˈzezu", "piː", "ɔːz", "zoː", "vɔ", "ɑ", "tuː", "næf",
    "en", "ˈɬuːʃvo", "ˈtiːllaː", "zæ", "ʃæː", "pab", "ɲiː", "ᵐbaːs", "ˈmamnæː",
    "føm", "ˈjɛmuːz", "yː", "myː"
]

# Rakennetaan Markovin ketju
markov_chain = build_markov_chain(example_names, order=2)

def generate_names_to_json(count=13025, output_file="generated_names.json"):
    """
    Generoi nimiä ja tallentaa ne JSON-tiedostoon.

    Args:
        count: Generoitavien nimien määrä.
        output_file: JSON-tiedoston nimi.
    """
    generated_names = []

    # Rakennetaan Markovin ketju
    markov_chain = build_markov_chain(example_names, order=2)

    # Generoidaan nimet ja tallennetaan ne listaan
    for _ in range(count):
        generated_name = generate_name(markov_chain, order=4, min_length=4, max_length=8)
        spelled_name = apply_spelling_rules(generated_name, spelling_rules)

        # Tallennetaan nimi listaan
        generated_names.append(spelled_name)

        # Tulostetaan myös konsoliin
        print(f"{generated_name} -> {spelled_name}")

    # Tallennetaan JSON-tiedostoon
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({"mothertree": generated_names}, f, ensure_ascii=False, indent=2)

    print(f"\nNimet tallennettu tiedostoon: {output_file}")

# Kutsutaan funktiota generoimaan ja tallentamaan nimet
if __name__ == "__main__":
    generate_names_to_json(13025, "generated_names.json")