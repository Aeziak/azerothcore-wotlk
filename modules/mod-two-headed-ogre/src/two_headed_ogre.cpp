/*
 * mod-two-headed-ogre : ogre registry, creation and shared-control events.
 */

#include "two_headed_ogre.h"
#include "Chat.h"
#include "Config.h"
#include "CreatureData.h"
#include "DatabaseEnv.h"
#include "DBCStores.h"
#include "Log.h"
#include "ObjectAccessor.h"
#include "ObjectMgr.h"
#include "Player.h"
#include "Random.h"
#include "SpellAuraDefines.h"
#include "SpellAuras.h"
#include "SpellInfo.h"
#include "SpellMgr.h"
#include "StringConvert.h"
#include "Tokenize.h"
#include "Util.h"
#include "WorldPacket.h"
#include "WorldSession.h"
#include <algorithm>
#include <cctype>
#include <cstdlib>
#include <mutex>
#include <unordered_set>

namespace
{
    // Head bar addon messages (AddOn client/addon/OgreHead): prefix and number of buttons.
    constexpr std::string_view HeadMessagePrefix = "OGRE\t";
    constexpr uint8 HeadBarButtons = 12;

    constexpr char const* HeadStateKey = "mod_two_headed_ogre_head";
    constexpr uint32 StartZone = 3522;              // Blade's Edge Mountains

    struct OgreStance
    {
        uint32 Aura;
        uint32 Extra;
        uint32 Ultimate;            // the stance's ultimate talent...
        uint32 UltimateBonus;       // ...and its bonus while in the stance
    };

    constexpr std::array<OgreStance, 3> Stances = {{
        { SPELL_OGRE_STANCE_HIT, SPELL_OGRE_STANCE_HIT_EXTRA, SPELL_OGRE_TALENT_HIT_ULTIMATE,
            SPELL_OGRE_STANCE_HIT_ULTIMATE },
        { SPELL_OGRE_STANCE_MAGIC, SPELL_OGRE_STANCE_MAGIC_EXTRA, SPELL_OGRE_TALENT_MAGIC_ULTIMATE,
            SPELL_OGRE_STANCE_MAGIC_ULTIMATE },
        { SPELL_OGRE_STANCE_TANK, SPELL_OGRE_STANCE_TANK_EXTRA, SPELL_OGRE_TALENT_TANK_ULTIMATE,
            SPELL_OGRE_STANCE_TANK_ULTIMATE },
    }};

    // Brute talents: Rage partagée 2 rage per rank, Fureur prolongée 5 s per rank, Idées fixes and Réflexe d'ogre
    // amélioré +3 / +5% chance, Chute lourde +25% damage per rank, the others as described in ogre_talents.py.
    constexpr int32 SharedRagePerRank = 2 * 10;     // rage counts in tenths
    constexpr int32 LongFuryPerRank = 5 * IN_MILLISECONDS;
    constexpr int32 QuickThinkingPerRank = 60 * IN_MILLISECONDS;
    constexpr std::array<float, 3> ProcTalentBonus = { 0.0f, 3.0f, 5.0f };
    constexpr float HeavyFallPerRank = 0.25f;
    constexpr int32 ShatteringPerRank = 500;        // stun, ms
    constexpr float DoubleHitPerRank = 0.10f;
    constexpr uint32 DoubleHitWindow = 3 * IN_MILLISECONDS;
    constexpr uint32 ChatterPerMillePerRank = 5;    // of the maximum mana
    constexpr float BacklashChancePerRank = 50.0f;
    constexpr float SurvivalHealthPct = 30.0f;
    constexpr int32 SurvivalFuryDuration = 15 * IN_MILLISECONDS;
    constexpr uint32 SurvivalCooldown = 2 * MINUTE * IN_MILLISECONDS;
    constexpr uint32 SpareHeadCooldown = 3 * MINUTE * IN_MILLISECONDS;

    // Bond d'ogre lands after distance / speed (Spell::CalculateJumpSpeeds for a player: 3 x base run speed);
    // Saut d'ogre goes straight up (about 12 yards high) and its next landing hits at full power.
    constexpr float LeapSpeed = 21.0f;
    constexpr float LeapImpactRatio = 0.5f;         // 200%
    constexpr float JumpSpeedZ = 21.5f;
    constexpr uint32 JumpLandingWindow = 5 * IN_MILLISECONDS;

    void CountDown(uint32& timer, uint32 diff)
    {
        timer = timer > diff ? timer - diff : 0;
    }

    // Rank of a Brute talent (0: not learned), from the passive auras of its rank spells (consecutive ids).
    uint8 TalentRank(Player const* player, uint32 firstRank, uint8 maxRank)
    {
        for (uint8 rank = maxRank; rank > 0; --rank)
            if (player->HasAura(firstRank + rank - 1))
                return rank;

        return 0;
    }


    // Chute d'ogre: impact from MinHeight, full bonus (+200%) at MaxHeight.
    constexpr float FallImpactMinHeight = 4.0f;
    constexpr float FallImpactMaxHeight = 30.0f;
    constexpr uint32 FallImpactCooldown = 3 * IN_MILLISECONDS;

    bool SameChain(std::vector<uint32> const& spells, uint32 spellId)
    {
        uint32 const firstRank = sSpellMgr->GetFirstSpellInChain(spellId);
        return std::any_of(spells.begin(), spells.end(),
            [firstRank](uint32 spell) { return sSpellMgr->GetFirstSpellInChain(spell) == firstRank; });
    }

    std::string Lowercase(std::string text)
    {
        std::transform(text.begin(), text.end(), text.begin(), [](unsigned char c) { return std::tolower(c); });
        return text;
    }

    bool SameName(std::string const& left, std::string const& right)
    {
        return Lowercase(left) == Lowercase(right);
    }

    void Notify(WorldSession* session, std::string const& text)
    {
        if (session)
            ChatHandler(session).SendSysMessage("|cffd08c2e[Ogre]|r " + text);
    }
}

OgreMgr* OgreMgr::instance()
{
    static OgreMgr instance;
    return &instance;
}

