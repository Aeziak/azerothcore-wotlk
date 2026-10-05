"""The Ogre racial spells, shared by the client patch (Spell.dbc, SpellIcon.dbc) and the server (spell_dbc).

Each spell is a copy of a stock Spell.dbc record with a few fields changed, so the client and the server
always describe it the same way. Run gen_spell_sql.py after a change here to regenerate the server SQL.

Spell.dbc 3.3.5 field indexes used below (234 fields, strings are offsets into the string block):
  0 ID, 3 Mechanic, 28 CastingTimeIndex, 29 RecoveryTime, 40 DurationIndex, 71-73 Effect, 74-76 DieSides,
  80-82 BasePoints (value - 1), 83-85 EffectMechanic, 86-88 TargetA, 89-91 TargetB, 92-94 RadiusIndex,
  95-97 ApplyAuraName, 110-112 MiscValue, 133 SpellIconID, 134 ActiveIconID, 136-151 Name, 153-168 Rank,
  170-185 Description, 187-202 AuraDescription (16 locales each, then a flags field), 212 MaxTargets.
"""

import struct

FIELD_COUNT = 234
FLOAT_FIELDS = {47, 77, 78, 79, 101, 102, 103, 119, 120, 121, 216, 217, 218, 229, 230, 231}
STRING_GROUPS = {"name": 136, "rank": 153, "description": 170, "aura": 187}
LEVEL_FIELDS = (38, 39)     # baseLevel, spellLevel

OGRE_ICON_ID = 4400
OGRE_ICON_PATH = "Interface\\Icons\\Achievement_Reputation_Ogre"

SPELL_TWO_MINDS = 91050      # active racial: both heads act freely (module)
SPELL_OGRE_FALL = 91051      # passive racial: no fall damage, impact on landing (module)
SPELL_OGRE_IMPACT = 91052    # the impact itself, cast by the module with its damage
SPELL_OGRE_STRIDE = 91053    # +20% speed, applied by the module out of combat in Blade's Edge
SPELL_OGRE_STRIDE_RING = 91054   # equip effect of the first quest's ring (item 91004)
SPRINT_ICON = 516

# Stances (shared by both heads, one at a time, enforced by the module). Each has a visible aura (3 effects max)
# and a hidden one the module adds with it.
SPELL_STANCE_HIT = 91060          # MOI TAPER
SPELL_STANCE_MAGIC = 91061        # MOI MAGIE
SPELL_STANCE_TANK = 91062         # MOI ENCAISSER
SPELL_STANCE_HIT_EXTRA = 91063
SPELL_STANCE_MAGIC_EXTRA = 91064
SPELL_STANCE_TANK_EXTRA = 91065
BERSERKER_ICON, ARCANE_ICON, DEFENSIVE_ICON = 84, 125, 276

# Deux cerveaux (passive racial): the head's attacks may give it one free cast (Idée fixe), its damage may give the
# body a dodge on the next melee hit taken (Réflexe d'ogre). Procs rolled and consumed by the module.
SPELL_TWO_BRAINS = 91066
SPELL_OGRE_REFLEX = 91067
SPELL_FIXED_IDEA = 91068
EVASION_ICON, CLEARCASTING_ICON = 178, 212
DURATION_20S, DURATION_30S = 18, 9

AURA_MOD_DAMAGE_PERCENT_DONE = 79
AURA_MOD_HEALING_PCT = 118                  # healing received
AURA_MOD_INCREASE_ENERGY_PERCENT = 132      # max power, misc = power type
AURA_MOD_HEALING_DONE_PERCENT = 136
AURA_MOD_TOTAL_STAT_PERCENTAGE = 137        # misc = stat
STAT_STRENGTH, STAT_AGILITY, STAT_STAMINA, STAT_INTELLECT, STAT_SPIRIT = 0, 1, 2, 3, 4
POWER_MANA = 0
MAGIC_SCHOOLS = 126
ATTR0_DO_NOT_DISPLAY = 0x80
ATTR3_ALLOW_AURA_WHILE_DEAD = 0x00100000
ATTR2_USE_SHAPESHIFT_BAR = 0x10             # shown in the stance bar, like the paladin auras
BERSERKING_ATTRIBUTES = 0x50010             # Attributes of the template (26297)


