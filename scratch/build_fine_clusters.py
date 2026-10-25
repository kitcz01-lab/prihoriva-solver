#!/usr/bin/env python3
"""
High-Precision Focused Cluster Builder for Prihoriva Solver.
Builds cohesive, compact semantic clusters (20-80 words per cluster) with zero noisy mega-buckets.
"""

import json
import os
import unicodedata
from collections import defaultdict

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
WORDS_FILE = os.path.join(DATA_DIR, "words_cs.json")
OUTPUT_FILE = os.path.join(DATA_DIR, "clusters.json")

with open(WORDS_FILE, "r", encoding="utf-8") as f:
    VOCAB = json.load(f)
VOCAB_SET = set(VOCAB)

def norm_cz(s):
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn").lower()

NORM_VOCAB = {w: norm_cz(w) for w in VOCAB}

# Strategic Anchors across diverse conceptual axes
ANCHORS = [
    "věc", "člověk", "zvíře", "příroda", "kov", "dřevo", "hudba", "jídlo",
    "stavba", "vozidlo", "oblečení", "čas", "věda", "pocit", "tělo",
    "koruna", "událost", "práce", "sport", "umění", "obchod", "právo",
    "zdraví", "myšlenka", "rodina", "škola", "technologie", "stát"
]
ANCHORS = [a for a in ANCHORS if a in VOCAB_SET]

