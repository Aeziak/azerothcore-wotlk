"""Generate mod-two-headed-ogre starter zone SQL: every Blade's Edge Mountains creature rescaled to levels 1-10.

Two passes:
  - CREATURES: the start zone proper (Thunderlord Stronghold -> Mok'Nathal Village), tuned by hand.
  - every other attackable creature spawned in Blade's Edge (found from the server map files, see zones.py):
    levels by distance from Thunderlord Stronghold, elites kept but capped, and SmartAI casts of high level
    fixed-damage, healing or summoning spells removed automatically.
Both get Eversong Woods loot (Blood elf start zone) for their level and type.

Usage: python gen_start_zone.py [--data <server data dir with maps/ and dbc/>] [--db host:port:user:pass:db]
Reads the world database: it can run before or after the generated SQL was applied.
"""
import argparse
import math
import os
import struct

import mysql.connector

from zones import Zones

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "data", "sql", "db-world", "base",
                   "mod_two_headed_ogre_start_zone.sql")

BLADES_EDGE = 3522
OUTLAND = 530
THUNDERLORD = (2330.0, 6000.0)

HUMANOID = "humanoid"
BEAST = "beast"
NO_LOOT = "none"
# Eversong Woods loot (Blood elf start zone) by level.
LOOT_SOURCES = {
    HUMANOID: [(4, 15644), (6, 16162), (8, 15645), (99, 15643)],
    BEAST: [(1, 15366), (3, 15372), (5, 15649), (6, 15651), (7, 15650), (99, 15652)],
}

# entry: (min level, max level, kind, rank, health mod, damage mod, quest drops [(item, chance)])
CREATURES = {
    # Around Thunderlord Stronghold
    21033: (1, 2, BEAST, 0, 1, 1, [(38620, 60)]),           # Bladewing Bloodletter: bat wing (Old Orok)
    20748: (2, 3, BEAST, 0, 1, 1, []),                      # Thunderlord Dire Wolf (Horde-friendly, healed)
    # Bloodmaul Outpost (west)
    19948: (3, 4, HUMANOID, 0, 1, 1, [(91002, 30)]),        # Bloodmaul Skirmisher
    19956: (3, 4, HUMANOID, 0, 1, 1, [(91002, 30)]),        # Bloodmaul Lookout
    20058: (3, 4, BEAST, 0, 1, 1, []),                      # Bloodmaul Dire Wolf
    19952: (4, 5, HUMANOID, 0, 1, 1, [(91002, 30)]),        # Bloodmaul Geomancer
    19991: (4, 5, HUMANOID, 0, 1, 1, [(91002, 30)]),        # Bloodmaul Brute
    21238: (4, 5, HUMANOID, 0, 1, 1, [(91002, 30)]),        # Bloodmaul Drudger
    19992: (5, 5, HUMANOID, 0, 1, 1, [(91002, 30)]),        # Bloodmaul Shaman
    19957: (5, 5, HUMANOID, 0, 1, 1, [(91002, 80)]),        # Bloodmaul Brewmaster
    # Bladespire Hold (north-east)
    19995: (5, 6, HUMANOID, 0, 1, 1, []),                   # Bladespire Brute
    19998: (5, 6, HUMANOID, 0, 1, 1, []),                   # Bladespire Shaman
    20728: (5, 6, BEAST, 0, 1, 1, []),                      # Bladespire Raptor
    20334: (6, 6, HUMANOID, 0, 1, 1, []),                   # Bladespire Cook
    21975: (6, 7, HUMANOID, 0, 1, 1, []),                   # Bladespire Sober Defender (was elite)
    21296: (7, 7, HUMANOID, 0, 1.2, 1.1, []),               # Bladespire Champion
    # Road south to Mok'Nathal Village
    22123: (6, 7, BEAST, 0, 1, 1, []),                      # Rip-Blade Ravager
    21423: (6, 7, BEAST, 0, 1, 1, []),                      # Gore-Scythe Ravager
    20766: (7, 8, HUMANOID, 0, 1, 1, []),                   # Bladespire Mystic
    20765: (7, 8, HUMANOID, 0, 1, 1, []),                   # Bladespire Crusher
    20768: (9, 9, HUMANOID, 0, 1.5, 1.2, []),               # Gnosh Brognat
    20600: (10, 10, HUMANOID, 1, 2.5, 1.2, []),             # Maggoc (elite boss, ~500 HP)
    18690: (9, 9, HUMANOID, 4, 2, 1.2, []),                 # Morcrush (rare)
    21519: (8, 9, HUMANOID, 0, 1, 1, []),                   # Death's Might
    21516: (8, 9, HUMANOID, 0, 1, 1, []),                   # Death's Watch
    19980: (8, 9, HUMANOID, 0, 1, 1, []),                   # Void Terror
    19747: (10, 10, HUMANOID, 1, 2.5, 1.2, []),             # Baelmon the Hound-Master (elite)
    21837: (9, 9, NO_LOOT, 0, 1, 1, []),                    # Summoned Wrath Hound (Baelmon's patrol)
    20714: (7, 8, BEAST, 0, 1, 1, []),                      # Ridgespine Stalker
    20749: (7, 8, BEAST, 0, 1, 1, []),                      # Scalewing Serpent
    20751: (7, 8, BEAST, 0, 1, 1, []),                      # Daggermaw Lashtail
    # Around Mok'Nathal Village
    20747: (8, 9, BEAST, 0, 1, 1, [(30791, 80)]),           # Silkwing Larva: Silkwing Cocoon
    21839: (8, 9, BEAST, 0, 1, 1, [(30792, 80)]),           # Mature Silkwing: Iridescent Wing
    21373: (8, 9, BEAST, 0, 1, 1, [(30792, 80)]),           # Silkwing (summoned by larvae): Iridescent Wing
}
# Thunderlord Dire Wolf is never killed (quest heals it): no loot change needed but harmless.

