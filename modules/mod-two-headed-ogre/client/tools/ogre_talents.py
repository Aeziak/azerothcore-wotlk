"""The Brute's talent trees, one per stance, shared by the client patch and the server (talent_dbc, talenttab_dbc).

The three Paladin tabs (the carrier class) are renamed and get new talents. The Paladin talent ids are reused for
them: the server can only override DBC rows from the database, not delete them, so the Paladin ids left over are
emptied (no tab, no rank). Each rank of a passive talent is its own passive spell (ogre_spells.SPELLS gets them),
with consecutive ids: the module reads a talent's rank from them (dummy effects do nothing on their own, the
module or a spell script of the module gives them their effect). An active talent teaches one spell of ACTIVES.

Talent.dbc 3.3.5 fields: 0 ID, 1 TabID, 2 Tier, 3 Column, 4-12 SpellRank, 13-15 PrereqTalent, 16-18 PrereqRank
(0-based), 19 Flags (1: the spell goes to the spellbook), 20 RequiredSpellID, 21-22 CategoryMask.
TalentTab.dbc 3.3.5 fields: 0 ID, 1-16 Name, 17 Name flags, 18 SpellIconID, 19 RaceMask, 20 ClassMask,
21 PetTalentMask, 22 OrderIndex, 23 BackgroundFile.
"""

import struct

from ogre_spells import (AURA_DUMMY, AURA_MOD_DAMAGE_PERCENT_DONE, AURA_MOD_HEALING_DONE_PERCENT, AURA_MOD_HEALING_PCT,
                         AURA_MOD_INCREASE_ENERGY_PERCENT, AURA_MOD_TOTAL_STAT_PERCENTAGE, ARCANE_ICON, BERSERKER_ICON,
                         DEFENSIVE_ICON, EVASION_ICON, MAGIC_SCHOOLS, OGRE_ICON_ID, POWER_MANA,
                         STAT_AGILITY, STAT_INTELLECT, STAT_SPIRIT, STAT_STAMINA, STAT_STRENGTH, aura_effects, stance)

CARRIER_CLASS_MASK = 1 << (2 - 1)       # Paladin
TALENT_TEMPLATE = 20262                 # Divine Strength (Paladin talent): passive, no equipment needed

AURA_MOD_THREAT = 10
AURA_MOD_STUN = 12
AURA_MOD_PARRY_PERCENT = 47
AURA_MOD_DODGE_PERCENT = 49
AURA_MOD_WEAPON_CRIT_PERCENT = 52
AURA_MOD_HIT_CHANCE = 54
AURA_MOD_SPELL_HIT_CHANCE = 55
AURA_MOD_SPELL_CRIT_CHANCE = 57
AURA_MOD_DAMAGE_PERCENT_TAKEN = 87
AURA_MOD_RESISTANCE_PCT = 101
AURA_ADD_FLAT_MODIFIER = 107
AURA_MOD_OFFHAND_DAMAGE_PCT = 122
AURA_MOD_INCREASE_HEALTH_PERCENT = 133
AURA_MOD_MANA_REGEN_INTERRUPT = 134
AURA_MOD_MELEE_HASTE = 138
AURA_REDUCE_PUSHBACK = 149
AURA_MOD_ATTACK_POWER_PCT = 166
AURA_MOD_RAGE_FROM_DAMAGE_DEALT = 213
SPELLMOD_COST = 14
SCHOOL_PHYSICAL, ALL_SCHOOLS = 1, 127
SPELLFAMILY_WARRIOR, HEROIC_STRIKE_FAMILY_MASK = 4, 0x40

EFFECT_DUMMY, EFFECT_APPLY_AURA, EFFECT_JUMP = 3, 6, 41
POWER_RAGE = 1
DURATION_2S, DURATION_6S = 39, 32
RANGE_8_25 = 95
# Spell.dbc proc fields of the proc talents (their spell_proc rows ask for a critical hit).
PROC_FLAGS_FIELD, PROC_CHANCE_FIELD = 34, 35
PROC_FLAG_DONE_MELEE = 0x4 | 0x10               # auto attacks and melee abilities
PROC_FLAG_DONE_SPELL_MAGIC_NEG = 0x10000        # harmful magic spells

