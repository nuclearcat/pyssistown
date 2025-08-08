# TODO.md — Browser-Based 2D Sprite RPG (Multiplayer, Anti-Cheat, FastAPI)

## 0) Goals & Scope

* Top-down, tiled map; all entities are sprites.
* Multiplayer (≥2 players). Real-time movement, chat, emotes, trade, co-op quests.
* Server-authoritative simulation with anti-cheat. FastAPI + SQLite (via ORM; upgradeable to PostgreSQL).
* Content via Tiled (JSON). Client: Phaser 3 + TypeScript + Vite.

---

## 1) Architecture (high level)

* **Client (Phaser+TS)** → **WebSocket** (real-time inputs, snapshots) + **HTTP** (auth, metadata, save).
* **Game Server (FastAPI/Starlette)**

  * Realtime loop @ 30 Hz; authoritative physics/validation.
  * One **room** per map instance; AOI filtering.
  * Persistence: SQLAlchemy/SQLModel + Alembic; SQLite (WAL) → Postgres later.
  * Optional Redis Pub/Sub for horizontal scale.
* **Content Pipeline**: Tiled maps + Worlds; custom properties for terrain/collision/NPC/entrances/items.

---

## 2) Tech Stack

* **Frontend**: TypeScript, Phaser 3, Vite, Playwright (E2E), Vitest (unit).
* **Backend**: FastAPI, Starlette WebSockets, SQLAlchemy/SQLModel, Alembic, Uvicorn.
* **Infra**: Docker, docker-compose; NGINX (TLS, reverse proxy); Redis (scale).
* **Auth**: JWT (RFC 7519).
* **Serialization**: JSON (v1); MessagePack later.

---

## 3) Repo Structure

```
/client
  /src
    /scenes (Boot, Preload, Map, UI)
    /net   (ws.ts, protocol.ts, interp.ts)
    /game  (player.ts, npc.ts, items.ts, quests.ts)
    /ui    (hud, dialog, inventory, chat)
  vite.config.ts  tsconfig.json

/server
  /app
    main.py
    ws.py            # WebSocket endpoints & room hub
    sim/             # Tick loop, validators, AOI
    models/          # SQLModel/SQLAlchemy ORM
    api/             # REST routers
    services/        # inventory, quests, trade
    security/        # auth, rate-limit, bans
    schemas/         # Pydantic models
    migrations/      # Alembic
  pyproject.toml

/content
  /tiled/*.tmj  /worlds/*.world  /atlases/*.json  /sprites/*.png

/devops
  docker-compose.yml  Dockerfile.server  Dockerfile.client  nginx.conf
```

---

## 4) Milestones & Deliverables

### M0 — Project Skeleton (1–2 d)

* [ ] Client scaffold (Vite+TS+Phaser).
* [ ] Server scaffold (FastAPI+SQLModel+Alembic).
* [ ] Docker dev + compose; CI (lint, test).
* [ ] `/docs` OpenAPI online; CORS configured.

### M1 — Map Render & Movement (3–5 d)

* [ ] Load one Tiled map (JSON).
* [ ] Player sprite, 4-dir walk; collisions from tile property `collides=true`.
* [ ] Camera follow; fixed timestep client loop.

### M2 — Realtime Multiplayer Base (4–6 d)

* [ ] WS endpoint `/ws/game?room=:map&token=:jwt`.
* [ ] Server tick 30 Hz; snapshots 15 Hz.
* [ ] Client: input stream 20 Hz; local prediction + interpolation buffer 120–150 ms.
* [ ] Rooms by map; join/leave; heartbeats.

### M3 — Interactions & Inventory (3–5 d)

* [ ] Item spawns from Tiled objects; pickup radius; inventory UI.
* [ ] HTTP persistence (inventory, character pose).
* [ ] AOI filtering (radius 40 tiles).

### M4 — NPCs, Dialog, Quests (4–6 d)

* [ ] NPC spawn from Tiled object layer; dialog trees.
* [ ] Quest state machine (NotStarted/Active/Completed/Failed).
* [ ] Co-op quest flags (per-member progress, shared objectives).

### M5 — Player–Player Features (4–6 d)

* [ ] Proximity chat + emotes.
* [ ] Trade: request/accept/lock/commit (escrow, transactional).
* [ ] Entrances → cross-room transfer (sub-maps).

### S-Series — Anti-Cheat & Security (parallel; see §9)

* [ ] JWT on WS; Origin allowlist; rate limits (token bucket).
* [ ] Authoritative validators (speed/accel/terrain/LOS).
* [ ] Violation scoring; kick/ban pipeline; audit logs.

### M6 — Content & Polish (ongoing)

* [ ] Minimap, loading screen, SFX; basic analytics.
* [ ] Playwright E2E: login→join→move→pickup→trade→quest.

---

## 5) Data Model (ORM, minimal v1)

