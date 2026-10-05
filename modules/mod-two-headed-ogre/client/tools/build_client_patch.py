"""Build the mod-two-headed-ogre client patch (WoW 3.3.5a, build 12340).

Reads the stock files from the client's own MPQ archives and writes one patch MPQ with:
  - DBFilesClient\\ChrRaces.dbc            race 9 becomes "Ogre": playable, Horde, Orc sounds/cinematic,
                                          own model folder (ClientFileString "Ogre") and displays
  - DBFilesClient\\CreatureDisplayInfo.dbc,
    CreatureModelData.dbc                 one Ogre character display per sex (Character\\Ogre models)
  - Character\\Ogre\\{Male,Female}\\...     the two-headed ogre creature model turned into a character model
                                          (hardcoded skin): creation/selection screens, paper doll
  - DBFilesClient\\CharBaseInfo.dbc        race 9 may be created with the carrier class (Paladin)
  - DBFilesClient\\ChrClasses.dbc          the carrier class (Paladin) is shown as "Brute"
  - DBFilesClient\\SkillRaceClassInfo.dbc  every skill of the Orcs also for race 9 (Orcish language,
                                          weapons...), like the server's race alias (TwoHeadedOgre.RaceAliasMask)
  - DBFilesClient\\Item.dbc                the custom items (Brute's fist weapons, first quest's ring)
  - DBFilesClient\\CharSections.dbc,
    CharHairGeosets.dbc,
    CharacterFacialHairStyles.dbc          Orc customization options copied to race 9
  - Interface\\GlueXML\\GlueXML.toc,
    OgreCreate.xml, OgreCreate.lua         11th race button, second head name, no class choice
  - DBFilesClient\\Spell.dbc,
    SpellIcon.dbc                         the Ogre racial spells and their icon, the head's first spells usable
                                          from level 1 (see ogre_spells.py)
  - DBFilesClient\\Talent.dbc,
    TalentTab.dbc                         the Brute's talent trees, one per stance (see ogre_talents.py)

With --install, the AddOn client/addon/OgreHead (the head's action bar, spells cast through the server) is
also copied to <client>/Interface/AddOns/OgreHead: FrameXML is signature-checked by the client, AddOns are not.

Usage:
  python build_client_patch.py --client "D:/World of Warcraft 3.3.5" [--install]

Without --install the patch is written next to this script (build/patch-<locale>-4.MPQ).
With --install it is copied to <client>/Data/<locale>/patch-<locale>-4.MPQ (an existing file is kept as .bak).
"""

import argparse
import os
import shutil
import struct
import sys

import mpq
import ogre_spells
import ogre_talents

OGRE_RACE = 9
SOURCE_RACE = 2          # Orc: customization rows, sounds and cinematic
CARRIER_CLASS = 2        # Paladin, must match TwoHeadedOgre.CarrierClass
OGRE_NAME = "Ogre"
OGRE_FILE_STRING = "Ogre"   # ChrRaces.ClientFileString: model folder Character\<it>\<Sex>\<it><Sex>.m2
OGRE_SOURCE_MODEL = "Creature\\Ogre\\OgreMage"   # two-headed ogre mage
# The creation/selection screens load the model of ChrRaces.Male/FemaleDisplayId: one new display + model data
# row per sex (copies of the Orc rows) pointing to Character\Ogre. Unused ids, client side only.
# The skins match the in-game displays (TwoHeadedOgre.Display.*): 3250 yellow, 19930 blue.
OGRE_SEXES = (
    # sex, source (Orc) display, new display id, new model data id, skin
    ("Male", 51, 40001, 3501, "Creature\\Ogre\\OgreSkinYellow.blp"),
    ("Female", 52, 40002, 3502, "Creature\\Ogre\\OgreSkinBlue.blp"),
)


# The Ogre's class: the Paladin carrier, shown as "Brute" (warrior colour in the AddOn).
BRUTE_CLASS_NAME = "Brute"
# Item.dbc rows of the custom items: id, class, subclass, sound override, material, display, inventory type, sheath.
CUSTOM_ITEMS = (
    (91003, 2, 13, -1, 1, 34557, 13, 7),     # Jointures de brute: fist weapon, red knuckles, one hand
    (91004, 4, 0, -1, 1, 9823, 11, 0),       # Chevalière Sire-tonnerre: ring (first quest)
)

HERE = os.path.dirname(os.path.abspath(__file__))
GLUE_DIR = os.path.join(HERE, "..", "glue")
ADDON_DIR = os.path.join(HERE, "..", "addon", "OgreHead")