# (entry, row id) -> None (remove) or (new spell, comment)
SPELL_CHANGES = {
    (21033, 0): None,                                       # Poison Spit (39-63 + DoT)
    (21033, 1): None,                                       # Blood Leech
    (20728, 0): None,                                       # raptor DoT 28/tick + slow
    (20714, 0): None,                                       # Poison 13/tick
    (21423, 0): None,                                       # thorns 40 + 3.2/level per hit taken
    (22123, 0): None,                                       # thorns
    (20600, 1): None,                                       # Rock Rumble 101
    (20600, 2): None,                                       # Boulder 151
    (20600, 5): None,                                       # level 70 treasure chest
    (18690, 1): None, (18690, 2): None, (18690, 3): None,   # level 65 shardlings
    (19747, 12): None,                                      # fire DoT
    (19747, 13): None, (19747, 14): None,                   # summon + linked say
    (19980, 0): None,                                       # periodic trigger
    (21837, 9): None,                                       # periodic trigger
    (21516, 0): None,                                       # +50% damage taken
    (21516, 1): (172, "Death's Watch - In Combat - Cast 'Corruption' (Ogre start zone)"),
    (19992, 3): (403, "Bloodmaul Shaman - In Combat - Cast 'Lightning Bolt' (Ogre start zone)"),
    (19992, 4): None,                                       # Superior Healing Ward
    (20334, 2): None,                                       # Meat Slap (+30 flat)
    (19952, 3): (133, "Bloodmaul Geomancer - In Combat - Cast 'Fireball' (Ogre start zone)"),
    (19998, 3): (403, "Bladespire Shaman - In Combat - Cast 'Lightning Bolt' (Ogre start zone)"),
    (20749, 0): (403, "Scalewing Serpent - In Combat - Cast 'Lightning Bolt' (Ogre start zone)"),
    (20749, 1): None,                                       # credit of the original quest
    (20766, 4): (332, "Bladespire Mystic - Friendly HP below 40% - Cast 'Healing Wave' (Ogre start zone)"),
}

# Second pass: never touched (Mok'Nathal Village pets, quest props).
AUTO_SKIP = {22142, 22136, 22141, 22135, 22233, 22130, 22108}
# Second pass levels, by distance (yards) from Thunderlord Stronghold.
AUTO_LEVELS = [(700, 7, 8), (1200, 8, 9), (math.inf, 9, 10)]
# Second pass health/damage modifiers by rank (0 normal, 1 elite, 2 rare elite, 3 boss, 4 rare).
AUTO_MODIFIERS = {0: (1, 1), 1: (2, 1.3), 2: (2, 1.2), 3: (3, 1.5), 4: (2, 1.2)}

# SmartAI actions casting a spell (spell in action_param1) and summoning a creature.
CAST_ACTIONS = {11, 85, 86, 134}
SUMMON_CREATURE_ACTION = 12
LINK_EVENT = 61
CALL_ACTIONLIST_ACTION = 80

