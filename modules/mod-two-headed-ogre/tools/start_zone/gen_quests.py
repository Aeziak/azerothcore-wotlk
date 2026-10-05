"""Generate the mod-two-headed-ogre start zone quests (Blade's Edge, levels 1-10, French texts)."""
import os

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "data", "sql", "db-world", "base",
                   "mod_two_headed_ogre_quests.sql")

OGRE_RACE_MASK = 256        # race 9
BLADES_EDGE = 3522          # QuestSortID: zone
KEG_ITEM = 91002            # custom quest item, see below
RING_ITEM = 91004           # first quest reward: +20% speed out of combat in Blade's Edge (module)

TOR_CHUNK, GOR_DREK, OLD_OROK, ROKGAH, GARM, REXXAR = 21147, 21117, 19471, 21311, 21950, 21984
LEOROXX, TAEREK, SILMARA, DOHGAR, DERTROK, THRALL = 22004, 21895, 21896, 22312, 21496, 4949

THUNDERLORD = "au bastion des Sire-tonnerre"
MOK_NATHAL = "au village Mok'Nathal"
ENDER_TEXT = {
    GOR_DREK: "Gor'drek " + THUNDERLORD, OLD_OROK: "le Vieil Orok " + THUNDERLORD,
    TOR_CHUNK: "Tor'chunk Doublegriffes " + THUNDERLORD, ROKGAH: "Rokgah Poigne-sang " + THUNDERLORD,
    GARM: "Garm " + THUNDERLORD, LEOROXX: "Leoroxx " + MOK_NATHAL, TAEREK: "Taerek " + MOK_NATHAL,
    SILMARA: "Silmara " + MOK_NATHAL, DOHGAR: "le Mande-esprit Dohgar " + MOK_NATHAL,
    DERTROK: "Dertrok " + MOK_NATHAL, THRALL: "Thrall dans le fort Grommash, à Orgrimmar",
}

# Thrall stands in Grommash Hold (1919.9, -4123.8): arrive in front of him, facing him.
ORGRIMMAR = (1, 1920.0, -4131.0, 44.4, 1.57)