void OgreMgr::LoadConfig()
{
    _enabled = sConfigMgr->GetOption<bool>("TwoHeadedOgre.Enable", true);
    _race = sConfigMgr->GetOption<uint8>("TwoHeadedOgre.Race", 9);
    _carrierClass = sConfigMgr->GetOption<uint8>("TwoHeadedOgre.CarrierClass", 2);
    _raceAliasMask = sConfigMgr->GetOption<uint32>("TwoHeadedOgre.RaceAliasMask", 690);
    _skillClassMask = sConfigMgr->GetOption<uint32>("TwoHeadedOgre.SkillClassMask", 1535);
    _creatureEntry = sConfigMgr->GetOption<uint32>("TwoHeadedOgre.Display.CreatureEntry", 5473);
    _modelId = sConfigMgr->GetOption<uint32>("TwoHeadedOgre.Display.ModelId", 3250);
    _femaleModelId = sConfigMgr->GetOption<uint32>("TwoHeadedOgre.Display.FemaleModelId", 19930);
    _scale = sConfigMgr->GetOption<float>("TwoHeadedOgre.Display.Scale", 1.0f);
    _chatPrefix = sConfigMgr->GetOption<bool>("TwoHeadedOgre.ChatPrefix", true);
    _ignoreItemRestrictions = sConfigMgr->GetOption<bool>("TwoHeadedOgre.IgnoreItemRestrictions", true);

    _spells.clear();
    std::string const spells = sConfigMgr->GetOption<std::string>("TwoHeadedOgre.Spells",
        "750 8737 9077 9078 9116 674 196 197 198 199 200 201 202 227 264 266 1180 2567 5011 5009 15590 46917 669 "
        "2136 589 91050 91051 91060 91061 91062 91066");
    for (std::string_view token : Acore::Tokenize(spells, ' ', false))
    {
        if (Optional<uint32> spellId = Acore::StringTo<uint32>(token))
            _spells.push_back(*spellId);
        else
            LOG_ERROR("module.ogre", "TwoHeadedOgre.Spells: ignored invalid spell id '{}'.", token);
    }

    _headSpells.clear();
    std::string const headSpells = sConfigMgr->GetOption<std::string>("TwoHeadedOgre.Head.Spells", "2136 589");
    for (std::string_view token : Acore::Tokenize(headSpells, ' ', false))
    {
        if (Optional<uint32> spellId = Acore::StringTo<uint32>(token))
            _headSpells.push_back(*spellId);
        else
            LOG_ERROR("module.ogre", "TwoHeadedOgre.Head.Spells: ignored invalid spell id '{}'.", token);
    }

    _sharedSpells.clear();
    std::string const sharedSpells = sConfigMgr->GetOption<std::string>("TwoHeadedOgre.SharedSpells", "91050");
    for (std::string_view token : Acore::Tokenize(sharedSpells, ' ', false))
    {
        if (Optional<uint32> spellId = Acore::StringTo<uint32>(token))
            _sharedSpells.push_back(*spellId);
        else
            LOG_ERROR("module.ogre", "TwoHeadedOgre.SharedSpells: ignored invalid spell id '{}'.", token);
    }

    _rouletteEnabled = sConfigMgr->GetOption<bool>("TwoHeadedOgre.Roulette.Enable", true);
    _procChance = sConfigMgr->GetOption<float>("TwoHeadedOgre.TwoBrains.Chance", 5.0f);
    _rollInterval = std::max<uint8>(1, sConfigMgr->GetOption<uint8>("TwoHeadedOgre.Roulette.LevelInterval", 2));

    _bruteSpells.clear();
    std::string const bruteSpells = sConfigMgr->GetOption<std::string>("TwoHeadedOgre.Brute.Spells", "78 324");
    for (std::string_view token : Acore::Tokenize(bruteSpells, ' ', false))
    {
        if (Optional<uint32> spellId = Acore::StringTo<uint32>(token))
            _bruteSpells.push_back(*spellId);
        else
            LOG_ERROR("module.ogre", "TwoHeadedOgre.Brute.Spells: ignored invalid spell id '{}'.", token);
    }
    _bruteOffHand = sConfigMgr->GetOption<uint32>("TwoHeadedOgre.Brute.OffHand", 91003);

    _headActionBar.clear();
    std::string const headBar = sConfigMgr->GetOption<std::string>("TwoHeadedOgre.Head.ActionBar", "2136 589");
    for (std::string_view token : Acore::Tokenize(headBar, ' ', false))
    {
        Optional<uint32> spellId = Acore::StringTo<uint32>(token);
        if (spellId && _headActionBar.size() < MAX_ACTION_BUTTONS)
            _headActionBar.push_back(*spellId);
        else
            LOG_ERROR("module.ogre", "TwoHeadedOgre.Head.ActionBar: ignored invalid spell id '{}'.", token);
    }

    // The ogre counts as the configured stock races for quests, items, reputation and skills.
    SetRaceAlias(_race, _enabled ? _raceAliasMask : 0, _enabled ? _skillClassMask : 0);
}

void OgreMgr::LoadFromDB()
{
    std::unique_lock lock(_lock);
    _ogres.clear();

    QueryResult result = CharacterDatabase.Query("SELECT guid, head1_name, head1_account, head2_name, head2_account FROM mod_two_headed_ogre_pair");
    if (!result)
    {
        LOG_INFO("module.ogre", ">> Loaded 0 ogres.");
        return;
    }

    do
    {
        Field* fields = result->Fetch();
        OgreInfo ogre;
        ogre.Guid = ObjectGuid::Create<HighGuid::Player>(fields[0].Get<uint32>());
        ogre.Names = { fields[1].Get<std::string>(), fields[3].Get<std::string>() };
        ogre.Accounts = { fields[2].Get<uint32>(), fields[4].Get<uint32>() };
        _ogres[ogre.Guid] = ogre;
    } while (result->NextRow());

    LOG_INFO("module.ogre", ">> Loaded {} ogres.", _ogres.size());
}
namespace
{
    // Spell roulette: the body rolls melee spells and buffs, the head ranged spells, heals and buffs.
    OgreRollKind ClassifyRollSpell(SpellInfo const* spellInfo)
    {
        if (spellInfo->IsPassive() || spellInfo->RuneCostID || spellInfo->PowerType == POWER_RUNE
            || spellInfo->PowerType == POWER_RUNIC_POWER || spellInfo->PowerType == POWER_FOCUS
            || spellInfo->PowerType == POWER_HAPPINESS)
            return OgreRollKind::None;

        // Shaman totems need totem items, form abilities need the form.
        if (spellInfo->Totem[0] || spellInfo->Totem[1] || spellInfo->TotemCategory[0] || spellInfo->TotemCategory[1])
            return OgreRollKind::None;

        if (spellInfo->Stances && !spellInfo->HasAttribute(SPELL_ATTR2_ALLOW_WHILE_NOT_SHAPESHIFTED))
            return OgreRollKind::None;

        // Ogres are warlocks at heart: the warlock demons go to the head. No other pet or guardian.
        if (spellInfo->HasEffect(SPELL_EFFECT_SUMMON_PET))
            return spellInfo->SpellFamilyName == SPELLFAMILY_WARLOCK ? OgreRollKind::Ranged : OgreRollKind::None;

        if (spellInfo->HasEffect(SPELL_EFFECT_SUMMON))
            return OgreRollKind::None;

        for (SpellEffectInfo const& effect : spellInfo->Effects)
            if (effect.TargetA.GetTarget() == TARGET_UNIT_PET || effect.TargetB.GetTarget() == TARGET_UNIT_PET)
                return OgreRollKind::None;

        if (spellInfo->IsPositive())
        {
            bool const heal = spellInfo->HasEffect(SPELL_EFFECT_HEAL) || spellInfo->HasAura(SPELL_AURA_PERIODIC_HEAL);
            return heal ? OgreRollKind::Ranged : OgreRollKind::Buff;
        }

        // Charges and leaps carry the body into melee.
        if (spellInfo->HasEffect(SPELL_EFFECT_CHARGE) || spellInfo->HasEffect(SPELL_EFFECT_JUMP)
            || spellInfo->HasEffect(SPELL_EFFECT_JUMP_DEST))
            return OgreRollKind::Melee;

        if (spellInfo->DmgClass == SPELL_DAMAGE_CLASS_MELEE
            || spellInfo->GetMaxRange(false) <= NOMINAL_MELEE_RANGE + 0.5f)
            return OgreRollKind::Melee;

        return OgreRollKind::Ranged;
    }

    bool FitsRole(OgreRollCandidate const& candidate, uint8 role)
    {
        if (role == OGRE_ROLE_BODY)
            return candidate.Kind == OgreRollKind::Melee || candidate.Kind == OgreRollKind::Buff;

        // Hunter ranged spells need a ranged weapon and ammo: never for the head.
        return (candidate.Kind == OgreRollKind::Ranged || candidate.Kind == OgreRollKind::Buff)
            && candidate.Class != CLASS_HUNTER;
    }

    // Highest rank of the chain starting at `firstRank` that a character of `level` may know.
    uint32 HighestRankForLevel(uint32 firstRank, uint8 level)
    {
        uint32 best = firstRank;
        for (uint32 rank = sSpellMgr->GetNextSpellInChain(firstRank); rank; rank = sSpellMgr->GetNextSpellInChain(rank))
        {
            SpellInfo const* spellInfo = sSpellMgr->GetSpellInfo(rank);
            if (!spellInfo || spellInfo->SpellLevel > level)
                break;
            best = rank;
        }
        return best;
    }

    uint32 PowerBit(SpellInfo const* spellInfo)
    {
        bool const extraPower = spellInfo->PowerType == POWER_RAGE || spellInfo->PowerType == POWER_ENERGY;
        return extraPower ? 1 << spellInfo->PowerType : 0;
    }

    constexpr uint8 RollDecoys = 14;
    constexpr uint8 BodyBarButtons = 72;    // main bar pages and multi bars, not the stance bars
}

