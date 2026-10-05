-- mod-two-headed-ogre: Ogre start zone quests, Blade's Edge Mountains, levels 1-10 (Ogre race only).
-- Thunderlord Stronghold, then Mok'Nathal Village, then "Retour à Kalimdor": teleport to Orgrimmar and
-- turn in to Thrall for a choice of green weapons. Generated, French texts.

-- Quest item: Bloodmaul beer keg (the stock Bloodmaul Brutebane Keg is unique and usable).
DELETE FROM `item_template` WHERE `entry` = 91002;
INSERT INTO `item_template` (`entry`, `class`, `subclass`, `SoundOverrideSubclass`, `name`, `displayid`, `Quality`, `bonding`, `Material`, `maxcount`, `stackable`, `description`, `VerifiedBuild`) VALUES
(91002, 12, 0, -1, 'Tonnelet de bière de la Masse-sanglante', 7921, 1, 4, -1, 0, 20, 'Ça sent les pieds de gronn.', 0);

DELETE FROM `item_template` WHERE `entry` = 91004;
INSERT INTO `item_template` (`entry`, `class`, `subclass`, `SoundOverrideSubclass`, `name`, `displayid`, `Quality`, `InventoryType`, `Material`, `ItemLevel`, `RequiredLevel`, `bonding`, `SellPrice`, `stat_type1`, `stat_value1`, `stat_type2`, `stat_value2`, `spellid_1`, `spelltrigger_1`, `description`, `VerifiedBuild`) VALUES
(91004, 4, 0, -1, 'Chevalière Sire-tonnerre', 9823, 2, 11, 1, 5, 1, 1, 25, 7, 1, 6, 1, 91054, 1, 'Portée par les coursiers du clan Sire-tonnerre.', 0);