# Define 54 Compact, High-Cohesion Semantic Domains
DOMAINS = {
    # GASTRONOMIE
    "jidlo_pecivo_mouka": {
        "label": "Pečivo, mouka a obilniny",
        "triggers": ["chléb", "pečivo", "mouka", "rohlík", "těsto"],
        "seeds": ["chléb", "rohlík", "houska", "bageta", "koláč", "bábovka", "buchta", "mouka", "těsto", "kvasnice", "droždí", "preclík", "toast", "croissant", "těstovina", "špageta", "nudle", "otruby", "strouhanka", "bochník", "krajíc", "veka", "závin", "kobliha", "lívanec", "palačinka", "piškot", "perník", "oves", "pšenice", "ječmen", "žito", "kroupa", "zrno", "klas", "obilí"],
        "stems": ["chleb", "peciv", "pekar", "pekarn", "mouk", "test", "obil", "psenic", "zitn", "jecmen", "oves", "kroup", "housk", "rohlik", "baget", "kolac", "babovk", "bucht", "preclik", "testovin", "spaget", "nudl", "drozd"]
    },
    "jidlo_ovoce_plody": {
        "label": "Ovoce, lesní plody a ořechy",
        "triggers": ["ovoce", "jablko", "hruška", "jahoda", "plod"],
        "seeds": ["jablko", "hruška", "švestka", "třešeň", "višeň", "jahoda", "malina", "borůvka", "ostružina", "rybíz", "angrešt", "meloun", "banán", "pomeranč", "citron", "limetka", "mandarinka", "grep", "ananas", "mango", "broskev", "meruňka", "fík", "datle", "hrozen", "rozinka", "ořech", "mandle", "kaštan", "kokos", "avokádo", "kiwi", "plod", "bobule", "brusinka", "kdoule", "rakytník", "pecka"],
        "stems": ["ovoc", "jablk", "hrusk", "svestk", "tresn", "visn", "jahod", "malin", "boruvk", "ostruzin", "rybiz", "angrest", "meloun", "banan", "pomeranc", "citron", "mandarink", "broskv", "merunk", "orech", "mandl", "kastan", "kokos"]
    },
    "jidlo_zelenina_houby": {
        "label": "Zelenina, luštěniny a houby",
        "triggers": ["zelenina", "brambor", "mrkev", "cibule", "houba"],
        "seeds": ["zelenina", "brambor", "mrkev", "petržel", "celer", "cibule", "česnek", "rajče", "paprika", "okurka", "dýně", "cuketa", "lilek", "květák", "brokolice", "zelí", "kapusta", "kedluben", "ředkvička", "řepa", "špenát", "salát", "chřest", "fazole", "čočka", "hrách", "sója", "kukuřice", "hřib", "žampion", "kozák", "bedla", "liška", "smrž", "křen", "zázvor", "artyčok", "pastinák", "batát", "hlíva", "houba", "klouzek", "lanýž", "pór"],
        "stems": ["zelenin", "brambor", "mrkv", "petrzel", "celer", "cibul", "cesnek", "rajc", "paprik", "okurk", "dyne", "cuket", "lilk", "kvetak", "brokolic", "zeli", "kapust", "kedlub", "redkvic", "spenat", "salat", "chrest", "fazol", "cock", "hrach", "kukuric", "hrib", "zampion", "bedl", "houb"]
    },
    "jidlo_maso_uzeniny": {
        "label": "Maso, uzeniny a rybí pokrmy",
        "triggers": ["maso", "šunka", "salám", "řízek", "klobása"],
        "seeds": ["maso", "hovězí", "vepřové", "drůbež", "kuře", "kachna", "husa", "krůta", "králík", "zvěřina", "losos", "kapr", "pstruh", "tuňák", "šunka", "salám", "klobása", "párek", "jitrnice", "jelito", "tlačenka", "slanina", "špek", "sádlo", "paštika", "sekaná", "řízek", "guláš", "svíčková", "biftek", "pečeně", "kotleta", "žebírko", "špíz", "bůček", "uzené", "výpečky", "steak", "karbanátek", "řezník", "jatka"],
        "stems": ["mas", "hovez", "veprov", "drubez", "kurec", "kachn", "krut", "losos", "pstruh", "tunak", "sunk", "salam", "klobas", "parek", "jitrnic", "jelit", "tlacenk", "slanin", "spek", "sadlo", "pastik", "sekan", "rizek", "gulas", "kotlet", "uzenin"]
    },
    "jidlo_mlecne_syry": {
        "label": "Mléčné výrobky a sýry",
        "triggers": ["mléko", "sýr", "máslo", "tvaroh", "smetana"],
        "seeds": ["mléko", "smetana", "máslo", "tvaroh", "sýr", "jogurt", "kefír", "podmáslí", "syrovátka", "hermelín", "niva", "ementál", "gouda", "čedar", "parmazán", "mozzarella", "brynza", "oštěpek", "žervé", "syreček", "ricotta", "korbáčik", "pudink"],
        "stems": ["mlek", "mlec", "smetan", "masl", "tvaroh", "syr", "jogurt", "kefir", "hermelin", "parmazan", "mozzarell", "brynz"]
    },
    "jidlo_sladkosti_cukrovinky": {
        "label": "Sladkosti, dezerty a cukrovinky",
        "triggers": ["cukr", "čokoláda", "dort", "med", "bonbón"],
        "seeds": ["cukr", "med", "čokoláda", "bonbón", "lízátko", "karamel", "marcipán", "nugát", "poleva", "krém", "dort", "zákusek", "sušenka", "oplatek", "marmeláda", "povidla", "sirup", "pralinka", "šlehačka", "cukroví", "želé", "pendrek", "maršmeloun", "zmrzlina", "dražé", "perník"],
        "stems": ["cukr", "cokolad", "bonbon", "lizatk", "karamel", "marcipan", "dort", "zakusk", "susenk", "oplatk", "marmelad", "povidl", "sirup", "pralink", "zmrzlin", "cukrar"]
    },
    "jidlo_napoje_alkohol": {
        "label": "Nápoje, pivo, víno a káva",
        "triggers": ["nápoj", "voda", "pivo", "víno", "káva"],
        "seeds": ["nápoj", "voda", "minerálka", "limonáda", "šťáva", "džus", "mošt", "sirup", "čaj", "káva", "espresso", "kakao", "pivo", "ležák", "víno", "sekt", "šampaňské", "likér", "rum", "vodka", "gin", "whisky", "koňak", "slivovice", "medovina", "cider", "aperitiv", "tequila", "lihovina", "pivovar", "vinař", "koktejl", "drink"],
        "stems": ["napoj", "limonad", "kav", "piv", "vin", "liker", "vodk", "slivovic", "lihovin", "pivovar", "vinar", "koktejl"]
    },
    "jidlo_vareni_koreni": {
        "label": "Vaření, pečení, polévky a koření",
        "triggers": ["polévka", "omáčka", "koření", "sůl", "pepř"],
        "seeds": ["polévka", "vývar", "omáčka", "příloha", "sůl", "pepř", "kmín", "majoránka", "skořice", "hřebíček", "vanilka", "oregano", "bazalka", "ocet", "olej", "hořčice", "kečup", "majonéza", "tatarka", "jíška", "omastek", "bujón", "chilli", "vaření", "smažení", "pečení", "kuchař", "kuchyně", "recept", "bešamel", "příchuť"],
        "stems": ["polevk", "vyvar", "omack", "koren", "skoric", "oregan", "bazalk", "horcic", "kecup", "majonez", "kuchar", "kuchyn"]
    },

    # ŽIVÁ PŘÍRODA
    "priroda_savci_domaci": {
        "label": "Domácí a hospodářská zvířata",
        "triggers": ["pes", "kočka", "kůň", "kráva", "prase"],
        "seeds": ["pes", "štěně", "kočka", "kotě", "kocour", "kůň", "hříbě", "hřebec", "kobyla", "kráva", "býk", "tele", "vůl", "prase", "sele", "kanec", "ovce", "beran", "jehně", "koza", "kozel", "kůzle", "osel", "fena", "jalovice", "valach", "čuba", "prasnice"],
        "stems": ["psik", "stene", "kocic", "kocour", "hribe", "hrebec", "kobyl", "telat", "prasat", "beran", "jehnec", "kozel", "kuzl"]
    },
    "priroda_savci_divoci": {
        "label": "Volně žijící lesní a polní šelmy a savci",
        "triggers": ["vlk", "liška", "medvěd", "jelen", "srnec"],
        "seeds": ["vlk", "liška", "medvěd", "rys", "divočák", "jelen", "laň", "kolouch", "srnec", "srna", "daněk", "muflon", "kamzík", "bobr", "vydra", "jezevec", "kuna", "lasička", "tchoř", "veverka", "ježek", "křeček", "myš", "potkan", "krysa", "hraboš", "krtek", "netopýr", "zajíc", "plch", "sysel", "ondatra", "norek", "fretka", "los", "sob", "bizon", "zubr"],
        "stems": ["vlcek", "lisat", "medved", "divocak", "srnc", "muflon", "kamzik", "jezevec", "lasick", "veverk", "jezek", "krecek", "hrabos", "netopyr", "zajic", "fretk"]
    },
    "priroda_savci_exoticti": {
        "label": "Exotická zvířata a africká fauna",
        "triggers": ["lev", "slon", "tygr", "opice", "žirafa"],
        "seeds": ["lev", "lvice", "tygr", "levhart", "gepard", "jaguár", "puma", "hyena", "šakal", "slon", "nosorožec", "hroch", "žirafa", "zebra", "antilopa", "gazela", "velbloud", "lama", "klokan", "koala", "panda", "opice", "šimpanz", "gorila", "orangutan", "pavián", "lemur", "lenochod", "mravenečník", "pásovec", "dikobraz", "tapír", "surikata"],
        "stems": ["levhart", "gepard", "jaguar", "nosorozec", "ziraf", "zebr", "antilop", "velbloud", "klokan", "simpanz", "goril", "orangutan", "pavian", "lemur", "surikat"]
    },
    "priroda_ptaci": {
        "label": "Ptáci, dravci a opeřenci",
        "triggers": ["pták", "orel", "holub", "sova", "vrabec"],
        "seeds": ["pták", "orel", "sokol", "jestřáb", "káně", "sova", "výr", "sýček", "havran", "vrána", "krkavec", "straka", "sojka", "holub", "hrdlička", "vrabec", "sýkora", "kos", "drozd", "pěnkava", "slavík", "vlaštovka", "jiřička", "rorýs", "skřivan", "špaček", "stehlík", "hýl", "kukačka", "strakapoud", "datel", "žluna", "dudek", "ledňáček", "koroptev", "bažant", "křepelka", "labuť", "husa", "kachna", "čáp", "volavka", "pelikán", "plameňák", "racek", "tučňák", "pštros", "papoušek", "andulka", "kanár", "páv", "krocan", "peří", "pírko", "hnízdo"],
        "stems": ["ptac", "orl", "sokol", "jastrab", "kane", "sycek", "havran", "hrdlick", "sykor", "penkav", "slavik", "vlastovk", "skrivan", "spacek", "kukack", "strakapoud", "koroptev", "bazant", "plamenak", "tucnak", "papousek", "andulk"]
    },
    "priroda_vodni_zivocisi": {
        "label": "Ryby, paryby a mořští živočichové",
        "triggers": ["ryba", "kapr", "pstruh", "žralok", "velryba"],
        "seeds": ["ryba", "kapr", "štika", "candát", "sumec", "okoun", "pstruh", "siven", "lipan", "lín", "cejn", "plotice", "karas", "úhoř", "losos", "treska", "tuňák", "makrela", "sleď", "sardinka", "žralok", "rejnok", "delfín", "velryba", "kosatka", "vorvaň", "tuleň", "lachtan", "mrož", "medúza", "chobotnice", "oliheň", "sépie", "hvězdice", "ježovka", "krab", "humr", "kreveta", "rak", "mušle", "ústřice", "škeble", "ploutev", "šupina", "korál"],
        "stems": ["rybar", "rybnik", "candat", "sumec", "pstruh", "losos", "tresk", "tunak", "makrel", "sardink", "zralok", "rejnok", "delfin", "velryb", "kosatk", "chobotnic", "hvezdic", "krevet", "ustric"]
    },
    "priroda_hmyz": {
        "label": "Hmyz, pavouci a bezobratlí",
        "triggers": ["hmyz", "moucha", "včela", "brouk", "motýl"],
        "seeds": ["hmyz", "moucha", "komár", "včela", "vosa", "sršeň", "čmelák", "mravenec", "motýl", "můra", "housenka", "brouk", "chrobák", "střevlík", "tesařík", "beruška", "slunéčko", "chroust", "světluška", "vážka", "kobylka", "saranče", "cvrček", "šváb", "škvor", "blecha", "veš", "klíště", "pavouk", "sekáč", "křižák", "sklípkan", "štír", "stonožka", "žížala", "pijavice", "larva", "kukla", "slimák", "červ"],
        "stems": ["komar", "vcel", "cmelak", "mraven", "motyl", "housenk", "brouk", "berusk", "chroust", "kobylk", "saranc", "cvrcek", "pavouk", "sklipkan", "stonozk", "zizal"]
    },
    "priroda_stromy_les": {
        "label": "Stromy, keře a lesní porost",
        "triggers": ["strom", "les", "dub", "smrk", "borovice"],
        "seeds": ["strom", "keř", "dub", "buk", "bříza", "lípa", "javor", "jasan", "jilm", "habr", "topol", "vrba", "olše", "platan", "smrk", "jedle", "borovice", "modřín", "tis", "jalovec", "šeřík", "bez", "trnka", "šípek", "hloh", "břečťan", "pařez", "větev", "kmen", "kůra", "jehličí", "šiška", "žalud", "les", "prales", "háj", "mýtina"],
        "stems": ["strom", "lesn", "javor", "jasan", "topol", "jedl", "borovic", "modrin", "jalovec", "serik", "brectan", "jehlic"]
    },
    "priroda_rostliny_kvety": {
        "label": "Květiny, byliny a botanika",
        "triggers": ["květina", "rostlina", "bylina", "růže", "tráva"],
        "seeds": ["rostlina", "bylina", "květina", "tráva", "mech", "kapradí", "růže", "tulipán", "karafiát", "orchidej", "lilie", "fialka", "konvalinka", "sedmikráska", "pampeliška", "slunečnice", "heřmánek", "kopřiva", "máta", "meduňka", "šalvěj", "levandule", "rozmarýn", "tymián", "jitrocel", "řebříček", "třezalka", "jetel", "bodlák", "leknín", "stonek", "lodyha", "pupen", "okvětí", "kalich", "pyl", "nektar", "semeno", "narcis", "hyacint", "sněženka", "bledule"],
        "stems": ["rostlin", "bylin", "kvetin", "tulipan", "karafiat", "orchidej", "fialk", "konvalink", "sedmikrask", "pampelisk", "slunecnic", "hermanek", "kopriv", "levandul", "rozmaryn", "narcis"]
    },

    # KRAJINA, GEOGRAFIE A VESMÍR
    "priroda_krajina_hory": {
        "label": "Hory, údolí, skály a zemský povrch",
        "triggers": ["hora", "údolí", "skála", "kopec", "země"],
        "seeds": ["hora", "vrch", "kopec", "pahorek", "vrchol", "štít", "hřeben", "pohoří", "masiv", "údolí", "kotlina", "nížina", "rovina", "louka", "pastvina", "pole", "bažina", "močál", "rašeliniště", "poušť", "duna", "oáza", "tundra", "step", "savana", "džungle", "skála", "útes", "balvan", "jeskyně", "propast", "rokle", "kaňon", "hlína", "prach", "písek", "štěrk", "láva", "sopka", "kráter"],
        "stems": ["horsk", "pohori", "udol", "pastvin", "raselin", "poust", "savana", "dzungl", "jeskyn", "propast", "sopk"]
    },
    "priroda_voda_reky_more": {
        "label": "Řeky, jezera, moře a oceány",
        "triggers": ["řeka", "moře", "jezero", "potok", "oceán"],
        "seeds": ["řeka", "potok", "bystřina", "pramen", "studánka", "jezero", "rybník", "tůň", "nádrž", "přehrada", "vodopád", "moře", "oceán", "záliv", "zátoka", "průliv", "průplav", "kanál", "ostrov", "poloostrov", "mys", "pobřeží", "břeh", "pláž", "vlna", "příliv", "odliv", "proud", "peřej", "vír"],
        "stems": ["ricn", "bystrin", "studank", "prehrad", "vodopad", "morsk", "ocean", "zaliv", "zatok", "pruliv", "pobrezi"]
    },
    "priroda_pocasi_klima": {
        "label": "Počasí, podnebí a meteorologie",
        "triggers": ["déšť", "vítr", "sníh", "bouřka", "mráz"],
        "seeds": ["počasí", "klima", "podnebí", "teplota", "teplo", "horko", "chlad", "zima", "mráz", "vítr", "vánek", "vichřice", "vichr", "orkán", "tornádo", "hurikán", "bouře", "bouřka", "blesk", "hrom", "krupobití", "kroupa", "déšť", "liják", "mrholení", "rosa", "mlha", "opar", "smog", "mrak", "oblak", "obloha", "slunce", "sníh", "vločka", "vánice", "závěj", "led", "námraza", "jinovatka", "rampouch", "obleva"],
        "stems": ["pocas", "podneb", "vichric", "tornado", "hurikan", "bourk", "krupobit", "destiv", "lijak", "mrholen", "obloh", "vanic", "namraz", "jinovatk", "rampouch"]
    },
    "vesmir_astronomie": {
        "label": "Vesmír, hvězdy, planety a kosmos",
        "triggers": ["vesmír", "hvězda", "planeta", "měsíc", "kosmos", "raketa", "raketoplán"],
        "seeds": ["vesmír", "kosmos", "hvězda", "planeta", "měsíc", "slunce", "kometa", "asteroid", "meteorit", "meteor", "galaxie", "mlhovina", "souhvězdí", "orbita", "vakuum", "atmosféra", "gravitace", "záření", "zatmění", "teleskop", "dalekohled", "observatoř", "družice", "satelit", "raketa", "raketoplán", "kosmonaut", "kosmonautika", "kosmodrom", "modul", "sonda", "supernova", "pulsar", "astronom", "astrofyzik", "kvazar"],
        "stems": ["vesmir", "kosm", "hvezd", "planet", "komet", "asteroid", "meteorit", "galax", "mlhovin", "souhvezd", "observator", "satelit", "astronom", "raket"]
    },
    "chemie_mineraly_kovy": {
        "label": "Kovy, minerály, drahokamy a chemie",
        "triggers": ["kov", "železo", "zlato", "minerál", "chemie"],
        "seeds": ["kov", "ruda", "minerál", "nerost", "drahokam", "krystal", "zlato", "stříbro", "platina", "měď", "bronz", "mosaz", "železo", "ocel", "litina", "hliník", "dural", "cín", "olovo", "zinek", "nikl", "chrom", "titan", "wolfram", "rtuť", "uran", "křemík", "uhlík", "grafit", "diamant", "rubín", "safír", "smaragd", "křemen", "křišťál", "žula", "čedič", "pískovec", "vápenec", "mramor", "sádrovec", "křída", "uhlí", "nafta", "ropa", "kyselina", "zásada", "sloučenina", "amalgám", "prvek", "molekula", "atom", "draslík", "vápník", "kyslík", "dusík", "sodík", "hořčík", "fosfor"],
        "stems": ["kovov", "mineral", "drahokam", "krystal", "stribr", "platin", "mosaz", "zelez", "litin", "hlinik", "wolfram", "kremik", "diamant", "rubin", "safir", "smaragd", "kremen", "kristal", "vapenec", "mramor", "sloucenin", "draslik", "vapnik", "kyslik", "dusik", "sodik", "horcik"]
    },

    # TĚLO A MEDICÍNA
    "telo_anatomie_vnejsi": {
        "label": "Lidské tělo, končetiny a hlava",
        "triggers": ["tělo", "hlava", "ruka", "noha", "prst"],
        "seeds": ["tělo", "hlava", "temeno", "zátylek", "čelo", "spánek", "tvář", "líce", "brada", "čelist", "ret", "ústa", "zub", "stolička", "dáseň", "jazyk", "patro", "krk", "hrdlo", "hrtan", "záda", "lopatka", "bedra", "rameno", "paže", "loket", "předloktí", "zápěstí", "ruka", "dlaň", "prst", "palec", "ukazovák", "prostředník", "prsteník", "malík", "hrudník", "hruď", "prso", "břicho", "pupík", "bok", "kyčel", "stehno", "koleno", "lýtko", "holeň", "kotník", "pata", "chodidlo", "noha", "vlas", "vous", "nehet", "kůže", "pokožka", "oko", "ucho", "nos", "biceps", "sval"],
        "stems": ["temen", "zatylk", "celo", "spank", "celist", "stolic", "dasen", "predlokt", "zapast", "hrudn", "kycel", "stehn", "kolen", "lytk", "holen", "kotnik", "chodidl", "pokozk"]
    },
    "telo_organy_vnitrni": {
        "label": "Vnitřní orgány, krev a kosti",
        "triggers": ["srdce", "mozek", "plíce", "kost", "krev"],
        "seeds": ["mozek", "srdce", "plíce", "játra", "ledvina", "žaludek", "střevo", "slinivka", "slezina", "žlučník", "céva", "tepna", "žíla", "krev", "plazma", "lymfa", "kost", "kloub", "šlacha", "sval", "nerv", "kostra", "lebka", "páteř", "obratel", "žebro", "pánev", "dřeň", "chrupavka", "tkáň", "tep", "puls"],
        "stems": ["mozk", "srdec", "plicn", "jatern", "ledvin", "zaludk", "strevn", "slinivk", "slezan", "tepn", "kostn", "kloubn", "slach", "pater", "obratl", "chrupavk"]
    },
    "zdravi_leky_lecba": {
        "label": "Léky, léčiva a ošetření",
        "triggers": ["lék", "léčba", "injekce", "operace", "obvaz"],
        "seeds": ["lék", "léčivo", "tableta", "tabletka", "pilulka", "kapsle", "tobolka", "čípek", "kapky", "kapka", "mast", "injekce", "vakcína", "očkování", "obvaz", "náplast", "dlaha", "sádra", "operace", "chirurgie", "narkóza", "stetoskop", "skalpel", "pinzeta", "terapie", "rehabilitace", "masáž", "globule", "ampule", "tinktura", "sirup", "roztok", "kapačka", "vitamín", "vitamin", "minerál", "doplněk", "antibiotikum", "pastilka", "vápník", "hořčík", "výživa", "recept"],
        "stems": ["leciv", "tablet", "pilulk", "kapsl", "tobolk", "cipek", "injekc", "vakcin", "ockovan", "naplast", "chirurg", "narkoz", "stetoskop", "skalpel", "tinktur", "vitamin", "mineral", "doplnek", "antibiot", "pastilk", "vapnik", "horcik"]
    },
    "zdravi_nemoci_poruchy": {
        "label": "Nemoci, infekce, příznaky a bolesti",
        "triggers": ["nemoc", "bolest", "zánět", "horečka", "chřipka"],
        "seeds": ["nemoc", "choroba", "infekce", "virus", "bakterie", "epidemie", "pandemie", "zánět", "horečka", "kašel", "rýma", "chřipka", "angína", "alergie", "astma", "ekzém", "cukrovka", "infarkt", "mrtvice", "nádor", "rakovina", "zlomenina", "rána", "zranění", "úraz", "bolest", "křeč", "nevolnost", "kóma", "otok", "vřed"],
        "stems": ["chorob", "infekc", "bakteri", "epidem", "zanet", "horeck", "kasel", "chripk", "alerg", "cukrovk", "infarkt", "mrtvic", "nador", "rakovin", "zlomenin"]
    },
    "zdravi_nemocnice_doktor": {
        "label": "Nemocnice, ordinace, lékaři a lékárny",
        "triggers": ["nemocnice", "lékař", "ordinace", "lékárna", "doktor"],
        "seeds": ["nemocnice", "špitál", "poliklinika", "klinika", "ordinace", "ambulance", "sanatorium", "léčebna", "lázně", "lékárna", "laboratoř", "čekárna", "lůžko", "lékař", "doktor", "chirurg", "internista", "pediatr", "zubař", "dentista", "psychiatr", "neurolog", "primář", "sestra", "ošetřovatel", "záchranář", "pacient", "sanitka", "lékárník"],
        "stems": ["nemocnic", "poliklinik", "ordinac", "ambulanc", "lecebn", "lekarn", "zubarn", "psychiatr", "neurolog", "osetrovatel", "zachranar", "sanitk"]
    },

    # MONARCHIE A KLENOTY (VÍTĚZNÝ CLUSTER!)
    "monarchie_symboly_historie": {
        "label": "Monarchie, klenoty, trůn a symboly moci",
        "triggers": ["koruna", "král", "trůn", "žezlo", "císař"],
        "seeds": [
            "žezlo", "koruna", "trůn", "císař", "král", "královna", "císařovna", "princ", "princezna",
            "panovník", "monarchie", "království", "císařství", "kníže", "vévoda", "hrabě", "šlechtic",
            "šlechta", "rytíř", "diadém", "tiára", "klenot", "poklad", "insignie", "regálie", "erb",
            "znak", "pečeť", "prapor", "standarta", "dynastie", "rodokmen", "titul", "řád", "vyznamenání",
            "medaile", "korunovace", "majestát", "hrad", "zámek", "palác", "korunka"
        ],
        "stems": ["zezlo", "panovnik", "monarch", "kralov", "cisar", "diadem", "tiar", "insign", "regali", "korunovac", "majestat"]
    },

    # SPOLEČENSKÉ AKCE A KONFERENCE (MEGA-SLOVO CLUSTER!)
    "akce_konference_zasedani": {
        "label": "Konference, kongresy, zasedání a porady",
        "triggers": ["událost", "konference", "kongres", "zasedání", "sympozium", "schůze"],
        "seeds": [
            "sympozium", "konference", "kongres", "kolokvium", "seminář", "workshop", "zasedání",
            "schůze", "porada", "sněm", "sjezd", "shromáždění", "summit", "přednáška", "referát",
            "prezentace", "fórum", "mítink", "debata", "diskuze", "beseda", "plénum", "audience",
            "usnesení", "rezoluce", "delegace", "delegát", "auditorium", "panelista", "moderátor",
            "řečník", "projev", "program", "agenda", "událost"
        ],
        "stems": ["sympoz", "konferen", "kongres", "kolokvi", "seminar", "zasedan", "schuz", "summit", "plenum", "audienc"]
    },
    "akce_slavnosti_ceremonie": {
        "label": "Slavnosti, oslavy, obřady a plesy",
        "triggers": ["slavnost", "oslava", "obřad", "ples", "svatba"],
        "seeds": ["slavnost", "ceremonie", "obřad", "rituál", "oslava", "večírek", "párty", "mejdan", "bál", "ples", "karneval", "festival", "hody", "posvícení", "jarmark", "veletrh", "hostina", "banket", "raut", "recepce", "křtiny", "svatba", "jubileum", "výročí", "vernisáž", "křest", "masopust", "veselka"],
        "stems": ["slavnost", "ceremon", "obrad", "ritual", "karneval", "festival", "posvicen", "veletrh", "vernisaz", "svateb"]
    },

    # VZDĚLÁVÁNÍ A VĚDA
    "vzdelavani_skola_akademie": {
        "label": "Školy, univerzity a akademické studium",
        "triggers": ["škola", "univerzita", "student", "učitel", "výuka"],
        "seeds": ["škola", "gymnázium", "lyceum", "univerzita", "fakulta", "akademie", "rektorát", "děkanát", "katedra", "ústav", "knihovna", "studovna", "učebna", "třída", "posluchárna", "aula", "kolej", "menza", "studium", "výuka", "kurz", "zkouška", "test", "písemka", "maturita", "státnice", "zápočet", "diplom", "certifikát", "titul", "bakalář", "magistr", "inženýr", "profesor", "docent", "student", "absolvent", "pedagog", "školník"],
        "stems": ["skoln", "gymnaz", "lyceum", "univerzit", "fakult", "akademi", "rektorat", "poslucharn", "maturit", "statnic", "pedagog"]
    },
    "veda_vyzkum_obory": {
        "label": "Vědecký výzkum, teorie a objevy",
        "triggers": ["věda", "výzkum", "teorie", "objev", "experiment"],
        "seeds": ["věda", "výzkum", "bádání", "teorie", "hypotéza", "experiment", "pokus", "objev", "vynález", "inovace", "patent", "analýza", "syntéza", "simulace", "metoda", "vzorek", "laboratoř", "mikroskop", "publikace", "studie", "disertace", "monografie", "sborník", "citace", "vědec", "badatel", "fyzik", "biolog", "geolog", "chemik", "matematik"],
        "stems": ["vyzkum", "badatel", "hypotez", "experiment", "analyz", "syntenz", "laborator", "mikroskop", "disertac", "monograf"]
    },
    "filozofie_mysleni_vira": {
        "label": "Filozofie, etika, myšlení a víra",
        "triggers": ["filozofie", "myšlenka", "víra", "bůh", "náboženství"],
        "seeds": ["filozofie", "myšlenka", "rozum", "logika", "moudrost", "pravda", "morálka", "etika", "bůh", "víra", "náboženství", "církev", "kostel", "modlitba", "kněz", "biskup", "papež", "mnich", "klášter", "duše", "duch", "hřích", "spása", "ráj", "peklo", "dogma", "oltář", "bible"],
        "stems": ["filozof", "moralk", "nabozenstv", "cirkevn", "modlitb", "biskup", "papez", "klaster", "hrich", "oltar", "bibl"]
    },

    # STÁT, POLITIKA A PRÁVO
    "politika_stat_sprava": {
        "label": "Státní správa, vláda a politika",
        "triggers": ["vláda", "stát", "parlament", "prezident", "ministr"],
        "seeds": ["republika", "stát", "národ", "území", "kraj", "okres", "město", "obec", "vláda", "kabinet", "parlament", "sněmovna", "senát", "radnice", "magistrát", "ministerstvo", "úřad", "ambasáda", "prezident", "premiér", "ministr", "poslanec", "senátor", "starosta", "hejtman", "primátor", "diplomat", "velvyslanec", "volby", "referendum", "koalice", "opozice", "strana", "politik"],
        "stems": ["republik", "parlament", "snemovn", "senat", "radnic", "magistrat", "ministerstv", "prezident", "premier", "poslanec", "senator", "velvyslan"]
    },
    "pravo_soud_zakony": {
        "label": "Právo, soudnictví a spravedlnost",
        "triggers": ["soud", "zákon", "právo", "spravedlnost", "trest"],
        "seeds": ["právo", "spravedlnost", "zákon", "zákoník", "ústava", "norma", "předpis", "vyhláška", "nařízení", "smlouva", "paragraf", "článek", "vina", "nevina", "soud", "tribunál", "líčení", "proces", "žaloba", "obžaloba", "obhajoba", "odvolání", "rozsudek", "verdikt", "trest", "pokuta", "vězení", "amnestie", "důkaz", "svědectví", "výslech", "přiznání", "alibi", "zločin", "soudce", "státní zástupce", "advokát", "notář", "svědek"],
        "stems": ["spravedln", "zakonik", "ustav", "vyhlask", "paragraf", "tribunal", "zalob", "obzalob", "rozsudek", "advokat", "notar"]
    },
    "bezpecnost_policie_vojsko": {
        "label": "Policie, armáda a bezpečnost",
        "triggers": ["policie", "voják", "armáda", "zbraň", "válka"],
        "seeds": ["policie", "hlídka", "strážník", "detektiv", "vyšetřovatel", "komisař", "pouta", "obušek", "pistole", "maják", "siréna", "služebna", "cela", "věznice", "kriminál", "dozorce", "zatykač", "armáda", "vojsko", "voják", "důstojník", "generál", "kapitán", "velitel", "válka", "bitva", "boj", "útok", "obrana", "příměří", "mír", "fronta", "zbraň", "puška", "samopal", "kulomet", "dělo", "granát", "bomba", "raketa", "tank"],
        "stems": ["polic", "straznik", "detektiv", "vysetrovatel", "pouta", "pistol", "kriminal", "vojsk", "dustojnik", "general", "samopal", "kulomet"]
    },

    # EKONOMIKA A OBCHOD
    "finance_penize_banky": {
        "label": "Finance, bankovnictví a měna",
        "triggers": ["peníze", "banka", "finance", "měna", "úrok"],
        "seeds": ["měna", "platidlo", "hotovost", "peníz", "koruna", "euro", "dolar", "libra", "mince", "bankovka", "šek", "směnka", "akcie", "dluhopis", "dividenda", "kapitál", "majetek", "bohatství", "finance", "rozpočet", "schodek", "deficit", "přebytek", "zisk", "tržba", "příjem", "výdaj", "náklad", "cena", "hodnota", "kurz", "úrok", "inflace", "investice", "vklad", "úspora", "konto", "účet", "fond", "úvěr", "půjčka", "hypotéka", "dluh", "banka", "spořitelna", "burza", "pokladna", "bankomat"],
        "stems": ["platidl", "bankovk", "dluhopis", "dividend", "kapital", "bohatstv", "rozpocet", "investic", "hypotek", "sporiteln", "bankomat"]
    },
    "obchod_trh_nakup": {
        "label": "Obchod, trh, nákup a zboží",
        "triggers": ["obchod", "prodej", "nákup", "trh", "zboží"],
        "seeds": ["obchod", "prodejna", "supermarket", "stánek", "trh", "tržiště", "aukce", "dražba", "prodej", "nákup", "košík", "pult", "účtenka", "sleva", "akce", "výprodej", "reklamace", "záruka", "zboží", "produkt", "výrobek", "zásilka", "balík", "krabice", "obal", "zákazník", "klient", "prodavač", "dodavatel", "odběratel", "sklad", "zásoba", "export", "import", "clo"],
        "stems": ["prodejn", "supermarket", "trzist", "drazb", "uctenk", "vyprodej", "reklamac", "zakaznik", "dodavatel", "odberatel"]
    },

    # DOPRAVA
    "doprava_silnice_auta": {
        "label": "Automobily a silniční doprava",
        "triggers": ["auto", "silnice", "řidič", "motor", "doprava", "vozidlo"],
        "seeds": ["auto", "automobil", "náklaďák", "kamion", "cisterna", "dodávka", "autobus", "trolejbus", "tramvaj", "motorka", "motocykl", "skútr", "kolo", "bicykl", "koloběžka", "traktor", "bagr", "sanitka", "taxík", "přívěs", "silnice", "dálnice", "cesta", "ulice", "křižovatka", "most", "tunel", "parkoviště", "benzínka", "volant", "pedál", "brzda", "motor", "výfuk", "karoserie", "kapota", "blatník", "nárazník", "kufr", "pneumatika", "benzín", "nafta", "vozidlo", "doprava"],
        "stems": ["automobil", "nakladak", "kamion", "trolejbus", "motocykl", "kolobezk", "traktor", "dalnic", "krizovatk", "parkovist", "pneumatik"]
    },
    "doprava_koleje_vlaky": {
        "label": "Vlaky, železnice a nádraží",
        "triggers": ["vlak", "nádraží", "kolej", "železnice", "lokomotiva", "vozidlo"],
        "seeds": ["vlak", "lokomotiva", "souprava", "rychlík", "vagon", "železnice", "trať", "kolej", "kolejnice", "výhybka", "přejezd", "nástupiště", "nádraží", "stanice", "jízdenka", "peron", "drezína", "vozidlo", "doprava"],
        "stems": ["lokomotiv", "souprav", "rychlik", "zeleznic", "kolejnic", "vyhybk", "nastupist", "nadraz"]
    },
    "doprava_letectvi_kosmonautika": {
        "label": "Letadla, vrtulníky, letectví a kosmonautika",
        "triggers": ["letadlo", "letiště", "pilot", "vrtulník", "letenka", "raketa", "raketoplán", "kosmonaut", "vozidlo"],
        "seeds": ["letadlo", "letoun", "tryskáč", "vrtulník", "helikoptéra", "balón", "křídlo", "vrtule", "letiště", "hangár", "padák", "pilot", "letuška", "letenka", "odlet", "přílet", "paluba", "raketoplán", "raketa", "stíhačka", "kosmonaut", "kosmonautika", "kosmodrom", "družice", "satelit", "sonda", "modul", "kapsle", "kluzák", "letka", "aeroplán", "vznášedlo", "rotor", "trup", "pohon", "stroj", "turbína", "avionika", "start", "přistání", "kosmoloď", "raketonosič", "vozidlo", "doprava"],
        "stems": ["letadl", "letoun", "tryskac", "vrtulnik", "helikopter", "letist", "hangar", "letusk", "letenk", "raket", "kosmo", "stihac", "kluzak", "aeroplan", "vznasedl"]
    },
    "doprava_vodni_lode": {
        "label": "Lodě, plavba a přístavy",
        "triggers": ["loď", "přístav", "člun", "paluba", "plachetnice", "vozidlo"],
        "seeds": ["loď", "lodička", "člun", "kanoe", "kajak", "vor", "plachetnice", "jachta", "parník", "trajekt", "přístav", "dok", "molo", "maják", "paluba", "kajuta", "pádlo", "veslo", "kormidlo", "kotva", "plachta", "plavidlo", "vozidlo", "doprava"],
        "stems": ["lodick", "plachetnic", "jacht", "parnik", "trajekt", "pristav", "kajut", "kormidl"]
    },

    # TECHNIKA A NÁSTROJE
    "technika_naradi_dilna": {
        "label": "Dílna, nářadí a nástroje",
        "triggers": ["kladivo", "šroubovák", "pila", "kleště", "nářadí"],
        "seeds": ["nářadí", "nástroj", "kladivo", "sekera", "pila", "hoblík", "dláto", "pilník", "šroubovák", "klíč", "kleště", "hasák", "svěrák", "svorka", "metr", "pravítko", "vodováha", "šroub", "vrut", "matice", "podložka", "hřebík", "hmoždinka", "nýt", "lepidlo", "vrtačka", "bruska", "flexa", "svářečka", "dílna", "fréza"],
        "stems": ["naradi", "kladiv", "seker", "hoblik", "dlato", "pilnik", "sroubovak", "kleste", "hasak", "sverak", "vrtack", "brusk", "svareck"]
    },
    "technika_pocitace_it": {
        "label": "Počítače, elektronika a software",
        "triggers": ["počítač", "telefon", "internet", "program", "displej", "technologie"],
        "seeds": ["počítač", "notebook", "laptop", "tablet", "mobil", "telefon", "monitor", "displej", "obrazovka", "klávesnice", "myš", "tiskárna", "skener", "reproduktor", "sluchátka", "mikrofon", "kamera", "fotoaparát", "disk", "procesor", "čip", "kabel", "nabíječka", "baterie", "program", "aplikace", "software", "soubor", "data", "kód", "systém", "internet", "web", "server", "síť", "heslo", "účet", "prohlížeč", "algoritmus", "technologie"],
        "stems": ["pocitac", "notebook", "displej", "obrazovk", "klavesnic", "tiskarn", "reproduktor", "sluchatk", "mikrofon", "fotoaparat", "procesor", "aplikac", "softwar", "algoritm"]
    },

    # BYDLENÍ A STAVBA
    "stavba_dum_architektura": {
        "label": "Stavby, domy a architektura",
        "triggers": ["dům", "budova", "stavba", "kostel", "hrad"],
        "seeds": ["dům", "budova", "stavba", "chalupa", "chata", "panelák", "činžák", "vila", "mrakodrap", "palác", "zámek", "hrad", "tvrz", "pevnost", "kostel", "chrám", "katedrála", "klášter", "pomník", "hrobka", "hráz", "přehrada", "věž", "rozhledna", "stadion", "hala", "sklad", "garáž", "zeď", "stěna", "střecha", "okno", "dveře", "komín", "cihla", "beton", "malta", "omítka", "architektura"],
        "stems": ["stavb", "chalup", "panelak", "cinzak", "mrakodrap", "katedral", "rozhledn", "architektur"]
    },
    "domov_nabytek_vybaveni": {
        "label": "Nábytek, místnosti a vybavení bytu",
        "triggers": ["stůl", "židle", "postel", "skříň", "pokoj"],
        "seeds": ["byt", "místnost", "pokoj", "obývák", "ložnice", "kuchyně", "jídelna", "koupelna", "toaleta", "předsíň", "chodba", "schodiště", "sklep", "půda", "balkon", "terasa", "zahrada", "nábytek", "stůl", "stolek", "židle", "křeslo", "sedačka", "pohovka", "postel", "lůžko", "matrace", "skříň", "komoda", "police", "zrcadlo", "koberec", "záclona", "závěs", "lampa", "lustr", "lednička", "pračka", "sporák", "trouba", "vana", "sprcha", "umyvadlo"],
        "stems": ["mistnost", "loznoc", "koupeln", "toalet", "predsin", "schodist", "nabytek", "sedack", "pohovk", "matrac", "komod", "koberec", "lednick", "prack", "umyvadl"]
    },

    # SPORT
    "sport_hry_souteze": {
        "label": "Sport, míčové hry a turnaje",
        "triggers": ["sport", "fotbal", "hokej", "zápas", "turnaj"],
        "seeds": ["sport", "fotbal", "hokej", "basketbal", "volejbal", "házená", "tenis", "golf", "atletika", "plavání", "lyžování", "snowboarding", "cyklistika", "box", "judo", "šachy", "zápas", "utkání", "turnaj", "mistrovství", "šampionát", "olympiáda", "liga", "pohár", "soutěž", "závod", "běh", "maraton", "skok", "míč", "balon", "puk", "hokejka", "raketa", "branka", "dres", "kopačky", "trenér", "rozhodčí", "hráč", "sportovec", "vítěz", "stadion", "biatlon", "futsal", "squash"],
        "stems": ["sport", "fotbal", "hokej", "basketbal", "volejbal", "hazena", "cyklistik", "turnaj", "mistrovstv", "sampionat", "olympiad", "sportov", "stadion", "biatlon"]
    },

    # KULTURA A UMĚNÍ
    "kultura_hudba_nastroje": {
        "label": "Hudba, hudební nástroje a tóny",
        "triggers": ["hudba", "nástroj", "kytara", "klavír", "píseň"],
        "seeds": ["hudba", "nástroj", "housle", "viola", "violoncello", "kontrabas", "kytara", "harfa", "mandolína", "flétna", "klarinet", "hoboj", "fagot", "saxofon", "trubka", "pozoun", "trombon", "lesní roh", "tuba", "harmonika", "akordeon", "buben", "kotel", "činel", "triangl", "gong", "zvon", "xylofon", "klavír", "pianino", "varhany", "tón", "nota", "akord", "rytmus", "zpěv", "hlas", "orchestr", "kapela", "píseň", "skladatel", "koncert"],
        "stems": ["hudeb", "muzik", "housl", "violoncell", "kontrabas", "kytar", "klarinet", "saxofon", "akordeon", "varhan", "orchestr", "skladatel"]
    },
    "kultura_literatura_divadlo_film": {
        "label": "Literatura, divadlo, film a knihy",
        "triggers": ["kniha", "film", "divadlo", "umění", "obraz"],
        "seeds": ["umění", "kniha", "román", "povídka", "báseň", "poezie", "próza", "drama", "divadlo", "herec", "herečka", "režisér", "scénář", "jeviště", "opona", "kulisa", "kostým", "kino", "film", "kamera", "premiéra", "obraz", "malba", "kresba", "socha", "plastika", "ateliér", "plátno", "štětec", "barva", "galerie", "muzeum", "výstava", "spisovatel", "básník", "autor", "novinář", "článek", "časopis", "deník", "zpráva", "reportáž", "sochař", "malíř"],
        "stems": ["literat", "divadel", "filmov", "reziser", "scenar", "spisovatel", "novinar", "galeri", "vystav", "sochar", "malir"]
    },

    # LIDÉ A SPOLEČNOST
    "lide_rodina_pribuzni": {
        "label": "Rodina a příbuzenstvo",
        "triggers": ["rodina", "otec", "matka", "syn", "dcera"],
        "seeds": ["rodina", "rodič", "otec", "táta", "tatínek", "matka", "máma", "maminka", "syn", "synek", "dcera", "dcerka", "dítě", "miminko", "chlapec", "kluk", "dívka", "holka", "bratr", "sestra", "sourozenec", "dvojče", "dědeček", "děda", "babička", "vnuk", "vnučka", "strýc", "teta", "bratranec", "sestřenice", "synovec", "neteř", "tchán", "tchyně", "zeť", "snacha", "švagr", "kmotr", "sirotek", "vdovec", "vdova", "manžel", "manželka", "snoubenec", "ženich", "nevěsta", "partner"],
        "stems": ["rodinn", "rodic", "tatinek", "mamink", "sourozen", "dedecek", "babick", "bratran", "sestrenic", "synovec", "manzel", "snouben"]
    },
    "lide_profese_remesla": {
        "label": "Profese, řemesla a zaměstnání",
        "triggers": ["dělník", "zedník", "kovář", "kuchař", "řidič"],
        "seeds": ["řemeslník", "dělník", "mistr", "učeň", "zedník", "tesař", "truhlář", "klempíř", "instalatér", "elektrikář", "zámečník", "kovář", "svářeč", "soustružník", "mechanik", "opravář", "hodinář", "zlatník", "šperkař", "sklář", "kameník", "švec", "obuvník", "krejčí", "švadlena", "pekař", "cukrář", "řezník", "kuchař", "číšník", "barman", "hostinský", "řidič", "šofér", "pošťák", "hasič", "zahradník", "horník", "rolník"],
        "stems": ["remesln", "zednik", "truhlar", "klempir", "instalater", "elektrikar", "zamecnik", "kovar", "svarec", "mechanik", "hodinar", "zlatnik", "obuvnik", "svadlen"]
    },

    # OBLEČENÍ A MÓDA
    "obleceni_moda_doplnky": {
        "label": "Oblečení, obuv, móda a doplňky",
        "triggers": ["oblečení", "šaty", "kalhoty", "bota", "kabát"],
        "seeds": ["oblečení", "oděv", "šaty", "kostým", "oblek", "sako", "kabát", "bunda", "plášť", "kožich", "svetr", "mikina", "košile", "halenka", "tričko", "tílko", "kalhoty", "džíny", "kraťasy", "sukně", "šortky", "pyžamo", "župan", "prádlo", "ponožky", "punčochy", "plavky", "bota", "střevíc", "polobotka", "teniska", "sandál", "kozačka", "holínka", "pantofel", "klobouk", "čepice", "šátek", "šála", "kravata", "rukavice", "pásek", "taška", "kabelka", "batoh", "peněženka", "kufr", "šperk", "prsten", "náramek", "řetízek", "náušnice", "hodinky"],
        "stems": ["oblecen", "kostym", "kalhot", "halenk", "ponozk", "puncoch", "polobotk", "tenisk", "sandalt", "kozack", "holink", "pantofl", "klobouk", "rukavic", "kabelk", "naramk", "nausnic"]
    },

    # MYŠLENÍ, JAZYK A EMOCE
    "mysl_jazyk_emoce": {
        "label": "Myšlení, emoce, pocity a komunikace",
        "triggers": ["myšlenka", "pocit", "slovo", "láska", "radost"],
        "seeds": ["myšlenka", "nápad", "úvaha", "názor", "postoj", "přesvědčení", "víra", "vědomí", "paměť", "rozum", "inteligence", "logika", "cit", "emoce", "pocit", "nálada", "radost", "štěstí", "láska", "smutek", "žal", "strach", "obava", "hněv", "zlost", "vztek", "naděje", "odvaha", "slovo", "věta", "výraz", "pojem", "termín", "jazyk", "řeč", "hlas", "rozhovor", "dialog", "pravda", "lež", "tajemství", "zpráva", "dohoda", "slib", "omluva"],
        "stems": ["myslenk", "inteligenc", "emoc", "pocit", "smutek", "odvah", "vyraz", "rozhovor", "tajemstv"]
    }
}

