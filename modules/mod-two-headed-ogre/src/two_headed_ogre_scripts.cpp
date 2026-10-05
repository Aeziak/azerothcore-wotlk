/*
 * mod-two-headed-ogre : script hooks and module loader. No GM command is needed: the patched
 * character creation screen links the two players.
 */

#include "two_headed_ogre.h"
#include "Creature.h"
#include "GlobalScript.h"
#include "NPCPackets.h"
#include "Player.h"
#include "PlayerScript.h"
#include "ScriptMgr.h"
#include "SharedDefines.h"
#include "SpellAuraEffects.h"
#include "SpellInfo.h"
#include "SpellScript.h"
#include "SpellScriptLoader.h"
#include "Trainer.h"
#include "UnitDefines.h"
#include "UnitScript.h"
#include "WorldScript.h"
#include <algorithm>

class two_headed_ogre_world : public WorldScript
{
public:
    two_headed_ogre_world() : WorldScript("two_headed_ogre_world", { WORLDHOOK_ON_AFTER_CONFIG_LOAD, WORLDHOOK_ON_STARTUP }) { }

    void OnAfterConfigLoad(bool /*reload*/) override
    {
        sOgreMgr->LoadConfig();
    }

    void OnStartup() override
    {
        sOgreMgr->LoadFromDB();
        sOgreMgr->LoadRollPool();
    }
};

class two_headed_ogre_player : public PlayerScript
{
public:
    two_headed_ogre_player() : PlayerScript("two_headed_ogre_player",
        {
            PLAYERHOOK_ON_CHARACTER_CREATE_REQUEST, PLAYERHOOK_ON_CREATE, PLAYERHOOK_ON_DELETE, PLAYERHOOK_ON_SHARED_ACCESS_LEFT,
            PLAYERHOOK_CAN_JOIN_AS_COPILOT, PLAYERHOOK_ON_COPILOT_ATTACHED, PLAYERHOOK_ON_COPILOT_DETACHED,
            PLAYERHOOK_ON_COPILOT_SET_ACTION_BUTTON, PLAYERHOOK_CAN_USE_SPELL_FROM_SESSION,
            PLAYERHOOK_CAN_PLAYER_USE_PRIVATE_CHAT, PLAYERHOOK_ON_UPDATE, PLAYERHOOK_ON_FALL,
            PLAYERHOOK_ON_LEVEL_CHANGED, PLAYERHOOK_ON_PLAYER_HAS_ACTIVE_POWER_TYPE, PLAYERHOOK_ON_LOGOUT,
            PLAYERHOOK_ON_FIRST_LOGIN, PLAYERHOOK_ON_GET_TRAINER_SPELL_STATE,
            PLAYERHOOK_ON_BEFORE_RECEIVE_SPELL_LIST_FROM_TRAINER,
            PLAYERHOOK_ON_SESSION_HANDOVER, PLAYERHOOK_ON_LOAD_FROM_DB, PLAYERHOOK_ON_LOGIN, PLAYERHOOK_ON_BEFORE_SEND_CHAT_MESSAGE,
            PLAYERHOOK_ON_PLAYER_IS_CLASS, PLAYERHOOK_CAN_IGNORE_ITEM_RESTRICTIONS
        }) { }

    bool OnPlayerCharacterCreateRequest(WorldSession* session, std::string& name, uint8 race, uint8& playerClass,
        uint8& response) override
    {
        if (race != sOgreMgr->GetRace())
            return true;

        return sOgreMgr->HandleCreateRequest(session, name, playerClass, response);
    }

    void OnPlayerCreate(Player* player) override
    {
        sOgreMgr->OnCharacterCreated(player);
    }

    void OnPlayerDelete(ObjectGuid guid, uint32 /*accountId*/) override
    {
        sOgreMgr->OnCharacterDeleted(guid);
    }

    void OnPlayerSharedAccessLeft(ObjectGuid guid, uint32 accountId, uint32 /*newOwnerAccountId*/) override
    {
        sOgreMgr->OnSharedAccessLeft(guid, accountId);
    }

    bool OnPlayerCanJoinAsCopilot(Player* player, WorldSession* session) override
    {
        return sOgreMgr->CanJoin(player, session);
    }

    void OnPlayerCopilotAttached(Player* player, WorldSession* session) override
    {
        sOgreMgr->OnHeadAttached(player, session);
    }

    void OnPlayerCopilotDetached(Player* player, WorldSession* session) override
    {
        sOgreMgr->OnHeadDetached(player, session);
    }

