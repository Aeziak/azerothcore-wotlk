/*
 * mod-two-headed-ogre : one playable ogre character, two players.
 *
 * An ogre is ONE character (one Player, one GUID) that two accounts can log into. The first client in
 * steers it (the Body); the second one attaches as a co-pilot (the Head) through the core shared-control
 * sessions: same bags, equipment, experience, quests and group slot, because there is only one player.
 */

#ifndef MOD_TWO_HEADED_OGRE_H
#define MOD_TWO_HEADED_OGRE_H

#include "DataMap.h"
#include "Define.h"
#include "ObjectGuid.h"
#include <array>
#include <shared_mutex>
#include <string>
#include <unordered_map>
#include <unordered_set>
#include <vector>

class Player;
class SpellInfo;
class Unit;
class WorldSession;
struct ItemTemplate;

// Ogre racial spells (client/tools/ogre_spells.py, data/sql/db-world/base/mod_two_headed_ogre_spells.sql).
enum OgreSpells : uint32
{
    SPELL_OGRE_TWO_MINDS    = 91050,    // active: both heads act freely for 20 s
    SPELL_OGRE_FALL         = 91051,    // passive: no fall damage, impact on landing
    SPELL_OGRE_IMPACT       = 91052,    // the impact (damage + knock back around the ogre)
    SPELL_OGRE_STRIDE       = 91053,    // +20% speed out of combat in Blade's Edge...
    SPELL_OGRE_STRIDE_RING  = 91054,    // ...while wearing the first quest's ring (its equip effect)
    // Stances, one at a time, always one (MOI ENCAISSER without the head). Each visible aura has a hidden one.
    SPELL_OGRE_STANCE_HIT           = 91060,    // MOI TAPER
    SPELL_OGRE_STANCE_MAGIC         = 91061,    // MOI MAGIE
    SPELL_OGRE_STANCE_TANK          = 91062,    // MOI ENCAISSER
    SPELL_OGRE_STANCE_HIT_EXTRA     = 91063,
    SPELL_OGRE_STANCE_MAGIC_EXTRA   = 91064,
    SPELL_OGRE_STANCE_TANK_EXTRA    = 91065,
    // Deux cerveaux (passive): the head's attacks may give a free cast (Idée fixe), its damage a dodge (Réflexe).
    SPELL_OGRE_TWO_BRAINS           = 91066,
    SPELL_OGRE_REFLEX               = 91067,
    SPELL_OGRE_FIXED_IDEA           = 91068,
    // Ultimate talents: hidden bonus while their stance is on.
    SPELL_OGRE_STANCE_HIT_ULTIMATE      = 91070,
    SPELL_OGRE_STANCE_MAGIC_ULTIMATE    = 91071,
    SPELL_OGRE_STANCE_TANK_ULTIMATE     = 91072,
    // Brute talents the module drives (client/tools/ogre_talents.py): first rank, the next ranks follow.
    SPELL_OGRE_TALENT_SHARED_RAGE       = 91135,    // Rage partagée: the head's attacks give the body rage
    SPELL_OGRE_TALENT_DOUBLE_HIT        = 91145,    // Coup double: the body's hit after the head's spell
    SPELL_OGRE_TALENT_LONG_FURY         = 91155,    // Fureur prolongée: Fureur bicéphale lasts longer
    SPELL_OGRE_TALENT_HIT_ULTIMATE      = 91165,    // MOI TAPER FORT
    SPELL_OGRE_TALENT_CHATTER           = 91180,    // Bavardage: the body's melee hits taken give the head mana
    SPELL_OGRE_TALENT_FIXED_IDEAS       = 91215,    // Idées fixes: Idée fixe more often
    SPELL_OGRE_TALENT_BRAINSTORM        = 91220,    // Éclair de génie: Idée fixe casts are instant, then free
    SPELL_OGRE_TALENT_QUICK_THINKING    = 91230,    // Pensée rapide: shorter Fureur bicéphale cooldown
    SPELL_OGRE_TALENT_ONE_IDEA          = 91240,    // Deux cerveaux, une idée: Idée fixe and Réflexe together
    SPELL_OGRE_TALENT_MAGIC_ULTIMATE    = 91245,    // Tête pensante
    SPELL_OGRE_TALENT_REFLEX            = 91285,    // Réflexe d'ogre amélioré: Réflexe d'ogre more often
    SPELL_OGRE_TALENT_BACKLASH          = 91290,    // Riposte bicéphale: a crit after a Réflexe dodge
    SPELL_OGRE_TALENT_HEAVY_FALL        = 91295,    // Chute lourde: stronger Chute d'ogre impact
    SPELL_OGRE_TALENT_SHATTERING        = 91305,    // Atterrissage fracassant: the impact stuns
    SPELL_OGRE_TALENT_SURVIVAL          = 91310,    // Instinct de survie: Fureur bicéphale under 30% health
    SPELL_OGRE_TALENT_SPARE_HEAD        = 91315,    // Tête de rechange: a killing blow leaves 1 health
    SPELL_OGRE_TALENT_TANK_ULTIMATE     = 91316,    // Montagne
    // Spells of active talents (with a spell script of the module) and helper spells.
    SPELL_OGRE_GRIP                     = 91325,    // Poigne d'ogre
    SPELL_OGRE_LEAP                     = 91326,    // Bond d'ogre
    SPELL_OGRE_JUMP                     = 91327,    // Saut d'ogre
    SPELL_OGRE_MIGRAINE                 = 91328,    // Migraine's buff
    SPELL_OGRE_SHATTERING_LANDING       = 91329,    // Atterrissage fracassant's stun
};