void OgreMgr::LoadRollPool()
{
    // Ogres learn their class spells from the roulette only, never from class trainers.
    _classTrainers.clear();
    if (QueryResult trainers = WorldDatabase.Query("SELECT Id FROM trainer WHERE Type = 0"))
    {
        do
            _classTrainers.insert(trainers->Fetch()[0].Get<uint32>());
        while (trainers->NextRow());
    }

    _rollPool.clear();
    if (!_rouletteEnabled)
        return;

    // Every spell a class trainer teaches, as its first rank.
    QueryResult result = WorldDatabase.Query("SELECT DISTINCT CAST(t.Requirement AS UNSIGNED), "
        "CAST(ts.SpellId AS UNSIGNED) FROM trainer t JOIN trainer_spell ts ON ts.TrainerId = t.Id WHERE t.Type = 0");
    if (!result)
    {
        LOG_ERROR("module.ogre", "TwoHeadedOgre: no class trainer spell, the spell roulette is empty.");
        return;
    }

    std::unordered_set<uint32> seen;
    do
    {
        Field* fields = result->Fetch();
        uint32 firstRank = sSpellMgr->GetFirstSpellInChain(uint32(fields[1].Get<uint64>()));
        if (!seen.insert(firstRank).second)
            continue;

        SpellInfo const* spellInfo = sSpellMgr->GetSpellInfo(firstRank);
        if (!spellInfo)
            continue;

        OgreRollKind kind = ClassifyRollSpell(spellInfo);
        if (kind == OgreRollKind::None)
            continue;

        OgreRollCandidate candidate;
        candidate.Spell = firstRank;
        uint32 const spellLevel = spellInfo->SpellLevel ? spellInfo->SpellLevel : spellInfo->BaseLevel;
        candidate.Level = uint8(std::max<uint32>(1, spellLevel));
        candidate.Class = uint8(fields[0].Get<uint64>());
        candidate.Kind = kind;
        _rollPool.push_back(candidate);
    } while (result->NextRow());

    std::size_t const body = std::count_if(_rollPool.begin(), _rollPool.end(),
        [](OgreRollCandidate const& candidate) { return FitsRole(candidate, OGRE_ROLE_BODY); });
    std::size_t const head = std::count_if(_rollPool.begin(), _rollPool.end(),
        [](OgreRollCandidate const& candidate) { return FitsRole(candidate, OGRE_ROLE_HEAD); });
    LOG_INFO("module.ogre", ">> Spell roulette: {} body spells, {} head spells.", body, head);
}

void OgreMgr::LoadRolledSpells(Player* player)
{
    OgreRolledSpells rolled;
    QueryResult result = CharacterDatabase.Query("SELECT spell, owner, level FROM mod_two_headed_ogre_rolled_spell "
        "WHERE guid = {}", player->GetGUID().GetCounter());
    if (result)
    {
        do
        {
            Field* fields = result->Fetch();
            uint32 spellId = fields[0].Get<uint32>();
            rolled.Owners[spellId] = fields[1].Get<uint8>();
            rolled.Levels[fields[2].Get<uint8>()] = spellId;
        } while (result->NextRow());
    }

    std::unique_lock lock(_rollLock);
    _rolled[player->GetGUID()] = std::move(rolled);
}

void OgreMgr::RefreshPowerMask(Player* player)
{
    uint32 mask = 0;
    for (auto const& [spellId, spell] : player->GetSpellMap())
        if (spell->State != PLAYERSPELL_REMOVED && spell->Active)
            if (SpellInfo const* spellInfo = sSpellMgr->GetSpellInfo(spellId))
                mask |= PowerBit(spellInfo);

    std::unique_lock lock(_rollLock);
    _rolled[player->GetGUID()].PowerMask = mask;
}

void OgreMgr::ForgetRolledSpells(ObjectGuid guid)
{
    std::unique_lock lock(_rollLock);
    _rolled.erase(guid);
}

int32 OgreMgr::GetRolledOwner(Player const* player, uint32 spellId) const
{
    uint32 const firstRank = sSpellMgr->GetFirstSpellInChain(spellId);

    std::shared_lock lock(_rollLock);
    auto itr = _rolled.find(player->GetGUID());
    if (itr == _rolled.end())
        return -1;

    auto owner = itr->second.Owners.find(firstRank);
    return owner == itr->second.Owners.end() ? -1 : int32(owner->second);
}

uint32 OgreMgr::GetKnownRank(Player const* player, uint32 spellId)
{
    uint32 known = 0;
    for (uint32 rank = sSpellMgr->GetFirstSpellInChain(spellId); rank; rank = sSpellMgr->GetNextSpellInChain(rank))
        if (player->HasActiveSpell(rank))
            known = rank;
    return known;
}

bool OgreMgr::HasActivePowerType(Player const* player, uint8 power) const
{
    if (!IsOgre(player))
        return false;

    std::shared_lock lock(_rollLock);
    auto itr = _rolled.find(player->GetGUID());
    return itr != _rolled.end() && (itr->second.PowerMask & (1 << power));
}

void OgreMgr::SendResources(Player* player, WorldSession* session) const
{
    uint32 mask = 0;
    {
        std::shared_lock lock(_rollLock);
        auto itr = _rolled.find(player->GetGUID());
        if (itr != _rolled.end())
            mask = itr->second.PowerMask;
    }
    SendHeadMessage(player, session, Acore::StringFormat("RES {}", mask));
}

void OgreMgr::OnLevelChanged(Player* player, uint8 oldLevel)
{
    if (!IsOgre(player))
        return;

    for (uint8 level = oldLevel + 1; level <= player->GetLevel(); ++level)
        Roll(player, level);

    UpgradeRolledRanks(player);
}

void OgreMgr::CatchUpRolls(Player* player)
{
    if (!IsOgre(player))
        return;

    // Levels gained before the roulette existed, or while it found nothing to roll.
    for (uint8 level = 2; level <= player->GetLevel(); ++level)
        Roll(player, level);

    UpgradeRolledRanks(player);
}

void OgreMgr::Roll(Player* player, uint8 level)
{
    // One roll every `_rollInterval` levels, the body and the head in turn (the body first).
    if (!_rouletteEnabled || level < 2 || level % _rollInterval)
        return;

    uint8 const role = (level / _rollInterval) % 2 == 1 ? OGRE_ROLE_BODY : OGRE_ROLE_HEAD;
    {
        std::shared_lock lock(_rollLock);
        auto itr = _rolled.find(player->GetGUID());
        if (itr != _rolled.end() && itr->second.Levels.contains(level))
            return;
    }

    std::vector<OgreRollCandidate const*> candidates;
    std::vector<uint32> decoys;
    for (OgreRollCandidate const& candidate : _rollPool)
    {
        if (!FitsRole(candidate, role))
            continue;

        decoys.push_back(candidate.Spell);

        // A spell is rolled once per ogre, for one head only.
        if (candidate.Level <= level && !GetKnownRank(player, candidate.Spell)
            && GetRolledOwner(player, candidate.Spell) < 0)
            candidates.push_back(&candidate);
    }

    if (candidates.empty())
        return;

    OgreRollCandidate const* rolled = candidates[urand(0, candidates.size() - 1)];
    SpellInfo const* spellInfo = sSpellMgr->GetSpellInfo(rolled->Spell);

    // Owner first: the spell lists of both clients follow it.
    uint32 const powerBit = PowerBit(spellInfo);
    bool newPower = false;
    {
        std::unique_lock lock(_rollLock);
        OgreRolledSpells& spells = _rolled[player->GetGUID()];
        spells.Owners[rolled->Spell] = role;
        spells.Levels[level] = rolled->Spell;
        newPower = powerBit && !(spells.PowerMask & powerBit);
        spells.PowerMask |= powerBit;
    }
    CharacterDatabase.Execute("REPLACE INTO mod_two_headed_ogre_rolled_spell (guid, spell, owner, level) "
        "VALUES ({}, {}, {}, {})", player->GetGUID().GetCounter(), rolled->Spell, role, level);

    uint32 const rank = HighestRankForLevel(rolled->Spell, player->GetLevel());
    player->learnSpell(rank);
    AddToBars(player, role, rank);

    if (newPower && spellInfo->PowerType == POWER_ENERGY)
        player->SetPower(POWER_ENERGY, player->GetMaxPower(POWER_ENERGY));

    // Both clients play the roulette (the steering client's packets are mirrored to the head).
    WorldSession* session = player->GetSession();
    std::string message = Acore::StringFormat("ROLL {} {}", role == OGRE_ROLE_BODY ? "B" : "H", rank);
    for (uint8 i = 0; i < RollDecoys && !decoys.empty(); ++i)
        message += Acore::StringFormat(" {}", decoys[urand(0, decoys.size() - 1)]);
    SendHeadMessage(player, session, message);
    if (newPower)
        SendResources(player, session);

    char const* name = spellInfo->SpellName[session->GetSessionDbcLocale()];
    if (!name || !*name)
        name = spellInfo->SpellName[DEFAULT_LOCALE];
    Notify(session, Acore::StringFormat("Roulette du niveau {} : {} obtient {}.", level,
        role == OGRE_ROLE_BODY ? "le corps" : "la tete", name));

    LOG_INFO("module.ogre", "Roulette: {} level {} -> {} ({}) for the {}.", player->GetName(), level, rank, name,
        role == OGRE_ROLE_BODY ? "body" : "head");
}