# Ultimate talents: a hidden aura the module adds while the talent's stance is on (multiplies the stance's own).
SPELL_HIT_ULTIMATE_BONUS = 91070        # MOI TAPER FORT
SPELL_MAGIC_ULTIMATE_BONUS = 91071      # Tête pensante
SPELL_TANK_ULTIMATE_BONUS = 91072       # Montagne

# Spells taught by active talents, and the module's helper spells.
SPELL_HEADBUTT = 91320                  # Coup de boule
SPELL_BLOOD_FURY = 91321                # Fureur sanguine (Orc racial)
SPELL_BERSERKING = 91322                # Berserker (Troll racial)
SPELL_WAR_STOMP = 91323                 # Choc martial (Tauren racial)
SPELL_SHOUTING_MATCH = 91324            # Engueulade
SPELL_OGRE_GRIP = 91325                 # Poigne d'ogre (spell_ogre_grip)
SPELL_OGRE_LEAP = 91326                 # Bond d'ogre (spell_ogre_leap)
SPELL_OGRE_JUMP = 91327                 # Saut d'ogre (spell_ogre_jump)
SPELL_MIGRAINE = 91328                  # Migraine's buff, cast by spell_ogre_migraine
SPELL_SHATTERING_LANDING = 91329        # Atterrissage fracassant's stun, cast by the module with its duration


def dummy_effect(target=1):
    """Spell.dbc fields of a lone dummy effect (effect 0), the other effects cleared."""
    fields = aura_effects([])
    fields.update({71: EFFECT_DUMMY, 74: 1, 80: 0, 86: target})
    return fields


ACTIVES = [
    dict(id=SPELL_HEADBUTT, template=12809,     # Concussion Blow: the stun alone, free, 2 s
         fields={12: 0, 40: DURATION_2S, 41: POWER_RAGE, 42: 0, 68: -1, 69: 0,
                 72: 0, 73: 0, 75: 0, 76: 0, 81: 0, 82: 0, 84: 0, 85: 0, 87: 0, 88: 0, 96: 0, 97: 0,
                 208: 0, 209: 0},
         name="Coup de boule",
         description="Une des têtes donne un grand coup de boule à la cible, qui est étourdie pendant $d."),
    dict(id=SPELL_BLOOD_FURY, template=20572, fields={},
         name="Fureur sanguine",
         description="Augmente votre puissance d'attaque de $s1 pendant $d.",
         aura="Puissance d'attaque augmentée de $s1."),
    dict(id=SPELL_BERSERKING, template=26297, fields={},
         name="Berserker",
         description="Augmente de $s1 % votre vitesse d'attaque et d'incantation pendant $d.",
         aura="Vitesse d'attaque et d'incantation augmentées de $s1 %."),
    dict(id=SPELL_WAR_STOMP, template=20549, fields={},
         name="Choc martial",
         description="Étourdit jusqu'à 5 ennemis à moins de $a1 mètres pendant $d."),
    dict(id=SPELL_SHOUTING_MATCH, template=1161,    # Challenging Shout, free, 2 min
         fields={12: 0, 29: 120000, 42: 0, 208: 0, 209: 0},
         name="Engueulade",
         description="Les deux têtes se hurlent dessus si fort que tous les ennemis à moins de $a1 mètres vous "
                     "attaquent pendant $d."),
    dict(id=SPELL_OGRE_GRIP, template=49576,        # Death Grip, no rune, 25 s; the pull is spell_ogre_grip
         fields={29: 25000, 38: 1, 39: 1, 41: 0, 42: 0, 208: 0, 209: 0, 226: 0},
         name="Poigne d'ogre",
         description="Attrape la cible et l'attire jusqu'à vous en interrompant son incantation."),
    dict(id=SPELL_OGRE_LEAP, template=20252,        # Intercept turned into a jump at the target; spell_ogre_leap
         fields={1: 0, 4: 0x50010, 5: 0, 10: 0, 11: 0, 12: 0, 27: 0, 29: 30000, 30: 0, 41: POWER_RAGE, 42: 100,
                 46: RANGE_8_25, 71: EFFECT_JUMP, 72: 0, 86: 6, 87: 0, 110: 50, 117: 0, 133: 457, 208: 0, 209: 0},
         name="Bond d'ogre",
         description="Bondit sur la cible. À l'atterrissage, Chute d'ogre frappe à 200 % de sa puissance."),
    dict(id=SPELL_OGRE_JUMP, template=26297,        # Berserking turned into a dummy: spell_ogre_jump
         fields={**dummy_effect(), 29: 45000, 40: 0, 41: POWER_RAGE, 42: 100, 131: 0, 133: OGRE_ICON_ID},
         name="Saut d'ogre",
         description="Bondit très haut sur place. À l'atterrissage, Chute d'ogre frappe à 300 % de sa puissance."),
    dict(id=SPELL_MIGRAINE, template=26297,
         fields={**aura_effects([(AURA_MOD_WEAPON_CRIT_PERCENT, 2, 0)]),
                 29: 0, 40: DURATION_6S, 41: 0, 42: 0, 131: 0, 133: 1952},
         name="Migraine",
         description="Chances de coup critique en mêlée augmentées de $s1 %.",
         aura="Chances de coup critique en mêlée augmentées de $s1 %."),
    dict(id=SPELL_SHATTERING_LANDING, template=20549,   # War Stomp: instant, the module sets the duration
         fields={12: 0, 28: 1, 29: 0, 31: 0, 131: 0, 133: 129, 212: 0},
         name="Atterrissage fracassant",
         description="Étourdi."),
]