COLUMNS = ["entryorguid", "source_type", "id", "link", "event_type", "event_phase_mask", "event_chance",
           "event_flags", "event_param1", "event_param2", "event_param3", "event_param4", "event_param5",
           "event_param6", "action_type", "action_param1", "action_param2", "action_param3", "action_param4",
           "action_param5", "action_param6", "target_type", "target_param1", "target_param2", "target_param3",
           "target_param4", "target_x", "target_y", "target_z", "target_o", "comment"]


def sql_value(value):
    if value is None:
        return "NULL"
    if isinstance(value, str):
        return "'" + value.replace("\\", "\\\\").replace("'", "''") + "'"
    if isinstance(value, float):
        return repr(round(value, 6))
    return str(value)


def loot_source(kind, level):
    for max_level, source in LOOT_SOURCES[kind]:
        if level <= max_level:
            return source
    raise ValueError(level)


class Spells:
    """Server Spell.dbc: tells whether a creature spell is too strong for a level 1-10 zone."""

    SCHOOL_DAMAGE, HEALTH_LEECH, HEAL, TRIGGER_SPELL = 2, 9, 10, 64
    AURA_EFFECTS = {6, 27, 35, 65, 119, 128, 129}        # apply aura, persistent / area auras
    SUMMON_EFFECTS = {28, 41, 42, 56, 112}
    DAMAGE_AURAS = {3, 8, 15, 53, 89}                    # periodic damage/heal/leech, damage shield
    TRIGGER_AURAS = {23, 226, 227}

    def __init__(self, path):
        with open(path, "rb") as handle:
            self.data = handle.read()
        _, count, self.fields, self.record_size, _ = struct.unpack_from("<4sIIII", self.data)
        self.index = {struct.unpack_from("<I", self.data, 20 + i * self.record_size)[0]: i for i in range(count)}

    def record(self, spell_id):
        i = self.index.get(spell_id)
        return None if i is None else struct.unpack_from("<%di" % self.fields, self.data, 20 + i * self.record_size)

    def too_strong(self, spell_id, depth=0):
        r = self.record(spell_id)
        if r is None or depth > 2:
            return False
        for k in range(3):
            effect, aura, trigger = r[71 + k], r[95 + k], r[116 + k]
            amount = r[80 + k] + max(1, r[74 + k])
            if effect in (self.SCHOOL_DAMAGE, self.HEALTH_LEECH, self.HEAL) and amount > 25:
                return True
            if effect in self.SUMMON_EFFECTS:
                return True
            if effect in self.AURA_EFFECTS and aura in self.DAMAGE_AURAS and amount > 8:
                return True
            if (effect == self.TRIGGER_SPELL or (effect in self.AURA_EFFECTS and aura in self.TRIGGER_AURAS)) \
                    and trigger and self.too_strong(trigger, depth + 1):
                return True
        return False


def faction_attitudes(path):
    """FactionTemplate id -> 'friend' | 'hostile' | 'neutral', as seen by the Horde."""
    with open(path, "rb") as handle:
        data = handle.read()
    _, count, fields, record_size, _ = struct.unpack_from("<4sIIII", data)
    horde_factions = {67, 76}
    attitudes = {}
    for i in range(count):
        r = struct.unpack_from("<%dI" % fields, data, 20 + i * record_size)
        our, friend, enemy, enemies, friends = r[3], r[4], r[5], r[6:10], r[10:14]
        if friend & 4 or our & 4 or horde_factions & set(friends):
            attitudes[r[0]] = "friend"
        elif enemy & 5 or horde_factions & set(enemies):
            attitudes[r[0]] = "hostile"
        else:
            attitudes[r[0]] = "neutral"
    return attitudes


