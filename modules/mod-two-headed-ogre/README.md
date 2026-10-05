# mod-two-headed-ogre (v2) — l'Ogre à deux têtes jouable

Un **Ogre** est **un seul personnage** (un seul `Player`, un seul GUID) que **deux joueurs** pilotent
depuis leurs deux clients. Il n'y a plus deux personnages synchronisés : sac, équipement, expérience,
quêtes, argent, réputation et place dans le groupe sont *naturellement* partagés, car ils n'existent
qu'une fois. Un groupe de 5 Ogres = 5 membres de groupe = 10 joueurs.

- **Le premier joueur connecté est le CORPS** : il se déplace, il voit et contrôle tout.
- **Le second est la TÊTE** : son client affiche le même personnage (même sac, même équipement, même
  barre d'XP, même vue), il peut agir (sorts, inventaire, chat, butin...) mais ne peut pas le déplacer.
- Si le corps se déconnecte, la tête **devient le corps** sans que l'Ogre quitte le monde.
- Aucune commande MJ : tout passe par l'écran de création de personnage.

## Créer un Ogre

1. Joueur A choisit la race **Ogre** (côté Horde). Pas de choix de classe. Deux champs de nom :
   **Joueur 1 (vous)** et **Joueur 2 (partenaire)**, par exemple `Grok` et `Zug`.
   Le personnage `Grok` est créé sur le compte de A.
2. Joueur B, sur **son** compte, crée lui aussi un Ogre avec **les deux mêmes noms** (dans n'importe
   quel ordre). Aucun personnage n'est créé : l'Ogre `Grok` apparaît dans la liste de B.
3. Chacun se connecte sur l'Ogre. Le premier arrivé est le corps, le second la tête.

Supprimer l'Ogre depuis sa liste revient à **quitter** l'Ogre : l'autre joueur le garde (il en devient
propriétaire si besoin). Un nouveau partenaire peut le rejoindre avec les deux mêmes noms. L'Ogre n'est
réellement supprimé que lorsque le dernier joueur le supprime.

Les messages de chat d'un Ogre sont préfixés par la tête qui écrit : `[Zug] salut`.

## Installation

### 1. Serveur (core + module)

Ce module s'appuie sur une fonctionnalité générique ajoutée au core, le **contrôle partagé** :

| Fichier | Rôle |
|---|---|
| `WorldSession.cpp/.h` | sessions co-pilotes : miroir des paquets, filtrage des mouvements, passage de relais, resynchro après téléportation |
| `Player.cpp/.h` | liste des sessions co-pilotes, session « agissante », instantané du monde pour un client qui arrive |
| `CharacterHandler.cpp` | connexion d'un 2ᵉ compte sur un personnage en jeu, liste des persos partagés, suppression = quitter |
| `Map.cpp` | traitement des paquets des co-pilotes dans le thread de la map |
| `MovementHandler.cpp`, `MiscHandler.cpp` | mouvements du corps renvoyés à la tête, déconnexion instantanée |
| `DBCStores.cpp/.h`, `Unit.cpp/.h` | alias de race : l'Ogre compte comme les races de la Horde (quêtes, objets, réputations, compétences) |
| `PlayerStorage.cpp` | objets réservés à une autre classe/race autorisés si un script l'accepte |
| `PlayerScript.*`, `ScriptMgr.h` | 7 nouveaux hooks (création, co-pilote, relais, restrictions d'objets) |
| `data/sql/updates/pending_db_characters/rev_*.sql` | table `character_shared_access` |

Étapes :

1. Relancer CMake puis compiler `worldserver` (le module reste `MODULE_MOD-TWO-HEADED-OGRE=static`).
   La v1 (sources, addon, SQL, patch du core) est archivée dans `.agents/plans/two-headed-ogre-v2/legacy/`.
2. Copier `conf/two_headed_ogre.conf.dist` vers le dossier `configs/modules` en `two_headed_ogre.conf`
   (les clés ont changé : repartir du `.dist`).
3. Démarrer `worldserver` : le DB updater applique `character_shared_access`, la table
   `mod_two_headed_ogre_pair` et les données de la race (`chrraces_dbc`, `playercreateinfo`...).
   Les anciennes paires `.ogre pair` ne sont pas reprises : recréer les Ogres.

### 2. Client (les deux joueurs)

```bash
python client/tools/build_client_patch.py --client "D:/World of Warcraft 3.3.5" --install
```

L'outil lit les fichiers d'origine **dans les MPQ du client** (aucun fichier Blizzard n'est fourni par le
module), les modifie et écrit `Data/<locale>/patch-<locale>-4.MPQ` (un patch existant est gardé en
`.bak`). Sans `--install`, le patch est écrit dans `client/tools/build/` pour être distribué.
Supprimer ensuite le dossier `Cache` du client.

Contenu du patch :
- `ChrRaces.dbc` : la race 9 (emplacement « Gobelin » inutilisé) devient **Ogre**, jouable, Horde.
- `CharBaseInfo.dbc` : race 9 + classe porteuse (Paladin) autorisée.
- `CharSections.dbc`, `CharHairGeosets.dbc`, `CharacterFacialHairStyles.dbc` : options de
  personnalisation de l'Orc copiées sur la race 9.
- `GlueXML` : 11ᵉ bouton de race, second champ de nom, panneau de classe masqué.

Si le client signale des fichiers d'interface corrompus, c'est que son `Wow.exe` vérifie la signature
du GlueXML : utiliser un `Wow.exe` 3.3.5a avec la vérification d'interface désactivée (patch classique
des serveurs custom).

