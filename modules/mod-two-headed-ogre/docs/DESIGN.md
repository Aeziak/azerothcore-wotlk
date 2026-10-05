# Two-headed ogre v2 — design

See [README](../README.md) for installation, behaviour and tests.

## One character, two clients

The v1 design synchronised two Player objects (vehicle seat, mirrored stats, mirrored bags, quest
reward routing). Every shared feature needed its own copy logic and each one leaked. v2 removes the
second Player: the Head is a second WorldSession attached to the Body's Player ("co-pilot").

Core shared control (generic, module independent):
- `character_shared_access(guid, account)`: extra accounts listed in the char enum and accepted by
  `Player::LoadFromDB`. Deleting the character from such an account only removes the access; the owner
  deleting it while others share it transfers ownership.
- Login on a character already in world: `OnPlayerCanJoinAsCopilot` decides (default: refuse).
  `WorldSession::HandlePlayerLoginAsCopilot` sends a private snapshot (self + every visible object),
  then `SMSG_CLIENT_CONTROL_UPDATE(0)`.
- `WorldSession::SendPacket` on the primary session mirrors every packet to co-pilots, except
  connection/account-scoped opcodes and movement control.
- Co-pilot movement opcodes are dropped before dispatch; the primary's movement broadcast is also sent
  to co-pilots (the stock broadcast skips the moving player).
- `Map::Update` updates co-pilot sessions with the player's map (thread-safe opcodes).
- Far teleport: mirroring pauses at `SMSG_NEW_WORLD`, the co-pilot's worldport ack schedules a fresh
  snapshot once the player is back in a map.
- Primary logout/disconnect with a co-pilot: hand over (`OnPlayerSessionHandover`), the player never
  leaves the world. A co-pilot logging out simply detaches. No offline (60 s) session for shared players.
- `Player::GetActingSession()`: which client sent the packet being handled.

Module: race 9 data and client patch, `Name1Name2` (split at the second capital) creation/join, head names,
chat prefix, all proficiencies, `IsClass` equip contexts, item restriction bypass, race/skill alias, ogre display scale.

v1 sources and its core patch are kept in `.agents/plans/two-headed-ogre-v2/legacy/`.