def find_auto_creatures(cur, zones, attitudes):
    """Every other attackable creature spawned in Blade's Edge only: entry -> CREATURES-like tuple."""
    cur.execute("SELECT id, map, position_x, position_y FROM creature")
    in_zone, other_maps = {}, set()
    for spawn in cur.fetchall():
        if spawn["map"] != OUTLAND:
            other_maps.add(spawn["id"])
        elif zones.zone_at(OUTLAND, spawn["position_x"], spawn["position_y"]) == BLADES_EDGE:
            in_zone.setdefault(spawn["id"], []).append((spawn["position_x"], spawn["position_y"]))

    cur.execute("SELECT entry, `rank`, faction, type, unit_flags, npcflag, flags_extra FROM creature_template "
                "WHERE entry IN (%s)" % ",".join(map(str, in_zone)))
    auto = {}
    for t in cur.fetchall():
        entry = t["entry"]
        attitude = attitudes.get(t["faction"], "neutral")
        if (entry in CREATURES or entry in AUTO_SKIP or entry in other_maps or attitude == "friend"
                or (attitude == "neutral" and t["type"] == 7)              # neutral people: expeditions...
                or t["unit_flags"] & 0x2000002 or t["flags_extra"] & 0x80 or t["npcflag"]
                or t["type"] in (8, 10)):                                  # critters, triggers
            continue
        points = in_zone[entry]
        x = sum(p[0] for p in points) / len(points)
        y = sum(p[1] for p in points) / len(points)
        distance = math.hypot(x - THUNDERLORD[0], y - THUNDERLORD[1])
        min_level, max_level = next((lo, hi) for limit, lo, hi in AUTO_LEVELS if distance < limit)
        kind = BEAST if t["type"] in (1, 2) else NO_LOOT if t["type"] == 9 else HUMANOID
        health, damage = AUTO_MODIFIERS.get(t["rank"], (1, 1))
        auto[entry] = (min_level, max_level, kind, t["rank"], health, damage, [])
    return auto