DELETE FROM `quest_template` WHERE `ID` IN (91001,91002,91003,91004,91005,91006,91007,91008,91009,91010,91011,91012,91013,91014,91016,91017,91018,91015);
INSERT INTO `quest_template` (`ID`, `QuestType`, `QuestLevel`, `MinLevel`, `QuestSortID`, `RewardXPDifficulty`, `RewardMoney`, `StartItem`, `AllowableRaces`, `LogTitle`, `LogDescription`, `QuestDescription`, `QuestCompletionLog`, `RequiredNpcOrGo1`, `RequiredNpcOrGo2`, `RequiredNpcOrGo3`, `RequiredNpcOrGo4`, `RequiredNpcOrGoCount1`, `RequiredNpcOrGoCount2`, `RequiredNpcOrGoCount3`, `RequiredNpcOrGoCount4`, `RequiredItemId1`, `RequiredItemId2`, `RequiredItemId3`, `RequiredItemId4`, `RequiredItemId5`, `RequiredItemId6`, `RequiredItemCount1`, `RequiredItemCount2`, `RequiredItemCount3`, `RequiredItemCount4`, `RequiredItemCount5`, `RequiredItemCount6`, `RewardItem1`, `RewardAmount1`, `RewardItem2`, `RewardAmount2`, `RewardItem3`, `RewardAmount3`, `RewardItem4`, `RewardAmount4`, `RewardChoiceItemID1`, `RewardChoiceItemQuantity1`, `RewardChoiceItemID2`, `RewardChoiceItemQuantity2`, `RewardChoiceItemID3`, `RewardChoiceItemQuantity3`, `RewardChoiceItemID4`, `RewardChoiceItemQuantity4`, `RewardChoiceItemID5`, `RewardChoiceItemQuantity5`, `RewardChoiceItemID6`, `RewardChoiceItemQuantity6`, `ObjectiveText1`, `ObjectiveText2`, `ObjectiveText3`, `ObjectiveText4`, `VerifiedBuild`) VALUES
(91001, 2, 1, 1, 3522, 8, 75, 0, 256, 'Deux têtes, un seul ogre', 'Parlez à Gor''drek au bastion des Sire-tonnerre.', 'Alors c''est toi, l''ogre à deux têtes dont parlent nos éclaireurs ? Hmph. Une tête pour réfléchir, une tête pour cogner... on verra bien laquelle commande.$B$BLe clan Sire-tonnerre accueille tous ceux qui savent se battre. Va voir Gor''drek, près des enclos. Il a toujours du travail pour des bras solides... et toi, tu en as quatre.', 'Retournez voir Gor''drek au bastion des Sire-tonnerre.', 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 91004, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, '', '', '', '', 0),
(91002, 2, 2, 1, 3522, 8, 150, 0, 256, 'La nature envahissante', 'Tuez 8 Saigneurs Aile-rasoir pour Gor''drek au bastion des Sire-tonnerre.', 'Les saigneurs aile-rasoir pullulent autour du bastion. Ils s''attaquent à nos loups, à nos réserves, et même à nos guerriers quand ils dorment.$B$BVa dans les collines à l''ouest et tues-en huit. Deux têtes, ça devrait faire deux fois moins de travail, non ?', 'Retournez voir Gor''drek au bastion des Sire-tonnerre.', 21033, 0, 0, 0, 8, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, '', '', '', '', 0),
(91003, 2, 3, 1, 3522, 8, 225, 30175, 256, 'Protéger les nôtres', 'Soignez 5 Loups redoutables sire-tonnerre avec la Pommade de Gor''drek.', 'Nos loups redoutables rôdent librement autour du bastion, mais beaucoup ont été blessés par les saigneurs. Prends cette pommade et applique-la sur cinq d''entre eux.$B$BAttention : un loup blessé ne fait pas toujours la différence entre un ami et un repas. S''il te mord, défends-toi... mais pas trop fort.', 'Retournez voir Gor''drek au bastion des Sire-tonnerre.', 21142, 0, 0, 0, 5, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 'Loup redoutable sire-tonnerre soigné', '', '', '', 0),
(91004, 2, 3, 1, 3522, 7, 225, 0, 256, 'Des produits hors du commun', 'Rapportez 6 Ailes de chauve-souris impeccables au Vieil Orok au bastion des Sire-tonnerre.', 'Toi, l''ogre ! Le vieil Orok a besoin d''ingrédients. Les ailes des saigneurs aile-rasoir font un ragoût... intéressant.$B$BRapporte-m''en six, et je te garderai une part. Ou deux, vu que tu as deux bouches.', 'Retournez voir le Vieil Orok au bastion des Sire-tonnerre.', 0, 0, 0, 0, 0, 0, 0, 0, 38620, 0, 0, 0, 0, 0, 6, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, '', '', '', '', 0),
(91005, 2, 4, 2, 3522, 8, 300, 0, 256, 'Les ogres de la Masse-sanglante', 'Tuez 8 Tirailleurs de la Masse-sanglante et 3 Loups redoutables de la Masse-sanglante pour Tor''chunk Doublegriffes.', 'La Masse-sanglante... Des ogres, comme toi. Enfin, avec une seule tête et encore moins de cervelle. Ils ont dressé leur camp à l''ouest et ils menacent nos routes.$B$BMontre-leur ce qu''un ogre du clan Sire-tonnerre sait faire : tue huit tirailleurs et trois de leurs loups.', 'Retournez voir Tor''chunk Doublegriffes au bastion des Sire-tonnerre.', 19948, 20058, 0, 0, 8, 3, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, '', '', '', '', 0),
(91006, 2, 5, 3, 3522, 8, 375, 0, 256, 'Les géomanciens', 'Tuez 6 Géomanciens de la Masse-sanglante et 4 Brutes de la Masse-sanglante pour Tor''chunk Doublegriffes.', 'Les géomanciens de la Masse-sanglante manipulent la pierre et le feu. Tant qu''ils vivent, leur camp tiendra.$B$BVa plus loin à l''ouest, tue six géomanciens et quatre brutes. Et si l''une de tes têtes a peur, que l''autre la fasse taire.', 'Retournez voir Tor''chunk Doublegriffes au bastion des Sire-tonnerre.', 19952, 19991, 0, 0, 6, 4, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, '', '', '', '', 0),
(91007, 2, 5, 3, 3522, 7, 375, 0, 256, 'Une bière à tomber', 'Rapportez 6 Tonnelets de bière de la Masse-sanglante à Rokgah Poigne-sang au bastion des Sire-tonnerre.', 'Psst. Les ogres de la Masse-sanglante brassent une bière si forte qu''elle ferait tomber un kodo. Leur brasseur en garde des tonnelets entiers, et les autres en ont toujours un sur eux.$B$BRapporte-m''en six. C''est pour... l''étude. Oui, l''étude. Tor''chunk n''a pas besoin de le savoir.', 'Retournez voir Rokgah Poigne-sang au bastion des Sire-tonnerre.', 0, 0, 0, 0, 0, 0, 0, 0, 91002, 0, 0, 0, 0, 0, 6, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, '', '', '', '', 0),
(91008, 2, 6, 4, 3522, 8, 450, 0, 256, 'La menace Flèchelame', 'Tuez 10 Brutes de Flèchelame et 5 Raptors de Flèchelame pour Tor''chunk Doublegriffes.', 'À l''est, les Flèchelame ne valent pas mieux que la Masse-sanglante. Leurs brutes pillent nos patrouilles et leurs raptors dévorent nos montures.$B$BTue dix brutes et cinq raptors de Flèchelame.', 'Retournez voir Tor''chunk Doublegriffes au bastion des Sire-tonnerre.', 19995, 20728, 0, 0, 10, 5, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, '', '', '', '', 0),
(91009, 2, 6, 4, 3522, 7, 450, 0, 256, 'Les chamans de Flèchelame', 'Tuez 6 Chamans de Flèchelame et 3 Cuisiniers de Flèchelame pour Garm au bastion des Sire-tonnerre.', 'Les esprits sont agités. Les chamans de Flèchelame les tourmentent pour en tirer du pouvoir, et leurs cuisiniers nourrissent toute cette horde d''ogres.$B$BFais taire six chamans et trois cuisiniers, à l''est. Les esprits t''en seront reconnaissants... et moi aussi.', 'Retournez voir Garm au bastion des Sire-tonnerre.', 19998, 20334, 0, 0, 6, 3, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, '', '', '', '', 0),
(91010, 2, 7, 5, 3522, 8, 525, 0, 256, 'Le champion de Flèchelame', 'Tuez un Champion de Flèchelame pour Tor''chunk Doublegriffes.', 'Les Flèchelame ont des champions, des montagnes de muscles qui se croient invincibles. Prouve-leur le contraire.$B$BAbats l''un d''eux, et tu seras un vrai guerrier du clan Sire-tonnerre.', 'Retournez voir Tor''chunk Doublegriffes au bastion des Sire-tonnerre.', 21296, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, '', '', '', '', 0),
(91011, 2, 7, 5, 3522, 8, 525, 0, 256, 'La route de Mok''Nathal', 'Tuez 6 Ravageurs Arrachelame et 6 Ravageurs fauche-sang sur la route du sud, puis rendez-vous au village Mok''Nathal et parlez à Leoroxx.', 'Tu as fait tes preuves. Moi aussi, j''ai du sang d''ogre dans les veines : je suis Mok''Nathal, à moitié orc, à moitié ogre. Mon peuple vit au sud, au village Mok''Nathal, et mon père Leoroxx saura quoi faire de deux têtes aussi dures que les tiennes.$B$BMais la route est coupée : les ravageurs, rendus fous par le gangrefeu de la Porte de la mort, dévorent tout ce qui passe. Nettoie le chemin en descendant : six ravageurs arrachelames et six ravageurs fauche-sang. Les Mok''Nathal sauront qui a rouvert la route.', 'Retournez voir Leoroxx au village Mok''Nathal.', 22123, 21423, 0, 0, 6, 6, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 3305, 1, 2970, 1, 4242, 1, 0, 0, 0, 0, 0, 0, '', '', '', '', 0),
(91012, 2, 8, 6, 3522, 8, 600, 0, 256, 'Depuis des temps oubliés', 'Tuez Gnosh Brognat, 4 Mystiques de Flèchelame et 4 Écraseurs de Flèchelame pour Leoroxx au village Mok''Nathal.', 'Les Flèchelame ont installé un campement au nord, entre notre village et le bastion. Leur chef, Gnosh Brognat, se vante d''avoir massacré des Mok''Nathal.$B$BVa là-bas, abats Gnosh ainsi que quatre mystiques et quatre écraseurs.', 'Retournez voir Leoroxx au village Mok''Nathal.', 20768, 20766, 20765, 0, 1, 4, 4, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1211, 1, 2977, 1, 6527, 1, 0, 0, 0, 0, 0, 0, '', '', '', '', 0),
(91013, 2, 8, 6, 3522, 8, 600, 0, 256, 'Cocons d''aile-de-soie', 'Rapportez 8 Cocons d''aile-de-soie à Taerek au village Mok''Nathal.', 'Les larves d''aile-de-soie, à l''ouest du village, tissent des cocons d''une soie incomparable. Rapporte-m''en huit.$B$BAttention : quand on les menace, elles éclosent... et ce qui en sort a des ailes.', 'Retournez voir Taerek au village Mok''Nathal.', 0, 0, 0, 0, 0, 0, 0, 0, 30791, 0, 0, 0, 0, 0, 8, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 14724, 1, 4771, 1, 2308, 1, 0, 0, 0, 0, 0, 0, '', '', '', '', 0),
(91014, 2, 8, 6, 3522, 7, 600, 0, 256, 'Les ailes les plus douces', 'Rapportez 8 Ailes iridescentes à Silmara au village Mok''Nathal.', 'Les ailes des ailes-de-soie adultes font les plus beaux ornements de Mok''Nathal. Rapporte-m''en huit.$B$BEt essaie de ne pas les abîmer... j''ai vu comment tu tiens tes armes.', 'Retournez voir Silmara au village Mok''Nathal.', 0, 0, 0, 0, 0, 0, 0, 0, 30792, 0, 0, 0, 0, 0, 8, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 3474, 1, 4768, 1, 2312, 1, 0, 0, 0, 0, 0, 0, '', '', '', '', 0),
(91016, 2, 9, 7, 3522, 8, 675, 0, 256, 'Écailles et crocs', 'Tuez 6 Serpents ailécailles et 6 Flagellants Crocs-lames pour Dertrok au village Mok''Nathal.', 'Les serpents ailécailles et les flagellants crocs-lames chassent sur nos terres, au nord du village. Les premiers crachent la foudre, les seconds mordent jusqu''à l''os.$B$BDébarrasse-nous de six de chaque.', 'Retournez voir Dertrok au village Mok''Nathal.', 20749, 20751, 0, 0, 6, 6, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 3302, 1, 4312, 1, 5968, 1, 0, 0, 0, 0, 0, 0, '', '', '', '', 0),
(91017, 2, 10, 8, 3522, 8, 750, 0, 256, 'Maggoc, fils de Gruul', 'Tuez Maggoc pour Leoroxx au village Mok''Nathal.', 'Il est temps de te parler de Maggoc. C''est un fils de Gruul, un géant parmi les ogres, et il rôde au nord, près du campement des Flèchelame. Tant qu''il vivra, aucun Mok''Nathal ne sera en sécurité.$B$BUn ogre contre un ogre... mais toi, tu as l''avantage : deux têtes.', 'Retournez voir Leoroxx au village Mok''Nathal.', 20600, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1219, 1, 3651, 1, 15944, 1, 8350, 1, 0, 0, 0, 0, '', '', '', '', 0),
(91018, 2, 10, 8, 3522, 5, 750, 0, 256, 'Retour à Kalimdor', 'Parlez à Thrall dans le fort Grommash, à Orgrimmar.', 'La nouvelle de ta victoire a déjà traversé la Porte des ténèbres. Le chef de guerre Thrall en personne veut rencontrer l''ogre à deux têtes.$B$BLes esprits vont te porter jusqu''à Orgrimmar. Présente-toi à lui dans le fort Grommash. Et essayez de vous mettre d''accord avant de parler : le chef de guerre n''aime pas qu''on lui réponde deux fois.', 'Retournez voir Thrall dans le fort Grommash, à Orgrimmar.', 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 826, 1, 6214, 1, 3188, 1, 1928, 1, 6205, 1, 1925, 1, '', '', '', '', 0);