void OgreMgr::UpgradeRolledRanks(Player* player)
{
    std::vector<uint32> firstRanks;
    {
        std::shared_lock lock(_rollLock);
        auto itr = _rolled.find(player->GetGUID());
        if (itr == _rolled.end())
            return;
        for (auto const& [spellId, owner] : itr->second.Owners)
            firstRanks.push_back(spellId);
    }

    for (uint32 firstRank : firstRanks)
    {
        uint32 const rank = HighestRankForLevel(firstRank, player->GetLevel());
        if (!player->HasSpell(rank))
            player->learnSpell(rank);
    }
}

void OgreMgr::AddToBars(Player* player, uint8 role, uint32 spellId)
{
    if (role == OGRE_ROLE_BODY)
    {
        for (uint8 button = 0; button < BodyBarButtons; ++button)
        {
            if (player->GetActionButton(button))
                continue;

            player->addActionButton(button, spellId, ACTION_BUTTON_SPELL);
            player->SendActionButtons(1);
            break;
        }
        return;
    }

    // The head's bars belong to the accounts: each account gets the spell for the times it plays the head.
    std::array<uint32, 2> accounts{};
    {
        std::shared_lock lock(_lock);
        auto itr = _ogres.find(player->GetGUID());
        if (itr == _ogres.end())
            return;
        accounts = itr->second.Accounts;
    }

    uint32 const packed = ACTION_BUTTON_ACTION(spellId) | (uint32(ACTION_BUTTON_SPELL) << 24);
    for (uint32 accountId : accounts)
    {
        if (!accountId)
            continue;

        std::array<uint32, MAX_ACTION_BUTTONS> const bar = LoadHeadBar(player, accountId);
        for (uint8 button = 0; button < HeadBarButtons; ++button)
        {
            if (bar[button])
                continue;

            SetHeadBarButton(player, accountId, button, packed);
            break;
        }
    }

    if (WorldSession* head = GetHeadSession(player))
        SendHeadBar(player, head);
}


bool OgreMgr::IsOgre(Player const* player) const
{
    return _enabled && player && player->getRace() == _race;
}

bool OgreMgr::HandleCreateRequest(WorldSession* session, std::string& name, uint8& playerClass, uint8& response)
{
    if (!_enabled)
    {
        response = CHAR_CREATE_DISABLED;
        return false;
    }

    // Logged so a server refusal can be told apart from a client-side one.
    auto refuse = [&](uint8 code)
    {
        LOG_INFO("module.ogre", "Account {} could not create ogre '{}': response {}.", session->GetAccountId(), name,
            code);
        response = code;
        return false;
    };

    // The client only lets letters through: both head names arrive glued, the second one starts at the
    // second capital letter ("GrokkMurg").
    std::wstring wideName;
    if (!Utf8toWStr(name, wideName))
        return refuse(CHAR_NAME_INVALID_CHARACTER);

    std::size_t separator = 1;
    while (separator < wideName.size() && wideName[separator] == wcharToLower(wideName[separator]))
        ++separator;

    // Both head names are required: an ogre is never created alone.
    if (separator >= wideName.size())
        return refuse(CHAR_NAME_NO_NAME);

    std::array<std::string, 2> names;
    if (!WStrToUtf8(wideName.substr(0, separator), names[0]) || !WStrToUtf8(wideName.substr(separator), names[1]))
        return refuse(CHAR_NAME_INVALID_CHARACTER);

    for (std::string& headName : names)
    {
        if (!normalizePlayerName(headName))
            return refuse(CHAR_NAME_NO_NAME);

        uint8 check = ObjectMgr::CheckPlayerName(headName, true);
        if (check != CHAR_NAME_SUCCESS)
            return refuse(check);
    }

    if (SameName(names[0], names[1]))
        return refuse(CHAR_NAME_FAILURE);

    uint32 accountId = session->GetAccountId();

    {
        std::unique_lock lock(_lock);
        for (auto& [guid, ogre] : _ogres)
        {
            bool samePair = (SameName(ogre.Names[0], names[0]) && SameName(ogre.Names[1], names[1]))
                || (SameName(ogre.Names[0], names[1]) && SameName(ogre.Names[1], names[0]));

            if (!samePair)
            {
                // A head name belongs to one ogre only.
                for (std::string const& used : ogre.Names)
                    if (SameName(used, names[0]) || SameName(used, names[1]))
                    {
                        response = CHAR_CREATE_NAME_IN_USE;
                        return false;
                    }

                continue;
            }

            // Same pair typed on the partner's account: join the existing ogre instead of creating one.
            uint8 freeHead = ogre.Accounts[0] ? 1 : 0;
            if (ogre.Accounts[freeHead] || ogre.Accounts[0] == accountId || ogre.Accounts[1] == accountId)
            {
                response = CHAR_CREATE_NAME_IN_USE;
                return false;
            }

            ogre.Accounts[freeHead] = accountId;
            SaveOgre(ogre);

            CharacterDatabasePreparedStatement* stmt = CharacterDatabase.GetPreparedStatement(CHAR_INS_CHARACTER_SHARED_ACCESS);
            stmt->SetData(0, guid.GetCounter());
            stmt->SetData(1, accountId);
            CharacterDatabase.Execute(stmt);

            LOG_INFO("module.ogre", "Account {} joined ogre {} ({}) as head '{}'.", accountId, ogre.Names[0], guid.ToString(),
                ogre.Names[freeHead]);
            response = CHAR_CREATE_SUCCESS;
            return false;
        }

        _pendingCreates[accountId] = names;
    }

    // New ogre: the character carries the first name, the ogre carries no class choice.
    name = names[0];
    playerClass = _carrierClass;
    return true;
}

void OgreMgr::OnCharacterCreated(Player* player)
{
    if (!IsOgre(player))
        return;

    uint32 accountId = player->GetSession()->GetAccountId();

    std::unique_lock lock(_lock);
    auto pending = _pendingCreates.find(accountId);
    if (pending == _pendingCreates.end() || !SameName(pending->second[0], player->GetName()))
        return;

    OgreInfo ogre;
    ogre.Guid = player->GetGUID();
    ogre.Names = { player->GetName(), pending->second[1] };
    ogre.Accounts = { accountId, 0 };
    _pendingCreates.erase(pending);

    _ogres[ogre.Guid] = ogre;
    SaveOgre(ogre);
    LOG_INFO("module.ogre", "Account {} created ogre {} ({}), waiting for head '{}'.", accountId, ogre.Names[0],
        ogre.Guid.ToString(), ogre.Names[1]);
}

void OgreMgr::OnCharacterDeleted(ObjectGuid guid)
{
    std::unique_lock lock(_lock);
    if (_ogres.erase(guid))
    {
        CharacterDatabase.Execute("DELETE FROM mod_two_headed_ogre_pair WHERE guid = {}", guid.GetCounter());
        CharacterDatabase.Execute("DELETE FROM mod_two_headed_ogre_head_action WHERE guid = {}", guid.GetCounter());
    }
}

void OgreMgr::OnSharedAccessLeft(ObjectGuid guid, uint32 accountId)
{
    std::unique_lock lock(_lock);
    auto itr = _ogres.find(guid);
    if (itr == _ogres.end())
        return;

    // The head becomes free: the next account creating an ogre with the same two names takes it.
    for (uint32& headAccount : itr->second.Accounts)
        if (headAccount == accountId)
            headAccount = 0;

    SaveOgre(itr->second);
    CharacterDatabase.Execute("DELETE FROM mod_two_headed_ogre_head_action WHERE guid = {} AND account = {}",
        guid.GetCounter(), accountId);
}