def aura_effects(effects):
    """Spell.dbc fields of up to 3 self auras: (aura, percent, misc value)."""
    fields = {}
    for k in range(3):
        aura, value, misc = effects[k] if k < len(effects) else (0, 0, 0)
        fields.update({71 + k: 6 if aura else 0, 74 + k: 1 if aura else 0, 77 + k: 0, 80 + k: value - 1 if aura else 0,
                       83 + k: 0, 86 + k: 1 if aura else 0, 89 + k: 0, 92 + k: 0, 95 + k: aura, 98 + k: 0,
                       110 + k: misc, 113 + k: 0, 116 + k: 0})
    return fields


def stance(spell_id, icon, effects, hidden, name, description="", aura=""):
    fields = {7: ATTR3_ALLOW_AURA_WHILE_DEAD, 28: 1, 29: 0 if hidden else 1500, 40: DURATION_INFINITE,
              133: icon, 134: 0, 131: 0 if hidden else 14331}
    if hidden:
        fields[4] = BERSERKING_ATTRIBUTES | ATTR0_DO_NOT_DISPLAY
    else:
        fields[6] = ATTR2_USE_SHAPESHIFT_BAR
    fields.update(aura_effects(effects))
    return dict(id=spell_id, template=26297, fields=fields, name=name, description=description, aura=aura)

AURA_MOD_INCREASE_SPEED = 31
DURATION_INFINITE = 21

AURA_DUMMY = 4