def talent(spell_id, tier, column, icon, name, values, effects, description, prereq=None, fields=None):
    """A passive talent. values: the talent's value per rank; effects: (aura, misc) per effect, all of the rank's
    value (aura None: a dummy carrying the value for the module). description: "{v}" is the value, "{a}" its
    absolute value, "{t}" a tenth of it, "{s}" a thousandth (ms to s). prereq: first rank of the talent needed at
    its maximum rank."""
    return dict(id=spell_id, tier=tier, column=column, icon=icon, name=name, values=values, effects=effects,
                description=description, prereq=prereq, fields=fields or {})


def active(spell_id, tier, column, prereq=None):
    """An active talent: one rank, the spell (ACTIVES) goes to the spellbook."""
    return dict(id=spell_id, tier=tier, column=column, values=[0], active=True, prereq=prereq)


def proc(flags):
    return {PROC_FLAGS_FIELD: flags, PROC_CHANCE_FIELD: 100}


# Talents the module or its spell scripts drive (first rank).
SHARED_RAGE, DOUBLE_HIT, LONG_FURY, BATTLE_TRANCE, HIT_ULTIMATE = 91135, 91145, 91155, 91160, 91165
CHATTER, MIGRAINE, FIXED_IDEAS, BRAINSTORM, QUICK_THINKING, ONE_IDEA, MAGIC_ULTIMATE = (91180, 91205, 91215, 91220,
                                                                                    91230, 91240, 91245)
IMPROVED_REFLEX, BACKLASH, HEAVY_FALL, SHATTERING, SURVIVAL, SPARE_HEAD, TANK_ULTIMATE = (91285, 91290, 91295, 91305,
                                                                                       91310, 91315, 91316)
PROC_TALENTS = (BATTLE_TRANCE, MIGRAINE)

