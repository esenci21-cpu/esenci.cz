"""
Build bewit-urls.json by matching PDF product names to bewit.love URLs.
The PDFs contain ONLY internal navigation links (GoTo), not external URLs.
This script matches product names from PDF bookmarks to URLs scraped from bewit.love.
"""

import json
import glob
import unicodedata
from pathlib import Path
from pypdf import PdfReader
from pypdf.generic import DictionaryObject

AFFILIATE_PARAM = "?i=3fqlzp0xrllj7"
BASE_URL = "https://bewit.love/produkt/"

# Complete slug->canonical_name mapping built from bewit.love category pages
SLUG_TO_NAME = {
    # Single oils - page 1
    "acacia-esencialni-olej": "Akácie",
    "aksamitnik-rozkladity-esencialni-olej": "Aksamitník rozkladitý",
    "bewit-aksamitnik-zpereny-esencialni-olej": "Aksamitník zpeřený",
    "alpinia-esencialni-olej": "Alpinie",
    "amyris-esencialni-olej": "Amyris",
    "andelika-esencialni-olej": "Andělika, kořen",
    "anyz-esencialni-olej": "Anýz",
    "badyan-pravy-esencialni-olej": "Badyán pravý",
    "bay-st.-thomas-esencialni-olej": "Bay St. Thomas",
    "bazalka-kafrova-esencialni-olej": "Bazalka kafrová",
    "bazalka-posvatna-esencialni-olej": "Bazalka posvátná",
    "bazalka-esencialni-olej": "Bazalka pravá",
    "benzoin-absolue-esencialni-olej": "Benzoin",
    "bergamot-esencialni-olej": "Bergamot RAW",
    "bergamot-sun-esencialni-olej": "Bergamot SUN",
    "blue-tansy-esencialni-olej": "Blue tansy - Vratič",
    "borovice-banksova-bio": "Borovice Banksova BIO",
    "bewit-borovice-lesni-bio-esencialni-olej": "Borovice lesní BIO",
    "borovice-lesni-esencialni-olej": "Borovice lesní",
    "borovice-smolna": "Borovice smolná",
    "borovice-sumaterska-esencialni-olej": "Borovice sumaterská",
    "borovice-vejmutovka-bio-esencialni-olej": "Borovice vejmutovka BIO",
    "calamus-esencialni-olej": "Calamus",
    "cedr-atlasky-esencialni-olej": "Cedr atlaský",
    "cedr-himalajsky-esencialni-olej": "Cedr himalájský",
    "celer-semena-esencialni-olej": "Celer, semena",
    "garlic-esencialni-olej": "Česnek",
    "chmel-esencialni-olej": "Chmel",
    "lemon-sun-esencialni-olej": "Citron SUN",
    "bewit-citron-bio-raw-esencialni-olej": "Citron, BIO RAW",
    "citron-destilovany-esencialni-olej": "Citron, destilovaný",
    "citron-esencialni-olej": "Citron, RAW",
    "citronela-esencialni-olej": "Citronela",
    "citronova-trava-esencialni-olej": "Citrónová tráva",
    "cubeb-esencialni-olej": "Cubeb",
    "cypriol-esencialni-olej": "Cypriol",
    "bewit-cypris-stalezeleny-esencialni-olej": "Cypřiš BIO",
    "cypris1-esencialni-olej": "Cypřiš",
    "drmek-esencialni-olej": "Drmek",
    "elemi-esencialni-olej": "Elemi",
    # page 2
    "eukalyptus-blue-esencialni-olej": "Eukalyptus Blue",
    "eukalyptus-camaldulensis-esencialni-olej": "Eukalyptus Camaldulensis",
    "eukalyptus-citriodora-esencialni-olej": "Eukalyptus Citriodora",
    "bewit-blahovicnik-kulatoplody-bio-esencialni-olej": "Eukalyptus Globulus BIO",
    "eukalyptus-esencialni-olej": "Eukalyptus Globulus",
    "eukalyptus-radiata-esencialni-olej": "Eukalyptus Radiata",
    "eukalyptus-staigeriana-esencialni-olej": "Eukalyptus Staigeriana",
    "fenykl-esencialni-olej": "Fenykl",
    "fenykl-co2-esencialni-olej": "Fenykl RAW, CO2",
    "bewit-fenykl-obecny-esencialni-olej": "Fenykl sladký BIO",
    "galbanum-esencialni-olej": "Galbanum",
    "galangal-esencialni-olej": "Galgán",
    "geranium-bourbon-esencialni-olej": "Geránium Bourbon",
    "geranie-esencialni-olej": "Geránium",
    "ginger-lily-esencialni-olej": "Ginger Lily",
    "white-grapefruit-esencialni-olej": "Grapefruit bílý",
    "pink-grapefruit-esencialni-olej": "Grapefruit růžový",
    "bewit-grapefruit-sun-esencialni-olej": "Grapefruit SUN",
    "gurjun-balsam-esencialni-olej": "Gurjum Balsam",
    "bewit-hermanek-pravy-bio-esencialni-olej": "Heřmánek pravý BIO",
    "hermanek-pravy-esencialni-olej": "Heřmánek pravý",
    "bewit-hinoki-esencialni-olej": "Hinoki",
    "clove-esencialni-olej": "Hřebíček, list",
    "clove-bud-esencialni-olej": "Hřebíček, pupen",
    "iary-esencialni-olej": "Iary",
    "ibiskovec-pizmovy-esencialni-olej": "Ibiškovec pižmový",
    "cade-esencialni-olej": "Jalovec Cade",
    "jalovec-leaf-esencialni-olej": "Jalovec, list",
    "jalovec-esencialni-olej": "Jalovec, plod",
    "jasmine-absolue-esencialni-olej": "Jasmín",
    "jedle-balzamova-esencialni-olej": "Jedle balzámová",
    "jedle-balzamova-jehlici-bio-esencialni-olej": "Jedle balzámová, jehličí BIO",
    "jedle-balzamova-kura-bio-esencialni-olej": "Jedle balzámová, kůra BIO",
    "jedle-sibirska-jehlici-esencialni-olej": "Jedle sibiřská, jehličí",
    "frankincense-carterii-esencialni-olej": "Kadidlo Carterii",
    "frankincense-frereana-esencialni-olej": "Kadidlo Frereana",
    "boswellia-sacra-esencialni-olej": "Kadidlo Sacra",
    "kadidlo-esencialni-olej": "Kadidlo Serrata",
    "kafr-esencialni-olej": "Kafr",
    "kaffir-lime-esencialni-olej": "Kafrová limetka",
    # page 3
    "kajeput-esencialni-olej": "Kajeput bělodřevý",
    "cananga-esencialni-olej": "Kananga",
    "bewit-kanuka-esencialni-olej": "Kanuka",
    "kardamom-cerny-esencialni-olej": "Kardamom černý",
    "kardamom-esencialni-olej": "Kardamom zelený",
    "kardamom-raw-esencialni-olej": "Kardamom zelený RAW, CO2",
    "bewit-katrafay-esencialni-olej": "Katrafay",
    "kewra-esencialni-olej": "Kewra",
    "khella-esencialni-olej": "Khella",
    "clementina-esencialni-olej": "Klementinka",
    "bewit-klementinka-bio-raw-esencialni-olej": "Klementinka, BIO RAW",
    "ajowan-esencialni-olej": "Kmín koptský",
    "caraway-esencialni-olej": "Kmín kořenný",
    "kmin-esencialni-olej": "Kmín římský",
    "kopaiva-esencialni-olej": "Kopaiva",
    "palo-santo-esencialni-olej": "Kopál vonný - Palo Santo",
    "dill-seed-esencialni-olej": "Kopr, semena",
    "bewit-koriandr-sety-esencialni-olej": "Koriandr, list",
    "koriandr-esencialni-olej": "Koriandr, semena",
    "koriandr-co2-esencialni-olej": "Koriandr, semena RAW, CO2",
    "kozlik-esencialni-olej": "Kozlík",
    "kozlik-v-jojobe-esencialni-olej": "Kozlík v jojobě",
    "zedoary-esencialni-olej": "Kurkuma Zedoary",
    "turmeric-root-esencialni-olej": "Kurkuma, kořen",
    "turmeric-leaves-esencialni-olej": "Kurkuma, list",
    "labdanum-esencialni-olej": "Labdanum (cistus)",
    "lavandin-esencialni-olej": "Lavandin",
    "bewit-levandule-hybridni-bio-esencialni-olej": "Lavandin Super BIO",
    "levandule-esencialni-olej": "Levandule",
    "levandule-francie-esencialni-olej": "Levandule Francie",
    "levandule-kasmir-esencialni-olej": "Levandule Kašmír",
    "levandule-CO2-esencialni-olej": "Levandule RAW, CO2",
    "spike-lavender-esencialni-olej": "Levandule Spike",
    "bewit-levandule-bio-esencialni-olej": "Levandule, BIO",
    "libavka-esencialni-olej": "Libavka",
    "libora-meniva-esencialni-olej": "Libora měnivá",
    "limetka-esencialni-olej": "Limetka",
    "litsea-cubeba-esencialni-olej": "Litsea Cubeba",
    "pink-lotus-esencialni-olej": "Lotos růžový ABSOLUE",
    "majoranka-esencialni-olej": "Majoránka",
    # page 4
    "cervena-mandarinka-esencialni-olej": "Mandarinka červená",
    "zelena-mandarinka-esencialni-olej": "Mandarinka zelená",
    "zluta-mandarinka-esencialni-olej": "Mandarinka žlutá",
    "prunus-amygdalus-esencialni-olej": "Mandle, hořké",
    "manuka-esencialni-olej": "Manuka",
    "massoia-bark-esencialni-olej": "Massoia",
    "mastic-esencialni-olej": "Mastic",
    "bewit-mint-bergamot-esencialni-olej": "Máta citronová",
    "spearmint-esencialni-olej": "Máta klasnatá",
    "mata-peprna-esencialni-olej": "Máta peprná",
    "mata-rolni-esencialni-olej": "Máta rolní",
    "materidouskovec-vonny-esencialni-olej": "Mateřídouškovec vonný BIO",
    "melissa-esencialni-olej": "Meduňka",
    "mrkev-semena-esencialni-olej": "Mrkev, semena",
    "muskatovy-orisek-esencialni-olej": "Muškátový oříšek",
    "muskatovy-orisek-co2-esencialni-olej": "Muškátový oříšek RAW, CO2",
    "bewit-myrrh-confusa-esencialni-olej": "Myrha Confusa",
    "myrha-esencialni-olej": "Myrha",
    "bewit-myrrh-kataf-esencialni-olej": "Myrha Kataf",
    "bewit-myrrh-kua-esencialni-olej": "Myrha Kua",
    "myrta-esencialni-olej": "Myrta",
    "spikenard-esencialni-olej": "Nard",
    "nard-modry-esencialni-olej": "Nard modrý",
    "nard-zeleny-esencialni-olej": "Nard zelený",
    "neroli-esencialni-olej": "Neroli",
    "niaouli-esencialni-olej": "Niaouli",
    "nove-koreni-list-esencialni-olej": "Nové koření, list",
    "pimento-berry-esencialni-olej": "Nové koření, plod",
    "opoponax-esencialni-olej": "Opoponax (sladká myrha)",
    "dobromysl-esencialni-olej": "Oregano",
    "paculi-esencialni-olej": "Pačuli",
    "palmarosa-esencialni-olej": "Palmarosa",
    "pelynek-bily-esencialni-olej": "Pelyněk bílý",
    "pelynek-cernobyl-esencialni-olej": "Pelyněk černobýl, BIO",
    "pelynek-davana-esencialni-olej": "Pelyněk davana",
    "pelynek-estragon-esencialni-olej": "Pelyněk estragon",
    "pelynek-esencialni-olej": "Pelyněk roční",
    "pepr-bily-esencialni-olej": "Pepř bílý",
    "cerny-pepr-esencialni-olej": "Pepř černý",
    "pepr-ruzovy-esencialni-olej": "Pepř růžový",
    "cerveny-pomeranc-esencialni-olej": "Pomeranč červený RAW",
    # page 5
    "peprovnik-betelovy-esencialni-olej": "Pepřovník betelový",
    "parsley-seed-esencialni-olej": "Petržel, semena",
    "fenugreek1-esencialni-olej": "Pískavice řecké seno RAW CO2",
    "bewit-pomeranc-cerveny-esencialni-olej": "Pomeranč červený, BIO",
    "pomeranc-esencialni-olej": "Pomeranč",
    "orange-sun-esencialni-olej": "Pomeranč SUN",
    "ravensara-esencialni-olej": "Ravensara",
    "bewit-ravintsara-esencialni-olej": "Ravintsara",
    "blue-yarrow-esencialni-olej": "Řebříček modrý",
    "rmen-esencialni-olej": "Rmen (Heřmánek římský)",
    "rododendron-anthopogon-esencialni-olej": "Rododendron Anthopogon BIO",
    "rododendron-gronsky-bio-esencialni-olej": "Rododendron grónský BIO",
    "rozmaryn-esencialni-olej": "Rozmarýn",
    "rozmaryn-co2-esencialni-olej": "Rozmarýn RAW, CO2",
    "rue-esencialni-olej": "Rue",
    "rose-white-esencialni-olej": "Růže bílá",
    "rose-white-in-carrier-oil-esencialni-olej": "Růže bílá v MCT oleji",
    "rosa-damascena-absolue-esencialni-olej": "Růže damašská ABSOLUE",
    "rosa-damascena-absolue-in-mct-oil-esencialni-olej": "Růže damašská ABSOLUE v MCT oleji",
    "ruze-damasska-dvakrat-destilovana-esencialni-olej": "Růže damašská dvakrát destilovaná",
    "ruze-damasska-dvakrat-destilovana-v-mct-oleji-esencialni-olej": "Růže damašská dvakrát destilovaná v MCT oleji",
    "rosa-damascena-esencialni-olej": "Růže damašská",
    "ruze-damasska-jednou-destilovana-esencialni-olej": "Růže damašská jednou destilovaná",
    "ruze-damasska-jednou-destilovana-v-mct-oleji-esencialni-olej": "Růže damašská jednou destilovaná v MCT oleji",
    "rosa-damascena-in-jojoba-esencialni-olej": "Růže damašská v jojobě",
    "rosa-centifolia-esencialni-olej": "Růže stolistá",
    "ruze-v-MCT-oleji-esencialni-olej": "Růže stolistá v MCT oleji",
    "ruzove-drevo-esencialni-olej": "Růžové dřevo",
    "salvej-esencialni-olej": "Šalvěj muškátová",
    "sandalwood-esencialni-olej": "Santalové dřevo",
    "saro-esencialni-olej": "Saro",
    "savory-esencialni-olej": "Saturejka",
    "skorice-kura-esencialni-olej": "Skořice cejlonská, kůra",
    "skorice-list-esencialni-olej": "Skořice cejlonská, list",
    "kasie-esencialni-olej": "Skořice Kasie",
    "skorice-lawang-esencialni-olej": "Skořice Lawang",
    "bewit-smil-bracteiferum-esencialni-olej": "Smil Bracteiferum",
    "helichrysum-esencialni-olej": "Smil italský",
    "bewit-smil-rambiazina-esencialni-olej": "Smil Rambiazina",
    # page 6
    "bewit-smrk-cerny-esencialni-olej": "Smrk černý",
    "smrk-cerny-drevo-bio-esencialni-olej": "Smrk černý, dřevo BIO",
    "smrk-cerny-jehlici-bio": "Smrk černý, jehličí BIO",
    "smrk-cerny-kura-bio-esencialni-olej": "Smrk černý, kůra BIO",
    "smrk-sivy-bio": "Smrk sivý BIO",
    "smrk-esencialni-olej": "Smrk ztepilý",
    "sugandha-kokila-esencialni-olej": "Sugandha Kokila",
    "tea-tree-esencialni-olej": "Tea tree",
    "topol-balzamovy-bio-esencialni-olej": "Topol balzámový BIO",
    "arborvitae-esencialni-olej": "Túje (Arborvitae)",
    "tuje-esencialni-olej": "Túje",
    "tymian-borneol-esencialni-olej": "Tymián borneol",
    "tymian-horsky-esencialni-olej": "Tymián horský (Mateřídouška)",
    "tymian-esencialni-olej": "Tymián thymol",
    "bewit-tymian-obecny-bio-esencialni-olej": "Tymián, linalool BIO",
    "bio-tymian-obecny-esencialni-olej": "Tymián, thymol BIO",
    "vanilla-esencialni-olej": "Vanilka, CO2",
    "vavrin-esencialni-olej": "Vavřín",
    "vetiver-esencialni-olej": "Vetiver",
    "jamarosa-esencialni-olej": "Voňatka",
    "vresna-bahenni-bio": "Vřesna bahenní BIO",
    "ylang-ylang-esencialni-olej": "Ylang ylang",
    "bewit-ylang-ylang-extra-esencialni-olej": "Ylang ylang Extra",
    "bewit-yuzu-esencialni-olej": "Yuzu",
    "yzop-esencialni-olej": "Yzop",
    "zanthoxylum-esencialni-olej": "Zanthoxylum",
    "zazvor-cinsky-esencialni-olej": "Zázvor čínský",
    "zazvor-esencialni-olej": "Zázvor",
    "zazvor-co2-esencialni-olej": "Zázvor RAW, CO2",
    "gingergrass-esencialni-olej": "Zázvorová tráva",
    "zlatobyl-kanadsky-bio-esencialni-olej": "Zlatobýl kanadský BIO",
    # Blends
    "33-esencialni-olej": "33",
    "3s-esencialni-olej": "3S",
    "apar-esencialni-olej": "A-Par",
    "bewit-afrodite-esencialni-olej": "Afrodite",
    "ag-esencialni-olej": "Ag",
    "alg-esencialni-olej": "Alg",
    "bewit-amor-esencialni-olej": "Amor",
    "ancan-esencialni-olej": "Ancan",
    "ane-esencialni-olej": "Ane",
    "angel-esencialni-olej": "Angel",
    "antis-esencialni-olej": "Antis",
    "bewit-ast-esencialni-olej": "Ast",
    "aura": "Aura",
    "bewit-baby-sleep-esencialni-olej": "Baby Sleep",
    "baby-sleep-roll-on": "Baby Sleep roll-on",
    "balance-esencialni-olej": "Balance",
    "balze-esencialni-olej": "Balze",
    "bewit-best-friend-esencialni-olej": "Best friend",
    "blue-diamond-esencialni-olej": "Blue diamond",
    "bewit-bo-esencialni-olej": "Bo",
    "bodyguard-esencialni-olej": "Bodyguard",
    "breast-plus-esencialni-olej": "Breast plus",
    "breath-esencialni-olej": "Breath",
    "bref-esencialni-olej": "Bref",
    "bro": "Bro",
    "bewit-bruises-esencialni-olej": "Bruises",
    "bewit-bulce-esencialni-olej": "Bulce",
    "buni-esencialni-olej": "Buni",
    "byd-esencialni-olej": "Byd",
    "bewit-bydia-esencialni-olej": "Bydia",
    "bewit-byf-esencialni-olej": "Byf",
    "bewit-byfev-esencialni-olej": "Byfev",
    "calming-esencialni-olej": "Calming",
    "chakra-1-esencialni-olej": "Chakra 1",
    "chakra-2-esencialni-olej": "Chakra 2",
    "bewit-chakra-3-esencialni-olej": "Chakra 3",
    "bewit-chakra-4-esencialni-olej": "Chakra 4",
    "chakra-5-esencialni-olej": "Chakra 5",
    "bewit-chakra-6-esencialni-olej": "Chakra 6",
    "bewit-chakra-7-esencialni-olej": "Chakra 7",
    "cholbal-esencialni-olej": "Cholbal",
    "clarity-esencialni-olej": "Clarity",
    "bewit-clean-home-esencialni-olej": "Clean Home",
    "coldet-esencialni-olej": "Coldet",
    "colwit-esencialni-olej": "Colwit",
    "comunication-esencialni-olej": "Communication",
    "compassion-esencialni-olej": "Compassion",
    "confession-esencialni-olej": "Confession",
    "confidence-esencialni-olej": "Confidence",
    "coriander-deux-esencialni-olej": "Coriander Deux",
    "courage-esencialni-olej": "Courage",
    "creativity-esencialni-olej": "Creativity",
    "dark-circles-help-esencialni-olej": "Dark Circles Help",
    "deep-sleep-esencialni-olej": "Deep Sleep",
    "bewit-dent-esencialni-olej": "Dent",
    "desi-esencialni-olej": "Desi",
    "bewit-despcito-esencialni-olej": "Despacito",
    "detol-esencialni-olej": "Detol",
    "dry-c-esencialni-olej": "Dry C",
    "dupreg-esencialni-olej": "Dupreg",
    "bewit-dx-esencialni-olej": "Dx",
    "bewit-e-smo-esencialni-olej": "E-Smo",
    "earth-esencialni-olej": "Earth",
    "elli-esencialni-olej": "Elli",
    "empathy-esencialni-olej": "Empathy",
    "bewit-epi-esencialni-olej": "Epi",
    "eros-esencialni-olej": "Eros",
    "ether-esencialni-olej": "Ether",
    "faith-esencialni-olej": "Faith",
    "bewit-fascia-esencialni-olej": "Fascia",
    "fire-esencialni-olej": "Fire",
    "bewit-flow-b-esencialni-olej": "Flow B",
    "bewit-flow-esencialni-olej": "Flow",
    "bewit-focus-esencialni-olej": "Focus",
    "forever-esencialni-olej": "Forever",
    "forgiveness-esencialni-olej": "Forgiveness",
    "bewit-frankincense-quattuor-esencialni-olej": "Frankincense Quattuor",
    "freedom-esencialni-olej": "Freedom",
    "fresh-esencialni-olej": "Fresh",
    "bewit-gasto-esencialni-olej": "Gasto",
    "bewit-generator-esencialni-olej": "Generator",
    "bewit-gentle-smile-esencialni-olej": "Gentle Smile",
    "get-up-esencialni-olej": "Get Up",
    "goddess-esencialni-olej": "Goddess",
    "gold-esencialni-olej": "Gold",
    "bewit-gold-a-esencialni-olej": "Gold A",
    "bewit-gold-a-sha-man-esencialni-olej": "Gold A-Sha Man",
    "bewit-gold-a-sha-woman-esencialni-olej": "Gold A-Sha Woman",
    "bewit-gold-aa-serum-esencialni-olej": "Gold AA Serum",
    "bewit-gold-an-cell-esencialni-olej": "Gold An-Cell",
    "bewit-gold-baby-esencialni-olej": "Gold Baby",
    "gold-balance-oily-esencialni-olej": "Gold Balance Oily",
    "bewit-gold-beauty-esencialni-olej": "Gold Beauty",
    "bewit-gold-body-esencialni-olej": "Gold Body",
    "bewit-gold-c-esencialni-olej": "Gold C",
    "bewit-gold-col-esencialni-olej": "Gold Col",
    "bewit-gold-d-esencialni-olej": "Gold D",
    "bewit-gold-deo-esencialni-olej": "Gold Deo",
    "bewit-gold-first-esencialni-olej": "Gold First",
    "bewit-gold-he-esencialni-olej": "Gold He",
    "gold-lavender-esencialni-olej": "Gold Lavender",
    "bewit-gold-lips-esencialni-olej": "Gold Lips",
    "bewit-gold-man-esencialni-olej": "Gold Man",
    "gold-moisturising-esencialni-olej": "Gold Moisturising",
    "bewit-gold-nowa-esencialni-olej": "Gold Nowa",
    "gold-provance-esencialni-olej": "Gold Provance",
    "bewit-gold-ps-esencialni-olej": "Gold Ps",
    "gold-red-esencialni-olej": "Gold Red",
    "gold-sca-esencialni-olej": "Gold Sca",
    "bewit-gold-sca-roll-on": "Gold Sca roll-on",
    "bewit-gold-sensitive-esencialni-olej": "Gold Sensitive",
    "bewit-gold-shi-esencialni-olej": "Gold Shi",
    "bewit-gold-sun-b-esencialni-olej": "Gold Sun B",
    "bewit-gold-superrior-esencialni-olej": "Gold Superior",
    "bewit-gold-wr-serum-esencialni-olej": "Gold WR Serum",
    "grounding-esencialni-olej": "Grounding",
    "gur-esencialni-olej": "Gur",
    "h-plant-esencialni-olej": "H Plant",
    "h-plus-esencialni-olej": "H Plus",
    "hair-esencialni-olej": "Hair",
    "hebaut-esencialni-olej": "Hebaut",
    "help-gb-esencialni-olej": "Help GB",
    "help-h-esencialni-olej": "Help H",
    "bewit-help-k-esencialni-olej": "Help K",
    "help-p-esencialni-olej": "Help P",
    "help-sp-esencialni-olej": "Help Sp",
    "bewit-hemo-esencialni-olej": "Hemo",
    "bewit-hemus-esencialni-olej": "Hemus",
    "bewit-hepar-esencialni-olej": "Hepar",
    "high-vibration-esencialni-olej": "High Vibration",
    "holy-anointing-esencialni-olej": "Holy Anointing",
    "hormbal-esencialni-olej": "Hormbal",
    "humility-esencialni-olej": "Humility",
    "bewit-hyp-esencialni-olej": "Hyp",
    "bewit-hypot-esencialni-olej": "Hypot",
    "i-am-esencialni-olej": "I Am",
    "i-dont-smoke-esencialni-olej": "I Don't Smoke",
    "im-happy-esencialni-olej": "I'm Happy",
    "imm-esencialni-olej": "Imm",
    "bewit-inf-esencialni-olej": "Inf",
    "inner-child-esencialni-olej": "Inner Child",
    "bewit-inner-woman-esencialni-olej": "Inner Woman",
    "insect-stop-esencialni-olej": "Insect Stop",
    "inspiration-esencialni-olej": "Inspiration",
    "integrity-esencialni-olej": "Integrity",
    "intuition-esencialni-olej": "Intuition",
    "bewit-joy-esencialni-olej": "Joy",
    "bewit-king-esencialni-olej": "King",
    "laundry-citrus-esencialni-olej": "Laundry Citrus",
    "lavender-deux-esencialni-olej": "Lavender Deux",
    "leader-esencialni-olej": "Leader",
    "learning-esencialni-olej": "Learning",
    "bewit-legut-esencialni-olej": "Legut",
    "let-go-esencialni-olej": "Let Go",
    "lice": "Lice",
    "life-esencialni-olej": "Life",
    "bewit-love-esencialni-olej": "Love",
    "bewit-love-roll-on": "Love roll-on",
    "bewit-lym-esencialni-olej": "Lym",
    "bewit-magic-esencialni-olej": "Magic",
    "man-no-1-prirodni-parfem-esencialni-olej": "Man No. 1",
    "man-pr-esencialni-olej": "Man Pr",
    "bewit-manifestor-esencialni-olej": "Manifestor",
    "massage-kids-esencialni-olej": "Massage Kids",
    "meditation-esencialni-olej": "Meditation",
    "memory-esencialni-olej": "Memory",
    "merry-christmas-esencialni-olej": "Merry Christmas",
    "metal-esencialni-olej": "Metal",
    "mig-esencialni-olej": "Mig",
    "miracle-esencialni-olej": "Miracle",
    "money-esencialni-olej": "Money",
    "moon-esencialni-olej": "Moon",
    "bewit-motivation-esencialni-olej": "Motivation",
    "move-gt-esencialni-olej": "Move GT",
    "move-it-esencialni-olej": "Move It",
    "bewit-mucra-esencialni-olej": "Mucra",
    "mystery-esencialni-olej": "Mystery",
    "bewit-nase-esencialni-olej": "Nase",
    "nirvana": "Nirvana",
    "no-esencialni-olej": "No",
    "bewit-nobapa-esencialni-olej": "Nobapa",
    "bewit-nocon-esencialni-olej": "Nocon",
    "bewit-nohepa-esencialni-olej": "Nohepa",
    "nomad-from-the-stars-esencialni-olej": "Nomad From the Stars",
    "nopa-esencialni-olej": "Nopa",
    "bewit-nopa-nr-esencialni-olej": "Nopa Nr",
    "nose-esencialni-olej": "Nose",
    "bewit-now-esencialni-olej": "Now",
    "o-2-max-esencialni-olej": "O2 Max",
    "ok-dig-esencialni-olej": "Ok Dig",
    "only-one-esencialni-olej": "Only One",
    "bewit-open-heart-esencialni-olej": "Open Heart",
    "bewit-oracle-esencialni-olej": "Oracle",
    "bewit-ospo-esencialni-olej": "Ospo",
    "partnership-esencialni-olej": "Partnership",
    "peace-esencialni-olej": "Peace",
    "bewit-pigment-spots-esencialni-olej": "Pigment Spots",
    "po-w-er-esencialni-olej": "Po-W-Er",
    "bewit-polos-esencialni-olej": "Polos",
    "prana-esencialni-olej": "Prana",
    "prayer-esencialni-olej": "Prayer",
    "prena-esencialni-olej": "Prena",
    "pro-no-esencialni-olej": "Pro No",
    "bewit-projector-esencialni-olej": "Projector",
    "bewit-protect-b-esencialni-olej": "Protect B",
    "protect-esencialni-olej": "Protect",
    "pure-esencialni-olej": "Pure",
    "px": "Px",
    "bewit-queen-esencialni-olej": "Queen",
    "bewit-reflector-esencialni-olej": "Reflector",
    "bewit-relax-esencialni-olej": "Relax",
    "bewit-reles-esencialni-olej": "Reles",
    "resolution-esencialni-olej": "Resolution",
    "rhe": "Rhe",
    "rosa-vibe-esencialni-olej": "Rosa Vibe",
    "bewit-s-stop-esencialni-olej": "S Stop",
    "sauna": "Sauna",
    "bewit-self-love-esencialni-olej": "Self Love",
    "bewit-shoes-esencialni-olej": "Shoes",
    "so-happy-together-esencialni-olej": "So Happy Together",
    "soulguard-esencialni-olej": "Soulguard",
    "stem-plus-esencialni-olej": "Stem Plus",
    "stop-add-esencialni-olej": "Stop Add",
    "bewit-suby-c-1-esencialni-olej": "Suby C-1",
    "bewit-suby-c-2-esencialni-olej": "Suby C-2",
    "bewit-suby-c-3-esencialni-olej": "Suby C-3",
    "bewit-sunshine-esencialni-olej": "Sunshine",
    "bewit-sup-er-man-esencialni-olej": "Sup-Er-Man",
    "bewit-sw-esencialni-olej": "Sw",
    "bewit-tantra-esencialni-olej": "Tantra",
    "tattoo": "Tattoo",
    "thank-you-esencialni-olej": "Thank You",
    "tin-esencialni-olej": "Tin",
    "bewit-tonafu-esencialni-olej": "Tonafu",
    "transformation-esencialni-olej": "Transformation",
    "bewit-trauma-free-esencialni-olej": "Trauma Free",
    "travelling-esencialni-olej": "Travelling",
    "vahe-esencialni-olej": "Vahe",
    "bewit-vibe-esencialni-olej": "Vibe",
    "bewit-virgin-esencialni-olej": "Virgin",
    "bewit-vita-esencialni-olej": "Vita",
    "bewit-vitality-esencialni-olej": "Vitality",
    "bewit-warrior-esencialni-olej": "Warrior",
    "water-esencialni-olej": "Water",
    "wet-c-esencialni-olej": "Wet C",
    "wild-woman-esencialni-olej": "Wild Woman",
    "winner-esencialni-olej": "Winner",
    "wloss-esencialni-olej": "Wloss",
    "bewit-wofert-esencialni-olej": "Wofert",
    "woman-m-esencialni-olej": "Woman M",
    "woman-no-1-esencialni-olej": "Woman No. 1",
    "wood-esencialni-olej": "Wood",
    "yes-esencialni-olej": "Yes",
}

