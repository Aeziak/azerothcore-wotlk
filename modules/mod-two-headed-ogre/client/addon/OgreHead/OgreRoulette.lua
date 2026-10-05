-- mod-two-headed-ogre: spell roulette animation and the ogre's extra resources (both heads' clients).
--
-- Server -> client (addon messages, prefix "OGRE"):
--   "ROLL <B|H> <spell> <decoy spells...>"  a level up gave <spell> to the body (B) or the head (H)
--   "RES <mask>"                            extra power types the ogre uses (1 << power: 2 rage, 8 energy)

local ROULETTE_TITLE = { B = "Roulette de l'ogre : le corps", H = "Roulette de l'ogre : la tête" };
local ROULETTE_WON = { B = "Le corps obtient", H = "La tête obtient" };
local ICON_SIZE = 44;
local ICON_STEP = 52;
local VISIBLE = 3;                  -- icons shown on each side of the centre
local SPIN_TIME = 4.0;
local HOLD_TIME = 3.5;
local FADE_TIME = 0.6;

local queue = { };
local current = nil;

------------------------------------------------------------------------------------------------------------
-- Roulette frame
------------------------------------------------------------------------------------------------------------
local frame = CreateFrame("Frame", "OgreRouletteFrame", UIParent);
frame:SetWidth(ICON_STEP * (VISIBLE * 2 + 1) + 40);
frame:SetHeight(130);
frame:SetPoint("TOP", UIParent, "TOP", 0, -120);
frame:SetFrameStrata("DIALOG");
frame:SetBackdrop({
	bgFile = "Interface\\Tooltips\\UI-Tooltip-Background",
	edgeFile = "Interface\\Tooltips\\UI-Tooltip-Border",
	tile = true, tileSize = 16, edgeSize = 16,
	insets = { left = 4, right = 4, top = 4, bottom = 4 },
});
frame:SetBackdropColor(0, 0, 0, 0.85);
frame:SetBackdropBorderColor(1.0, 0.5, 0.1);
frame:Hide();

local title = frame:CreateFontString(nil, "OVERLAY", "GameFontNormalLarge");
title:SetPoint("TOP", frame, "TOP", 0, -10);

local result = frame:CreateFontString(nil, "OVERLAY", "GameFontHighlightLarge");
result:SetPoint("BOTTOM", frame, "BOTTOM", 0, 12);

-- The winning slot.
local marker = frame:CreateTexture(nil, "OVERLAY");
marker:SetTexture("Interface\\Buttons\\UI-ActionButton-Border");
marker:SetBlendMode("ADD");
marker:SetWidth(ICON_SIZE * 1.9);
marker:SetHeight(ICON_SIZE * 1.9);
marker:SetPoint("CENTER", frame, "CENTER", 0, 0);