# Quests are grouped by place: the Bloodmaul ones (91005-91007) come together after the wolves, the Bladespire
# ones (91008-91010) together after the Bloodmaul camp, and the Mok'Nathal ones together on arrival.
QUESTS = [
    dict(id=91001, level=1, xp=8, giver=TOR_CHUNK, ender=GOR_DREK, prev=0,
         title="Deux têtes, un seul ogre",
         objectives="Parlez à Gor'drek au bastion des Sire-tonnerre.",
         details="Alors c'est toi, l'ogre à deux têtes dont parlent nos éclaireurs ? Hmph. Une tête pour réfléchir, "
                 "une tête pour cogner... on verra bien laquelle commande.$B$BLe clan Sire-tonnerre accueille tous "
                 "ceux qui savent se battre. Va voir Gor'drek, près des enclos. Il a toujours du travail pour des bras "
                 "solides... et toi, tu en as quatre.",
         reward="Tor'chunk t'envoie ? Par les ancêtres, deux têtes... J'espère qu'au moins l'une d'elles sait écouter.$B$B"
                "Tiens, Tor'chunk m'a demandé de te donner ça : la chevalière des coursiers du clan. Avec elle, tu "
                "traverseras les Tranchantes plus vite que tes deux têtes ne se disputent.",
         reward_items=[(RING_ITEM, 1)]),
    dict(id=91002, level=2, xp=8, giver=GOR_DREK, ender=GOR_DREK, prev=91001,
         title="La nature envahissante",
         objectives="Tuez 8 Saigneurs Aile-rasoir pour Gor'drek au bastion des Sire-tonnerre.",
         details="Les saigneurs aile-rasoir pullulent autour du bastion. Ils s'attaquent à nos loups, à nos réserves, "
                 "et même à nos guerriers quand ils dorment.$B$BVa dans les collines à l'ouest et tues-en huit. Deux "
                 "têtes, ça devrait faire deux fois moins de travail, non ?",
         request="Les saigneurs rôdent toujours, $N ?",
         reward="Bien. Les loups dormiront mieux cette nuit... et moi aussi.",
         npcs=[(21033, 8)]),
    dict(id=91003, level=3, xp=8, giver=GOR_DREK, ender=GOR_DREK, prev=91002,
         title="Protéger les nôtres",
         objectives="Soignez 5 Loups redoutables sire-tonnerre avec la Pommade de Gor'drek.",
         details="Nos loups redoutables rôdent librement autour du bastion, mais beaucoup ont été blessés par les "
                 "saigneurs. Prends cette pommade et applique-la sur cinq d'entre eux.$B$BAttention : un loup blessé ne "
                 "fait pas toujours la différence entre un ami et un repas. S'il te mord, défends-toi... mais pas trop "
                 "fort.",
         request="Les loups ont-ils reçu leurs soins ?",
         reward="Les loups te sentiront désormais comme un membre de la meute. Enfin, l'une de tes têtes, au moins.",
         npcs=[(21142, 5)], objective_texts=["Loup redoutable sire-tonnerre soigné"], start_item=30175),
    dict(id=91004, level=3, xp=7, giver=OLD_OROK, ender=OLD_OROK, prev=91001,
         title="Des produits hors du commun",
         objectives="Rapportez 6 Ailes de chauve-souris impeccables au Vieil Orok au bastion des Sire-tonnerre.",
         details="Toi, l'ogre ! Le vieil Orok a besoin d'ingrédients. Les ailes des saigneurs aile-rasoir font un "
                 "ragoût... intéressant.$B$BRapporte-m'en six, et je te garderai une part. Ou deux, vu que tu as deux "
                 "bouches.",
         request="Tu as mes ailes ? Le ragoût n'attend pas.",
         reward="Parfait ! Croustillantes à souhait. Ne dis à personne ce qu'il y a dans le ragoût.",
         items=[(38620, 6)]),
    dict(id=91005, level=4, xp=8, giver=TOR_CHUNK, ender=TOR_CHUNK, prev=91003,
         title="Les ogres de la Masse-sanglante",
         objectives="Tuez 8 Tirailleurs de la Masse-sanglante et 3 Loups redoutables de la Masse-sanglante pour "
                    "Tor'chunk Doublegriffes.",
         details="La Masse-sanglante... Des ogres, comme toi. Enfin, avec une seule tête et encore moins de cervelle. "
                 "Ils ont dressé leur camp à l'ouest et ils menacent nos routes.$B$BMontre-leur ce qu'un ogre du clan "
                 "Sire-tonnerre sait faire : tue huit tirailleurs et trois de leurs loups.",
         request="La Masse-sanglante est-elle toujours aussi bruyante ?",
         reward="Ha ! Ils ne s'attendaient pas à se faire rosser par l'un des leurs.",
         npcs=[(19948, 8), (20058, 3)]),
    dict(id=91006, level=5, xp=8, giver=TOR_CHUNK, ender=TOR_CHUNK, prev=91003,
         title="Les géomanciens",
         objectives="Tuez 6 Géomanciens de la Masse-sanglante et 4 Brutes de la Masse-sanglante pour Tor'chunk "
                    "Doublegriffes.",
         details="Les géomanciens de la Masse-sanglante manipulent la pierre et le feu. Tant qu'ils vivent, leur camp "
                 "tiendra.$B$BVa plus loin à l'ouest, tue six géomanciens et quatre brutes. Et si l'une de tes têtes a "
                 "peur, que l'autre la fasse taire.",
         request="Les géomanciens sont-ils tombés ?",
         reward="Le camp de la Masse-sanglante ne s'en remettra pas de sitôt. Tu apprends vite, ogre.",
         npcs=[(19952, 6), (19991, 4)]),
    dict(id=91007, level=5, xp=7, giver=ROKGAH, ender=ROKGAH, prev=91003,
         title="Une bière à tomber",
         objectives="Rapportez 6 Tonnelets de bière de la Masse-sanglante à Rokgah Poigne-sang au bastion des "
                    "Sire-tonnerre.",
         details="Psst. Les ogres de la Masse-sanglante brassent une bière si forte qu'elle ferait tomber un kodo. Leur "
                 "brasseur en garde des tonnelets entiers, et les autres en ont toujours un sur eux.$B$BRapporte-m'en "
                 "six. C'est pour... l'étude. Oui, l'étude. Tor'chunk n'a pas besoin de le savoir.",
         request="Alors, cette bière ? Chut, pas si fort.",
         reward="Ah, l'odeur ! On dirait des pieds de gronn. Parfait. Garde ça pour toi, hein ?",
         items=[(KEG_ITEM, 6)]),
    dict(id=91008, level=6, xp=8, giver=TOR_CHUNK, ender=TOR_CHUNK, prev=91006,
         title="La menace Flèchelame",
         objectives="Tuez 10 Brutes de Flèchelame et 5 Raptors de Flèchelame pour Tor'chunk Doublegriffes.",
         details="À l'est, les Flèchelame ne valent pas mieux que la Masse-sanglante. Leurs brutes pillent nos "
                 "patrouilles et leurs raptors dévorent nos montures.$B$BTue dix brutes et cinq raptors de Flèchelame.",
         request="Les Flèchelame rôdent encore près de nos murs.",
         reward="Bon travail. Les Flèchelame vont apprendre à craindre le bastion.",
         npcs=[(19995, 10), (20728, 5)]),
    dict(id=91009, level=6, xp=7, giver=GARM, ender=GARM, prev=91006,
         title="Les chamans de Flèchelame",
         objectives="Tuez 6 Chamans de Flèchelame et 3 Cuisiniers de Flèchelame pour Garm au bastion des "
                    "Sire-tonnerre.",
         details="Les esprits sont agités. Les chamans de Flèchelame les tourmentent pour en tirer du pouvoir, et "
                 "leurs cuisiniers nourrissent toute cette horde d'ogres.$B$BFais taire six chamans et trois "
                 "cuisiniers, à l'est. Les esprits t'en seront reconnaissants... et moi aussi.",
         request="Les esprits gémissent encore.",
         reward="Les esprits s'apaisent. Le clan Sire-tonnerre n'oubliera pas ce que tu as fait.",
         npcs=[(19998, 6), (20334, 3)]),
    dict(id=91010, level=7, xp=8, giver=TOR_CHUNK, ender=TOR_CHUNK, prev=91006,
         title="Le champion de Flèchelame",
         objectives="Tuez un Champion de Flèchelame pour Tor'chunk Doublegriffes.",
         details="Les Flèchelame ont des champions, des montagnes de muscles qui se croient invincibles. Prouve-leur "
                 "le contraire.$B$BAbats l'un d'eux, et tu seras un vrai guerrier du clan Sire-tonnerre.",
         request="Le champion vit encore ?",
         reward="Tu as abattu leur champion ? À deux têtes contre une, il n'avait aucune chance. Tu es des nôtres, "
                "ogre. Rexxar voudra te voir.",
         npcs=[(21296, 1)]),
    dict(id=91011, level=7, xp=8, giver=REXXAR, ender=LEOROXX, prev=91010,
         title="La route de Mok'Nathal",
         objectives="Tuez 6 Ravageurs Arrachelame et 6 Ravageurs fauche-sang sur la route du sud, puis rendez-vous au "
                    "village Mok'Nathal et parlez à Leoroxx.",
         details="Tu as fait tes preuves. Moi aussi, j'ai du sang d'ogre dans les veines : je suis Mok'Nathal, à "
                 "moitié orc, à moitié ogre. Mon peuple vit au sud, au village Mok'Nathal, et mon père Leoroxx "
                 "saura quoi faire de deux têtes aussi dures que les tiennes.$B$BMais la route est coupée : les "
                 "ravageurs, rendus fous par le gangrefeu de la Porte de la mort, dévorent tout ce qui passe. "
                 "Nettoie le chemin en descendant : six ravageurs arrachelames et six ravageurs fauche-sang. Les "
                 "Mok'Nathal sauront qui a rouvert la route.",
         request="La route est-elle libre ?",
         reward="Rexxar t'envoie, et tu as rouvert la route du nord ? Alors tu es le bienvenu au village Mok'Nathal, "
                "ogre. Ici, personne ne se moque d'un sang mêlé... ni d'une tête en trop.",
         npcs=[(22123, 6), (21423, 6)], choices=[3305, 2970, 4242]),
    dict(id=91012, level=8, xp=8, giver=LEOROXX, ender=LEOROXX, prev=91011,
         title="Depuis des temps oubliés",
         objectives="Tuez Gnosh Brognat, 4 Mystiques de Flèchelame et 4 Écraseurs de Flèchelame pour Leoroxx au "
                    "village Mok'Nathal.",
         details="Les Flèchelame ont installé un campement au nord, entre notre village et le bastion. Leur chef, "
                 "Gnosh Brognat, se vante d'avoir massacré des Mok'Nathal.$B$BVa là-bas, abats Gnosh ainsi que quatre "
                 "mystiques et quatre écraseurs.",
         request="Gnosh Brognat se vante-t-il encore ?",
         reward="Gnosh ne se vantera plus. Les anciens Mok'Nathal chanteront ton nom... tes deux noms.",
         npcs=[(20768, 1), (20766, 4), (20765, 4)], choices=[1211, 2977, 6527]),
    dict(id=91013, level=8, xp=8, giver=TAEREK, ender=TAEREK, prev=91011,
         title="Cocons d'aile-de-soie",
         objectives="Rapportez 8 Cocons d'aile-de-soie à Taerek au village Mok'Nathal.",
         details="Les larves d'aile-de-soie, à l'ouest du village, tissent des cocons d'une soie incomparable. "
                 "Rapporte-m'en huit.$B$BAttention : quand on les menace, elles éclosent... et ce qui en sort a des "
                 "ailes.",
         request="Les cocons, ogre ?",
         reward="Magnifiques ! Cette soie habillera tout le village pour l'hiver.",
         items=[(30791, 8)], choices=[14724, 4771, 2308]),
    dict(id=91014, level=8, xp=7, giver=SILMARA, ender=SILMARA, prev=91011,
         title="Les ailes les plus douces",
         objectives="Rapportez 8 Ailes iridescentes à Silmara au village Mok'Nathal.",
         details="Les ailes des ailes-de-soie adultes font les plus beaux ornements de Mok'Nathal. Rapporte-m'en "
                 "huit.$B$BEt essaie de ne pas les abîmer... j'ai vu comment tu tiens tes armes.",
         request="Tu as les ailes ? Pas trop froissées ?",
         reward="Elles sont parfaites. Pour un ogre, tu as la main étonnamment légère.",
         items=[(30792, 8)], choices=[3474, 4768, 2312]),
    dict(id=91016, level=9, xp=8, giver=DERTROK, ender=DERTROK, prev=91011,
         title="Écailles et crocs",
         objectives="Tuez 6 Serpents ailécailles et 6 Flagellants Crocs-lames pour Dertrok au village Mok'Nathal.",
         details="Les serpents ailécailles et les flagellants crocs-lames chassent sur nos terres, au nord du village. "
                 "Les premiers crachent la foudre, les seconds mordent jusqu'à l'os.$B$BDébarrasse-nous de six de "
                 "chaque.",
         request="Mes chasseurs ont encore croisé des serpents.",
         reward="Nos chasseurs pourront de nouveau sortir. Merci, ogre.",
         npcs=[(20749, 6), (20751, 6)], choices=[3302, 4312, 5968]),
    dict(id=91017, level=10, xp=8, giver=LEOROXX, ender=LEOROXX, prev=91012,
         title="Maggoc, fils de Gruul",
         objectives="Tuez Maggoc pour Leoroxx au village Mok'Nathal.",
         details="Il est temps de te parler de Maggoc. C'est un fils de Gruul, un géant parmi les ogres, et il rôde "
                 "au nord, près du campement des Flèchelame. Tant qu'il vivra, aucun Mok'Nathal ne sera en "
                 "sécurité.$B$BUn ogre contre un ogre... mais toi, tu as l'avantage : deux têtes.",
         request="Maggoc vit encore ?",
         reward="Maggoc est mort ?! Un fils de Gruul, abattu par un ogre à deux têtes... Les Mok'Nathal te "
                "doivent beaucoup. Et quelqu'un de très important veut te rencontrer.",
         npcs=[(20600, 1)], choices=[1219, 3651, 15944, 8350]),
    dict(id=91018, level=10, xp=5, giver=LEOROXX, ender=THRALL, prev=91017,
         title="Retour à Kalimdor",
         objectives="Parlez à Thrall dans le fort Grommash, à Orgrimmar.",
         details="La nouvelle de ta victoire a déjà traversé la Porte des ténèbres. Le chef de guerre Thrall en "
                 "personne veut rencontrer l'ogre à deux têtes.$B$BLes esprits vont te porter jusqu'à Orgrimmar. "
                 "Présente-toi à lui dans le fort Grommash. Et essayez de vous mettre d'accord avant de parler : le chef "
                 "de guerre n'aime pas qu'on lui réponde deux fois.",
         reward="Ainsi, c'est toi l'ogre que les Sire-tonnerre et les Mok'Nathal acclament. Deux têtes, une seule "
                "loyauté : celle de la Horde.$B$BChoisis une arme dans notre armurerie, $N... si tes deux têtes "
                "parviennent à se mettre d'accord. Ensuite, le monde t'appartient. Lok'tar ogar !",
         choices=[826, 6214, 3188, 1928, 6205, 1925]),
]