# Reverse: name (normalized) -> slug
def normalize(s):
    """Normalize string for comparison: lowercase, remove diacritics, strip."""
    s = s.lower().strip()
    s = "".join(c for c in unicodedata.normalize("NFD", s)
                if unicodedata.category(c) != "Mn")
    # Remove common suffixes
    for suffix in [", korun", ", list", ", semena", ", jehlici", ", kura", ", koren",
                   " esencialni olej", " esencialni", " raw", " bio", " co2", " absolue"]:
        if s.endswith(suffix):
            s = s[:-len(suffix)].strip()
    return s


def get_products_with_pages(pdf_path):
    reader = PdfReader(pdf_path)
    root = reader.trailer["/Root"].get_object()
    outlines = root.get("/Outlines")
    if not outlines:
        return []
    outlines_obj = outlines.get_object()
    named_dests = reader.named_destinations

    page_ref_to_num = {}
    for i, pg in enumerate(reader.pages):
        if hasattr(pg, "indirect_reference") and pg.indirect_reference:
            page_ref_to_num[pg.indirect_reference.idnum] = i + 1

    products = []

    def collect(node):
        if not isinstance(node, DictionaryObject):
            return
        title = node.get("/Title")
        a = node.get("/A")
        if a and title:
            a_obj = a.get_object() if hasattr(a, "get_object") else a
            if isinstance(a_obj, DictionaryObject):
                d = a_obj.get("/D")
                if d:
                    d_str = d.decode("utf-16-be") if isinstance(d, bytes) else str(d)
                    title_str = str(title).strip().replace("\n", " ")
                    if not any(x in title_str.lower() for x in ["upozorn", "obsah", "disclaimer", "osah"]):
                        page_num = None
                        if d_str in named_dests:
                            nd = named_dests[d_str]
                            page_ref = nd.get("/Page")
                            if page_ref and hasattr(page_ref, "idnum"):
                                page_num = page_ref_to_num.get(page_ref.idnum)
                        products.append({"title": title_str, "page": page_num})

        first = node.get("/First")
        if first:
            collect(first.get_object())
        next_node = node.get("/Next")
        if next_node:
            collect(next_node.get_object())

    collect(outlines_obj)
    return products