def rewrite_rows(rows, remove_ids):
    """Drop rows and the link chains they start; unlink rows linking to a dropped row."""
    by_id = {row["id"]: row for row in rows}
    pending = list(remove_ids)
    removed = set()
    while pending:
        row_id = pending.pop()
        if row_id in removed or row_id not in by_id:
            continue
        removed.add(row_id)
        link = by_id[row_id]["link"]
        if link and link in by_id and by_id[link]["event_type"] == LINK_EVENT:
            pending.append(link)
    kept = [row for row in rows if row["id"] not in removed]
    for row in kept:
        if row["link"] in removed:
            row["link"] = 0
    return kept, bool(removed)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--data", default=r"D:/Aeziak/Plateforme/Concepts/Build/bin/Debug")
    parser.add_argument("--db", default="127.0.0.1:3307:acore:acore:acore_world")
    args = parser.parse_args()

    host, port, user, password, database = args.db.split(":")
    db = mysql.connector.connect(host=host, port=int(port), user=user, password=password, database=database)
    cur = db.cursor(dictionary=True)

    zones = Zones(args.data)
    spells = Spells(os.path.join(args.data, "dbc", "Spell.dbc"))
    attitudes = faction_attitudes(os.path.join(args.data, "dbc", "FactionTemplate.dbc"))

    auto = find_auto_creatures(cur, zones, attitudes)
    creatures = dict(CREATURES)
    creatures.update(auto)

    cur.execute("SELECT entry, name, ScriptName FROM creature_template WHERE entry IN (%s)" % ",".join(map(str, creatures)))
    templates = {row["entry"]: row for row in cur.fetchall()}
    names = {entry: row["name"] for entry, row in templates.items()}
    assert len(names) == len(creatures), set(creatures) - set(names)

    lines = [
        "-- mod-two-headed-ogre: Ogre start zone in Blade's Edge Mountains (Thunderlord Stronghold -> Mok'Nathal Village).",
        "-- Generated by tools/start_zone/gen_start_zone.py: every attackable creature of the zone becomes level 1-10,",
        "-- with Eversong Woods loot (Blood elf start zone) and its fixed-damage high level spells removed or swapped",
        "-- for low level ranks. Nobody plays the 65+ content of the zone on this server (XP is capped below it), so the",
        "-- creatures are changed in place.",
        "",
    ]

    # Templates.
    for entry, (min_level, max_level, kind, rank, health, damage, _) in creatures.items():
        gold = "`mingold` = %d, `maxgold` = %d" % ((min_level, max_level * 2 + 5) if kind == HUMANOID else (0, 0))
        skin = 100002 if kind == BEAST else 0
        lootid = 0 if kind == NO_LOOT else entry
        lines.append(
            "UPDATE `creature_template` SET `minlevel` = %d, `maxlevel` = %d, `exp` = 0, `rank` = %d, "
            "`HealthModifier` = %s, `DamageModifier` = %s, `ManaModifier` = 1, `ArmorModifier` = 1, `lootid` = %d, "
            "`skinloot` = %d, %s WHERE `entry` = %d; -- %s"
            % (min_level, max_level, rank, sql_value(float(health)), sql_value(float(damage)), lootid, skin, gold,
               entry, names[entry]))
    lines.append("")

    # Loot.
    ids = ",".join(map(str, creatures))
    lines.append("DELETE FROM `creature_loot_template` WHERE `Entry` IN (%s);" % ids)
    # The original loot conditions point to items that no longer drop (quest drops use QuestRequired instead).
    lines.append("DELETE FROM `conditions` WHERE `SourceTypeOrReferenceId` = 1 AND `SourceGroup` IN (%s);" % ids)
    for entry, (min_level, max_level, kind, _, _, _, drops) in creatures.items():
        if kind == NO_LOOT:
            continue
        source = loot_source(kind, max_level)
        lines.append(
            "INSERT INTO `creature_loot_template` (`Entry`, `Item`, `Reference`, `Chance`, `QuestRequired`, `LootMode`, "
            "`GroupId`, `MinCount`, `MaxCount`, `Comment`) SELECT %d, `Item`, `Reference`, `Chance`, `QuestRequired`, "
            "`LootMode`, `GroupId`, `MinCount`, `MaxCount`, %s FROM `creature_loot_template` WHERE `Entry` = %d;"
            % (entry, sql_value("%s - Ogre start zone (loot of %d)" % (names[entry], source)), source))
        for item, chance in drops:
            lines.append(
                "INSERT INTO `creature_loot_template` (`Entry`, `Item`, `Reference`, `Chance`, `QuestRequired`, "
                "`LootMode`, `GroupId`, `MinCount`, `MaxCount`, `Comment`) VALUES (%d, %d, 0, %d, 1, 1, 0, 1, 1, %s);"
                % (entry, item, chance, sql_value("%s - Ogre start zone quest item" % names[entry])))
    lines.append("")

    # SmartAI: full blocks of every changed creature (and of the action lists the second pass creatures call).
    columns = ", ".join("`%s`" % c for c in COLUMNS)

    def write_block(entry, source_type, rows, ai_entry):
        lines.append("DELETE FROM `smart_scripts` WHERE `entryorguid` = %d AND `source_type` = %d;" % (entry, source_type))
        if rows:
            lines.append("INSERT INTO `smart_scripts` (%s) VALUES" % columns)
            lines.append(",\n".join("(" + ", ".join(sql_value(r[c]) for c in COLUMNS) + ")" for r in rows) + ";")
        elif ai_entry:
            lines.append("UPDATE `creature_template` SET `AIName` = '' WHERE `entry` = %d;" % ai_entry)

    def fetch(entry, source_type):
        cur.execute("SELECT %s FROM smart_scripts WHERE entryorguid = %d AND source_type = %d ORDER BY id"
                    % (columns, entry, source_type))
        return cur.fetchall()

    def too_strong_rows(rows):
        bad = set()
        for row in rows:
            if row["action_type"] in CAST_ACTIONS and spells.too_strong(row["action_param1"]):
                bad.add(row["id"])
            elif row["action_type"] == SUMMON_CREATURE_ACTION and row["action_param1"] not in creatures:
                bad.add(row["id"])
        return bad

    for entry in sorted({entry for entry, _ in SPELL_CHANGES}):
        kept = []
        for row in fetch(entry, 0):
            change = SPELL_CHANGES.get((entry, row["id"]), "keep")
            if change is None:
                continue
            if change != "keep":
                assert row["action_type"] == 11, (entry, row["id"])
                row["action_param1"], row["comment"] = change
            kept.append(row)
        write_block(entry, 0, kept, entry)

    removed_spells = 0
    action_lists = set()
    for entry in sorted(auto):
        rows = fetch(entry, 0)
        action_lists |= {row["action_param1"] for row in rows if row["action_type"] == CALL_ACTIONLIST_ACTION}
        kept, changed = rewrite_rows(rows, too_strong_rows(rows))
        if changed:
            removed_spells += len(rows) - len(kept)
            write_block(entry, 0, kept, entry)
    for action_list in sorted(action_lists):
        rows = fetch(action_list, 9)
        kept, changed = rewrite_rows(rows, too_strong_rows(rows))
        if changed:
            removed_spells += len(rows) - len(kept)
            write_block(action_list, 9, kept, 0)
    lines.append("")

    with open(OUT, "w", encoding="utf-8", newline="\n") as handle:
        handle.write("\n".join(lines).rstrip("\n") + "\n")
    print("written %s: %d hand-tuned + %d other creatures, %d SmartAI rows removed by the second pass"
          % (OUT, len(CREATURES), len(auto), removed_spells))
    scripted = sorted((entry, names[entry], templates[entry]["ScriptName"]) for entry in auto
                      if templates[entry]["ScriptName"])
    for entry, name, script in scripted:
        print("  C++ AI, spells unchanged: %d %s (%s)" % (entry, name, script))


if __name__ == "__main__":
    main()
