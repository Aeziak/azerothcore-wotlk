-- mod-two-headed-ogre: the head's action bar (AddOn OgreHead, installed by client/tools/build_client_patch.py).
-- The head's client never steers the ogre, so the game greys its own action bars. This bar is laid over
-- the main action bar of the head's client only: its buttons send the head's spells to the server as
-- addon messages (prefix "OGRE", whispered to oneself) and the server casts them for the ogre on the
-- head's target. The server also keeps the bar's content (one bar per ogre and per head).
--
-- Server -> client: "ROLE HEAD" | "ROLE BODY" | "BAR 1:116 2:133 ..." (slot:spell) | "FREE 0|1"
--                   "CASTBAR <spell> <ms>" | "CASTSTOP" | "GCD <ms>" (Fureur bicéphale: the head casts on its
--                   own timeline and global cooldown, the server tells this bar about them)
-- Client -> server: "HELLO" | "CAST <spell> <target guid or 0>" | "SET <slot> <spell>" | "CLR <slot>"

OGRE_HEAD_PREFIX = "OGRE";

-- The Ogre's class, the Paladin carrier renamed "Brute" by the client patch, takes the warrior colour.
if ( RAID_CLASS_COLORS and RAID_CLASS_COLORS.WARRIOR ) then
	local warrior = RAID_CLASS_COLORS.WARRIOR;
	RAID_CLASS_COLORS.PALADIN = { r = warrior.r, g = warrior.g, b = warrior.b };
end
OGRE_HEAD_TITLE = "Tête de l'ogre";
OGRE_HEAD_TITLE_FREE = "Tête de l'ogre - Fureur bicéphale !";
OGRE_HEAD_BUTTONS = 12;

local spells = { };         -- slot -> spell id
local isHead = false;
local bindingsPending = false;
local refreshTimer = 0;
local isFree = false;
local gcdStart, gcdDuration = 0, 0;     -- the head's own global cooldown while free

local function Ogre_Send(message)
	SendAddonMessage(OGRE_HEAD_PREFIX, message, "WHISPER", UnitName("player"));
end

local function Ogre_SpellFromCursor()
	local cursorType, slot, bookType = GetCursorInfo();
	if ( cursorType ~= "spell" ) then
		return nil;
	end
	local link = GetSpellLink(slot, bookType);
	return link and tonumber(string.match(link, "spell:(%d+)"));
end

local function OgreHeadButton_Update(button)
	local spell = spells[button:GetID()];
	local icon = _G[button:GetName().."Icon"];
	local cooldown = _G[button:GetName().."Cooldown"];
	if ( not spell ) then
		icon:Hide();
		cooldown:Hide();
		return;
	end

	local _, _, texture, cost, _, powerType = GetSpellInfo(spell);
	icon:SetTexture(texture);
	icon:Show();
	if ( cost and cost > 0 and UnitPower("player", powerType) < cost ) then
		icon:SetVertexColor(0.5, 0.5, 1.0);
	else
		icon:SetVertexColor(1.0, 1.0, 1.0);
	end

	local start, duration, enable = GetSpellCooldown(spell);
	if ( isFree ) then
		-- The ogre's global cooldown is the body's now: only real cooldowns and the head's own one count.
		if ( duration and duration <= 1.5 ) then
			start, duration = 0, 0;
		end
		if ( gcdStart + gcdDuration > GetTime() and (not start or start + duration < gcdStart + gcdDuration) ) then
			start, duration, enable = gcdStart, gcdDuration, 1;
		end
	end
	if ( start ) then
		CooldownFrame_SetTimer(cooldown, start, duration, enable or 1);
	end

	-- No range colouring: this client does not steer the ogre, its own range checks are unreliable.
	-- The server checks range from the ogre's real position (the body's).
end

local function OgreHead_UpdateAll()
	for i = 1, OGRE_HEAD_BUTTONS do
		OgreHeadButton_Update(_G["OgreHeadButton"..i]);
	end
end