* **users**(id, email, password\_hash, created\_at)
* **characters**(id, user\_id, name, map\_key, x, y, facing, updated\_at)
* **items**(id, key, name, stackable, payload\_json)
* **inventory**(id, character\_id, item\_id, qty, updated\_at)
* **quests**(id, key, name, definition\_json)
* **quest\_progress**(id, character\_id, quest\_id, state, step, vars\_json, updated\_at)
* **npcs**(id, key, map\_key, x, y, facing, dialog\_id)
* **maps**(id, key, name, json\_url, width, height, spawn\_x, spawn\_y)
* **sessions**(player\_id, room, last\_heartbeat)
* **trades**(id, a\_id, b\_id, state, payload\_json, created\_at)
* **violations**(id, player\_id, rule, details\_json, score, ts)
* **bans**(id, player\_id, reason, expires\_at)

---

## 6) HTTP API (REST)

* **Auth**

  * `POST /auth/register` → 201
  * `POST /auth/login` → {jwt}
* **Profile/Character**

  * `GET /me`
  * `GET /me/character` / `PUT /me/character` (map, x, y, facing)
* **World**

  * `GET /world/maps/:key` (metadata)
  * `GET /world/maps/:key/json` (signed/static URL)
* **Content**

  * `GET /npcs?map=:key`
  * `GET /items?map=:key`
  * `GET /quests` / `GET /quests/:key`
  * `GET /inventory` / `POST /inventory/consume`
* **Admin**

  * `POST /admin/ban` / `DELETE /admin/ban/:id`
  * `GET /admin/violations?player=:id`

---

## 7) WebSocket Protocol (v1)

**Connect:** `/ws/game?room=:map_key&token=:jwt` (subprotocol: `pony.v1`)

**Client → Server**

```json
{ "t":"join","char_id":123 }
{ "t":"input","seq":417,"dt":50,"up":0,"down":1,"left":0,"right":1,"act":0 }
{ "t":"interact","target":"player:57","kind":"trade_request" }
{ "t":"chat","text":"Hello" }
{ "t":"ack","last_seq":417 }
{ "t":"pong" }
```

**Server → Client**

```json
{ "t":"welcome","player_id":57,"server_time":123456789,"room":"field_01" }
{ "t":"snapshot","st":123456820,
  "players":[{"id":57,"x":128,"y":256,"vx":0,"vy":80,"anim":"walk_s"}],
  "items":[...],"npcs":[...] }
{ "t":"event","kind":"player_join","id":91 }
{ "t":"trade","kind":"offer","from":57,"items":[{"id":"apple","qty":2}] }
{ "t":"kick","reason":"violation_speed" }
{ "t":"ping" }
```

---

## 8) Simulation Loop (server)

* Fixed timestep: 30 Hz (Δt≈33.3 ms).
* Per tick (per room):

  1. Drain inputs; discard duplicates/out-of-order (seq).
  2. Validate intents (see §9).
  3. Integrate velocities → positions; resolve collisions.
  4. Run interactions (pickups, trades, quests).
  5. Emit snapshots @ 15 Hz (AOI-filtered).

---

## 9) Anti-Cheat & Validation (authoritative)

**Transport & Session**

* Enforce TLS; JWT required on connect.
* Validate `Origin` against allowlist; no cookie auth on WS.
* Heartbeat: server→`ping` every 5 s; disconnect on timeout.
* Token-bucket rate limits (UID+IP):

  * Inputs ≤ 25 msg/s (burst 15)
  * Interact ≤ 8/s (burst 8)
  * Trade ≤ 4 / 10 s
  * Chat ≤ 5 / 10 s (burst 3)

**Movement**

* Server ignores client positions and client-supplied `dt`.
* Cap speed/accel per terrain (e.g., grass ≤ 3 tiles/s; water ≤ 1.5 tiles/s).
* Collision vs `collision` layer; reject collider penetration.
* Teleport detection: displacement > `speed_max * (Δt * jitter_factor)` → flag.

**Map Transitions**

* Only via `entrance` objects `{target_map, spawn_x, spawn_y}`.

**Interactions/Items**

* Pickup only within radius ≤ 1 tile; respect respawn/cooldown.
* Inventory changes are server-side, transactional, idempotent.

**Trading**

* Two-phase escrow: request/accept → lock → commit/abort.
* Validate ownership/qty at commit. One DB transaction for both players.

**Quests/NPCs**

* All quest state changes from verified triggers (area/kill/talk/collect).
* Client cannot set quest state.

**Anomaly Scoring**

* Increment on: speed, collider pass, OOB, spam, dup keys, invalid LOS.
* Decay: −1 / 60 s. Thresholds:

  * ≥5 within 60 s → **kick**; ≥15 within 24 h → **24 h block**; repeat → **ban**.
* Persist to `violations`; admin review UI.

---

## 10) Tiled & Content Conventions

* Layers: `ground`, `collision` (tile property `collides=true`), `decor`, `overlay`, `objects`.
* Object types on `objects`:

  * `entrance` → `{target_map, spawn_x, spawn_y}`
  * `npc` → `{id, dialog_id, quest_giver}`
  * `item_spawn` → `{item_id, quantity, respawn_s}`