// Spell roulette: who gets the spell rolled at a level up.
enum OgreHeadRole : uint8
{
    OGRE_ROLE_BODY  = 0,
    OGRE_ROLE_HEAD  = 1,
};

// Spell roulette: what kind of spell a candidate is. The body rolls melee and buffs, the head ranged
// (healing included) and buffs.
enum class OgreRollKind : uint8
{
    None,
    Melee,
    Ranged,
    Buff,
};

struct OgreRollCandidate
{
    uint32 Spell = 0;                   // first rank of the chain
    uint8 Level = 1;                    // level of the first rank
    uint8 Class = 0;                    // class whose trainers teach it
    OgreRollKind Kind = OgreRollKind::None;
};

// Spells rolled by one ogre (first rank -> owner) and the extra power types they unlocked.
struct OgreRolledSpells
{
    std::unordered_map<uint32, uint8> Owners;
    std::unordered_map<uint8, uint32> Levels;   // level -> rolled spell
    uint32 PowerMask = 0;                       // 1 << Powers
};

// Per ogre state of the head's casting, kept on the Player (CustomData).
struct OgreHeadState : public DataMap::Base
{
    uint32 PendingSpell = 0;            // free cast in progress (Fureur bicéphale)
    ObjectGuid PendingTarget;
    uint32 PendingTimer = 0;            // ms
    uint32 GlobalCooldown = 0;          // the head's own global cooldown while free, ms
    uint32 ImpactCooldown = 0;          // Chute d'ogre, ms
    uint32 Stance = 0;                  // current stance aura
    bool Free = false;                  // last free state told to the head's client
    bool PendingNoCost = false;         // the free cast in progress costs nothing (Éclair de génie)
    bool AutoFury = false;              // Fureur bicéphale given by Instinct de survie: not extended
    uint32 PendingImpactTimer = 0;      // Bond d'ogre: impact when it lands, ms...
    float PendingImpactRatio = 0.0f;    // ...at this power (0: 100%, 1: 300%)
    uint32 ForcedImpactTimer = 0;       // Saut d'ogre: the next landing hits at full power while running, ms
    ObjectGuid DoubleHitTarget;         // Coup double: last target hit by the head's spells...
    uint32 DoubleHitTimer = 0;          // ...for this long, ms
    uint32 SurvivalCooldown = 0;        // Instinct de survie, ms
    uint32 SpareHeadCooldown = 0;       // Tête de rechange, ms
    bool BacklashCrit = false;          // Riposte bicéphale: the body's next auto attack is a critical hit
};