-- The head's keys (bound to the main action bar) press the head's buttons instead.
local function OgreHead_UpdateBindings()
	if ( InCombatLockdown() ) then
		bindingsPending = true;
		return;
	end
	bindingsPending = false;

	ClearOverrideBindings(OgreHeadBar);
	for i = 1, OGRE_HEAD_BUTTONS do
		local hotkey = _G["OgreHeadButton"..i.."HotKey"];
		local key = GetBindingKey("ACTIONBUTTON"..i);
		hotkey:SetText(key and GetBindingText(key, "KEY_", 1) or "");
		if ( isHead and key ) then
			SetOverrideBindingClick(OgreHeadBar, true, key, "OgreHeadButton"..i);
		end
	end
end

local function OgreHead_SetRole(head)
	isHead = head;
	if ( head ) then
		OgreHeadBar:Show();
	else
		OgreHeadBar:Hide();
	end
	OgreHead_UpdateBindings();
end

local function OgreHead_SetFree(free)
	isFree = free;
	OgreHeadBarTitle:SetText(free and OGRE_HEAD_TITLE_FREE or OGRE_HEAD_TITLE);
	if ( free ) then
		OgreHeadBarTitle:SetTextColor(1.0, 0.3, 0.1);
	else
		OgreHeadBarTitle:SetTextColor(1.0, 0.82, 0.0);
	end
	OgreHead_UpdateAll();
end

-- The head's own cast bar, for casts on its own timeline (the ogre's cast bar belongs to the body then).
local castBar = CreateFrame("StatusBar", "OgreHeadCastBar", OgreHeadBar);
castBar:SetWidth(240);
castBar:SetHeight(14);
castBar:SetPoint("BOTTOMLEFT", OgreHeadBar, "TOPLEFT", 0, 22);
castBar:SetStatusBarTexture("Interface\\TargetingFrame\\UI-StatusBar");
castBar:SetStatusBarColor(1.0, 0.5, 0.1);
castBar:Hide();
local castBarBackground = castBar:CreateTexture(nil, "BACKGROUND");
castBarBackground:SetTexture(0, 0, 0, 0.6);
castBarBackground:SetAllPoints(castBar);
local castBarText = castBar:CreateFontString(nil, "OVERLAY", "GameFontHighlightSmall");
castBarText:SetPoint("CENTER", castBar, "CENTER");
castBar:SetScript("OnUpdate", function(self)
	local now = GetTime();
	if ( now >= self.endTime ) then
		self:Hide();
		return;
	end
	self:SetValue(now - self.startTime);
end);

local function OgreHead_StartCastBar(spell, milliseconds)
	local duration = milliseconds / 1000;
	castBar.startTime = GetTime();
	castBar.endTime = castBar.startTime + duration;
	castBar:SetMinMaxValues(0, duration);
	castBar:SetValue(0);
	castBarText:SetText(GetSpellInfo(spell) or "");
	castBar:Show();
end

local function OgreHead_SetBar(content)
	spells = { };
	for slot, spell in string.gmatch(content or "", "(%d+):(%d+)") do
		spells[tonumber(slot)] = tonumber(spell);
	end
	OgreHead_UpdateAll();
end

local function OgreHeadButton_Place(button, spell)
	spells[button:GetID()] = spell;
	Ogre_Send("SET "..button:GetID().." "..spell);
	ClearCursor();
	OgreHeadButton_Update(button);
end

local function OgreHeadButton_OnClick(self)
	self:SetChecked(false);
	local cursorSpell = Ogre_SpellFromCursor();
	if ( cursorSpell ) then
		OgreHeadButton_Place(self, cursorSpell);
		return;
	end

	local spell = spells[self:GetID()];
	if ( spell ) then
		Ogre_Send("CAST "..spell.." "..(UnitGUID("target") or "0"));
	end
end

local function OgreHeadButton_OnReceiveDrag(self)
	local cursorSpell = Ogre_SpellFromCursor();
	if ( cursorSpell ) then
		OgreHeadButton_Place(self, cursorSpell);
	end
end