# Build name->slug lookup (from SLUG_TO_NAME reversed)
name_to_slug = {}
for slug, name in SLUG_TO_NAME.items():
    key = normalize(name)
    if key not in name_to_slug:
        name_to_slug[key] = slug

# Also build a simple key based on first word(s) for fuzzy fallback
name_to_slug_full = {name.lower().strip(): slug for slug, name in SLUG_TO_NAME.items()}


# Manual overrides for products with encoding issues or unusual names
MANUAL_OVERRIDES = {
    # Single oils
    "copaiba": "kopaiva-esencialni-olej",
    "kopal vonny (palo santo)": "palo-santo-esencialni-olej",
    "mandle hork": "prunus-amygdalus-esencialni-olej",
    "pelargonie ruzov": "geranie-esencialni-olej",
    "puskvorec": "calamus-esencialni-olej",
    "skorice prav": "skorice-kura-esencialni-olej",
    "salvej lekarsk": "salvej-esencialni-olej",
    "tulsi": "bazalka-posvatna-esencialni-olej",
    "tymian obecn": "tymian-esencialni-olej",
    "vrtic modr": "blue-tansy-esencialni-olej",
    # Ylang
    "ylang-ylang": "ylang-ylang-esencialni-olej",
    # Blends with non-breaking spaces (xa0)
    "i am": "i-am-esencialni-olej",
    "i don": "i-dont-smoke-esencialni-olej",
    "i'm happy": "im-happy-esencialni-olej",
    "im happy": "im-happy-esencialni-olej",
    "i\x80m happy": "im-happy-esencialni-olej",
    "s stop": "bewit-s-stop-esencialni-olej",
}