ANCHOR_DOMAINS_MAP = {
    "vozidlo": ["doprava_silnice_auta", "doprava_koleje_vlaky", "doprava_letectvi_kosmonautika", "doprava_vodni_lode"],
    "doprava": ["doprava_silnice_auta", "doprava_koleje_vlaky", "doprava_letectvi_kosmonautika", "doprava_vodni_lode"],
    "technologie": ["technika_pocitace_it", "technika_naradi_dilna", "doprava_letectvi_kosmonautika", "veda_vyzkum_obory"],
    "jídlo": ["jidlo_pecivo_mouka", "jidlo_ovoce_plody", "jidlo_zelenina_houby", "jidlo_maso_uzeniny", "jidlo_mlecne_syry", "jidlo_sladkosti_cukrovinky", "jidlo_napoje_alkohol", "jidlo_vareni_koreni"],
    "zvíře": ["priroda_savci_domaci", "priroda_savci_divoci", "priroda_savci_exoticti", "priroda_ptaci", "priroda_vodni_zivocisi", "priroda_hmyz"],
    "příroda": ["priroda_stromy_les", "priroda_rostliny_kvety", "priroda_krajina_hory", "priroda_voda_reky_more", "priroda_pocasi_klima", "vesmir_astronomie"],
    "dřevo": ["priroda_stromy_les", "domov_nabytek_vybaveni", "technika_naradi_dilna", "stavba_dum_architektura"],
    "čas": ["priroda_pocasi_klima", "akce_konference_zasedani", "mysl_jazyk_emoce"],
    "práce": ["lide_profese_remesla", "obchod_trh_nakup", "akce_konference_zasedani"],
    "zdraví": ["zdravi_leky_lecba", "zdravi_nemoci_poruchy", "zdravi_nemocnice_doktor", "telo_anatomie_vnejsi", "telo_organy_vnitrni"],
    "člověk": ["lide_rodina_pribuzni", "lide_profese_remesla", "telo_anatomie_vnejsi"],
    "kov": ["chemie_mineraly_kovy", "technika_naradi_dilna"],
    "věda": ["veda_vyzkum_obory", "chemie_mineraly_kovy", "vesmir_astronomie"],
    "hudba": ["kultura_hudba_nastroje"],
    "stavba": ["stavba_dum_architektura", "domov_nabytek_vybaveni"],
    "oblečení": ["obleceni_moda_doplnky"],
    "sport": ["sport_hry_souteze"],
    "umění": ["kultura_literatura_divadlo_film"],
    "obchod": ["obchod_trh_nakup", "finance_penize_banky"],
    "právo": ["pravo_soud_zakony", "politika_stat_sprava"],
    "rodina": ["lide_rodina_pribuzni"],
    "škola": ["vzdelavani_skola_akademie"],
}