TREES = [
    dict(tab=381, name="MOI TAPER", icon=BERSERKER_ICON, order=0, background="PaladinCombat", talents=[
        talent(91100, 0, 0, 63, "Poings lourds", [2, 4, 6, 8, 10], [(AURA_MOD_TOTAL_STAT_PERCENTAGE, STAT_STRENGTH)],
               "Augmente votre force de {v} %."),
        talent(91105, 0, 1, 86, "Colère d'ogre", [10, 20, 30], [(AURA_MOD_RAGE_FROM_DAMAGE_DEALT, 0)],
               "Augmente de {v} % la rage générée par vos attaques."),
        talent(91110, 0, 2, 856, "Gros calibre", [-10, -20], [(AURA_ADD_FLAT_MODIFIER, SPELLMOD_COST)],
               "Réduit de {t} le coût en rage de Frappe héroïque.",
               fields={122: HEROIC_STRIKE_FAMILY_MASK, 208: SPELLFAMILY_WARRIOR}),
        talent(91115, 1, 0, 138, "Brutalité", [1, 2, 3, 4, 5], [(AURA_MOD_WEAPON_CRIT_PERCENT, 0)],
               "Augmente de {v} % vos chances de coup critique en mêlée."),
        talent(91120, 1, 1, 533, "Quatre poings", [5, 10, 15], [(AURA_MOD_OFFHAND_DAMAGE_PCT, 0)],
               "Augmente de {v} % les dégâts de votre arme de main gauche."),
        active(SPELL_HEADBUTT, 1, 2),
        talent(91125, 2, 0, 108, "Frénésie", [2, 4, 6, 8, 10], [(AURA_MOD_MELEE_HASTE, 0)],
               "Augmente de {v} % votre vitesse d'attaque en mêlée."),
        talent(91130, 2, 1, 126, "Poigne", [1, 2, 3], [(AURA_MOD_HIT_CHANCE, 0)],
               "Augmente de {v} % vos chances de toucher en mêlée."),
        active(SPELL_BLOOD_FURY, 2, 2),
        talent(SHARED_RAGE, 3, 0, 2024, "Rage partagée", [2, 4, 6], [(None, 0)],
               "Chaque sort offensif lancé par la tête donne {v} points de rage au corps."),
        talent(91140, 3, 1, 1531, "Sauvagerie", [2, 4, 6], [(AURA_MOD_ATTACK_POWER_PCT, 0)],
               "Augmente votre puissance d'attaque de {v} %."),
        talent(DOUBLE_HIT, 3, 2, 559, "Coup double", [10, 20, 30], [(None, 0)],
               "Quand la tête vient de toucher une cible avec un sort, la prochaine attaque du corps sur cette "
               "cible dans les 3 s inflige {v} % de dégâts en plus."),
        talent(91150, 4, 0, 25, "Coups sonnants", [2, 4, 6], [(AURA_MOD_DAMAGE_PERCENT_DONE, SCHOOL_PHYSICAL)],
               "Augmente de {v} % vos dégâts physiques."),
        active(SPELL_OGRE_LEAP, 4, 1),
        talent(LONG_FURY, 5, 0, OGRE_ICON_ID, "Fureur prolongée", [5, 10], [(None, 0)],
               "Fureur bicéphale dure {v} s de plus."),
        talent(BATTLE_TRANCE, 5, 2, 1962, "Ivresse du combat", [2, 4], [(None, 0)],
               "Chaque coup critique du corps en mêlée réduit de {v} s le temps de recharge de Fureur bicéphale.",
               prereq=DOUBLE_HIT, fields=proc(PROC_FLAG_DONE_MELEE)),
        talent(HIT_ULTIMATE, 6, 1, 2006, "MOI TAPER FORT", [1], [(None, 0)],
               "En posture MOI TAPER, vos dégâts physiques sont augmentés de 10 % et le mana maximum de la tête "
               "n'est plus réduit que de 60 %."),
    ]),
    dict(tab=382, name="MOI MAGIE", icon=ARCANE_ICON, order=1, background="PaladinHoly", talents=[
        talent(91170, 0, 0, 125, "Esprit vif", [2, 4, 6, 8, 10], [(AURA_MOD_TOTAL_STAT_PERCENTAGE, STAT_INTELLECT)],
               "Augmente votre intelligence de {v} %."),
        talent(91175, 0, 1, 44, "Méditation d'ogre", [10, 20, 30], [(AURA_MOD_MANA_REGEN_INTERRUPT, 0)],
               "Permet à {v} % de votre récupération de mana de continuer pendant les incantations."),
        talent(CHATTER, 0, 2, 502, "Bavardage", [5, 10], [(None, 0)],
               "« Aïe ! » Chaque coup reçu par le corps en mêlée rend {v} pour mille du mana maximum à la tête."),
        talent(91185, 1, 0, 1918, "Précision", [1, 2, 3], [(AURA_MOD_SPELL_HIT_CHANCE, 0)],
               "Augmente de {v} % vos chances de toucher avec vos sorts."),
        talent(91190, 1, 1, 2215, "Concentration", [23, 46, 70], [(AURA_REDUCE_PUSHBACK, 0)],
               "Réduit de {v} % le temps d'incantation perdu quand vous subissez des dégâts."),
        active(SPELL_BERSERKING, 1, 2),
        talent(91195, 2, 0, 1952, "Puissance mentale", [1, 2, 3, 4, 5], [(AURA_MOD_SPELL_CRIT_CHANCE, 0)],
               "Augmente de {v} % vos chances de coup critique avec vos sorts."),
        talent(91200, 2, 1, 306, "Sagesse d'ogre", [3, 6, 9], [(AURA_MOD_TOTAL_STAT_PERCENTAGE, STAT_SPIRIT)],
               "Augmente votre esprit de {v} %."),
        talent(MIGRAINE, 2, 2, 98, "Migraine", [2, 4, 6], [(None, 0)],
               "Chaque coup critique d'un sort offensif de la tête augmente de {v} % les chances de coup critique "
               "du corps en mêlée pendant 6 s.", fields=proc(PROC_FLAG_DONE_SPELL_MAGIC_NEG)),
        talent(91210, 3, 0, 184, "Pouvoir des sorts", [2, 4, 6, 8, 10], [(AURA_MOD_DAMAGE_PERCENT_DONE, MAGIC_SCHOOLS)],
               "Augmente de {v} % les dégâts de vos sorts."),
        talent(FIXED_IDEAS, 3, 1, 212, "Idées fixes", [3, 5], [(None, 0)],
               "Augmente de {v} % les chances que la tête gagne Idée fixe (Deux cerveaux)."),
        talent(BRAINSTORM, 3, 2, 1872, "Éclair de génie", [1, 2], [(None, 0)],
               "Idée fixe rend aussi instantané le prochain sort de la tête. Au rang 2, ce sort ne coûte en plus "
               "rien.", prereq=FIXED_IDEAS),
        talent(91225, 4, 0, 70, "Guérisseur ogre", [3, 6, 9], [(AURA_MOD_HEALING_DONE_PERCENT, 0)],
               "Augmente de {v} % les soins prodigués par vos sorts."),
        talent(QUICK_THINKING, 4, 1, 58, "Pensée rapide", [1, 2], [(None, 0)],
               "Réduit de {v} min le temps de recharge de Fureur bicéphale."),
        talent(91235, 5, 0, 2152, "Réserves", [5, 10], [(AURA_MOD_INCREASE_ENERGY_PERCENT, POWER_MANA)],
               "Augmente votre mana maximum de {v} %."),
        talent(ONE_IDEA, 5, 2, 71, "Deux cerveaux, une idée", [1], [(None, 0)],
               "Quand la tête gagne Idée fixe, le corps gagne aussi Réflexe d'ogre, et inversement.",
               prereq=BRAINSTORM),
        talent(MAGIC_ULTIMATE, 6, 1, 2121, "Tête pensante", [1], [(None, 0)],
               "En posture MOI MAGIE, votre mana maximum est augmenté de 20 % et le corps ne perd plus que 30 % de "
               "sa force et de son agilité."),
    ]),
    dict(tab=383, name="MOI ENCAISSER", icon=DEFENSIVE_ICON, order=2, background="PaladinProtection", talents=[
        talent(91250, 0, 0, 1558, "Peau épaisse", [2, 4, 6, 8, 10], [(AURA_MOD_RESISTANCE_PCT, SCHOOL_PHYSICAL)],
               "Augmente de {v} % l'armure apportée par vos objets."),
        talent(91255, 0, 1, 312, "Robustesse", [2, 4, 6, 8, 10], [(AURA_MOD_TOTAL_STAT_PERCENTAGE, STAT_STAMINA)],
               "Augmente votre endurance de {v} %."),
        active(SPELL_SHOUTING_MATCH, 0, 2),
        talent(91260, 1, 0, 30, "Réflexes", [1, 2, 3, 4, 5], [(AURA_MOD_DODGE_PERCENT, 0)],
               "Augmente de {v} % vos chances d'esquiver."),
        talent(91265, 1, 1, 1463, "Cuir dur", [-2, -4, -6], [(AURA_MOD_DAMAGE_PERCENT_TAKEN, ALL_SCHOOLS)],
               "Réduit de {a} % tous les dégâts subis."),
        active(SPELL_OGRE_GRIP, 1, 2),
        talent(91270, 2, 0, 963, "Second souffle", [5, 10, 15], [(AURA_MOD_HEALING_PCT, 0)],
               "Augmente de {v} % les soins que vous recevez."),
        talent(91275, 2, 1, 1477, "Rancune", [10, 20, 30], [(AURA_MOD_THREAT, ALL_SCHOOLS)],
               "Augmente de {v} % la menace que vous générez."),
        active(SPELL_WAR_STOMP, 2, 2),
        talent(91280, 3, 0, 558, "Bloc de chair", [1, 2, 3], [(AURA_MOD_PARRY_PERCENT, 0)],
               "Augmente de {v} % vos chances de parer."),
        talent(IMPROVED_REFLEX, 3, 1, EVASION_ICON, "Réflexe d'ogre amélioré", [3, 5], [(None, 0)],
               "Augmente de {v} % les chances que le corps gagne Réflexe d'ogre (Deux cerveaux)."),
        talent(BACKLASH, 3, 2, 563, "Riposte bicéphale", [50, 100], [(None, 0)],
               "Après une esquive due à Réflexe d'ogre, la prochaine attaque automatique du corps a {v} % de "
               "chances d'être un coup critique.", prereq=IMPROVED_REFLEX),
        active(SPELL_OGRE_JUMP, 4, 0),
        talent(HEAVY_FALL, 4, 1, 129, "Chute lourde", [25, 50], [(None, 0)],
               "Augmente de {v} % les dégâts de l'impact de Chute d'ogre."),
        talent(91300, 5, 0, 238, "Gros dos", [2, 4, 6], [(AURA_MOD_INCREASE_HEALTH_PERCENT, 0)],
               "Augmente votre vie maximum de {v} %."),
        talent(SHATTERING, 5, 1, 66, "Atterrissage fracassant", [500, 1000], [(None, 0)],
               "L'impact de Chute d'ogre étourdit aussi les ennemis touchés pendant {s} s.", prereq=HEAVY_FALL),
        talent(SURVIVAL, 5, 2, 2178, "Instinct de survie", [1], [(None, 0)],
               "Quand votre vie passe sous 30 % en combat, Fureur bicéphale se déclenche pendant 15 s sans "
               "déclencher son temps de recharge. Une fois toutes les 2 min au plus."),
        talent(SPARE_HEAD, 6, 2, 2785, "Tête de rechange", [1], [(None, 0)],
               "Un coup qui devrait vous tuer vous laisse à 1 point de vie : la tête encaisse à la place du corps. "
               "Une fois toutes les 3 min au plus.", prereq=SURVIVAL),
        talent(TANK_ULTIMATE, 7, 1, 281, "Montagne", [1], [(None, 0)],
               "En posture MOI ENCAISSER, votre vie maximum est augmentée de 10 % et les soins que vous recevez "
               "sont augmentés de 40 % au lieu de 25 %."),
    ]),
]