# Title-level direct overrides (raw title string -> slug, for encoding-broken titles)
TITLE_OVERRIDES = {
    # Detected by checking unmatched titles - these have replacement/garbled chars
    # Vratič modrý (Blue Tansy) - chars 0x10d (č) and 0xfd (ý)
    "Vratiè modr\xfd": "blue-tansy-esencialni-olej",
    "Vratič modr\xfd": "blue-tansy-esencialni-olej",
    # I'm Happy blend
    "I\xa0M HAPPY": "im-happy-esencialni-olej",
    "I\x80M HAPPY": "im-happy-esencialni-olej",
    # Eukalyptus (Eucalyptus globulus) - plain name, not 'blue' or 'radiata' etc.
    "Eukalyptus": "eukalyptus-esencialni-olej",
}


def find_slug(pdf_title):
    """Try to find the best matching slug for a PDF product title."""
    # Check raw title overrides first (for encoding-broken titles)
    if pdf_title in TITLE_OVERRIDES:
        return TITLE_OVERRIDES[pdf_title]
    # Strip variant with ? replacement chars -> check by stripping unknown chars
    title_stripped = "".join(c if ord(c) < 128 or c in "áčďéěíňóřšťúůýžÁČĎÉĚÍŇÓŘŠŤÚŮÝŽ" else "?" for c in pdf_title)
    for key, slug in TITLE_OVERRIDES.items():
        key_stripped = "".join(c if ord(c) < 128 or c in "áčďéěíňóřšťúůýžÁČĎÉĚÍŇÓŘŠŤÚŮÝŽ" else "?" for c in key)
        if title_stripped == key_stripped:
            return slug

    # Replace non-breaking spaces with regular spaces
    clean_title = pdf_title.replace("\xa0", " ").strip()

    # Direct match
    t = clean_title.lower().strip()
    if t in name_to_slug_full:
        return name_to_slug_full[t]

    # Normalized match
    norm = normalize(clean_title)
    if norm in name_to_slug:
        return name_to_slug[norm]

    # Check manual overrides (prefix match)
    for key, slug in MANUAL_OVERRIDES.items():
        if norm.startswith(key) or key.startswith(norm[:8]):
            return slug

    # Partial match: find all candidates, prefer the one whose name best matches
    candidates = []
    for slug, canon_name in SLUG_TO_NAME.items():
        cn = normalize(canon_name)
        if cn.startswith(norm) or norm.startswith(cn):
            # Score: prefer longer shared prefix (more specific match)
            shared = min(len(cn), len(norm))
            diff = abs(len(cn) - len(norm))
            candidates.append((diff, -shared, slug))

    if candidates:
        candidates.sort()
        return candidates[0][2]

    return None