## Choix techniques

- **Race 9.** Les races d'un client 3.3.5a sont limitées aux identifiants existants ; l'emplacement
  Gobelin est libre et déjà connu du core (`MAX_RACES`). Le serveur le rend jouable via
  `chrraces_dbc` (aucun fichier DBC serveur à modifier).
- **Apparence.** À l'écran de création, le patch client fournit un modèle de personnage tiré de
  l'ogre-mage à deux têtes (peau jaune pour les mâles, bleue pour les femelles). En jeu, le serveur donne
  l'affichage 3250 (jaune) ou 19930 (bleu), d'échelle propre 1,0 : le client calcule la collision à partir de
  cette échelle (les affichages 12003/13129, x2,65, bloquaient les portes).
- **Pas de classe.** Le client masque le choix ; le serveur impose `TwoHeadedOgre.CarrierClass`
  (Paladin : barre de mana pour les sorts à venir). Toutes les armures, boucliers, reliques, toutes les
  armes (y compris Poigne de titan) et les objets réservés à d'autres classes/races sont utilisables.
- **Départ.** Bastion des Sire-tonnerre, aux Tranchantes (voir « Zone de départ »), langue orque,
  réputations et quêtes de la Horde (l'Ogre compte comme toutes les races de la Horde :
  `TwoHeadedOgre.RaceAliasMask`). Pas encore de cinématique d'introduction.
- **Deux noms dans un seul champ.** Le protocole de création n'a qu'un champ de nom : le client envoie
  les deux noms collés, chacun avec sa majuscule (`GrokZug` : le client refuse tout ce qui n'est pas une
  lettre), le serveur les sépare à la deuxième majuscule avant toute validation. Le nom du Joueur 2 doit
  commencer par une lettre sans accent.

## Capacités raciales