bool OgreMgr::CanJoin(Player* player, WorldSession* session) const
{
    if (!IsOgre(player) || player->HasCopilotSessions())
        return false;

    std::shared_lock lock(_lock);
    auto itr = _ogres.find(player->GetGUID());
    if (itr == _ogres.end())
        return false;

    uint32 accountId = session->GetAccountId();
    return accountId && (itr->second.Accounts[0] == accountId || itr->second.Accounts[1] == accountId);
}

void OgreMgr::OnLoadFromDB(Player* player)
{
    if (!IsOgre(player))
        return;

    LoadRolledSpells(player);

    // Unit::SetDisplayId sets the gender of the creature model (the race display set before this hook already did):
    // the character's own gender is the one kept in PLAYER_BYTES_3.
    uint8 const gender = player->GetByteValue(PLAYER_BYTES_3, 0);
    if (uint32 displayId = ResolveDisplayId(gender))
    {
        player->SetNativeDisplayId(displayId);
        player->SetDisplayId(displayId, _scale);
        player->SetByteValue(UNIT_FIELD_BYTES_0, 2, gender);
    }
}

void OgreMgr::OnLogin(Player* player)
{
    if (!IsOgre(player))
        return;

    // No class, no equipment restriction: every weapon and armor proficiency.
    for (uint32 spellId : _spells)
    {
        if (player->HasSpell(spellId) || !sSpellMgr->GetSpellInfo(spellId))
            continue;

        player->learnSpell(spellId);
    }

    RefreshPowerMask(player);

    std::string body = GetHeadName(player->GetGUID(), player->GetSession()->GetAccountId());
    Notify(player->GetSession(), Acore::StringFormat("{} est le corps. La deuxieme tete peut se connecter.", body));
}

void OgreMgr::OnFirstLogin(Player* player)
{
    if (!IsOgre(player))
        return;

    // No Paladin: its class skills go, with the spells they gave (Seal of Righteousness, Holy Light...).
    for (uint16 skill : { uint16(SKILL_HOLY2), uint16(SKILL_PROTECTION2), uint16(SKILL_RETRIBUTION) })
        if (player->HasSkill(skill))
            player->SetSkill(skill, 0, 0, 0);

    // Stock action buttons of the removed spells.
    for (uint8 button = 0; button < MAX_ACTION_BUTTONS; ++button)
        if (ActionButton const* action = player->GetActionButton(button))
            if (action->GetType() == ACTION_BUTTON_SPELL && !player->HasSpell(action->GetAction()))
                player->removeActionButton(button);

    // The Brute's own start: its spells (the body's), and a fist in each hand.
    for (uint32 spellId : _bruteSpells)
    {
        if (player->HasSpell(spellId) || !sSpellMgr->GetSpellInfo(spellId))
            continue;

        player->learnSpell(spellId);
        AddToBars(player, OGRE_ROLE_BODY, spellId);
    }

    if (_bruteOffHand && !player->GetItemByPos(INVENTORY_SLOT_BAG_0, EQUIPMENT_SLOT_OFFHAND))
    {
        uint16 dest;
        if (player->CanEquipNewItem(EQUIPMENT_SLOT_OFFHAND, dest, _bruteOffHand, false) == EQUIP_ERR_OK)
            player->EquipNewItem(dest, _bruteOffHand, true);
    }

    RefreshPowerMask(player);
    player->SendActionButtons(1);
}

void OgreMgr::OnHeadAttached(Player* player, WorldSession* session)
{
    if (!IsOgre(player))
        return;

    SendHeadMessage(player, session, "ROLE HEAD");
    SendHeadBar(player, session);

    std::string body = GetHeadName(player->GetGUID(), player->GetSession()->GetAccountId());
    std::string head = GetHeadName(player->GetGUID(), session->GetAccountId());
    // Sent to the steering client, mirrored to every head.
    Notify(player->GetSession(), Acore::StringFormat("Ogre reuni : {} (corps) et {} (tete).", body, head));
}

void OgreMgr::OnHeadDetached(Player* player, WorldSession* session)
{
    if (!IsOgre(player))
        return;

    Notify(player->GetSession(), Acore::StringFormat("{} (tete) s'est deconnecte.",
        GetHeadName(player->GetGUID(), session->GetAccountId())));
}

void OgreMgr::OnHandover(Player* player, WorldSession* oldSession, WorldSession* newSession)
{
    if (!IsOgre(player))
        return;

    // The new body steers with the character's own spells and bars.
    player->SendInitialSpells();
    player->SendActionButtons(1);
    SendHeadMessage(player, newSession, "ROLE BODY");

    Notify(newSession, Acore::StringFormat("{} s'est deconnecte : {} devient le corps.",
        GetHeadName(player->GetGUID(), oldSession->GetAccountId()), GetHeadName(player->GetGUID(), newSession->GetAccountId())));
}

void OgreMgr::PrefixChat(Player* player, std::string& message) const
{
    if (!_chatPrefix || !IsOgre(player) || message.empty() || message[0] == '.' || message[0] == '!')
        return;

    std::string head = GetHeadName(player->GetGUID(), player->GetActingSession()->GetAccountId());
    if (!head.empty() && !SameName(head, player->GetName()))
        message = "[" + head + "] " + message;
}

void OgreMgr::ApplyScale(Player* player) const
{
    if (IsOgre(player) && player->GetDisplayId() == player->GetNativeDisplayId() && player->GetObjectScale() != _scale)
        player->SetObjectScale(_scale);
}

std::string OgreMgr::GetHeadName(ObjectGuid guid, uint32 accountId) const
{
    std::shared_lock lock(_lock);
    auto itr = _ogres.find(guid);
    if (itr == _ogres.end())
        return "";

    for (uint8 i = 0; i < 2; ++i)
        if (itr->second.Accounts[i] == accountId)
            return itr->second.Names[i];

    return "";
}

std::array<uint32, MAX_ACTION_BUTTONS> OgreMgr::LoadHeadBar(Player* player, uint32 accountId) const
{
    std::array<uint32, MAX_ACTION_BUTTONS> buttons{};

    QueryResult result = CharacterDatabase.Query("SELECT button, data FROM mod_two_headed_ogre_head_action "
        "WHERE guid = {} AND account = {}", player->GetGUID().GetCounter(), accountId);
    if (result)
    {
        do
        {
            Field* fields = result->Fetch();
            uint8 button = fields[0].Get<uint8>();
            if (button < MAX_ACTION_BUTTONS)
                buttons[button] = fields[1].Get<uint32>();
        } while (result->NextRow());
    }
    else
    {
        // First time this account gets a head bar for the ogre: its default spells, saved so it can rearrange them.
        for (uint8 button = 0; button < _headActionBar.size(); ++button)
        {
            buttons[button] = ACTION_BUTTON_ACTION(_headActionBar[button]) | (uint32(ACTION_BUTTON_SPELL) << 24);
            SetHeadBarButton(player, accountId, button, buttons[button]);
        }
    }

    return buttons;
}

void OgreMgr::SendHeadBar(Player* player, WorldSession* session) const
{
    std::array<uint32, MAX_ACTION_BUTTONS> const buttons = LoadHeadBar(player, session->GetAccountId());

    // The head's own bar shows the spells; its greyed stock bars stay empty underneath.
    WorldPacket data(SMSG_ACTION_BUTTONS, 1 + MAX_ACTION_BUTTONS * 4);
    data << uint8(1);
    for (uint8 button = 0; button < MAX_ACTION_BUTTONS; ++button)
        data << uint32(0);
    session->SendPacket(&data);

    // Only what the head may cast (the stances, for instance, are the body's).
    std::string bar = "BAR";
    for (uint8 button = 0; button < HeadBarButtons; ++button)
        if (buttons[button] && ACTION_BUTTON_TYPE(buttons[button]) == ACTION_BUTTON_SPELL
            && CanUseSpellFromSession(player, session, ACTION_BUTTON_ACTION(buttons[button])))
            bar += Acore::StringFormat(" {}:{}", button + 1, ACTION_BUTTON_ACTION(buttons[button]));
    SendHeadMessage(player, session, bar);
}