class Dbc:
    def __init__(self, data):
        magic, self.count, self.fields, self.record_size, string_size = struct.unpack_from("<4sIIII", data)
        if magic != b"WDBC":
            raise ValueError("not a DBC file")
        start = 20
        self.records = [bytearray(data[start + i * self.record_size:start + (i + 1) * self.record_size])
                        for i in range(self.count)]
        self.strings = bytearray(data[start + self.count * self.record_size:])
        assert len(self.strings) == string_size

    def u32(self, record, field):
        return struct.unpack_from("<I", record, field * 4)[0]

    def set_u32(self, record, field, value):
        struct.pack_into("<I", record, field * 4, value)

    def add_string(self, text):
        offset = len(self.strings)
        self.strings += text.encode("utf-8") + b"\0"
        return offset

    def build(self):
        header = struct.pack("<4sIIII", b"WDBC", len(self.records), self.fields, self.record_size, len(self.strings))
        return header + b"".join(bytes(r) for r in self.records) + bytes(self.strings)


def patch_chr_races(data):
    dbc = Dbc(data)
    source = next(r for r in dbc.records if dbc.u32(r, 0) == SOURCE_RACE)
    ogre = bytearray(source)
    dbc.set_u32(ogre, 0, OGRE_RACE)
    name = dbc.add_string(OGRE_NAME)
    dbc.set_u32(ogre, 11, dbc.add_string(OGRE_FILE_STRING))
    dbc.set_u32(ogre, 4, OGRE_SEXES[0][2])
    dbc.set_u32(ogre, 5, OGRE_SEXES[1][2])
    # Name_Lang, NameFemale_Lang, NameMale_Lang: 16 locales + flags each, from field 14.
    for group in range(3):
        for locale in range(16):
            dbc.set_u32(ogre, 14 + group * 17 + locale, name)
    dbc.records = [r for r in dbc.records if dbc.u32(r, 0) != OGRE_RACE] + [ogre]
    dbc.records.sort(key=lambda r: dbc.u32(r, 0))
    return dbc.build()


def ogre_model_base(sex):
    """Character\\Ogre\\<Sex>\\Ogre<Sex>, without extension."""
    return "Character\\%s\\%s\\%s%s" % (OGRE_FILE_STRING, sex, OGRE_FILE_STRING, sex)


def patch_creature_display_info(display_data, model_data):
    """Add one display and one model data row per sex for the Ogre character model."""
    displays = Dbc(display_data)
    models = Dbc(model_data)
    for sex, source_display, display_id, model_id, _ in OGRE_SEXES:
        displays.records = [r for r in displays.records if displays.u32(r, 0) != display_id]
        models.records = [r for r in models.records if models.u32(r, 0) != model_id]

        display = bytearray(next(r for r in displays.records if displays.u32(r, 0) == source_display))
        source_model = displays.u32(display, 1)
        model = bytearray(next(r for r in models.records if models.u32(r, 0) == source_model))

        models.set_u32(model, 0, model_id)
        models.set_u32(model, 2, models.add_string(ogre_model_base(sex) + ".mdx"))
        models.records.append(model)

        displays.set_u32(display, 0, display_id)
        displays.set_u32(display, 1, model_id)
        displays.records.append(display)
    return displays.build(), models.build()


def patch_chr_classes(data):
    dbc = Dbc(data)
    name = dbc.add_string(BRUTE_CLASS_NAME)
    for record in dbc.records:
        if dbc.u32(record, 0) == CARRIER_CLASS:
            # Name, female name, male name: 16 locales + flags each, from field 4.
            for group in range(3):
                for locale in range(16):
                    dbc.set_u32(record, 4 + group * 17 + locale, name)
    return dbc.build()


def patch_item_dbc(data):
    dbc = Dbc(data)
    ids = {item[0] for item in CUSTOM_ITEMS}
    dbc.records = [r for r in dbc.records if dbc.u32(r, 0) not in ids]
    dbc.records += [bytearray(struct.pack("<8i", *item)) for item in CUSTOM_ITEMS]
    return dbc.build()


def patch_skill_race_class_info(data):
    """The client only knows a skill (a language among them) if a row allows the race: give race 9 the Orcs' rows."""
    dbc = Dbc(data)
    orc_bit, ogre_bit = 1 << (SOURCE_RACE - 1), 1 << (OGRE_RACE - 1)
    for record in dbc.records:
        race_mask = dbc.u32(record, 2)
        if race_mask != 0xFFFFFFFF and race_mask & orc_bit:
            dbc.set_u32(record, 2, race_mask | ogre_bit)
    return dbc.build()