* World linking: Tiled **World** file to stitch maps.
* Budgets: tile size 32 px; atlas ≤ 2048² px per texture; animation ≤ 8 frames/dir.

---

## 11) Performance Budgets (initial)

* Tick CPU (room): ≤ 5 ms @ 50 entities.
* Snapshot size (room): ≤ 8 KiB @ 20 Hz (AOI-filtered).
* Interp buffer: 120–150 ms; client send rate: 20 Hz.
* Latency tolerance target: ≤ 200 ms one-way.

---

## 12) Testing Plan

* **Unit (client)**: movement, prediction/reconciliation math, UI state.
* **Unit (server)**: validators, inventory math, quest transitions, trade escrow.
* **Property-based**: random input streams; invariants (no negative qty; position never inside collider).
* **Integration**: two clients vs local server; trade success; anti-cheat kicks.
* **E2E (Playwright)**: login → join → move → pickup → quest → trade.
* **Load**: synthetic 100 bot clients; measure tick time, drop rate, memory.
* **Security**: WS CSWSH check (Origin), replay/dup inputs, fuzz JSON.

---

## 13) Deployment

* Docker images: `server`, `client`, `nginx`.
* Environments: `dev` (hot-reload), `staging`, `prod` (TLS).
* DB: SQLite (WAL) in dev/staging; Postgres in prod.
* Secrets: JWT key, DB URL, CORS allowlist.
* Sticky sessions at LB if multi-process WS.
* Optional Redis for room fan-out across processes.

---

## 14) Acceptance Criteria (per milestone)

* **M2**: Two browsers in same room see each other smoothly; packet loss 5 % still smooth.
* **M3**: Item pickup persists across reconnect; duping attempts fail.
* **M4**: Quest progress shared when specified; server rejects forged quest updates.
* **M5**: Trade completes atomically; forged trade fails; attempt triggers violation.
* **S**: Speed hack/teleport attempts → kick within ≤ 1 s; CSWSH blocked; rate limits enforce.

---

## 15) Configuration (example)

```yaml
server:
  tick_hz: 30
  snapshot_hz: 15
  interp_ms: 140
  aoi_tiles: 40
  speed_tiles_per_s:
    grass: 3.0
    water: 1.5
security:
  jwt_secret: "<env>"
  ws_allowed_origins: ["https://game.example.com"]
  rate_limits:
    input_per_s: 25
    interact_per_s: 8
    chat_per_10s: 5
```

---

## 16) Implementation Checklist (granular)

### Backend

* [ ] Models & migrations (users, characters, items, inventory, quests, npcs, maps, sessions, trades, violations, bans).
* [ ] JWT auth; password hashing; CORS.
* [ ] REST routers (auth, me, world, items, npcs, quests, inventory).
* [ ] WS hub (rooms, join/leave, heartbeats, ping/pong).
* [ ] Simulation loop; AOI; snapshot builder.
* [ ] Validators (movement/terrain/collision/entrance/LOS).
* [ ] Rate limiter (token-bucket per UID+IP+type).
* [ ] Trade service (escrow, transactional commit).
* [ ] Violation scoring; kick/ban; admin endpoints.
* [ ] Content loader (Tiled JSON ingestion, caches).
* [ ] Metrics/logging (requests/s, latency, tick time, violations).

### Frontend

* [ ] Scenes (Boot, Preload, Map, UI).
* [ ] Net client (WS connect/reconnect, backoff, subprotocol).
* [ ] Input stream (20 Hz), seq#, local prediction, reconciliation.
* [ ] Interpolation buffer; snapshot replay.
* [ ] Entities: player (self/remote), NPC, items.
* [ ] UI: HUD, dialog, inventory, chat, trade modal, quest journal.
* [ ] Map transitions (entrances) and autosave.
* [ ] Error/kick handling with reasons.

---

## 17) References (vendor/primary docs)

* Phaser 3 docs: [https://newdocs.phaser.io](https://newdocs.phaser.io)
* Tiled Map Editor & Worlds: [https://doc.mapeditor.org](https://doc.mapeditor.org)
* FastAPI docs: [https://fastapi.tiangolo.com](https://fastapi.tiangolo.com)
* Starlette WebSockets: [https://www.starlette.io/websockets/](https://www.starlette.io/websockets/)
* SQLAlchemy / SQLModel: [https://docs.sqlalchemy.org](https://docs.sqlalchemy.org) / [https://sqlmodel.tiangolo.com](https://sqlmodel.tiangolo.com)
* Alembic migrations: [https://alembic.sqlalchemy.org](https://alembic.sqlalchemy.org)
* MDN WebSocket API: [https://developer.mozilla.org/docs/Web/API/WebSocket](https://developer.mozilla.org/docs/Web/API/WebSocket)
* JWT (RFC 7519): [https://datatracker.ietf.org/doc/html/rfc7519](https://datatracker.ietf.org/doc/html/rfc7519)
* Redis Pub/Sub: [https://redis.io/docs/latest/develop/pubsub/](https://redis.io/docs/latest/develop/pubsub/)

---