def sql_value(value):
    if value is None:
        return "NULL"
    if isinstance(value, str):
        return "'" + value.replace("\\", "\\\\").replace("'", "''") + "'"
    return str(value)


def insert(table, rows):
    columns = list(rows[0].keys())
    out = ["INSERT INTO `%s` (%s) VALUES" % (table, ", ".join("`%s`" % c for c in columns))]
    out.append(",\n".join("(" + ", ".join(sql_value(r[c]) for c in columns) + ")" for r in rows) + ";")
    return out


# Quests that no longer exist: "Les ravageurs" (91015) is now part of "La route de Mok'Nathal" (91011).
RETIRED_QUESTS = [91015]

ids = [q["id"] for q in QUESTS] + RETIRED_QUESTS
id_list = ",".join(map(str, ids))
lines = [
    "-- mod-two-headed-ogre: Ogre start zone quests, Blade's Edge Mountains, levels 1-10 (Ogre race only).",
    "-- Thunderlord Stronghold, then Mok'Nathal Village, then \"Retour à Kalimdor\": teleport to Orgrimmar and",
    "-- turn in to Thrall for a choice of green weapons. Generated, French texts.",
    "",
    "-- Quest item: Bloodmaul beer keg (the stock Bloodmaul Brutebane Keg is unique and usable).",
    "DELETE FROM `item_template` WHERE `entry` = %d;" % KEG_ITEM,
]
lines += insert("item_template", [dict(entry=KEG_ITEM, **{"class": 12}, subclass=0, SoundOverrideSubclass=-1,
                                       name="Tonnelet de bière de la Masse-sanglante", displayid=7921, Quality=1,
                                       bonding=4, Material=-1, maxcount=0, stackable=20,
                                       description="Ça sent les pieds de gronn.", VerifiedBuild=0)])