    void OnPlayerCopilotSetActionButton(Player* player, WorldSession* session, uint8 button, uint32 packedData) override
    {
        sOgreMgr->SetHeadActionButton(player, session, button, packedData);
    }

    bool OnPlayerCanUseChat(Player* player, uint32 type, uint32 language, std::string& msg, Player* receiver) override
    {
        // The head's bar whispers its commands to the ogre itself.
        if (language == LANG_ADDON && type == CHAT_MSG_WHISPER && receiver == player)
            return !sOgreMgr->HandleHeadMessage(player, player->GetActingSession(), msg);

        return true;
    }

    void OnPlayerFirstLogin(Player* player) override
    {
        sOgreMgr->OnFirstLogin(player);
    }

    void OnPlayerGetTrainerSpellState(Player const* player, uint32 trainerId, uint32 /*spellId*/,
        Trainer::SpellState& state) override
    {
        if (sOgreMgr->IsOgre(player) && sOgreMgr->IsClassTrainer(trainerId))
            state = Trainer::SpellState::Unavailable;
    }

    void OnPlayerBeforeReceiveSpellListFromTrainer(Player* player, Creature* /*trainer*/,
        WorldPackets::NPC::TrainerList& trainerList) override
    {
        // The Brute learns its class spells from the roulette only.
        if (sOgreMgr->IsOgre(player) && trainerList.TrainerType == int32(Trainer::Type::Class))
            trainerList.Spells.clear();
    }

    void OnPlayerLevelChanged(Player* player, uint8 oldLevel) override
    {
        sOgreMgr->OnLevelChanged(player, oldLevel);
    }

    bool OnPlayerHasActivePowerType(Player const* player, Powers power) override
    {
        return sOgreMgr->HasActivePowerType(player, power);
    }

    void OnPlayerLogout(Player* player) override
    {
        sOgreMgr->ForgetRolledSpells(player->GetGUID());
    }

    void OnPlayerUpdate(Player* player, uint32 diff) override
    {
        sOgreMgr->OnUpdate(player, diff);
    }

    void OnPlayerFall(Player* player, float fallHeight, bool& fallDamage) override
    {
        sOgreMgr->OnFall(player, fallHeight, fallDamage);
    }

    bool OnPlayerCanUseSpellFromSession(Player const* player, WorldSession const* session, uint32 spellId) override
    {
        return sOgreMgr->CanUseSpellFromSession(player, session, spellId);
    }

    void OnPlayerSessionHandover(Player* player, WorldSession* oldSession, WorldSession* newSession) override
    {
        sOgreMgr->OnHandover(player, oldSession, newSession);
    }

    void OnPlayerLoadFromDB(Player* player) override
    {
        sOgreMgr->OnLoadFromDB(player);
    }

    void OnPlayerLogin(Player* player) override
    {
        sOgreMgr->OnLogin(player);
    }

    void OnPlayerBeforeSendChatMessage(Player* player, uint32& type, uint32& lang, std::string& msg) override
    {
        if (lang == LANG_ADDON)
            return;

        switch (type)
        {
            case CHAT_MSG_SAY:
            case CHAT_MSG_YELL:
            case CHAT_MSG_PARTY:
            case CHAT_MSG_PARTY_LEADER:
            case CHAT_MSG_RAID:
            case CHAT_MSG_RAID_LEADER:
            case CHAT_MSG_RAID_WARNING:
            case CHAT_MSG_GUILD:
            case CHAT_MSG_OFFICER:
            case CHAT_MSG_WHISPER:
            case CHAT_MSG_CHANNEL:
            case CHAT_MSG_BATTLEGROUND:
            case CHAT_MSG_BATTLEGROUND_LEADER:
                sOgreMgr->PrefixChat(player, msg);
                break;
            default:
                break;
        }
    }

    // No class: the ogre can wear every armor type, shields and relics, and swap any weapon.
    Optional<bool> OnPlayerIsClass(Player const* player, Classes /*playerClass*/, ClassContext context) override
    {
        if (!sOgreMgr->IsOgre(player))
            return std::nullopt;

        switch (context)
        {
            case CLASS_CONTEXT_EQUIP_RELIC:
            case CLASS_CONTEXT_EQUIP_SHIELDS:
            case CLASS_CONTEXT_EQUIP_ARMOR_CLASS:
            case CLASS_CONTEXT_WEAPON_SWAP:
                return true;
            default:
                return std::nullopt;
        }
    }

    bool OnPlayerCanIgnoreItemRestrictions(Player const* player, ItemTemplate const* /*proto*/) override
    {
        return sOgreMgr->IgnoresItemRestrictions() && sOgreMgr->IsOgre(player);
    }
};