DELETE FROM `quest_template_addon` WHERE `ID` IN (91001,91002,91003,91004,91005,91006,91007,91008,91009,91010,91011,91012,91013,91014,91016,91017,91018,91015);
INSERT INTO `quest_template_addon` (`ID`, `PrevQuestID`, `ProvidedItemCount`) VALUES
(91001, 0, 0),
(91002, 91001, 0),
(91003, 91002, 1),
(91004, 91001, 0),
(91005, 91003, 0),
(91006, 91003, 0),
(91007, 91003, 0),
(91008, 91006, 0),
(91009, 91006, 0),
(91010, 91006, 0),
(91011, 91010, 0),
(91012, 91011, 0),
(91013, 91011, 0),
(91014, 91011, 0),
(91016, 91011, 0),
(91017, 91012, 0),
(91018, 91017, 0);

DELETE FROM `quest_offer_reward` WHERE `ID` IN (91001,91002,91003,91004,91005,91006,91007,91008,91009,91010,91011,91012,91013,91014,91016,91017,91018,91015);
INSERT INTO `quest_offer_reward` (`ID`, `RewardText`, `VerifiedBuild`) VALUES
(91001, 'Tor''chunk t''envoie ? Par les ancêtres, deux têtes... J''espère qu''au moins l''une d''elles sait écouter.$B$BTiens, Tor''chunk m''a demandé de te donner ça : la chevalière des coursiers du clan. Avec elle, tu traverseras les Tranchantes plus vite que tes deux têtes ne se disputent.', 0),
(91002, 'Bien. Les loups dormiront mieux cette nuit... et moi aussi.', 0),
(91003, 'Les loups te sentiront désormais comme un membre de la meute. Enfin, l''une de tes têtes, au moins.', 0),
(91004, 'Parfait ! Croustillantes à souhait. Ne dis à personne ce qu''il y a dans le ragoût.', 0),
(91005, 'Ha ! Ils ne s''attendaient pas à se faire rosser par l''un des leurs.', 0),
(91006, 'Le camp de la Masse-sanglante ne s''en remettra pas de sitôt. Tu apprends vite, ogre.', 0),
(91007, 'Ah, l''odeur ! On dirait des pieds de gronn. Parfait. Garde ça pour toi, hein ?', 0),
(91008, 'Bon travail. Les Flèchelame vont apprendre à craindre le bastion.', 0),
(91009, 'Les esprits s''apaisent. Le clan Sire-tonnerre n''oubliera pas ce que tu as fait.', 0),
(91010, 'Tu as abattu leur champion ? À deux têtes contre une, il n''avait aucune chance. Tu es des nôtres, ogre. Rexxar voudra te voir.', 0),
(91011, 'Rexxar t''envoie, et tu as rouvert la route du nord ? Alors tu es le bienvenu au village Mok''Nathal, ogre. Ici, personne ne se moque d''un sang mêlé... ni d''une tête en trop.', 0),
(91012, 'Gnosh ne se vantera plus. Les anciens Mok''Nathal chanteront ton nom... tes deux noms.', 0),
(91013, 'Magnifiques ! Cette soie habillera tout le village pour l''hiver.', 0),
(91014, 'Elles sont parfaites. Pour un ogre, tu as la main étonnamment légère.', 0),
(91016, 'Nos chasseurs pourront de nouveau sortir. Merci, ogre.', 0),
(91017, 'Maggoc est mort ?! Un fils de Gruul, abattu par un ogre à deux têtes... Les Mok''Nathal te doivent beaucoup. Et quelqu''un de très important veut te rencontrer.', 0),
(91018, 'Ainsi, c''est toi l''ogre que les Sire-tonnerre et les Mok''Nathal acclament. Deux têtes, une seule loyauté : celle de la Horde.$B$BChoisis une arme dans notre armurerie, $N... si tes deux têtes parviennent à se mettre d''accord. Ensuite, le monde t''appartient. Lok''tar ogar !', 0);