def _talent_spells():
    spells = []
    for tree in TREES:
        for entry in tree["talents"]:
            if entry.get("active"):
                continue
            ranks = len(entry["values"])
            for rank, value in enumerate(entry["values"]):
                fields = aura_effects([(aura or AURA_DUMMY, value, misc) for aura, misc in entry["effects"]])
                fields[133] = entry["icon"]
                fields.update(entry["fields"])
                text = entry["description"].format(v=value, a=abs(value), t=abs(value) // 10,
                                                   s=("%g" % (value / 1000)).replace(".", ","))
                spells.append(dict(id=entry["id"] + rank, template=TALENT_TEMPLATE, fields=fields, name=entry["name"],
                                   rank="Rang %d" % (rank + 1) if ranks > 1 else "", description=text, aura=""))
    return spells


# Ultimate bonuses: (aura, percent, misc), multiplying the stance's own effects (percent modifiers multiply).
ULTIMATE_BONUSES = [
    stance(SPELL_HIT_ULTIMATE_BONUS, BERSERKER_ICON, [
        (AURA_MOD_DAMAGE_PERCENT_DONE, 10, SCHOOL_PHYSICAL),
        (AURA_MOD_INCREASE_ENERGY_PERCENT, 100, POWER_MANA)], True, "MOI TAPER FORT"),     # x0.2 -> x0.4 mana
    stance(SPELL_MAGIC_ULTIMATE_BONUS, ARCANE_ICON, [
        (AURA_MOD_INCREASE_ENERGY_PERCENT, 20, POWER_MANA),
        (AURA_MOD_TOTAL_STAT_PERCENTAGE, 40, STAT_STRENGTH),                                # x0.5 -> x0.7
        (AURA_MOD_TOTAL_STAT_PERCENTAGE, 40, STAT_AGILITY)], True, "Tête pensante"),
    stance(SPELL_TANK_ULTIMATE_BONUS, DEFENSIVE_ICON, [
        (AURA_MOD_INCREASE_HEALTH_PERCENT, 10, 0),
        (AURA_MOD_HEALING_PCT, 12, 0)], True, "Montagne"),                                  # x1.25 -> x1.4
]

