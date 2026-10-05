-- mod-two-headed-ogre: Ogre race on the character creation screen.
-- An Ogre has two heads, played by two players: "Joueur 1" (the stock name box, also the character
-- name) and "Joueur 2" (the partner). The client refuses anything but letters in a name, so the server
-- receives both names glued, each with its capital ("GrokkMurg"), and links both accounts:
-- the partner creates an Ogre with the same two names on his own account to join it.
-- Ogres have no class: the class panel is hidden and the server always uses its carrier class.

OGRE_CLASS_INDEX = 2;           -- must match TwoHeadedOgre.CarrierClass (Paladin)
OGRE_LABEL_HEAD1 = "Joueur 1 (vous)";
OGRE_LABEL_HEAD2 = "Joueur 2 (partenaire)";
OGRE_ERROR_NAMES = "Un Ogre a deux tetes : saisissez le nom des deux joueurs.";
OGRE_ERROR_LETTERS = "Les noms des deux tetes ne peuvent contenir que des lettres (ni chiffres, ni espaces, ni ponctuation).";
OGRE_ERROR_SAME = "Les deux tetes doivent avoir des noms differents.";
OGRE_ERROR_ACCENT = "Le nom du Joueur 2 doit commencer par une lettre sans accent.";
-- ChrRaces.ClientFileString of the Ogre (Character\Ogre\... model, *_OGRE glue strings).
OGRE_FILE_STRING = "OGRE";
OGRE_ICON = "Interface\\Icons\\Achievement_Reputation_Ogre";
OGRE_BACKGROUND = "Orc";
RACE_ICONS_TEXTURE = "Interface\\Glues\\CharacterCreate\\UI-CharacterCreate-Races";
RACE_ICONS_ROUND_TEXTURE = "Interface\\Glues\\CharacterCreate\\UI-CharacterCreate-RacesRound";
OGRE_RACE_TEXT = "Les ogres a deux tetes ne savent jamais vraiment qui commande. Un seul corps, une seule "..
	"armure, un seul sac... et deux joueurs pour se les disputer.|n|n"..
	"Le premier joueur connecte devient le corps : il se deplace et combat. Le second devient la tete. "..
	"Pour lier l'Ogre, votre partenaire cree lui aussi un Ogre avec les deux memes noms sur son compte.";
OGRE_ABILITY_TEXT = "- Aucune classe a choisir.|n|n- Toutes les armes et toutes les armures.|n|n"..
	"- Equipement, sacs et experience partages par les deux tetes.";

MAX_RACES = 11;

-- The Ogre has its own icon file: the stock lookups only need full-texture coordinates.
RACE_ICON_TCOORDS[OGRE_FILE_STRING.."_MALE"] = {0, 1, 0, 1};
RACE_ICON_TCOORDS[OGRE_FILE_STRING.."_FEMALE"] = {0, 1, 0, 1};
_G["RACE_INFO_"..OGRE_FILE_STRING] = OGRE_RACE_TEXT;

-- No Ogre glue scenery: the selection/creation screens look up their music, fog and lights by race name
-- (CharacterSelect.currentModel = "Ogre"), so the Ogre borrows the Orc entries.
for _, raceTable in ipairs({ GlueAmbienceTracks, CharModelFogInfo, CharModelGlowInfo, RaceLights }) do
	raceTable[OGRE_FILE_STRING] = raceTable[strupper(OGRE_BACKGROUND)];
end
_G["ABILITY_INFO_"..OGRE_FILE_STRING.."1"] = OGRE_ABILITY_TEXT;

local ogreLabelHead1 = nil;
local ogreNameLabelText = nil;
local ogreUpdating = false;

local function Ogre_Trim(text)
	return (string.gsub(text or "", "^%s*(.-)%s*$", "%1"));
end

-- The stock "Name" label of the name box has no name: find it once.
local function Ogre_FindNameLabel()
	if ( ogreLabelHead1 ) then
		return ogreLabelHead1;
	end
	local regions = { CharacterCreateNameEdit:GetRegions() };
	for _, region in ipairs(regions) do
		if ( region:GetObjectType() == "FontString" and region:GetText() == NAME ) then
			ogreLabelHead1 = region;
			ogreNameLabelText = region:GetText();
			break;
		end
	end
	return ogreLabelHead1;
end

function Ogre_IsSelected()
	local _, fileString = GetNameForRace();
	return strupper(fileString or "") == OGRE_FILE_STRING;
end

local function Ogre_HasOnlyLetters(text)
	return not string.find(text, "[%d%p%s]");
end

-- "grokk" -> "Grokk": the server splits the glued names at the capitals (accented letters are left as typed).
local function Ogre_Capitalize(text)
	return strupper(string.sub(text, 1, 1))..strlower(string.sub(text, 2));
end