def main():
    pdf_files = sorted(glob.glob(r"C:\Users\x2\Desktop\xx\*.pdf"))
    # Filter to the two main PDFs
    pdf1 = [f for f in pdf_files if "Jednodruhov" in f][0]
    pdf2 = [f for f in pdf_files if "Sm" in f and "1.pdf" not in f][0]

    print(f"PDF1: {pdf1}")
    print(f"PDF2: {pdf2}")

    pdf1_products = get_products_with_pages(pdf1)
    pdf2_products = get_products_with_pages(pdf2)

    all_results = []
    unmatched1 = []
    unmatched2 = []

    # Process PDF1 (single oils)
    pdf1_matched = 0
    for prod in pdf1_products:
        slug = find_slug(prod["title"])
        if slug:
            url = f"{BASE_URL}{slug}{AFFILIATE_PARAM}"
            all_results.append({
                "source": "single_oils",
                "page": prod["page"],
                "url": url,
                "text": prod["title"],
                "slug": slug,
            })
            pdf1_matched += 1
        else:
            unmatched1.append(prod["title"])

    # Process PDF2 (blends)
    pdf2_matched = 0
    for prod in pdf2_products:
        slug = find_slug(prod["title"])
        if slug:
            url = f"{BASE_URL}{slug}{AFFILIATE_PARAM}"
            all_results.append({
                "source": "blends",
                "page": prod["page"],
                "url": url,
                "text": prod["title"],
                "slug": slug,
            })
            pdf2_matched += 1
        else:
            unmatched2.append(prod["title"])

    # Save combined JSON
    output_path = Path(r"C:\Claude\projekty\www\esenci.cz\bewit-urls.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)

    # Save per-PDF JSONs
    single_oils = [r for r in all_results if r["source"] == "single_oils"]
    blends = [r for r in all_results if r["source"] == "blends"]

    with open(output_path.parent / "bewit-urls-single-oils.json", "w", encoding="utf-8") as f:
        json.dump(single_oils, f, ensure_ascii=False, indent=2)

    with open(output_path.parent / "bewit-urls-blends.json", "w", encoding="utf-8") as f:
        json.dump(blends, f, ensure_ascii=False, indent=2)

    # Print summary
    print(f"\n=== SUMMARY ===")
    print(f"PDF1 (single oils): {len(pdf1_products)} products, {pdf1_matched} matched URLs")
    print(f"PDF2 (blends):      {len(pdf2_products)} products, {pdf2_matched} matched URLs")
    print(f"Total matched:      {len(all_results)} URLs saved")
    print(f"\nUnique URLs PDF1: {len(set(r['url'] for r in single_oils))}")
    print(f"Unique URLs PDF2: {len(set(r['url'] for r in blends))}")

    if unmatched1:
        print(f"\nPDF1 unmatched ({len(unmatched1)}):")
        for u in unmatched1:
            print(f"  - {u!r}")

    if unmatched2:
        print(f"\nPDF2 unmatched ({len(unmatched2)}):")
        for u in unmatched2:
            print(f"  - {u!r}")

    print(f"\nOutput: {output_path}")


if __name__ == "__main__":
    main()