SPELLS = _talent_spells() + ULTIMATE_BONUSES + ACTIVES


def talent_spell_ids():
    """Every spell a learned talent is saved as (character_talent.spell)."""
    return sorted(entry["id"] + rank for tree in TREES for entry in tree["talents"]
                  for rank in range(len(entry["values"])))


def _carrier_talent_ids(talent_dbc):
    tabs = {tree["tab"] for tree in TREES}
    magic, count, fields, record_size, _ = struct.unpack_from("<4sIIII", talent_dbc)
    ids = []
    for i in range(count):
        talent_id, tab = struct.unpack_from("<II", talent_dbc, 20 + i * record_size)
        if tab in tabs:
            ids.append(talent_id)
    return sorted(ids)


def talent_rows(talent_dbc):
    """Talent.dbc rows (23 ints) replacing the carrier class' talents: the new talents, then the emptied ids."""
    ids = _carrier_talent_ids(talent_dbc)
    entries = [(tree, entry) for tree in TREES for entry in tree["talents"]]
    if len(entries) > len(ids):
        raise SystemExit("Talent.dbc: %d talents for %d Paladin ids" % (len(entries), len(ids)))
    by_spell = {entry["id"]: (talent_id, entry) for talent_id, (_, entry) in zip(ids, entries)}
    rows = []
    for talent_id, (tree, entry) in zip(ids, entries):
        ranks = [entry["id"] + rank for rank in range(len(entry["values"]))]
        prereq, prereq_rank = 0, 0
        if entry["prereq"]:
            prereq, needed = by_spell[entry["prereq"]]
            prereq_rank = len(needed["values"]) - 1
        flags = 1 if entry.get("active") else 0
        rows.append([talent_id, tree["tab"], entry["tier"], entry["column"]] + ranks + [0] * (9 - len(ranks))
                    + [prereq, 0, 0, prereq_rank, 0, 0, flags, 0, 0, 0])
    empty = [[talent_id] + [0] * 22 for talent_id in ids[len(entries):]]
    return rows, empty