local function OgreHeadButton_OnDragStart(self)
	if ( spells[self:GetID()] ) then
		spells[self:GetID()] = nil;
		Ogre_Send("CLR "..self:GetID());
		OgreHeadButton_Update(self);
	end
end

local function OgreHeadButton_OnEnter(self)
	local spell = spells[self:GetID()];
	if ( spell ) then
		GameTooltip:SetOwner(self, "ANCHOR_RIGHT");
		GameTooltip:SetHyperlink("spell:"..spell);
		GameTooltip:Show();
	end
end

OgreHeadBarTitle:SetText(OGRE_HEAD_TITLE);
for i = 1, OGRE_HEAD_BUTTONS do
	local button = CreateFrame("CheckButton", "OgreHeadButton"..i, OgreHeadBar, "ActionButtonTemplate");
	button:SetID(i);
	if ( i == 1 ) then
		button:SetPoint("TOPLEFT", OgreHeadBar, "TOPLEFT", 0, 0);
	else
		button:SetPoint("LEFT", _G["OgreHeadButton"..(i - 1)], "RIGHT", 6, 0);
	end

	-- Hides the greyed main action button underneath (on the bar, below the button's own icon).
	local background = OgreHeadBar:CreateTexture(nil, "BACKGROUND");
	background:SetTexture(0, 0, 0, 0.85);
	background:SetAllPoints(button);

	button:RegisterForClicks("AnyUp");
	button:RegisterForDrag("LeftButton");
	button:SetScript("OnClick", OgreHeadButton_OnClick);
	button:SetScript("OnReceiveDrag", OgreHeadButton_OnReceiveDrag);
	button:SetScript("OnDragStart", OgreHeadButton_OnDragStart);
	button:SetScript("OnEnter", OgreHeadButton_OnEnter);
	button:SetScript("OnLeave", function() GameTooltip:Hide(); end);
end

OgreHeadBar:SetScript("OnUpdate", function(self, elapsed)
	refreshTimer = refreshTimer - elapsed;
	if ( refreshTimer <= 0 ) then
		refreshTimer = 0.2;
		OgreHead_UpdateAll();
	end
end);

local events = CreateFrame("Frame");
events:RegisterEvent("PLAYER_ENTERING_WORLD");
events:RegisterEvent("CHAT_MSG_ADDON");
events:RegisterEvent("PLAYER_REGEN_ENABLED");
events:RegisterEvent("SPELL_UPDATE_COOLDOWN");
events:SetScript("OnEvent", function(self, event, prefix, message, channel, sender)
	if ( event == "PLAYER_ENTERING_WORLD" ) then
		-- The server only answers the head's client.
		Ogre_Send("HELLO");
	elseif ( event == "CHAT_MSG_ADDON" ) then
		if ( prefix ~= OGRE_HEAD_PREFIX or sender ~= UnitName("player") ) then
			return;
		end
		local command, argument = string.match(message, "^(%S+)%s*(.*)$");
		if ( command == "ROLE" ) then
			OgreHead_SetRole(argument == "HEAD");
		elseif ( command == "BAR" ) then
			OgreHead_SetBar(argument);
		elseif ( command == "FREE" ) then
			OgreHead_SetFree(argument == "1");
		elseif ( command == "CASTBAR" ) then
			local spell, milliseconds = string.match(argument, "^(%d+)%s+(%d+)$");
			if ( spell ) then
				OgreHead_StartCastBar(tonumber(spell), tonumber(milliseconds));
			end
		elseif ( command == "CASTSTOP" ) then
			castBar:Hide();
		elseif ( command == "GCD" ) then
			gcdStart, gcdDuration = GetTime(), (tonumber(argument) or 0) / 1000;
			OgreHead_UpdateAll();
		end
	elseif ( event == "PLAYER_REGEN_ENABLED" ) then
		if ( bindingsPending ) then
			OgreHead_UpdateBindings();
		end
	elseif ( event == "SPELL_UPDATE_COOLDOWN" and isHead ) then
		OgreHead_UpdateAll();
	end
end);