// One ogre character and the two heads (accounts) sharing it.
struct OgreInfo
{
    ObjectGuid Guid;
    std::array<std::string, 2> Names;   // Names[0] is the character name given at creation
    std::array<uint32, 2> Accounts{};   // 0 = free head, waiting for a partner
};

class OgreMgr
{
public:
    static OgreMgr* instance();

    void LoadConfig();
    void LoadFromDB();

    [[nodiscard]] bool IsEnabled() const { return _enabled; }
    [[nodiscard]] uint8 GetRace() const { return _race; }
    [[nodiscard]] bool IsOgre(Player const* player) const;
    [[nodiscard]] bool IgnoresItemRestrictions() const { return _ignoreItemRestrictions; }

    // Character creation: "Name1Name2" (split at the second capital) sent by the patched client.
    bool HandleCreateRequest(WorldSession* session, std::string& name, uint8& playerClass, uint8& response);
    void OnCharacterCreated(Player* player);
    void OnCharacterDeleted(ObjectGuid guid);
    void OnSharedAccessLeft(ObjectGuid guid, uint32 accountId);

    // Shared control.
    [[nodiscard]] bool CanJoin(Player* player, WorldSession* session) const;
    void OnLoadFromDB(Player* player);
    void OnLogin(Player* player);
    // The Brute (the Ogre's class, a renamed Paladin carrier): its start, at the first login.
    void OnFirstLogin(Player* player);
    [[nodiscard]] bool IsClassTrainer(uint32 trainerId) const { return _classTrainers.contains(trainerId); }
    void OnHeadAttached(Player* player, WorldSession* session);
    void OnHeadDetached(Player* player, WorldSession* session);
    void OnHandover(Player* player, WorldSession* oldSession, WorldSession* newSession);
    // The head has its own action bars, saved per ogre and account; the body uses the character's bars.
    void SetHeadActionButton(Player* player, WorldSession* session, uint8 button, uint32 packedData) const;
    // The head's client casts through its own bar (AddOn client/addon/OgreHead): addon messages "OGRE\t..."
    // whispered to oneself. Returns false when `message` is not one of them.
    bool HandleHeadMessage(Player* player, WorldSession* session, std::string_view message);
    // Spells belong to one head: the head's spells (TwoHeadedOgre.Head.Spells, all ranks) are cast and listed
    // by the head's client only, every other spell by the body's client.
    [[nodiscard]] bool CanUseSpellFromSession(Player const* player, WorldSession const* session, uint32 spellId) const;
    void PrefixChat(Player* player, std::string& message) const;
    void OnUpdate(Player* player, uint32 diff) const;
    void UpdateStance(Player* player, bool headPresent, OgreHeadState* state) const;

    // Deux cerveaux.
    [[nodiscard]] bool IsHeadSpell(Player const* player, uint32 spellId) const;
    // Spell damage done by the ogre: the head's (Réflexe d'ogre, Coup double), the body's (Coup double).
    void OnSpellDamage(Unit* target, Unit* attacker, int32& damage, SpellInfo const* spellInfo) const;
    // Melee damage: done by the body (Coup double), taken by the body (Bavardage).
    void OnMeleeDamage(Unit* target, Unit* attacker, uint32& damage) const;
    // Any damage taken (Tête de rechange).
    void OnDamageTaken(Unit* victim, uint32& damage) const;
    // A harmful spell of the head went off: Idée fixe proc, Rage partagée.
    void OnHeadAttack(Player* player) const;
    // Réflexe d'ogre: the next melee hit taken from the front is dodged (Riposte bicéphale may follow).
    void OnMeleeRollAgainst(Unit const* attacker, Unit const* victim, int32& critChance, int32& dodgeChance) const;
    // Idée fixe and Réflexe d'ogre, one bringing the other with Deux cerveaux, une idée.
    void GiveFixedIdea(Player* player) const;
    void GiveReflex(Player* player) const;

    // Spell scripts of the Brute's active talents.
    void OnOgreLeap(Player* player, Unit* target) const;
    void OnOgreJump(Player* player) const;