void OgreMgr::SendHeadMessage(Player* player, WorldSession* session, std::string_view text) const
{
    // Sent to that client only: a co-pilot session never mirrors what it receives.
    WorldPacket data;
    ChatHandler::BuildChatPacket(data, CHAT_MSG_WHISPER, LANG_ADDON, player, player,
        std::string(HeadMessagePrefix) + std::string(text));
    session->SendPacket(&data);
}

bool OgreMgr::HandleHeadMessage(Player* player, WorldSession* session, std::string_view message)
{
    if (!message.starts_with(HeadMessagePrefix))
        return false;

    if (!IsOgre(player) || !session)
        return true;

    std::vector<std::string_view> args = Acore::Tokenize(message.substr(HeadMessagePrefix.size()), ' ', false);
    if (args.empty())
        return true;

    // The body's client keeps its stock bars. Its interface is ready: missing roulette rolls are done now so
    // it plays them, and it learns the extra resources the ogre uses.
    if (session == player->GetSteeringSession())
    {
        if (args[0] == "HELLO")
        {
            CatchUpRolls(player);
            SendResources(player, session);
        }
        return true;
    }

    auto headSpell = [&](std::string_view token) -> SpellInfo const*
    {
        // Any rank of the chain: the head casts the highest one the ogre knows.
        Optional<uint32> spellId = Acore::StringTo<uint32>(token);
        uint32 const rank = spellId ? GetKnownRank(player, *spellId) : 0;
        if (!rank || !CanUseSpellFromSession(player, session, rank))
            return nullptr;
        return sSpellMgr->GetSpellInfo(rank);
    };

    auto barSlot = [](std::string_view token) -> Optional<uint8>
    {
        Optional<uint32> slot = Acore::StringTo<uint32>(token);
        if (!slot || !*slot || *slot > HeadBarButtons)
            return std::nullopt;
        return uint8(*slot - 1);
    };

    if (args[0] == "HELLO")
    {
        SendHeadMessage(player, session, "ROLE HEAD");
        SendHeadMessage(player, session, player->HasAura(SPELL_OGRE_TWO_MINDS) ? "FREE 1" : "FREE 0");
        SendResources(player, session);
        SendHeadBar(player, session);
    }
    else if (args[0] == "CAST" && args.size() >= 3)
    {
        SpellInfo const* spellInfo = headSpell(args[1]);
        if (!spellInfo)
            return true;

        // UnitGUID() of the head's own target ("0x..."), 0 without target.
        uint64 rawGuid = std::strtoull(std::string(args[2]).c_str(), nullptr, 16);
        Unit* target = rawGuid ? ObjectAccessor::GetUnit(*player, ObjectGuid(rawGuid)) : nullptr;
        if (player->HasAura(SPELL_OGRE_TWO_MINDS))
        {
            StartFreeCast(player, session, spellInfo, target);
            return true;
        }

        // Idée fixe: one cast on the head's own timeline, like Fureur bicéphale.
        if (player->HasAura(SPELL_OGRE_FIXED_IDEA))
        {
            player->RemoveAurasDueToSpell(SPELL_OGRE_FIXED_IDEA);
            uint8 const brainstorm = TalentRank(player, SPELL_OGRE_TALENT_BRAINSTORM, 2);
            StartFreeCast(player, session, spellInfo, target, brainstorm >= 1, brainstorm >= 2);
            return true;
        }

        // Range, facing and line of sight are checked from the ogre's real position (the body's).
        SpellCastResult result = player->CastSpell(target, spellInfo, TRIGGERED_NONE);
        LOG_INFO("module.ogre", "Head of {} casts {} on {} ({:.1f} yd): result {}.", player->GetName(), spellInfo->Id,
            target ? target->GetName() : "no target", target ? player->GetDistance(target) : 0.0f, uint32(result));

        if (result == SPELL_CAST_OK && !spellInfo->IsPositive())
            OnHeadAttack(player);
    }
    else if (args[0] == "SET" && args.size() >= 3)
    {
        Optional<uint8> slot = barSlot(args[1]);
        if (SpellInfo const* spellInfo = headSpell(args[2]); slot && spellInfo)
            SetHeadActionButton(player, session, *slot,
                ACTION_BUTTON_ACTION(spellInfo->Id) | (uint32(ACTION_BUTTON_SPELL) << 24));
    }
    else if (args[0] == "CLR" && args.size() >= 2)
    {
        if (Optional<uint8> slot = barSlot(args[1]))
            SetHeadActionButton(player, session, *slot, 0);
    }

    return true;
}

void OgreMgr::SetHeadActionButton(Player* player, WorldSession* session, uint8 button, uint32 packedData) const
{
    if (IsOgre(player))
        SetHeadBarButton(player, session->GetAccountId(), button, packedData);
}

void OgreMgr::SetHeadBarButton(Player* player, uint32 accountId, uint8 button, uint32 packedData) const
{
    uint32 guid = player->GetGUID().GetCounter();
    if (packedData)
        CharacterDatabase.Execute("REPLACE INTO mod_two_headed_ogre_head_action (guid, account, button, data) "
            "VALUES ({}, {}, {}, {})", guid, accountId, button, packedData);
    else
        CharacterDatabase.Execute("DELETE FROM mod_two_headed_ogre_head_action "
            "WHERE guid = {} AND account = {} AND button = {}", guid, accountId, button);
}

bool OgreMgr::CanUseSpellFromSession(Player const* player, WorldSession const* session, uint32 spellId) const
{
    if (!IsOgre(player))
        return true;

    bool const headSession = session != player->GetSteeringSession();
    if (SameChain(_sharedSpells, spellId))
        return true;

    if (int32 owner = GetRolledOwner(player, spellId); owner >= 0)
        return headSession == (owner == OGRE_ROLE_HEAD);

    if (SameChain(_headSpells, spellId))
        return headSession;

    if (!headSession)
        return true;

    // The head's client still lists passive spells (proficiencies, languages...): it never casts them.
    SpellInfo const* spellInfo = sSpellMgr->GetSpellInfo(spellId);
    return spellInfo && spellInfo->IsPassive();
}

WorldSession* OgreMgr::GetHeadSession(Player const* player)
{
    std::vector<WorldSession*> const& copilots = player->GetCopilotSessions();
    return copilots.empty() ? nullptr : copilots.front();
}

void OgreMgr::StartFreeCast(Player* player, WorldSession* session, SpellInfo const* spellInfo, Unit* target,
    bool instant, bool noCost) const
{
    OgreHeadState* state = player->CustomData.GetDefault<OgreHeadState>(HeadStateKey);
    if (state->PendingSpell || state->GlobalCooldown)
        return;

    // The head's own global cooldown, started with the cast like the stock one.
    if (spellInfo->StartRecoveryTime)
    {
        state->GlobalCooldown = spellInfo->StartRecoveryTime;
        SendHeadMessage(player, session, Acore::StringFormat("GCD {}", state->GlobalCooldown));
    }

    ObjectGuid targetGuid = target ? target->GetGUID() : ObjectGuid::Empty;
    uint32 castTime = instant ? 0 : spellInfo->CalcCastTime(player);
    if (!castTime)
    {
        FinishFreeCast(player, spellInfo->Id, targetGuid, noCost);
        return;
    }

    state->PendingSpell = spellInfo->Id;
    state->PendingTarget = targetGuid;
    state->PendingTimer = castTime;
    state->PendingNoCost = noCost;
    SendHeadMessage(player, session, Acore::StringFormat("CASTBAR {} {}", spellInfo->Id, castTime));
}