SPELLS = [
    dict(id=SPELL_TWO_MINDS, template=26297,  # Berserking (Troll): instant self buff, off the global cooldown
         fields={29: 300000, 40: 18, 71: 6, 72: 0, 73: 0, 80: 0, 95: AURA_DUMMY, 133: OGRE_ICON_ID, 134: 0},
         name="Fureur bicéphale",
         description="Pendant $d, les deux têtes agissent librement : la tête lance ses sorts sans être "
                     "interrompue par le corps, et chaque tête a son propre temps de recharge global.",
         aura="Les deux têtes agissent librement."),
    dict(id=SPELL_OGRE_FALL, template=20550,  # Endurance (Tauren): passive
         fields={80: 0, 95: AURA_DUMMY, 133: OGRE_ICON_ID},
         name="Chute d'ogre",
         description="Vous ne subissez aucun dégât de chute. Quand vous retombez d'au moins 4 mètres, l'impact "
                     "blesse et renverse les ennemis à moins de 8 mètres, d'autant plus fort que la chute est "
                     "haute (jusqu'à 300 %).",
         aura=""),
    dict(id=SPELL_OGRE_IMPACT, template=20549,  # War Stomp (Tauren): stomp visual, enemies within 8 yards
         fields={3: 0, 28: 1, 29: 0, 40: 0,
                 71: 2, 72: 98, 73: 0,             # school damage, knock back
                 74: 1, 75: 1, 76: 0,
                 80: 4, 81: 39, 82: 0,             # 5 damage (set by the module), 4 yd/s up
                 83: 0, 84: 0, 85: 0,
                 86: 18, 87: 18, 88: 0, 89: 16, 90: 16, 91: 0,
                 92: 14, 93: 14, 94: 0,
                 95: 0, 96: 0, 97: 0,
                 110: 0, 111: 60, 112: 0,          # 6 yd/s away
                 133: OGRE_ICON_ID, 212: 0},
         name="Chute d'ogre",
         description="Inflige des dégâts physiques aux ennemis proches et les renverse.",
         aura=""),
    dict(id=SPELL_OGRE_STRIDE, template=13141,  # Gnomish Rocket Boots: self speed buff
         fields={40: DURATION_INFINITE, 80: 19, 95: AURA_MOD_INCREASE_SPEED, 131: 0, 133: SPRINT_ICON},
         name="Pas de l'ogre",
         description="Vitesse de déplacement augmentée de 20 % hors combat dans les Tranchantes.",
         aura="Vitesse de déplacement augmentée de 20 %."),
    dict(id=SPELL_OGRE_STRIDE_RING, template=20550,  # Endurance: passive, here the ring's equip effect
         fields={80: 0, 95: AURA_DUMMY, 133: SPRINT_ICON},
         name="Pas de l'ogre",
         description="Augmente de 20 % votre vitesse de déplacement hors combat dans les Tranchantes.",
         aura=""),
    dict(id=SPELL_TWO_BRAINS, template=20550,  # Endurance: passive
         fields={80: 0, 95: AURA_DUMMY, 133: OGRE_ICON_ID},
         name="Deux cerveaux",
         description="Chaque attaque de la tête a 5 % de chances de lui donner Idée fixe : son sort suivant ne "
                     "peut être interrompu ni par les mouvements ni par les attaques du corps. Chaque fois que la "
                     "tête inflige des dégâts, le corps a 5 % de chances de gagner Réflexe d'ogre : il esquive la "
                     "prochaine attaque de mêlée qu'il reçoit de face.",
         aura=""),
    dict(id=SPELL_OGRE_REFLEX, template=26297,  # Berserking: visible self buff
         fields={29: 0, 40: DURATION_30S, 71: 6, 72: 0, 73: 0, 80: 0, 95: AURA_DUMMY, 131: 0, 133: EVASION_ICON,
                 134: 0},
         name="Réflexe d'ogre",
         description="Le corps esquive la prochaine attaque de mêlée qu'il reçoit de face.",
         aura="Esquive la prochaine attaque de mêlée reçue de face."),
    dict(id=SPELL_FIXED_IDEA, template=26297,
         fields={29: 0, 40: DURATION_20S, 71: 6, 72: 0, 73: 0, 80: 0, 95: AURA_DUMMY, 131: 0, 133: CLEARCASTING_ICON,
                 134: 0},
         name="Idée fixe",
         description="Le prochain sort de la tête ne peut être interrompu ni par les mouvements ni par les "
                     "attaques du corps.",
         aura="Le prochain sort de la tête ne peut pas être interrompu par le corps."),
    stance(SPELL_STANCE_HIT, BERSERKER_ICON, [
        (AURA_MOD_TOTAL_STAT_PERCENTAGE, -20, STAT_STAMINA),
        (AURA_MOD_INCREASE_ENERGY_PERCENT, -80, POWER_MANA),
        (AURA_MOD_TOTAL_STAT_PERCENTAGE, 15, STAT_INTELLECT)], False,
        "MOI TAPER",
        "Le corps se lâche : endurance réduite de 20 %. La tête suit : intelligence augmentée de 15 % et dégâts des "
        "sorts augmentés de 20 %, mais mana maximum réduit de 80 %. Une seule posture à la fois.",
        "Endurance -20 %. Intelligence +15 %, dégâts des sorts +20 %, mana maximum -80 %."),
    stance(SPELL_STANCE_MAGIC, ARCANE_ICON, [
        (AURA_MOD_TOTAL_STAT_PERCENTAGE, 20, STAT_STAMINA),
        (AURA_MOD_TOTAL_STAT_PERCENTAGE, -50, STAT_STRENGTH),
        (AURA_MOD_TOTAL_STAT_PERCENTAGE, -50, STAT_AGILITY)], False,
        "MOI MAGIE",
        "La tête prend les commandes : intelligence augmentée de 30 %, dégâts et soins des sorts augmentés de 20 %. "
        "Le corps s'en remet à elle : endurance augmentée de 20 %, force et agilité réduites de 50 %. Une seule "
        "posture à la fois.",
        "Intelligence +30 %, dégâts et soins des sorts +20 %. Endurance +20 %, force et agilité -50 %."),
    stance(SPELL_STANCE_TANK, DEFENSIVE_ICON, [
        (AURA_MOD_TOTAL_STAT_PERCENTAGE, 40, STAT_STAMINA),
        (AURA_MOD_TOTAL_STAT_PERCENTAGE, -50, STAT_STRENGTH),
        (AURA_MOD_TOTAL_STAT_PERCENTAGE, -50, STAT_AGILITY)], False,
        "MOI ENCAISSER",
        "Le corps encaisse : endurance augmentée de 40 %, soins reçus augmentés de 25 %, mais force et agilité "
        "réduites de 50 %. La tête n'est pas affectée. L'Ogre prend cette posture quand la tête n'est pas là. Une "
        "seule posture à la fois.",
        "Endurance +40 %, soins reçus +25 %. Force et agilité -50 %."),
    stance(SPELL_STANCE_HIT_EXTRA, BERSERKER_ICON, [
        (AURA_MOD_DAMAGE_PERCENT_DONE, 20, MAGIC_SCHOOLS)], True, "MOI TAPER"),
    stance(SPELL_STANCE_MAGIC_EXTRA, ARCANE_ICON, [
        (AURA_MOD_TOTAL_STAT_PERCENTAGE, 30, STAT_INTELLECT),
        (AURA_MOD_DAMAGE_PERCENT_DONE, 20, MAGIC_SCHOOLS),
        (AURA_MOD_HEALING_DONE_PERCENT, 20, 0)], True, "MOI MAGIE"),
    stance(SPELL_STANCE_TANK_EXTRA, DEFENSIVE_ICON, [
        (AURA_MOD_HEALING_PCT, 25, 0)], True, "MOI ENCAISSER"),
]