local icons = { };
for i = -VISIBLE - 1, VISIBLE + 1 do
	local icon = frame:CreateTexture(nil, "ARTWORK");
	icon:SetWidth(ICON_SIZE);
	icon:SetHeight(ICON_SIZE);
	icons[#icons + 1] = icon;
end

local function RandomDecoy()
	if ( #current.decoys == 0 ) then
		return current.spell;
	end
	return current.decoys[math.random(#current.decoys)];
end

local function SpellIcon(spell)
	local _, _, texture = GetSpellInfo(spell);
	return texture or "Interface\\Icons\\INV_Misc_QuestionMark";
end

-- Lays the reel out around position `position` (fractional index into current.reel).
local function DrawReel(position)
	local centre = math.floor(position + 0.5);
	local offset = position - centre;
	for i, icon in ipairs(icons) do
		local index = centre + (i - VISIBLE - 2);
		local spell = current.reel[index];
		local x = (index - position) * ICON_STEP;
		if ( spell and math.abs(x) <= (VISIBLE + 0.5) * ICON_STEP ) then
			icon:SetTexture(SpellIcon(spell));
			icon:ClearAllPoints();
			icon:SetPoint("CENTER", frame, "CENTER", x, 0);
			-- Fade towards the edges.
			icon:SetAlpha(1 - math.min(1, math.abs(x) / ((VISIBLE + 0.5) * ICON_STEP)) * 0.8);
			icon:Show();
		else
			icon:Hide();
		end
	end
	return centre, offset;
end

local function StartNext()
	current = table.remove(queue, 1);
	if ( not current ) then
		frame:Hide();
		return;
	end

	-- A long reel of decoys, the rolled spell at its end.
	local reel = { };
	local length = 36;
	for i = 1, length - 1 do
		reel[i] = RandomDecoy();
	end
	reel[length] = current.spell;
	for i = length + 1, length + VISIBLE + 1 do
		reel[i] = RandomDecoy();
	end
	current.reel = reel;
	current.target = length;
	current.elapsed = 0;
	current.lastTick = 0;

	title:SetText(ROULETTE_TITLE[current.owner] or ROULETTE_TITLE.B);
	result:SetText("");
	frame:SetAlpha(1);
	frame:Show();
	DrawReel(1);
end

frame:SetScript("OnUpdate", function(self, elapsed)
	if ( not current ) then
		return;
	end
	current.elapsed = current.elapsed + elapsed;
	local t = current.elapsed;

	if ( t < SPIN_TIME ) then
		-- Fast at first, slowing down onto the rolled spell (ease out).
		local progress = 1 - (1 - t / SPIN_TIME) ^ 3;
		local position = 1 + (current.target - 1) * progress;
		local centre = DrawReel(position);
		if ( centre ~= current.lastTick ) then
			current.lastTick = centre;
			PlaySound("igMainMenuOptionCheckBoxOn");
		end
	elseif ( not current.landed ) then
		current.landed = true;
		DrawReel(current.target);
		local name = GetSpellInfo(current.spell) or "?";
		result:SetText((ROULETTE_WON[current.owner] or ROULETTE_WON.B).." : |cffffd100"..name.."|r");
		PlaySoundFile("Sound\\Interface\\LevelUp.wav");
	elseif ( t < SPIN_TIME + HOLD_TIME ) then
		-- hold
	elseif ( t < SPIN_TIME + HOLD_TIME + FADE_TIME ) then
		self:SetAlpha(1 - (t - SPIN_TIME - HOLD_TIME) / FADE_TIME);
	else
		StartNext();
	end
end);

local function QueueRoll(argument)
	local owner, spell, decoyText = string.match(argument, "^(%a)%s+(%d+)%s*(.*)$");
	if ( not owner ) then
		return;
	end
	local decoys = { };
	for decoy in string.gmatch(decoyText, "%d+") do
		decoys[#decoys + 1] = tonumber(decoy);
	end
	queue[#queue + 1] = { owner = owner, spell = tonumber(spell), decoys = decoys };
	if ( not current ) then
		StartNext();
	end
end

------------------------------------------------------------------------------------------------------------
-- Extra resources: rage and energy bars under the player frame once a rolled spell uses them.
------------------------------------------------------------------------------------------------------------
local RESOURCES = {
	{ power = 1, name = "Rage", color = { 1.0, 0.0, 0.0 } },
	{ power = 3, name = "Énergie", color = { 1.0, 1.0, 0.0 } },
};

local resourceFrame = CreateFrame("Frame", "OgreResourceFrame", UIParent);
resourceFrame:SetWidth(120);
resourceFrame:SetHeight(1);
resourceFrame:SetPoint("TOPLEFT", PlayerFrame, "BOTTOMLEFT", 106, 26);

local bars = { };
local function ShowResources(mask)
	local shown = 0;
	for i, resource in ipairs(RESOURCES) do
		local bar = bars[i];
		if ( not bar ) then
			bar = CreateFrame("StatusBar", nil, resourceFrame);
			bar:SetWidth(120);
			bar:SetHeight(10);
			bar:SetStatusBarTexture("Interface\\TargetingFrame\\UI-StatusBar");
			bar:SetStatusBarColor(unpack(resource.color));
			local background = bar:CreateTexture(nil, "BACKGROUND");
			background:SetTexture(0, 0, 0, 0.6);
			background:SetAllPoints(bar);
			bar.text = bar:CreateFontString(nil, "OVERLAY", "TextStatusBarText");
			bar.text:SetPoint("CENTER", bar, "CENTER");
			bar.power = resource.power;
			bar.name = resource.name;
			bars[i] = bar;
		end

		if ( bit.band(mask, bit.lshift(1, resource.power)) ~= 0 ) then
			bar:ClearAllPoints();
			bar:SetPoint("TOPLEFT", resourceFrame, "TOPLEFT", 0, -shown * 12);
			bar:Show();
			shown = shown + 1;
		else
			bar:Hide();
		end
	end
end

resourceFrame:SetScript("OnUpdate", function(self, elapsed)
	self.timer = (self.timer or 0) - elapsed;
	if ( self.timer > 0 ) then
		return;
	end
	self.timer = 0.1;
	for _, bar in ipairs(bars) do
		if ( bar:IsShown() ) then
			local value, maximum = UnitPower("player", bar.power), UnitPowerMax("player", bar.power);
			bar:SetMinMaxValues(0, math.max(1, maximum));
			bar:SetValue(value);
			bar.text:SetText(bar.name.." "..value);
		end
	end
end);

------------------------------------------------------------------------------------------------------------
local events = CreateFrame("Frame");
events:RegisterEvent("CHAT_MSG_ADDON");
events:SetScript("OnEvent", function(self, event, prefix, message, channel, sender)
	if ( prefix ~= OGRE_HEAD_PREFIX or sender ~= UnitName("player") ) then
		return;
	end
	local command, argument = string.match(message, "^(%S+)%s*(.*)$");
	if ( command == "ROLL" ) then
		QueueRoll(argument);
	elseif ( command == "RES" ) then
		ShowResources(tonumber(argument) or 0);
	end
end);