lines.append("")

# First quest reward: the Thunderlord runners' ring. Its equip spell (91054) tells the module to speed the ogre up
# out of combat in Blade's Edge (91053).
lines.append("DELETE FROM `item_template` WHERE `entry` = %d;" % RING_ITEM)
lines += insert("item_template", [dict(entry=RING_ITEM, **{"class": 4}, subclass=0, SoundOverrideSubclass=-1,
                                       name="Chevalière Sire-tonnerre", displayid=9823, Quality=2, InventoryType=11,
                                       Material=1, ItemLevel=5, RequiredLevel=1, bonding=1, SellPrice=25,
                                       stat_type1=7, stat_value1=1, stat_type2=6, stat_value2=1,
                                       spellid_1=91054, spelltrigger_1=1,
                                       description="Portée par les coursiers du clan Sire-tonnerre.",
                                       VerifiedBuild=0)])
lines.append("")

templates, addons, offers, requests, starters, enders = [], [], [], [], [], []
for q in QUESTS:
    npcs = q.get("npcs", []) + [(0, 0)] * 4
    items = q.get("items", []) + [(0, 0)] * 6
    choices = q.get("choices", []) + [0] * 6
    texts = q.get("objective_texts", []) + [""] * 4
    t = dict(ID=q["id"], QuestType=2, QuestLevel=q["level"], MinLevel=max(1, q["level"] - 2),
             QuestSortID=BLADES_EDGE, RewardXPDifficulty=q["xp"], RewardMoney=q["level"] * 75,
             StartItem=q.get("start_item", 0), AllowableRaces=OGRE_RACE_MASK, LogTitle=q["title"],
             LogDescription=q["objectives"], QuestDescription=q["details"],
             QuestCompletionLog="Retournez voir %s." % ENDER_TEXT[q["ender"]])
    for i in range(4):
        t["RequiredNpcOrGo%d" % (i + 1)] = npcs[i][0]
    for i in range(4):
        t["RequiredNpcOrGoCount%d" % (i + 1)] = npcs[i][1]
    for i in range(6):
        t["RequiredItemId%d" % (i + 1)] = items[i][0]
    for i in range(6):
        t["RequiredItemCount%d" % (i + 1)] = items[i][1]
    rewards = q.get("reward_items", []) + [(0, 0)] * 4
    for i in range(4):
        t["RewardItem%d" % (i + 1)] = rewards[i][0]
        t["RewardAmount%d" % (i + 1)] = rewards[i][1]
    for i in range(6):
        t["RewardChoiceItemID%d" % (i + 1)] = choices[i]
        t["RewardChoiceItemQuantity%d" % (i + 1)] = 1 if choices[i] else 0
    for i in range(4):
        t["ObjectiveText%d" % (i + 1)] = texts[i]
    t["VerifiedBuild"] = 0
    templates.append(t)
    addons.append(dict(ID=q["id"], PrevQuestID=q["prev"], ProvidedItemCount=1 if q.get("start_item") else 0))
    offers.append(dict(ID=q["id"], RewardText=q["reward"], VerifiedBuild=0))
    if q.get("request"):
        requests.append(dict(ID=q["id"], CompletionText=q["request"], VerifiedBuild=0))
    starters.append(dict(id=q["giver"], quest=q["id"]))
    enders.append(dict(id=q["ender"], quest=q["id"]))