function Ogre_UpdateUI()
	if ( ogreUpdating ) then
		return;
	end
	ogreUpdating = true;

	local isOgre = Ogre_IsSelected();
	local label = Ogre_FindNameLabel();

	if ( isOgre ) then
		-- No class choice: always the carrier class.
		local _, _, classIndex = GetSelectedClass();
		if ( classIndex ~= OGRE_CLASS_INDEX and IsRaceClassValid(GetSelectedRace(), OGRE_CLASS_INDEX) ) then
			SetSelectedClass(OGRE_CLASS_INDEX);
			SetCharacterClass(OGRE_CLASS_INDEX);
		end
		for i = 1, MAX_CLASSES_PER_RACE do
			_G["CharacterCreateClassButton"..i]:Hide();
		end
		CharacterCreateCharacterClass:Hide();
		CharacterCreateClassName:Hide();

		CharacterCreateRaceIcon:SetTexture(OGRE_ICON);
		CharacterCreateRaceIcon:SetTexCoord(0, 1, 0, 1);
		CharacterCreateRaceText:SetText(OGRE_RACE_TEXT.."|n|n");
		CharacterCreateRaceAbilityText:SetText(OGRE_ABILITY_TEXT);

		OgreCreatePartnerEditLabel:SetText(OGRE_LABEL_HEAD2);
		OgreCreatePartnerEdit:Show();
		if ( label ) then
			label:SetText(OGRE_LABEL_HEAD1);
		end
	else
		for i = 1, CharacterCreate.numClasses do
			_G["CharacterCreateClassButton"..i]:Show();
		end
		CharacterCreateCharacterClass:Show();
		CharacterCreateClassName:Show();
		CharacterCreateRaceIcon:SetTexture(RACE_ICONS_ROUND_TEXTURE);

		OgreCreatePartnerEdit:Hide();
		if ( label ) then
			label:SetText(ogreNameLabelText);
		end
	end

	ogreUpdating = false;
end

-- The Horde column holds six races now: tighten it so the last button stays above the gender buttons.
for i = 7, MAX_RACES do
	local button = _G["CharacterCreateRaceButton"..i];
	button:ClearAllPoints();
	button:SetPoint("TOPLEFT", _G["CharacterCreateRaceButton"..(i - 1)], "BOTTOMLEFT", 0, -12);
end

-- Race buttons: the Ogre button shows its own icon, the others keep the stock atlas.
local Ogre_Stock_CharacterCreateEnumerateRaces = CharacterCreateEnumerateRaces;
function CharacterCreateEnumerateRaces(...)
	Ogre_Stock_CharacterCreateEnumerateRaces(...);
	for i = 1, select("#", ...) / 3 do
		local isOgre = strupper(select(i * 3 - 1, ...)) == OGRE_FILE_STRING;
		for _, part in ipairs({ "NormalTexture", "PushedTexture" }) do
			local texture = _G["CharacterCreateRaceButton"..i..part];
			texture:SetTexture(isOgre and OGRE_ICON or RACE_ICONS_TEXTURE);
			if ( isOgre ) then
				texture:SetTexCoord(0, 1, 0, 1);
			end
		end
	end
end

-- There is no Ogre glue scenery: creation and selection screens use the Orc one.
local Ogre_Stock_SetBackgroundModel = SetBackgroundModel;
function SetBackgroundModel(model, name)
	if ( name and strupper(name) == OGRE_FILE_STRING ) then
		name = OGRE_BACKGROUND;
	end
	Ogre_Stock_SetBackgroundModel(model, name);
end

local Ogre_Stock_SetCharacterRace = SetCharacterRace;
function SetCharacterRace(id)
	Ogre_Stock_SetCharacterRace(id);
	Ogre_UpdateUI();
end

local Ogre_Stock_SetCharacterClass = SetCharacterClass;
function SetCharacterClass(id)
	Ogre_Stock_SetCharacterClass(id);
	Ogre_UpdateUI();
end

local Ogre_Stock_CharacterCreate_OnShow = CharacterCreate_OnShow;
function CharacterCreate_OnShow()
	OgreCreatePartnerEdit:SetText("");
	Ogre_Stock_CharacterCreate_OnShow();
	Ogre_UpdateUI();
end

local Ogre_Stock_CharacterCreate_Okay = CharacterCreate_Okay;
function CharacterCreate_Okay()
	if ( PAID_SERVICE_TYPE or not Ogre_IsSelected() ) then
		Ogre_Stock_CharacterCreate_Okay();
		return;
	end

	local head1 = Ogre_Trim(CharacterCreateNameEdit:GetText());
	local head2 = Ogre_Trim(OgreCreatePartnerEdit:GetText());
	if ( head1 == "" or head2 == "" ) then
		message(OGRE_ERROR_NAMES);
		return;
	end
	if ( not Ogre_HasOnlyLetters(head1) or not Ogre_HasOnlyLetters(head2) ) then
		message(OGRE_ERROR_LETTERS);
		return;
	end
	if ( strlower(head1) == strlower(head2) ) then
		message(OGRE_ERROR_SAME);
		return;
	end

	if ( string.byte(head2, 1) >= 128 ) then
		message(OGRE_ERROR_ACCENT);
		return;
	end

	CreateCharacter(Ogre_Capitalize(head1)..Ogre_Capitalize(head2));
	PlaySound("gsCharacterCreationCreateChar");
end

CharacterCreateNameEdit:SetScript("OnTabPressed", function()
	if ( OgreCreatePartnerEdit:IsShown() ) then
		OgreCreatePartnerEdit:SetFocus();
	end
end);