# Warrior abilities that only ask for one of the warrior stances can be used without stance: the Ogre has no
# stance, and the spell roulette may give it any of them (a warrior is always in a stance anyway).
SPELLFAMILY_WARRIOR = 4
WARRIOR_STANCES = 0x70000           # battle, defensive, berserker (1 << (form - 1))
STANCES_FIELD = 12
SPELLFAMILY_FIELD = 208
# Warlock demon summons need no soul shard (the roulette gives them without Drain Soul).
SPELLFAMILY_WARLOCK = 5
EFFECT_SUMMON_PET = 56
EFFECT_FIELDS = (71, 72, 73)
REAGENT_FIELDS = range(52, 68)              # 8 reagents, 8 counts

# The head's first spells (TwoHeadedOgre.Head.Spells) are level 4-6 spells the ogre knows from level 1: shown
# as level 1 spells.
LEVEL_ONE_SPELLS = (2136, 589)


def _header(data):
    magic, count, fields, record_size, string_size = struct.unpack_from("<4sIIII", data)
    if magic != b"WDBC" or fields != FIELD_COUNT:
        raise ValueError("unexpected Spell.dbc layout")
    return count, record_size, string_size


def all_spells():
    """The racial spells, then the Brute's talent ranks (ogre_talents.py, which builds on this module)."""
    import ogre_talents
    return SPELLS + ogre_talents.SPELLS


def read_string(data, offset):
    count, record_size, _ = _header(data)
    start = 20 + count * record_size + offset
    return data[start:data.index(b"\0", start)].decode("utf-8")


def build_records(spell_dbc):
    """New records as {field index: int or str} from their stock templates (strings already resolved)."""
    count, record_size, _ = _header(spell_dbc)
    spells = all_spells()
    templates = {spell["template"] for spell in spells}
    raw = {}
    for i in range(count):
        offset = 20 + i * record_size
        spell_id = struct.unpack_from("<I", spell_dbc, offset)[0]
        if spell_id in templates:
            raw[spell_id] = list(struct.unpack_from("<%di" % FIELD_COUNT, spell_dbc, offset))
    missing = templates - set(raw)
    if missing:
        raise SystemExit("Spell.dbc: template spells not found: %s" % sorted(missing))

    records = []
    for spell in spells:
        values = dict(enumerate(raw[spell["template"]]))
        for group in STRING_GROUPS.values():
            for locale in range(16):
                values[group + locale] = ""
        values[0] = spell["id"]
        values.update(spell["fields"])
        for key, group in STRING_GROUPS.items():
            text = spell.get(key, "")
            for locale in range(16):
                values[group + locale] = text
        records.append(values)
    return records