void OgreMgr::FinishFreeCast(Player* player, uint32 spellId, ObjectGuid targetGuid, bool noCost) const
{
    WorldSession* head = GetHeadSession(player);
    SpellInfo const* spellInfo = sSpellMgr->GetSpellInfo(spellId);
    if (!head || !spellInfo)
        return;

    SendHeadMessage(player, head, "CASTSTOP");

    // Still a head: stuns, fears and silences stop it, the body's moves and casts do not.
    if (!player->IsAlive() || player->HasUnitFlag(UNIT_FLAG_SILENCED)
        || player->HasUnitState(UNIT_STATE_STUNNED | UNIT_STATE_FLEEING | UNIT_STATE_CONFUSED))
        return;

    Unit* target = targetGuid ? ObjectAccessor::GetUnit(*player, targetGuid) : nullptr;

    // The head looks at its own target: the body's facing does not matter. Cast directly, outside the
    // ogre's cast slot (the body's cast goes on) and without its global cooldown.
    float const orientation = player->GetOrientation();
    if (target && target != player)
        player->SetOrientation(player->GetAngle(target));

    uint32 flags = TRIGGERED_IGNORE_GCD | TRIGGERED_CAST_DIRECTLY | TRIGGERED_IGNORE_CAST_IN_PROGRESS;
    if (noCost)
        flags |= TRIGGERED_IGNORE_POWER_AND_REAGENT_COST;

    SpellCastResult result = player->CastSpell(target, spellInfo, TriggerCastFlags(flags));
    player->SetOrientation(orientation);

    LOG_INFO("module.ogre", "Head of {} freely casts {} on {}: result {}.", player->GetName(), spellId,
        target ? target->GetName() : "no target", uint32(result));

    if (result == SPELL_CAST_OK && !spellInfo->IsPositive())
        OnHeadAttack(player);
}

void OgreMgr::OnHeadAttack(Player* player) const
{
    if (uint8 rank = TalentRank(player, SPELL_OGRE_TALENT_SHARED_RAGE, 3))
        player->ModifyPower(POWER_RAGE, rank * SharedRagePerRank);

    // Deux cerveaux: an attack of the head may give it Idée fixe.
    float const chance = _procChance + ProcTalentBonus[TalentRank(player, SPELL_OGRE_TALENT_FIXED_IDEAS, 2)];
    if (player->HasSpell(SPELL_OGRE_TWO_BRAINS) && roll_chance_f(chance))
        GiveFixedIdea(player);
}

void OgreMgr::GiveFixedIdea(Player* player) const
{
    player->AddAura(SPELL_OGRE_FIXED_IDEA, player);
    if (player->HasAura(SPELL_OGRE_TALENT_ONE_IDEA) && !player->HasAura(SPELL_OGRE_REFLEX))
        player->AddAura(SPELL_OGRE_REFLEX, player);
}

void OgreMgr::GiveReflex(Player* player) const
{
    player->AddAura(SPELL_OGRE_REFLEX, player);
    if (player->HasAura(SPELL_OGRE_TALENT_ONE_IDEA) && !player->HasAura(SPELL_OGRE_FIXED_IDEA))
        player->AddAura(SPELL_OGRE_FIXED_IDEA, player);
}

void OgreMgr::OnUpdate(Player* player, uint32 diff) const
{
    if (!IsOgre(player))
        return;

    // The first quest's ring: faster out of combat in the start zone.
    bool const stride = player->HasAura(SPELL_OGRE_STRIDE_RING) && player->GetZoneId() == StartZone
        && !player->IsInCombat() && player->IsAlive();
    if (stride != player->HasAura(SPELL_OGRE_STRIDE))
    {
        if (stride)
            player->AddAura(SPELL_OGRE_STRIDE, player);
        else
            player->RemoveAurasDueToSpell(SPELL_OGRE_STRIDE);
    }

    OgreHeadState* state = player->CustomData.GetDefault<OgreHeadState>(HeadStateKey);
    CountDown(state->ImpactCooldown, diff);
    CountDown(state->GlobalCooldown, diff);
    CountDown(state->ForcedImpactTimer, diff);
    CountDown(state->DoubleHitTimer, diff);
    CountDown(state->SurvivalCooldown, diff);
    CountDown(state->SpareHeadCooldown, diff);

    // Bond d'ogre: the impact when the jump ends.
    if (state->PendingImpactTimer)
    {
        CountDown(state->PendingImpactTimer, diff);
        if (!state->PendingImpactTimer && player->IsAlive())
            TriggerImpact(player, state->PendingImpactRatio);
    }

    WorldSession* head = GetHeadSession(player);
    if (player->IsAlive())
        UpdateStance(player, head != nullptr, state);

    // Instinct de survie: Fureur bicéphale for 15 s, without its cooldown.
    if (player->IsAlive() && player->IsInCombat() && !state->SurvivalCooldown
        && player->HealthBelowPct(int32(SurvivalHealthPct)) && !player->HasAura(SPELL_OGRE_TWO_MINDS)
        && player->HasAura(SPELL_OGRE_TALENT_SURVIVAL))
    {
        if (Aura* fury = player->AddAura(SPELL_OGRE_TWO_MINDS, player))
        {
            fury->SetMaxDuration(SurvivalFuryDuration);
            fury->SetDuration(SurvivalFuryDuration);
            state->AutoFury = true;
            state->SurvivalCooldown = SurvivalCooldown;
        }
    }

    bool const free = player->HasAura(SPELL_OGRE_TWO_MINDS);
    if (free != state->Free)
    {
        state->Free = free;

        // Fureur prolongée and Pensée rapide: once, when the fury starts (not the one of Instinct de survie).
        Aura* fury = free && !state->AutoFury ? player->GetAura(SPELL_OGRE_TWO_MINDS) : nullptr;
        if (uint8 rank = fury ? TalentRank(player, SPELL_OGRE_TALENT_LONG_FURY, 2) : 0)
        {
            fury->SetMaxDuration(fury->GetMaxDuration() + rank * LongFuryPerRank);
            fury->SetDuration(fury->GetDuration() + rank * LongFuryPerRank);
        }

        if (uint8 rank = fury ? TalentRank(player, SPELL_OGRE_TALENT_QUICK_THINKING, 2) : 0)
            player->ModifySpellCooldown(SPELL_OGRE_TWO_MINDS, -rank * QuickThinkingPerRank);

        if (!free)
            state->AutoFury = false;

        if (head)
            SendHeadMessage(player, head, free ? "FREE 1" : "FREE 0");
    }

    if (!state->PendingSpell)
        return;

    if (!head)
    {
        state->PendingSpell = 0;
        return;
    }

    if (state->PendingTimer > diff)
    {
        state->PendingTimer -= diff;
        return;
    }

    uint32 const spellId = state->PendingSpell;
    state->PendingSpell = 0;
    FinishFreeCast(player, spellId, state->PendingTarget, state->PendingNoCost);
}

void OgreMgr::UpdateStance(Player* player, bool headPresent, OgreHeadState* state) const
{
    // A stance just taken replaces the previous one (both auras are there for one update).
    uint32 current = 0;
    for (OgreStance const& stance : Stances)
        if (player->HasAura(stance.Aura) && (!current || stance.Aura != state->Stance))
            current = stance.Aura;

    // Always a stance, and the body holds the wall when the head is not there.
    if (!current || !headPresent)
        current = SPELL_OGRE_STANCE_TANK;

    for (OgreStance const& stance : Stances)
    {
        bool const active = stance.Aura == current;
        std::array<std::pair<uint32, bool>, 3> const auras = {{
            { stance.Aura, active },
            { stance.Extra, active },
            { stance.UltimateBonus, active && player->HasAura(stance.Ultimate) },
        }};

        for (auto const& [aura, on] : auras)
        {
            if (on == player->HasAura(aura))
                continue;

            if (on)
                player->AddAura(aura, player);
            else
                player->RemoveAurasDueToSpell(aura);
        }
    }

    state->Stance = current;
}

bool OgreMgr::IsHeadSpell(Player const* player, uint32 spellId) const
{
    return SameChain(_headSpells, spellId) || GetRolledOwner(player, spellId) == OGRE_ROLE_HEAD;
}