DELETE FROM `quest_request_items` WHERE `ID` IN (91001,91002,91003,91004,91005,91006,91007,91008,91009,91010,91011,91012,91013,91014,91016,91017,91018,91015);
INSERT INTO `quest_request_items` (`ID`, `CompletionText`, `VerifiedBuild`) VALUES
(91002, 'Les saigneurs rôdent toujours, $N ?', 0),
(91003, 'Les loups ont-ils reçu leurs soins ?', 0),
(91004, 'Tu as mes ailes ? Le ragoût n''attend pas.', 0),
(91005, 'La Masse-sanglante est-elle toujours aussi bruyante ?', 0),
(91006, 'Les géomanciens sont-ils tombés ?', 0),
(91007, 'Alors, cette bière ? Chut, pas si fort.', 0),
(91008, 'Les Flèchelame rôdent encore près de nos murs.', 0),
(91009, 'Les esprits gémissent encore.', 0),
(91010, 'Le champion vit encore ?', 0),
(91011, 'La route est-elle libre ?', 0),
(91012, 'Gnosh Brognat se vante-t-il encore ?', 0),
(91013, 'Les cocons, ogre ?', 0),
(91014, 'Tu as les ailes ? Pas trop froissées ?', 0),
(91016, 'Mes chasseurs ont encore croisé des serpents.', 0),
(91017, 'Maggoc vit encore ?', 0);