    // Spell roulette.
    void LoadRollPool();
    void LoadRolledSpells(Player* player);
    void ForgetRolledSpells(ObjectGuid guid);
    void OnLevelChanged(Player* player, uint8 oldLevel);
    void CatchUpRolls(Player* player);
    [[nodiscard]] bool HasActivePowerType(Player const* player, uint8 power) const;
    void SendResources(Player* player, WorldSession* session) const;
    // Highest rank of `spellId`'s chain that `player` knows, 0 if none.
    [[nodiscard]] static uint32 GetKnownRank(Player const* player, uint32 spellId);
    // Chute d'ogre: no fall damage, an impact around the ogre when it lands from high enough.
    void OnFall(Player* player, float fallHeight, bool& fallDamage) const;
    // The impact of Chute d'ogre at a power from 0 (100%) to 1 (300%).
    void TriggerImpact(Player* player, float ratio) const;
    void ApplyScale(Player* player) const;

private:
    OgreMgr() = default;

    [[nodiscard]] std::string GetHeadName(ObjectGuid guid, uint32 accountId) const;
    [[nodiscard]] uint32 ResolveDisplayId(uint8 gender) const;
    void SendHeadBar(Player* player, WorldSession* session) const;
    void SendHeadMessage(Player* player, WorldSession* session, std::string_view text) const;
    [[nodiscard]] static WorldSession* GetHeadSession(Player const* player);
    // Owner of a rolled spell chain (OGRE_ROLE_*), -1 when the spell was not rolled.
    [[nodiscard]] int32 GetRolledOwner(Player const* player, uint32 spellId) const;
    void Roll(Player* player, uint8 level);
    void UpgradeRolledRanks(Player* player);
    // Extra power types (rage, energy) the ogre uses: every known spell costing them.
    void RefreshPowerMask(Player* player);
    void AddToBars(Player* player, uint8 owner, uint32 spellId);
    [[nodiscard]] std::array<uint32, 144> LoadHeadBar(Player* player, uint32 accountId) const;
    void SetHeadBarButton(Player* player, uint32 accountId, uint8 button, uint32 packedData) const;
    // Fureur bicéphale: the head casts on its own timeline, off the ogre's cast slot and global cooldown.
    // Éclair de génie: Idée fixe casts may be instant and free of cost.
    void StartFreeCast(Player* player, WorldSession* session, SpellInfo const* spellInfo, Unit* target,
        bool instant = false, bool noCost = false) const;
    void FinishFreeCast(Player* player, uint32 spellId, ObjectGuid targetGuid, bool noCost) const;
    void SaveOgre(OgreInfo const& ogre) const;

    bool _enabled{ true };
    bool _chatPrefix{ true };
    bool _ignoreItemRestrictions{ true };
    uint8 _race{ 9 };
    uint8 _carrierClass{ 2 };
    uint32 _raceAliasMask{ 0 };
    uint32 _skillClassMask{ 0 };
    uint32 _creatureEntry{ 5473 };
    uint32 _modelId{ 0 };
    uint32 _femaleModelId{ 0 };
    float _scale{ 1.0f };
    std::vector<uint32> _spells;
    std::vector<uint32> _headActionBar;
    std::vector<uint32> _headSpells;            // any rank of each head spell chain
    std::vector<uint32> _sharedSpells;          // cast by both heads (any rank)
    bool _rouletteEnabled{ true };
    float _procChance{ 5.0f };
    uint8 _rollInterval{ 2 };
    std::vector<OgreRollCandidate> _rollPool;
    std::unordered_set<uint32> _classTrainers;
    std::vector<uint32> _bruteSpells;
    uint32 _bruteOffHand{ 0 };

    mutable std::shared_mutex _rollLock;
    std::unordered_map<ObjectGuid, OgreRolledSpells> _rolled;

    mutable std::shared_mutex _lock;
    std::unordered_map<ObjectGuid, OgreInfo> _ogres;
    std::unordered_map<uint32, std::array<std::string, 2>> _pendingCreates; // account -> requested names
};

#define sOgreMgr OgreMgr::instance()

#endif // MOD_TWO_HEADED_OGRE_H