Sorts personnalisés 91050-91052, décrits une seule fois dans `client/tools/ogre_spells.py` : le patch
client les ajoute à `Spell.dbc` (icône d'ogre ajoutée à `SpellIcon.dbc`) et
`client/tools/gen_spell_sql.py` écrit les mêmes lignes côté serveur
(`data/sql/db-world/base/mod_two_headed_ogre_spells.sql`, table `spell_dbc`).

- **Chute d'ogre** (passif, 91051) : aucun dégât de chute (hook core `OnPlayerFall`). À partir de 4 m de
  chute, l'impact (91052, visuel du Choc martial) inflige `(5 + 2 × niveau) × (1 à 3)` dégâts physiques
  aux ennemis à moins de 8 m (bonus maximal à 30 m de chute) et les renverse. 3 s de recharge interne.
- **Deux cerveaux** (passif, 91066, `TwoHeadedOgre.TwoBrains.Chance` = 5 %) : chaque attaque de la tête
  peut lui donner **Idée fixe** (91068, 20 s : son sort suivant suit sa propre incantation, comme pendant
  Fureur bicéphale) ; chaque dégât de la tête, direct ou sur la durée, peut donner au corps **Réflexe
  d'ogre** (91067, 30 s : il esquive la prochaine attaque de mêlée reçue de face).
- **Fureur bicéphale** (actif, 91050, 5 min, utilisable par les deux têtes) : pendant 20 s, les sorts de
  la tête suivent leur propre incantation (barre d'incantation dans la barre de la tête) et leur propre
  temps de recharge global, hors de l'emplacement d'incantation de l'Ogre : le corps continue ses sorts
  et ses attaques, ses déplacements n'interrompent plus la tête, et la tête n'a plus besoin que le corps
  fasse face à sa cible. Étourdissements, peurs et silences arrêtent toujours la tête.

## Classe : la Brute

L'Ogre n'a pas de vraie classe : c'est un Paladin « porteur » (barre de mana, talents de Paladin) que le
patch client renomme **Brute** (`ChrClasses.dbc`, donc pour tous les Paladins) et que l'AddOn colore comme
un guerrier. À la première connexion, le module retire les compétences et les sorts de Paladin, apprend
`TwoHeadedOgre.Brute.Spells` (Frappe héroïque, Bouclier de foudre : sorts du corps) et équipe la seconde
« Jointure de brute » (arme de pugilat 1-3, objet 91003 ajouté à `Item.dbc`). Équipement de départ : une
robe en tissu et les deux poings. Les maîtres de classe n'enseignent rien aux Ogres : les sorts viennent
de la roulette. Les techniques de guerrier qui ne demandent qu'une posture de guerrier s'utilisent sans
posture (client et serveur), pour que la roulette puisse les donner.

## Postures

Trois postures du **corps seul** (barre de postures, 1,5 s de recharge) : c'est lui qui décide, au risque de
couper le mana de la tête. Une seule à la fois et toujours une active :
**MOI ENCAISSER** par défaut, et imposée quand la tête n'est pas connectée (le corps seul survit mais tape
faiblement).

| Posture | Corps | Tête |
|---|---|---|
| MOI TAPER (91060) | Endurance -20 %, mana maximum -80 % | Intelligence +15 %, dégâts des sorts +20 % |
| MOI MAGIE (91061) | Endurance +20 %, force et agilité -50 % | Intelligence +30 %, dégâts et soins des sorts +20 % |
| MOI ENCAISSER (91062) | Endurance +40 %, force et agilité -50 %, soins reçus +25 % | - |

Chaque posture est une aura visible (3 effets au plus) et une aura cachée (91063-91065) que le module ajoute
avec elle (`OgreMgr::UpdateStance`).

## Roulette des sorts

Tous les 2 niveaux (`TwoHeadedOgre.Roulette.LevelInterval`), l'Ogre tire au hasard un sort enseigné par
un maître de n'importe quelle classe, de son niveau ou en dessous (`TwoHeadedOgre.Roulette.Enable`), à tour
de rôle :
- niveaux 2, 6, 10… : **le corps**, parmi les sorts de mêlée et les améliorations ;
- niveaux 4, 8, 12… : **la tête**, parmi les sorts à distance, les soins et les améliorations (pas de sort
  de chasseur).

Le sort appartient à cette tête seulement (grimoire, lancement), se place dans la première case libre de
sa barre et monte de rang tout seul avec les niveaux. Un sort tiré sort de la roulette des deux têtes.
Un sort à rage ou à énergie débloque cette ressource (hook `OnPlayerHasActivePowerType`), affichée sous
le portrait. Exclus : sorts passifs, à runes ou puissance runique, à totem, de familier (sauf les démons
du démoniste, réservés à la tête et sans fragment d'âme), ou qui exigent une forme ou une posture. Les tirages manqués (niveaux gagnés avant) sont faits quand le client du corps
a chargé son interface. Les deux clients jouent l'animation de la roulette (`OgreRoulette.lua`).
Tirages : table `mod_two_headed_ogre_rolled_spell`.

## Zone de départ (niveaux 1 à 10)

Les Ogres apparaissent au **bastion des Sire-tonnerre** (Tranchantes, Outreterre), devant Tor'chunk
Doublegriffes, puis descendent au **village Mok'Nathal**. 18 quêtes réservées aux Ogres (masque de race
256, textes en français), calquées sur celles de la zone, mènent au niveau 10 environ ; la dernière,
« Retour à Kalimdor », téléporte l'Ogre devant Thrall à Orgrimmar, qui offre le choix entre six armes
vertes.

- `data/sql/db-world/base/mod_two_headed_ogre_start_zone.sql` : toutes les créatures attaquables des
  Tranchantes ramenées aux niveaux 1 à 10. Le chemin des quêtes (34 créatures) est réglé à la main ; le
  reste de la zone (environ 130 créatures, trouvées grâce aux fichiers `maps/` du serveur) passe de 7-8
  près du bastion à 9-10 aux confins, élites conservées mais plafonnées. Butin du Bois des Chants
  éternels, sorts à gros dégâts fixes, soins et invocations de haut niveau retirés.
  Les créatures sont modifiées directement : le contenu 65+ de la zone n'est plus jouable sur ce serveur.
- `data/sql/db-world/base/mod_two_headed_ogre_quests.sql` : quêtes 91001-91018, objet 91002.
- Les deux fichiers sont générés par `tools/start_zone/gen_start_zone.py` (lit la base world et les
  fichiers `maps/` et `dbc/` du serveur) et
  `tools/start_zone/gen_quests.py` : modifier les tables du script puis le relancer.

## Limites connues (étape suivante : les sorts)

- **Barre de la tête.** Le client de la tête ne pilote pas l'Ogre : le jeu grise donc ses barres d'action.
  L'AddOn `client/addon/OgreHead` (copié dans `Interface/AddOns` par `build_client_patch.py --install` :
  le client refuse un FrameXML modifié) ajoute la barre « Tête de l'ogre », posée sur la barre
  principale du seul client de la tête, avec ses raccourcis (1 à =). Ses boutons envoient au serveur des
  messages d'addon (`OGRE`, chuchotés à soi-même) que le module traite : il lance le sort pour l'Ogre sur la
  cible de la tête et garde le contenu de la barre (`mod_two_headed_ogre_head_action`, Trait de feu et Mot
  de l'ombre : Douleur au premier lancement : `TwoHeadedOgre.Head.ActionBar`). Glisser un sort de la tête depuis le grimoire pour
  l'ajouter, faire glisser un bouton pour le vider. La tête garde sa propre cible (sa sélection ne change
  plus celle du corps). Après un passage de relais, la tête devenue corps reprend les barres du personnage.