def patch_char_base_info(data):
    dbc = Dbc(data)
    dbc.records = [r for r in dbc.records if r[0] != OGRE_RACE]
    dbc.records.append(bytearray(bytes([OGRE_RACE, CARRIER_CLASS])))
    return dbc.build()


def copy_race_rows(data, race_field, id_field):
    """Replace the rows of OGRE_RACE with copies of the SOURCE_RACE rows."""
    dbc = Dbc(data)
    kept = [r for r in dbc.records if dbc.u32(r, race_field) != OGRE_RACE]
    next_id = max(dbc.u32(r, id_field) for r in kept) + 1 if id_field is not None else 0
    for record in [r for r in kept if dbc.u32(r, race_field) == SOURCE_RACE]:
        copy = bytearray(record)
        dbc.set_u32(copy, race_field, OGRE_RACE)
        if id_field is not None:
            dbc.set_u32(copy, id_field, next_id)
            next_id += 1
        kept.append(copy)
    dbc.records = kept
    return dbc.build()


def convert_creature_model(read, source, target, skin):
    """Copy a creature M2 (with its skins and external animations) as a character model.

    Character models get their textures from CharSections, which knows nothing about creature texture
    layouts: every replaceable texture becomes a hardcoded one (type 0) pointing to the creature skin.
    """
    model = read(source + ".m2")
    if model is None or model[:4] != b"MD20":
        raise SystemExit("Missing or invalid model %s.m2" % source)
    model = bytearray(model)

    def m2_array(offset):
        return struct.unpack_from("<II", model, offset)

    texture_count, texture_offset = m2_array(0x50)
    for i in range(texture_count):
        entry = texture_offset + i * 16
        if struct.unpack_from("<I", model, entry)[0] == 0:
            continue
        model += b"\0" * (-len(model) % 16)
        name_offset = len(model)
        model += skin.encode("ascii") + b"\0"
        struct.pack_into("<IIII", model, entry, 0, 0, len(skin) + 1, name_offset)

    files = {target + ".m2": bytes(model)}

    # A character model shows or hides its geosets by group from the equipment (a robe hides the legs 13xx, boots
    # the feet 5xx...): the creature's parts all become group 0, always shown.
    view_count = struct.unpack_from("<I", model, 0x44)[0]
    for view in range(view_count):
        content = read("%s%02d.skin" % (source, view))
        if content is None:
            raise SystemExit("Missing %s%02d.skin" % (source, view))
        content = bytearray(content)
        submesh_count, submesh_offset = struct.unpack_from("<II", content, 0x1C)
        for i in range(submesh_count):
            struct.pack_into("<H", content, submesh_offset + i * 48, 0)
        files["%s%02d.skin" % (target, view)] = bytes(content)

    # Sequences without flag 0x20 live in <model><animId>-<subId>.anim files next to the model.
    sequence_count, sequence_offset = m2_array(0x1C)
    for i in range(sequence_count):
        entry = sequence_offset + i * 64
        anim_id, sub_id = struct.unpack_from("<HH", model, entry)
        if struct.unpack_from("<I", model, entry + 12)[0] & 0x20:
            continue
        content = read("%s%04d-%02d.anim" % (source, anim_id, sub_id))
        if content is not None:
            files["%s%04d-%02d.anim" % (target, anim_id, sub_id)] = content
    return files


def patch_glue_toc(data):
    text = data.decode("utf-8")
    if "OgreCreate.xml" in text:
        return data
    marker = "## This Always Runs Last"
    if marker not in text:
        raise ValueError("unexpected GlueXML.toc layout")
    return text.replace(marker, "OgreCreate.xml\r\n\r\n" + marker).encode("utf-8")


def find_locale(data_dir):
    for entry in sorted(os.listdir(data_dir)):
        if os.path.isfile(os.path.join(data_dir, entry, "locale-%s.MPQ" % entry)):
            return entry
    raise SystemExit("No locale folder (Data/xxXX/locale-xxXX.MPQ) found in %s" % data_dir)