// Transforms ending restore the native display at scale 1: keep the configured ogre size.
class two_headed_ogre_unit : public UnitScript
{
public:
    two_headed_ogre_unit() : UnitScript("two_headed_ogre_unit", true, { UNITHOOK_ON_DISPLAYID_CHANGE,
        UNITHOOK_MODIFY_SPELL_DAMAGE_TAKEN, UNITHOOK_MODIFY_PERIODIC_DAMAGE_AURAS_TICK,
        UNITHOOK_ON_BEFORE_ROLL_MELEE_OUTCOME_AGAINST, UNITHOOK_MODIFY_MELEE_DAMAGE, UNITHOOK_ON_DAMAGE }) { }

    // Deux cerveaux: the head's direct and periodic damage, and the body's dodge.
    void ModifySpellDamageTaken(Unit* target, Unit* attacker, int32& damage, SpellInfo const* spellInfo) override
    {
        sOgreMgr->OnSpellDamage(target, attacker, damage, spellInfo);
    }

    void ModifyPeriodicDamageAurasTick(Unit* target, Unit* attacker, uint32& damage,
        SpellInfo const* spellInfo) override
    {
        int32 amount = int32(damage);
        sOgreMgr->OnSpellDamage(target, attacker, amount, spellInfo);
        damage = uint32(std::max(amount, 0));
    }

    // Brute talents: Coup double, Bavardage, Tête de rechange.
    void ModifyMeleeDamage(Unit* target, Unit* attacker, uint32& damage) override
    {
        sOgreMgr->OnMeleeDamage(target, attacker, damage);
    }

    void OnDamage(Unit* /*attacker*/, Unit* victim, uint32& damage) override
    {
        sOgreMgr->OnDamageTaken(victim, damage);
    }

    void OnBeforeRollMeleeOutcomeAgainst(Unit const* attacker, Unit const* victim, WeaponAttackType /*attType*/,
        int32& /*attackerMaxSkillValueForLevel*/, int32& /*victimMaxSkillValueForLevel*/,
        int32& /*attackerWeaponSkill*/, int32& /*victimDefenseSkill*/, int32& critChance, int32& /*missChance*/,
        int32& dodgeChance,
        int32& /*parryChance*/, int32& /*blockChance*/) override
    {
        sOgreMgr->OnMeleeRollAgainst(attacker, victim, critChance, dodgeChance);
    }

    void OnDisplayIdChange(Unit* unit, uint32 /*displayId*/) override
    {
        if (Player* player = unit->ToPlayer())
            sOgreMgr->ApplyScale(player);
    }
};

// 91325 - Poigne d'ogre: the target jumps to the ogre (the Death Knight's grip jump), its cast interrupted.
class spell_ogre_grip : public SpellScript
{
    PrepareSpellScript(spell_ogre_grip);

    void HandleDummy(SpellEffIndex /*effIndex*/)
    {
        Unit* caster = GetCaster();
        Unit* target = GetHitUnit();
        if (!target || target == caster)
            return;

        Creature* creature = target->ToCreature();
        if (creature && (creature->isWorldBoss() || creature->IsDungeonBoss()))
            return;

        target->InterruptNonMeleeSpells(false);
        target->CastSpell(caster->GetPositionX(), caster->GetPositionY(), caster->GetPositionZ(), SpellDeathGripJump,
            true);
    }

    void Register() override
    {
        OnEffectHitTarget += SpellEffectFn(spell_ogre_grip::HandleDummy, EFFECT_0, SPELL_EFFECT_DUMMY);
    }

    static constexpr uint32 SpellDeathGripJump = 57604;
};

// 91326 - Bond d'ogre: the jump itself is the spell's, the module strikes when it lands.
class spell_ogre_leap : public SpellScript
{
    PrepareSpellScript(spell_ogre_leap);

    void HandleJump(SpellEffIndex /*effIndex*/)
    {
        if (Player* player = GetCaster()->ToPlayer(); player && GetHitUnit())
            sOgreMgr->OnOgreLeap(player, GetHitUnit());
    }

    void Register() override
    {
        OnEffectLaunchTarget += SpellEffectFn(spell_ogre_leap::HandleJump, EFFECT_0, SPELL_EFFECT_JUMP);
    }
};

// 91327 - Saut d'ogre: straight up, Chute d'ogre at full power on landing.
class spell_ogre_jump : public SpellScript
{
    PrepareSpellScript(spell_ogre_jump);