for table, rows in (("quest_template", templates), ("quest_template_addon", addons),
                    ("quest_offer_reward", offers), ("quest_request_items", requests)):
    lines.append("DELETE FROM `%s` WHERE `ID` IN (%s);" % (table, id_list))
    lines += insert(table, rows)
    lines.append("")

for table, rows in (("creature_queststarter", starters), ("creature_questender", enders)):
    lines.append("DELETE FROM `%s` WHERE `quest` IN (%s);" % (table, id_list))
    lines += insert(table, rows)
    lines.append("")

# "Retour à Kalimdor": Leoroxx sends the ogre to Orgrimmar when the quest is accepted.
lines.append("-- Leoroxx: accepting \"Retour à Kalimdor\" teleports the ogre in front of Thrall.")
lines.append("UPDATE `creature_template` SET `AIName` = 'SmartAI' WHERE `entry` = %d;" % LEOROXX)
lines.append("DELETE FROM `smart_scripts` WHERE `entryorguid` = %d AND `source_type` = 0;" % LEOROXX)
map_id, x, y, z, o = ORGRIMMAR
lines += insert("smart_scripts", [dict(
    entryorguid=LEOROXX, source_type=0, id=0, link=0, event_type=19, event_phase_mask=0, event_chance=100,
    event_flags=0, event_param1=91018, event_param2=0, event_param3=0, event_param4=0, event_param5=0,
    event_param6=0, action_type=62, action_param1=map_id, action_param2=0, action_param3=0, action_param4=0,
    action_param5=0, action_param6=0, target_type=7, target_param1=0, target_param2=0, target_param3=0,
    target_param4=0, target_x=x, target_y=y, target_z=z, target_o=o,
    comment="Leoroxx - On Quest 'Retour a Kalimdor' Accepted - Teleport Invoker to Orgrimmar")])

with open(OUT, "w", encoding="utf-8", newline="\n") as handle:
    handle.write("\n".join(lines).rstrip("\n") + "\n")
print("written", OUT)

# XP estimate (QuestXP.dbc values, difficulty 5/7/8).
QUEST_XP = {1: (80, 120, 160), 2: (170, 255, 340), 3: (250, 380, 500), 4: (355, 540, 710), 5: (450, 670, 900),
            6: (540, 810, 1080), 7: (630, 950, 1260), 8: (700, 1050, 1400), 9: (780, 1150, 1560),
            10: (840, 1250, 1680)}
total = sum(QUEST_XP[q["level"]][{5: 0, 7: 1, 8: 2}[q["xp"]]] for q in QUESTS)
print("quest xp total", total)
