# STARTING MEMORY — OMNIVERSEL ROLEPLAY
**Memory tag:** `STARTING MEMORY`
**Created:** 2026-09-24
**Purpose:** Preserve the earliest project-development context so a future conversation can understand how the Omniversel Roleplay project began, without altering the existing backup memory or development branches.

---

## 1. PROJECT IDEA

- Main game: **Omniversel Roleplay**.
- Planned as an original **Unity open-world multiplayer real-life roleplay game/platform**, inspired by the general RP genre (GTA RP / CRMP / SA-MP style), but intended to be built as its own project.
- The game is intended to be mobile-first eventually, with optimization and a small final install size as important design constraints.
- Target production/launch planning reference was around **2028-02-01**.
- The user is the project owner / idea owner and wants AI agents to perform much of the repetitive technical development rather than manually writing every system.
- Human approval remains the authority for important changes and actual Unity/runtime validation.

## 2. EARLY TECHNICAL DIRECTION

Initial intended architecture:

**Unity client → authoritative server → data layer → PostgreSQL/MySQL**

The project should be designed from scratch rather than blindly copying an existing CRMP/RP codebase. Existing RP schemas and systems may be used as references for requirements, but implementation should be original and rights/licensing must be respected.

The user wanted the development process itself to become AI-assisted and eventually highly automated through **DevRoom**, an orchestration system that coordinates specialized agents.

## 3. DEVROOM CONCEPT

The original development vision was an AI development factory with roles such as:

- **Lead / Orchestrator** — coordinates the work.
- **Architect** — turns requirements into implementation design.
- **Coder / Implementer** — creates or applies code.
- **Reviewer** — reviews proposed work.
- **QA** — tests/evaluates the implementation.
- Optional research/documentation agents.
- **Human/project owner** — provides the idea, reviews important results, and remains the final authority.

Original conceptual pipeline:

**Idea → Orchestrator → Lead/Architect → Coder → Review → Implementer → QA → Unity test → human feedback → correction cycle**

If Unity/runtime inspection reveals a problem, the user can provide feedback and the agents iterate until the user confirms the result.

## 4. CREATION SYSTEM

A later planned component was the **Creation System**, intended to make production of game content systematic and repeatable.

The initial planned artifact was:

`CREATION_SYSTEM.md`

The first tiny tool was intended to be:

**Asset Intake + Validation**

The Creation System was deliberately planned for later. The immediate priority was to make the provider-independent DevRoom orchestration reliable before beginning substantial game production.

## 5. GAME SCALE / CONTENT VISION

Early planning included:

### Vehicles
- Roughly **300–500 vehicle models** eventually.
- Economy vehicles: approximately 30–45.
- Mid-range vehicles: similar scale.
- Luxury: approximately 20–25.
- Super: approximately 5–10.
- Hyper: approximately 3–5.
- Some vehicles could remain hidden or be introduced later through events/rewards/exclusive content.
- Assets should be legitimately sourced/licensed and optimized for mobile.

### Characters
The intended character system uses a base character model plus customization references such as:
- body
- face
- clothing
- hair
- accessories

An initial testing target was roughly **50–60 customization combinations**, expanding later.

Cosmetics were considered an important monetization path.

## 6. VEHICLE/DATABASE MODEL

An early architectural distinction was made between:

- **VehicleDefinition** — static definition of a vehicle model/type.
- **PlayerVehicle** — an owned/instantiated vehicle containing player-specific state.

The database should store definitions/state, while Unity assets remain in the project.

This separation was intended to avoid duplicating static vehicle data for every owned vehicle.

## 7. OPTIMIZATION / SIZE GOALS

Early project goals included:

- Final installed size ideally around **2.5 GB**, with an upper target around **3 GB**.
- Mobile-first optimization.
- Smooth world streaming and LOD behavior.
- RenderWare was discussed only as inspiration for the idea of efficient streaming/LOD behavior, not as a dependency or engine requirement.
- Assets should be optimized rather than simply importing high-detail content.

## 8. POSSIBLE LEGACY-CODE CONVERTER

A future optional tool was discussed for source code the user has rights to:

**old Pawn/CRMP source → parser/AST → mapping/rules → AI for ambiguous logic → original C# API → generated C# → compiler/tests/fixes**

The intended modern API would expose project-owned concepts such as:

- `player.SetHealth`
- `player.GiveMoney`
- `player.Teleport`
- `vehicle.Spawn`
- faction operations
- messaging

This was a future possibility, not a requirement for the initial game foundation.

## 9. PROJECT PRINCIPLES FROM THE START

The project repeatedly emphasized:

- Build the project rather than merely planning it.
- Keep architecture deterministic and testable.
- Avoid unnecessary speculative systems.
- Use AI agents as specialized workers, not as uncontrolled autonomous decision-makers.
- Keep human review/approval where it matters.
- Use Git as durable project history and recovery.
- Validate actual Unity behavior rather than trusting an agent's claim that something works.
- Keep production assets legitimate and optimized.
- Preserve the separation between static definitions and player-owned state.
- Finish and validate the development factory before relying on it for major game production.

## 10. RELATION TO CURRENT DEVROOM

This file represents the **starting memory only**.

It is intentionally separate from the detailed ongoing continuity snapshot in `BACKUP_MEMORY_FOR_PROJECT.md`.

The detailed backup remains the current-state continuity record. This branch/file exists so a future conversation can recover the original project vision and early decisions without confusing them with later implementation/debugging history.

**Memory tag: STARTING MEMORY**