def patch_talent_dbc(data):
    """Client Talent.dbc: the Paladin talents removed, the Brute talents added."""
    magic, count, fields, record_size, string_size = struct.unpack_from("<4sIIII", data)
    rows, _ = talent_rows(data)
    removed = set(_carrier_talent_ids(data))
    records = [data[20 + i * record_size:20 + (i + 1) * record_size] for i in range(count)]
    records = [r for r in records if struct.unpack_from("<I", r, 0)[0] not in removed]
    records += [struct.pack("<23i", *row) for row in rows]
    strings = data[20 + count * record_size:]
    return struct.pack("<4sIIII", magic, len(records), fields, record_size, string_size) + b"".join(records) + strings


def patch_talent_tab_dbc(data):
    """Client TalentTab.dbc: the Paladin tabs renamed after the stances."""
    magic, count, fields, record_size, string_size = struct.unpack_from("<4sIIII", data)
    records = [bytearray(data[20 + i * record_size:20 + (i + 1) * record_size]) for i in range(count)]
    strings = bytearray(data[20 + count * record_size:])
    trees = {tree["tab"]: tree for tree in TREES}
    for record in records:
        tree = trees.get(struct.unpack_from("<I", record, 0)[0])
        if not tree:
            continue
        name = len(strings)
        strings += tree["name"].encode("utf-8") + b"\0"
        for locale in range(16):
            struct.pack_into("<I", record, (1 + locale) * 4, name)
        struct.pack_into("<I", record, 18 * 4, tree["icon"])
        struct.pack_into("<I", record, 22 * 4, tree["order"])
    header = struct.pack("<4sIIII", magic, count, fields, record_size, len(strings))
    return header + b"".join(bytes(r) for r in records) + bytes(strings)


