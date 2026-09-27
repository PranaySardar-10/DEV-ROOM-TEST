# Omniversel Roleplay — World & Customization Planning Backup

Date: 2026-09-27

## Player / Character Architecture
The player should be a **Player Entity**, not a character model.

PLAYER ENTITY
- Movement mechanics
- Camera
- Input
- Jump / crouch / sprint
- Interaction
- PlayerVisual
  - Joe
  - Future Model A
  - Future Model B
  - etc.

Joe is only the current visual representation. Future model swapping should preserve movement, camera, CharacterController, input, identity, networking, inventory, and database identity.

## Future Character Customization
Plan an ultra-light in-game Blender-like customization mode for the equipped character only:
- Face/shape/surface parameters
- Hair styles and colors
- Body type
- Skin/material colors
- Clothing/equipment: shirts, jackets, sunglasses, hats, pants, shoes, etc.
- Prefer parameter/material/equipment variation over huge numbers of complete character models.
- A small number of exclusive full models may exist.
- Do NOT build this customization system yet; only keep the Player Entity architecture compatible with it.

## World / Buildings / Houses / Interiors
We have not yet designed the house/building/interior production system. This is now an explicit future planning area.

Planned direction:
- Build the world from a reusable **modular asset library**, rather than manually modeling every building from scratch.
- Asset categories should eventually include:
  - Buildings / houses
  - Interior modules
  - Rooms and architectural pieces
  - Doors/windows/stairs
  - Furniture
  - Props
  - Roads/sidewalks
  - Environment assets
- Use legally usable free/commercial base assets where appropriate, then customize materials, colors, logos, signs, and other project-specific details in Blender.
- Track asset provenance/license information: source, creator, license, commercial permission, attribution requirements, modification permission, and project usage.
- Houses and buildings should be designed as reusable modular pieces where practical, so one architectural kit can produce many distinct-looking locations.
- Interiors should be reusable room/furniture kits rather than requiring a unique fully modeled interior for every building.
- World production should eventually have a dedicated specification/automation workflow similar to character production, but this is not part of the current character milestone.
- The architecture should leave room for future streamed/open-world content without prematurely implementing world streaming.

## Current Priority
Finish and stabilize the Player Entity/core character mechanics and animation first.
Do not start large-scale building/interior production yet.