def patch_spell_dbc(spell_dbc):
    """Client Spell.dbc: level-one spells, stance-free warrior abilities, the Ogre racial records appended."""
    count, record_size, string_size = _header(spell_dbc)
    new_records = build_records(spell_dbc)
    data = bytearray(spell_dbc[:20 + count * record_size])
    strings = bytearray(spell_dbc[20 + count * record_size:])

    new_ids = {record[0] for record in new_records}
    found = set()
    keep = bytearray()
    for i in range(count):
        record = data[20 + i * record_size:20 + (i + 1) * record_size]
        spell_id = struct.unpack_from("<I", record, 0)[0]
        if spell_id in new_ids:
            continue                     # already patched: replaced below
        if spell_id in LEVEL_ONE_SPELLS:
            for field in LEVEL_FIELDS:
                struct.pack_into("<I", record, field * 4, 1)
            found.add(spell_id)
        stances = struct.unpack_from("<I", record, STANCES_FIELD * 4)[0]
        family = struct.unpack_from("<I", record, SPELLFAMILY_FIELD * 4)[0]
        if family == SPELLFAMILY_WARRIOR and stances and not stances & ~WARRIOR_STANCES:
            struct.pack_into("<I", record, STANCES_FIELD * 4, 0)
        effects = [struct.unpack_from("<I", record, field * 4)[0] for field in EFFECT_FIELDS]
        if family == SPELLFAMILY_WARLOCK and EFFECT_SUMMON_PET in effects:
            for field in REAGENT_FIELDS:
                struct.pack_into("<I", record, field * 4, 0)
        keep += record
    missing = set(LEVEL_ONE_SPELLS) - found
    if missing:
        raise SystemExit("Spell.dbc: spells not found: %s" % sorted(missing))

    string_offsets = {}
    for record in new_records:
        packed = bytearray(record_size)
        for field in range(FIELD_COUNT):
            value = record[field]
            if isinstance(value, str):
                if value not in string_offsets:
                    if value == "":
                        string_offsets[value] = 0
                    else:
                        string_offsets[value] = len(strings)
                        strings += value.encode("utf-8") + b"\0"
                value = string_offsets[value]
            struct.pack_into("<i", packed, field * 4, value)
        keep += packed

    new_count = len(keep) // record_size
    header = struct.pack("<4sIIII", b"WDBC", new_count, FIELD_COUNT, record_size, len(strings))
    return header + bytes(keep) + bytes(strings)


def patch_spell_icon_dbc(data):
    magic, count, fields, record_size, string_size = struct.unpack_from("<4sIIII", data)
    records = [data[20 + i * record_size:20 + (i + 1) * record_size] for i in range(count)]
    records = [r for r in records if struct.unpack_from("<I", r, 0)[0] != OGRE_ICON_ID]
    strings = bytearray(data[20 + count * record_size:])
    offset = len(strings)
    strings += OGRE_ICON_PATH.encode("ascii") + b"\0"
    records.append(struct.pack("<II", OGRE_ICON_ID, offset))
    header = struct.pack("<4sIIII", magic, len(records), fields, record_size, len(strings))
    return header + b"".join(records) + bytes(strings)


def sql_value(field, value, unsigned=frozenset()):
    """unsigned: fields whose column is unsigned (Spell.dbc stores bit masks as signed 32-bit integers)."""
    if isinstance(value, str):
        return "'" + value.replace("\\", "\\\\").replace("'", "''") + "'"
    if field in FLOAT_FIELDS:
        return repr(round(struct.unpack("<f", struct.pack("<i", value))[0], 6))
    if field in unsigned and value < 0:
        return str(value & 0xFFFFFFFF)
    return str(value)


def spell_dbc_sql(spell_dbc, columns, unsigned=frozenset()):
    """Server spell_dbc rows (columns: the table's column names, in Spell.dbc field order; unsigned: indexes of
    the unsigned ones)."""
    if len(columns) != FIELD_COUNT:
        raise ValueError("spell_dbc has %d columns, expected %d" % (len(columns), FIELD_COUNT))
    records = build_records(spell_dbc)
    ids = ", ".join(str(record[0]) for record in records)
    lines = ["DELETE FROM `spell_dbc` WHERE `ID` IN (%s);" % ids,
             "INSERT INTO `spell_dbc` (%s) VALUES" % ", ".join("`%s`" % c for c in columns)]
    rows = ["(" + ", ".join(sql_value(f, record[f], unsigned) for f in range(FIELD_COUNT)) + ")" for record in records]
    lines.append(",\n".join(rows) + ";")
    return lines
