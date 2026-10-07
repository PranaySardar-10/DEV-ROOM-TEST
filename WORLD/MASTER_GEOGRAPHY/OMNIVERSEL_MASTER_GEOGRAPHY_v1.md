# Omniversel Roleplay — Master Geography v1

## Decision

The atlas is now treated as the **master spatial blueprint** for the world. The first terrain task is **not** to make one city. It is to create the entire macro-geographic skeleton first, then split that exact master surface into seamless Unity terrain tiles.

### World envelope

- **40 km east-west × 25 km north-south**
- **1,000 km² maximum terrain envelope**
- Origin: approximately the center of the world
- X = east/west, Z = north/south, Y = metres
- Sea level = **Y 0**
- Ocean remains a separate water surface and extends beyond the terrain envelope.
- Preferred terrain tile: **5 × 5 km**
- 8 × 5 grid = **40 tiles**
- 4097² heightmap per tile gives about **1.22 m/sample**.

## Why these references

The geography is fictional, but its morphology should feel believable.

- Japanese terrain is a strong reference for the northern mountain backbone, steep/short river systems, alluvial plains and dense lowland cities. Japan's MLIT describes the country as predominantly mountainous, with long mountain ranges, short steep rivers and cities concentrated on lowland plains. citeturn2search2
- South Florida/Miami is a reference for the Coastal City: low coastal relief, bays, beaches, barrier/island relationships and warm coastal environments. NOAA material describes South Florida as low relief with coastal/mangrove systems and barrier islands; Biscayne Bay is a shallow bay bordered by mainland and barrier islands. citeturn2search24turn2search6
- USGS hydrology principles are the structural reference: drainage networks should follow elevation, watersheds are defined by terrain, and hydrologically conditioned DEMs preserve continuous downhill flow. citeturn1search3turn1search0

These are **morphological references only**, not templates to copy.

## Master geographic layout

### North
- Military Zone in northwest.
- Main Northern Mountain Range across the upper-central world.
- Northern Rural Village east of the mountains.
- Desert Region in northeast.
- Rocky northern coastline.

### Center
- Main City in the central lowland basin.
- Mountain Lake Residential north of Main City.
- Japanese-style Rural Farm Village north/east of Main City.
- Eastern Rural Region between Main City and Coastal City.
- Western Forest between Port City and northern regions.

### West
- Port City on a sheltered industrial bay.
- Rugged coast and cliffs.
- Forested hills behind the port.

### East
- Coastal City on a low coastal plain.
- One commercial airport nearby on flat terrain.
- Desert transitions toward the eastern/northeastern coast.

### South
- Southern Rural Region.
- Resort Island in the southwest/south.
- Private Island in the southeast, connected by bridge.
- Beach-heavy southern/eastern coastline.

## Elevation philosophy

Do not make the terrain a generic noise field.

The master terrain should have intentional geographic hierarchy:

1. Ocean = 0 m.
2. Coastal plains = roughly 0–80 m.
3. Main urban basin = roughly 5–180 m.
4. Rural lowlands = roughly 30–250 m.
5. Hills = roughly 150–900 m.
6. Mountain foothills = roughly 400–1,000 m.
7. Mountain Lake basin = roughly 650–1,100 m.
8. Northern mountain range = roughly 900–1,900 m.
9. Highest peak target = about 2,100 m.
10. Desert = generally 40–650 m with one dominant lake around 55 m.

The exact final elevations can be tuned during the master-terrain generation pass, but the relative hierarchy is locked.

## Hydrology

Three major river systems are required:

- **Central River:** Northern Mountains → Main City region → Southern Ocean.
- **West River:** Western Forest/foothills → Port City → western coast/bay.
- **East River:** Northern Mountains/Mountain Lake → Eastern Rural → Coastal City/eastern ocean.

The terrain must be generated so these rivers have real downhill corridors rather than being painted onto unrelated terrain.

USGS describes drainage networks as structures derived from terrain and emphasizes hydrologic conditioning to maintain continuous flow across an elevation surface. citeturn1search3turn1search0

Major lakes:
- Mountain Lake: ~12 km².
- Desert Lake: ~10 km².
- One smaller northern/alpine lake: ~3 km².

The Desert Region intentionally has **one dominant lake**, not dozens of procedural ponds.

## First terrain milestone

The first output should be a **macro master terrain** with:

- complete coastline
- all major islands
- mountain backbone
- major valleys
- Mountain Lake
- Desert Lake
- three major river corridors
- Main City basin
- Port City bay
- Coastal City plain
- Military Zone plateau
- Airport flat
- broad rural/desert/forest geography

It should look recognizable from above as the Omniversel atlas **before** roads, buildings, vegetation or final materials are added.

## After master geography is validated

1. Split into seamless 5 km terrain tiles.
2. Validate height seams.
3. Apply biome/material masks.
4. Build rivers/lakes and roads.
5. Build cities/structures.
6. Add vegetation.
7. Add props.
8. Do final shaders/lighting/performance pass.

**Do not start city construction until the master geography passes the overhead-map test.**