domain_words = {k: set() for k in DOMAINS}

# 1. EXACT SEEDS & TRIGGERS (Guaranteed core words in each domain)
for d_key, d_info in DOMAINS.items():
    for w in d_info.get("seeds", []) + d_info.get("triggers", []):
        if w in VOCAB_SET:
            domain_words[d_key].add(w)

# Map anchors to their respective domain clusters
for anchor, target_domains in ANCHOR_DOMAINS_MAP.items():
    if anchor in VOCAB_SET:
        for t_dom in target_domains:
            if t_dom in DOMAINS:
                domain_words[t_dom].add(anchor)

# 2. CAREFUL PREFIX-ONLY STEM MATCHING (No arbitrary substrings!)
for d_key, d_info in DOMAINS.items():
    stems = [norm_cz(s) for s in d_info.get("stems", []) if len(norm_cz(s)) >= 4]
    for word, norm_w in NORM_VOCAB.items():
        # Match only prefix with stem length >= 4
        if any(norm_w.startswith(s) for s in stems):
            # Zrušen nesmyslný limit 150 slov, pokud slovo odpovídá kmenu, vezmeme ho!
            domain_words[d_key].add(word)

# Build clean final domains
final_domains = {}
all_clustered = set()

for d_key, d_info in DOMAINS.items():
    words_list = sorted(list(domain_words[d_key]))
    valid_triggers = [t for t in d_info.get("triggers", []) if t in VOCAB_SET]
    final_domains[d_key] = {
        "label": d_info["label"],
        "triggers": valid_triggers,
        "words": words_list
    }
    all_clustered.update(words_list)

final_data = {
    "anchors": ANCHORS,
    "domains": final_domains
}

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(final_data, f, ensure_ascii=False, indent=2)

print("=" * 60)
print(f"Successfully generated high-precision clusters at {OUTPUT_FILE}")
print(f"Total Anchors: {len(ANCHORS)}")
print(f"Total Focused Domains: {len(final_domains)}")
print(f"Total High-Precision Clustered Words: {len(all_clustered)}")
print(f"Average cluster size: {len(all_clustered) / len(final_domains):.1f} words")
print("Top 5 largest domains:")
for k, v in sorted(final_domains.items(), key=lambda x: len(x[1]["words"]), reverse=True)[:5]:
    print(f" - {v['label']}: {len(v['words'])} words")
print("=" * 60)