DELETE FROM `creature_queststarter` WHERE `quest` IN (91001,91002,91003,91004,91005,91006,91007,91008,91009,91010,91011,91012,91013,91014,91016,91017,91018,91015);
INSERT INTO `creature_queststarter` (`id`, `quest`) VALUES
(21147, 91001),
(21117, 91002),
(21117, 91003),
(19471, 91004),
(21147, 91005),
(21147, 91006),
(21311, 91007),
(21147, 91008),
(21950, 91009),
(21147, 91010),
(21984, 91011),
(22004, 91012),
(21895, 91013),
(21896, 91014),
(21496, 91016),
(22004, 91017),
(22004, 91018);

DELETE FROM `creature_questender` WHERE `quest` IN (91001,91002,91003,91004,91005,91006,91007,91008,91009,91010,91011,91012,91013,91014,91016,91017,91018,91015);
INSERT INTO `creature_questender` (`id`, `quest`) VALUES
(21117, 91001),
(21117, 91002),
(21117, 91003),
(19471, 91004),
(21147, 91005),
(21147, 91006),
(21311, 91007),
(21147, 91008),
(21950, 91009),
(21147, 91010),
(22004, 91011),
(22004, 91012),
(21895, 91013),
(21896, 91014),
(21496, 91016),
(22004, 91017),
(4949, 91018);

-- Leoroxx: accepting "Retour à Kalimdor" teleports the ogre in front of Thrall.
UPDATE `creature_template` SET `AIName` = 'SmartAI' WHERE `entry` = 22004;
DELETE FROM `smart_scripts` WHERE `entryorguid` = 22004 AND `source_type` = 0;
INSERT INTO `smart_scripts` (`entryorguid`, `source_type`, `id`, `link`, `event_type`, `event_phase_mask`, `event_chance`, `event_flags`, `event_param1`, `event_param2`, `event_param3`, `event_param4`, `event_param5`, `event_param6`, `action_type`, `action_param1`, `action_param2`, `action_param3`, `action_param4`, `action_param5`, `action_param6`, `target_type`, `target_param1`, `target_param2`, `target_param3`, `target_param4`, `target_x`, `target_y`, `target_z`, `target_o`, `comment`) VALUES
(22004, 0, 0, 0, 19, 0, 100, 0, 91018, 0, 0, 0, 0, 0, 62, 1, 0, 0, 0, 0, 0, 7, 0, 0, 0, 0, 1920.0, -4131.0, 44.4, 1.57, 'Leoroxx - On Quest ''Retour a Kalimdor'' Accepted - Teleport Invoker to Orgrimmar');