- **Sorts.** Chaque sort appartient à une tête : ceux de `TwoHeadedOgre.Head.Spells` (Trait de feu, Mot de
  l'ombre : Douleur, tous rangs) sont listés et lancés par le client de la tête seulement, tous les autres par le client du corps
  (hook `OnPlayerCanUseSpellFromSession`). Le patch client montre ces premiers sorts comme des sorts de
  niveau 1 (`LEVEL_ONE_SPELLS`). Les deux têtes partagent encore **le même mana et le même temps de recharge
  global** (c'est un seul personnage), et le corps doit faire face à la cible de la tête. Un seul sort à incantation peut être en cours à la fois, et le déplacement du corps
  interrompt les incantations de la tête. `Player::GetActingSession()` indique déjà quel client a
  envoyé une action : c'est la base pour répartir les sorts entre corps et tête.
- Le client de la tête ne pilote pas : s'il appuie sur les touches de déplacement, rien ne se passe.
- Les réglages d'interface *par personnage* (macros, disposition) sont ceux du corps ; ceux de la tête
  ne sont pas sauvegardés. Les réglages *par compte* restent propres à chaque joueur.
- Au passage de relais, si le corps était dans un véhicule, l'Ogre en descend.
- Ogre masculin : ogre-mage jaune (affichage 3250) ; féminin : ogre-mage bleu (19930). Taille 1,0, collision d'orc.

## Tests en jeu

1. Créer l'Ogre Joueur 1 `Grok` / Joueur 2 `Zug` sur le compte A, puis `Zug` / `Grok` sur le compte B : B voit `Grok` dans sa liste.
   Vérifier les refus : même compte deux fois, troisième compte, nom déjà pris, un seul nom saisi.
2. A se connecte (corps), puis B (tête) : B voit l'Ogre, son sac, son équipement, sa barre d'XP.
3. A se déplace : B voit le déplacement depuis l'Ogre. B appuie sur Z/Q/S/D : rien ne bouge.
4. B déplace un objet du sac / équipe une arme : A le voit immédiatement. B lance un sort : il part de
   l'Ogre. B parle : `[Zug] ...`.
5. Tuer un monstre / rendre une quête : une seule XP, une seule récompense, visibles des deux côtés.
6. A se déconnecte : B devient le corps et peut se déplacer. A revient : il devient la tête.
7. Pierre de foyer, entrée/sortie d'instance, téléportation lointaine : la tête suit (écran de chargement)
   et retrouve le monde ; déconnexion de la tête pendant un chargement.
8. Groupe de plusieurs Ogres, donjon, combat, mort, résurrection, commerce avec un autre joueur.
9. Supprimer l'Ogre depuis le compte B : il disparaît de la liste de B, A le garde.
   Supprimer depuis A alors que B est partenaire : B devient propriétaire.