def open_client(client_dir):
    data_dir = os.path.join(client_dir, "Data")
    locale = find_locale(data_dir)
    names = ["common.MPQ", "common-2.MPQ", "expansion.MPQ", "lichking.MPQ",
             "%s/locale-%s.MPQ" % (locale, locale), "%s/expansion-locale-%s.MPQ" % (locale, locale),
             "%s/lichking-locale-%s.MPQ" % (locale, locale),
             "patch.MPQ", "patch-2.MPQ", "patch-3.MPQ",
             "%s/patch-%s.MPQ" % (locale, locale), "%s/patch-%s-2.MPQ" % (locale, locale),
             "%s/patch-%s-3.MPQ" % (locale, locale)]
    archives = []
    for name in names:
        path = os.path.join(data_dir, name)
        if os.path.isfile(path):
            archives.append(mpq.MpqArchive(path))
    return locale, archives


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--client", required=True, help="WoW 3.3.5a folder (the one containing Wow.exe)")
    parser.add_argument("--install", action="store_true", help="copy the patch into the client")
    args = parser.parse_args()

    locale, archives = open_client(args.client)

    def stock(name):
        content = mpq.read_from_chain(archives, name)
        if content is None:
            raise SystemExit("Missing %s in the client archives" % name)
        return content

    files = {
        "DBFilesClient\\ChrRaces.dbc": patch_chr_races(stock("DBFilesClient\\ChrRaces.dbc")),
        "DBFilesClient\\CharBaseInfo.dbc": patch_char_base_info(stock("DBFilesClient\\CharBaseInfo.dbc")),
        "DBFilesClient\\ChrClasses.dbc": patch_chr_classes(stock("DBFilesClient\\ChrClasses.dbc")),
        "DBFilesClient\\Item.dbc": patch_item_dbc(stock("DBFilesClient\\Item.dbc")),
        "DBFilesClient\\SkillRaceClassInfo.dbc":
            patch_skill_race_class_info(stock("DBFilesClient\\SkillRaceClassInfo.dbc")),
        "DBFilesClient\\CharSections.dbc": copy_race_rows(stock("DBFilesClient\\CharSections.dbc"), 1, 0),
        "DBFilesClient\\CharHairGeosets.dbc": copy_race_rows(stock("DBFilesClient\\CharHairGeosets.dbc"), 1, 0),
        "DBFilesClient\\CharacterFacialHairStyles.dbc":
            copy_race_rows(stock("DBFilesClient\\CharacterFacialHairStyles.dbc"), 0, None),
        "Interface\\GlueXML\\GlueXML.toc": patch_glue_toc(stock("Interface\\GlueXML\\GlueXML.toc")),
        "DBFilesClient\\Spell.dbc": ogre_spells.patch_spell_dbc(stock("DBFilesClient\\Spell.dbc")),
        "DBFilesClient\\SpellIcon.dbc": ogre_spells.patch_spell_icon_dbc(stock("DBFilesClient\\SpellIcon.dbc")),
        "DBFilesClient\\Talent.dbc": ogre_talents.patch_talent_dbc(stock("DBFilesClient\\Talent.dbc")),
        "DBFilesClient\\TalentTab.dbc": ogre_talents.patch_talent_tab_dbc(stock("DBFilesClient\\TalentTab.dbc")),
    }
    displays, models = patch_creature_display_info(stock("DBFilesClient\\CreatureDisplayInfo.dbc"),
                                                   stock("DBFilesClient\\CreatureModelData.dbc"))
    files["DBFilesClient\\CreatureDisplayInfo.dbc"] = displays
    files["DBFilesClient\\CreatureModelData.dbc"] = models

    for sex, _, _, _, skin in OGRE_SEXES:
        files.update(convert_creature_model(lambda name: mpq.read_from_chain(archives, name), OGRE_SOURCE_MODEL,
                                            ogre_model_base(sex), skin))

    for name in ("OgreCreate.xml", "OgreCreate.lua"):
        with open(os.path.join(GLUE_DIR, name), "rb") as handle:
            files["Interface\\GlueXML\\" + name] = handle.read().replace(b"\r\n", b"\n").replace(b"\n", b"\r\n")


    patch_name = "patch-%s-4.MPQ" % locale
    out_dir = os.path.join(HERE, "build")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, patch_name)
    mpq.write_archive(out_path, files)

    # Self-check: the written archive must read back identically.
    check = mpq.MpqArchive(out_path)
    for name, content in files.items():
        if check.read(name) != content:
            raise SystemExit("Self-check failed for %s" % name)
    print("Patch written: %s (%d files)" % (out_path, len(files)))

    if args.install:
        target = os.path.join(args.client, "Data", locale, patch_name)
        if os.path.exists(target):
            shutil.copy2(target, target + ".bak")
            print("Existing patch kept as %s.bak" % target)
        shutil.copy2(out_path, target)
        print("Installed: %s" % target)

        addon_target = os.path.join(args.client, "Interface", "AddOns", "OgreHead")
        os.makedirs(addon_target, exist_ok=True)
        for name in sorted(os.listdir(ADDON_DIR)):
            shutil.copy2(os.path.join(ADDON_DIR, name), os.path.join(addon_target, name))
        print("Installed AddOn: %s" % addon_target)
        print("Delete the client's Cache folder before the next launch.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