    void HandleDummy(SpellEffIndex /*effIndex*/)
    {
        if (Player* player = GetCaster()->ToPlayer())
            sOgreMgr->OnOgreJump(player);
    }

    void Register() override
    {
        OnEffectHitTarget += SpellEffectFn(spell_ogre_jump::HandleDummy, EFFECT_0, SPELL_EFFECT_DUMMY);
    }
};

// Ivresse du combat (all ranks): the body's melee critical hits shorten Fureur bicéphale's cooldown.
class spell_ogre_battle_trance : public AuraScript
{
    PrepareAuraScript(spell_ogre_battle_trance);

    bool CheckProc(ProcEventInfo& eventInfo)
    {
        Player* player = GetTarget()->ToPlayer();
        SpellInfo const* spellInfo = eventInfo.GetSpellInfo();
        return player && (!spellInfo || !sOgreMgr->IsHeadSpell(player, spellInfo->Id));
    }

    void HandleProc(AuraEffect const* aurEff, ProcEventInfo& /*eventInfo*/)
    {
        if (Player* player = GetTarget()->ToPlayer())
            player->ModifySpellCooldown(SPELL_OGRE_TWO_MINDS, -aurEff->GetAmount() * IN_MILLISECONDS);
    }

    void Register() override
    {
        DoCheckProc += AuraCheckProcFn(spell_ogre_battle_trance::CheckProc);
        OnEffectProc += AuraEffectProcFn(spell_ogre_battle_trance::HandleProc, EFFECT_0, SPELL_AURA_DUMMY);
    }
};

// Migraine (all ranks): the head's critical spells raise the body's melee critical chance for 6 s.
class spell_ogre_migraine : public AuraScript
{
    PrepareAuraScript(spell_ogre_migraine);

    bool CheckProc(ProcEventInfo& eventInfo)
    {
        Player* player = GetTarget()->ToPlayer();
        SpellInfo const* spellInfo = eventInfo.GetSpellInfo();
        return player && spellInfo && sOgreMgr->IsHeadSpell(player, spellInfo->Id);
    }

    void HandleProc(AuraEffect const* aurEff, ProcEventInfo& /*eventInfo*/)
    {
        Unit* target = GetTarget();
        target->CastCustomSpell(SPELL_OGRE_MIGRAINE, SPELLVALUE_BASE_POINT0, aurEff->GetAmount(), target, true);
    }

    void Register() override
    {
        DoCheckProc += AuraCheckProcFn(spell_ogre_migraine::CheckProc);
        OnEffectProc += AuraEffectProcFn(spell_ogre_migraine::HandleProc, EFFECT_0, SPELL_AURA_DUMMY);
    }
};

// Loader: the CMake module system calls Add<dir-with-underscores>Scripts().
class two_headed_ogre_global : public GlobalScript
{
public:
    two_headed_ogre_global() : GlobalScript("two_headed_ogre_global", { GLOBALHOOK_ON_LOAD_SPELL_CUSTOM_ATTR }) { }

    // Spell changes for the roulette, the same in the client patch (client/tools/ogre_spells.py) or the client
    // greys these spells out. Warrior abilities that only ask for a warrior stance work without stance: the Ogre
    // has none and may roll any of them (a warrior is always in a stance anyway).
    void OnLoadSpellCustomAttr(SpellInfo* spellInfo) override
    {
        constexpr uint32 warriorStances = (1 << (FORM_BATTLESTANCE - 1)) | (1 << (FORM_DEFENSIVESTANCE - 1))
            | (1 << (FORM_BERSERKERSTANCE - 1));
        if (spellInfo->SpellFamilyName == SPELLFAMILY_WARRIOR && spellInfo->Stances
            && !(spellInfo->Stances & ~warriorStances))
            spellInfo->Stances = 0;

        // Warlock demons need no soul shard: the roulette gives the summons without Drain Soul.
        if (spellInfo->SpellFamilyName == SPELLFAMILY_WARLOCK && spellInfo->HasEffect(SPELL_EFFECT_SUMMON_PET))
        {
            spellInfo->Reagent.fill(0);
            spellInfo->ReagentCount.fill(0);
        }
    }
};

void Addmod_two_headed_ogreScripts()
{
    new two_headed_ogre_global();
    new two_headed_ogre_world();
    new two_headed_ogre_player();
    new two_headed_ogre_unit();
    RegisterSpellScript(spell_ogre_grip);
    RegisterSpellScript(spell_ogre_leap);
    RegisterSpellScript(spell_ogre_jump);
    RegisterSpellScript(spell_ogre_battle_trance);
    RegisterSpellScript(spell_ogre_migraine);
}