void OgreMgr::OnSpellDamage(Unit* target, Unit* attacker, int32& damage, SpellInfo const* spellInfo) const
{
    Player* player = attacker ? attacker->ToPlayer() : nullptr;
    if (!player || !target || !spellInfo || damage <= 0 || !IsOgre(player))
        return;

    OgreHeadState* state = player->CustomData.GetDefault<OgreHeadState>(HeadStateKey);
    if (IsHeadSpell(player, spellInfo->Id))
    {
        // Deux cerveaux: the head's damage (direct or over time) may give the body Réflexe d'ogre.
        float const chance = _procChance + ProcTalentBonus[TalentRank(player, SPELL_OGRE_TALENT_REFLEX, 2)];
        if (player->HasSpell(SPELL_OGRE_TWO_BRAINS) && !player->HasAura(SPELL_OGRE_REFLEX) && roll_chance_f(chance))
            GiveReflex(player);

        // Coup double: the body's next hit on this target.
        if (target != player && player->HasAura(SPELL_OGRE_TALENT_DOUBLE_HIT))
        {
            state->DoubleHitTarget = target->GetGUID();
            state->DoubleHitTimer = DoubleHitWindow;
        }
        return;
    }

    if (spellInfo->DmgClass != SPELL_DAMAGE_CLASS_MELEE || !state->DoubleHitTimer
        || state->DoubleHitTarget != target->GetGUID())
        return;

    state->DoubleHitTimer = 0;
    damage = int32(damage * (1.0f + DoubleHitPerRank * TalentRank(player, SPELL_OGRE_TALENT_DOUBLE_HIT, 3)));
}

void OgreMgr::OnMeleeDamage(Unit* target, Unit* attacker, uint32& damage) const
{
    // Coup double, on the body's auto attacks.
    if (Player* player = attacker ? attacker->ToPlayer() : nullptr; player && target && IsOgre(player))
    {
        OgreHeadState* state = player->CustomData.GetDefault<OgreHeadState>(HeadStateKey);
        if (state->DoubleHitTimer && state->DoubleHitTarget == target->GetGUID())
        {
            state->DoubleHitTimer = 0;
            damage = uint32(damage * (1.0f + DoubleHitPerRank * TalentRank(player, SPELL_OGRE_TALENT_DOUBLE_HIT, 3)));
        }
    }

    // Bavardage: "Aïe !", the head gets some mana back.
    Player* victim = target ? target->ToPlayer() : nullptr;
    if (!victim || !damage || !IsOgre(victim))
        return;

    if (uint8 rank = TalentRank(victim, SPELL_OGRE_TALENT_CHATTER, 2))
        victim->ModifyPower(POWER_MANA, int32(victim->GetMaxPower(POWER_MANA) * ChatterPerMillePerRank * rank / 1000));
}

void OgreMgr::OnDamageTaken(Unit* victim, uint32& damage) const
{
    Player* player = victim ? victim->ToPlayer() : nullptr;
    if (!player || damage < player->GetHealth() || !player->IsAlive() || !IsOgre(player)
        || !player->HasAura(SPELL_OGRE_TALENT_SPARE_HEAD))
        return;

    // Tête de rechange: the head takes the killing blow.
    OgreHeadState* state = player->CustomData.GetDefault<OgreHeadState>(HeadStateKey);
    if (state->SpareHeadCooldown)
        return;

    state->SpareHeadCooldown = SpareHeadCooldown;
    damage = player->GetHealth() - 1;
    ChatHandler(player->GetSession()).SendNotification("Tête de rechange : la tête encaisse le coup !");
}

void OgreMgr::OnMeleeRollAgainst(Unit const* attacker, Unit const* victim, int32& critChance, int32& dodgeChance) const
{
    // The roll only hands the units as const: the module's state on them changes all the same.
    // Riposte bicéphale: the body's auto attack after a Réflexe d'ogre dodge.
    if (Player* player = const_cast<Player*>(attacker ? attacker->ToPlayer() : nullptr); player && IsOgre(player))
    {
        OgreHeadState* state = player->CustomData.GetDefault<OgreHeadState>(HeadStateKey);
        if (state->BacklashCrit)
        {
            state->BacklashCrit = false;
            critChance = 10000;
        }
    }

    Player* player = const_cast<Player*>(victim ? victim->ToPlayer() : nullptr);
    if (!player || !attacker || !IsOgre(player) || !player->HasAura(SPELL_OGRE_REFLEX))
        return;

    // A dodge needs the attacker in front: from behind the reflex waits for the next hit.
    if (!player->HasInArc(float(M_PI), attacker))
        return;

    dodgeChance = 10000;
    player->RemoveAurasDueToSpell(SPELL_OGRE_REFLEX);

    uint8 const backlash = TalentRank(player, SPELL_OGRE_TALENT_BACKLASH, 2);
    if (backlash && roll_chance_f(BacklashChancePerRank * backlash))
        player->CustomData.GetDefault<OgreHeadState>(HeadStateKey)->BacklashCrit = true;
}

void OgreMgr::OnFall(Player* player, float fallHeight, bool& fallDamage) const
{
    if (!IsOgre(player) || !player->HasSpell(SPELL_OGRE_FALL))
        return;

    fallDamage = false;
    if (!player->IsAlive() || player->IsInWater())
        return;

    // Saut d'ogre: its landing hits at full power, whatever the height.
    OgreHeadState* state = player->CustomData.GetDefault<OgreHeadState>(HeadStateKey);
    if (state->ForcedImpactTimer)
    {
        state->ForcedImpactTimer = 0;
        state->ImpactCooldown = FallImpactCooldown;
        TriggerImpact(player, 1.0f);
        return;
    }

    if (fallHeight < FallImpactMinHeight || state->ImpactCooldown)
        return;

    state->ImpactCooldown = FallImpactCooldown;
    TriggerImpact(player, std::min(1.0f,
        (fallHeight - FallImpactMinHeight) / (FallImpactMaxHeight - FallImpactMinHeight)));
}

void OgreMgr::TriggerImpact(Player* player, float ratio) const
{
    // 5 + 2 per level, from 100% to 300% with the ratio, more with Chute lourde.
    float const heavyFall = 1.0f + HeavyFallPerRank * TalentRank(player, SPELL_OGRE_TALENT_HEAVY_FALL, 2);
    int32 const damage = int32((5 + 2 * player->GetLevel()) * (1.0f + 2.0f * ratio) * heavyFall);
    player->CastCustomSpell(SPELL_OGRE_IMPACT, SPELLVALUE_BASE_POINT0, damage, player, TRIGGERED_FULL_MASK);

    if (uint8 rank = TalentRank(player, SPELL_OGRE_TALENT_SHATTERING, 2))
        player->CastCustomSpell(SPELL_OGRE_SHATTERING_LANDING, SPELLVALUE_AURA_DURATION, rank * ShatteringPerRank,
            player, TRIGGERED_FULL_MASK);
}

void OgreMgr::OnOgreLeap(Player* player, Unit* target) const
{
    OgreHeadState* state = player->CustomData.GetDefault<OgreHeadState>(HeadStateKey);
    state->PendingImpactTimer = uint32(player->GetExactDist2d(target) / LeapSpeed * IN_MILLISECONDS) + 1;
    state->PendingImpactRatio = LeapImpactRatio;
}

void OgreMgr::OnOgreJump(Player* player) const
{
    player->JumpTo(0.0f, JumpSpeedZ);
    player->CustomData.GetDefault<OgreHeadState>(HeadStateKey)->ForcedImpactTimer = JumpLandingWindow;
}

uint32 OgreMgr::ResolveDisplayId(uint8 gender) const
{
    if (gender == GENDER_FEMALE && _femaleModelId)
        return _femaleModelId;

    if (_modelId)
        return _modelId;

    if (CreatureTemplate const* creature = sObjectMgr->GetCreatureTemplate(_creatureEntry))
        if (CreatureModel const* model = creature->GetFirstValidModel())
            return model->CreatureDisplayID;

    LOG_ERROR("module.ogre", "TwoHeadedOgre: no display for creature entry {}.", _creatureEntry);
    return 0;
}

void OgreMgr::SaveOgre(OgreInfo const& ogre) const
{
    // Names passed ObjectMgr::CheckPlayerName: letters only.
    CharacterDatabase.Execute("REPLACE INTO mod_two_headed_ogre_pair (guid, head1_name, head1_account, head2_name, head2_account) "
        "VALUES ({}, '{}', {}, '{}', {})", ogre.Guid.GetCounter(), ogre.Names[0], ogre.Accounts[0], ogre.Names[1], ogre.Accounts[1]);
}