def _quote(text):
    return "'" + text.replace("\\", "\\\\").replace("'", "''") + "'"


def talent_sql(talent_dbc):
    """Server rows: talent_dbc, talenttab_dbc, spell_proc of the proc talents (critical hits only) and the spell
    scripts of the module."""
    rows, empty = talent_rows(talent_dbc)
    all_rows = rows + empty
    lines = ["DELETE FROM `talent_dbc` WHERE `ID` IN (%s);" % ", ".join(str(row[0]) for row in all_rows),
             "INSERT INTO `talent_dbc` VALUES",
             ",\n".join("(" + ", ".join(str(v) for v in row) + ")" for row in all_rows) + ";",
             "DELETE FROM `talenttab_dbc` WHERE `ID` IN (%s);" % ", ".join(str(tree["tab"]) for tree in TREES),
             "INSERT INTO `talenttab_dbc` VALUES"]
    tabs = []
    for tree in TREES:
        values = [str(tree["tab"])] + [_quote(tree["name"])] * 16 + ["16712190", str(tree["icon"]), "2047",
                                                                     str(CARRIER_CLASS_MASK), "0", str(tree["order"]),
                                                                     _quote(tree["background"])]
        tabs.append("(" + ", ".join(values) + ")")
    lines.append(",\n".join(tabs) + ";")

    talents = {entry["id"]: entry for tree in TREES for entry in tree["talents"]}
    proc_ranks = [first + rank for first in PROC_TALENTS for rank in range(len(talents[first]["values"]))]
    lines += ["DELETE FROM `spell_proc` WHERE `SpellId` IN (%s);" % ", ".join(str(s) for s in proc_ranks),
              "INSERT INTO `spell_proc` (`SpellId`, `SpellTypeMask`, `SpellPhaseMask`, `HitMask`) VALUES",
              ",\n".join("(%d, 1, 2, 2)" % s for s in proc_ranks) + ";"]

    scripts = [(SPELL_OGRE_GRIP, "spell_ogre_grip"), (SPELL_OGRE_LEAP, "spell_ogre_leap"),
               (SPELL_OGRE_JUMP, "spell_ogre_jump")]
    scripts += [(first + rank, name) for first, name in ((BATTLE_TRANCE, "spell_ogre_battle_trance"),
                                                        (MIGRAINE, "spell_ogre_migraine"))
                for rank in range(len(talents[first]["values"]))]
    lines += ["DELETE FROM `spell_script_names` WHERE `spell_id` IN (%s);" % ", ".join(str(s) for s, _ in scripts),
              "INSERT INTO `spell_script_names` (`spell_id`, `ScriptName`) VALUES",
              ",\n".join("(%d, '%s')" % script for script in scripts) + ";"]
    return lines


def talent_reset_sql():
    """Characters: talents that are no talent any more (the Paladin's, or a Brute talent removed since) are
    dropped, the server refuses to load them; their points come back."""
    ids = ", ".join(str(spell) for spell in talent_spell_ids())
    return ["DELETE `ct` FROM `character_talent` `ct`",
            "INNER JOIN `characters` `c` ON `c`.`guid` = `ct`.`guid`",
            "WHERE `c`.`class` = 2 AND `ct`.`spell` NOT IN (%s);" % ids]
