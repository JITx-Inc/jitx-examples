# JLCPCB order sheet: jitxexamples.jumpstart_kits.js5_diplexer.main.Diplexer

## Board

- Stackup: Proxied
- Layers: 2
- Base material: Rogers, laminate RO4350B, PCB thickness 0.76 mm on the form (the laminate)
- Thickness: 0.86 mm including soldermask, 0.83 mm laminate and copper
- Outer copper: 1 oz
- Dimensions: 31.75 x 31.75 mm
- Surface finish: ENIG (PRELIMINARY, confirm on the form; JLCPCB offers only ENIG or OSP on Rogers)
- Minimum hole size: 0.3 mm
- Minimum trace/space: 0.1 / 0.1 mm

## Assembly

- Assemble: top
- Placements: 11 (11 top, 0 bottom)
- Mounting: 11 SMT, 0 through-hole (JLCPCB prices these differently and asks which you want)
- BOM lines: 9, 0 with an LCSC part number, 9 needing manual matching
- Use JLCPCB's Confirm Parts Placement preview. It is the only chance to catch a wrong rotation before the boards are built. Correct one by editing that part's `orientation` in `lcsc.lock.json`.

## Footprints taken from landpattern class names

JLCPCB will most likely raise a package verification warning on each of these, needing a click to confirm. Supply `LCSCPart(footprint=...)` to avoid it.

- J1, J2, J3

## Placed with no orientation correction

JLCPCB takes a part's tape-and-reel orientation as zero, which is a property of the catalogue part rather than of the landpattern it sits on. The exporter measures that correction against the catalogue footprint and records it in `lcsc.lock.json`. These parts have no entry there, either because they carry no LCSC part number or because the measurement could not be made, so they are placed at the design's own rotation and may need turning.

Give a part an entry in `lcsc.lock.json` to correct it:

```json
{"version": 1, "parts": {"C2286": {"orientation": 90}}}
```

Counter-clockwise degrees, added to the design's own rotation. `lcsc.lock.json` outranks `LCSCPart(orientation=...)`, so it is also where to correct a measured value that turns out to be wrong on a part that is not in this list.

It is keyed by LCSC part number, so a part that has none cannot be corrected there and needs an `LCSCPart` on the component first. Note also that a two-terminal part symmetric under a half turn cannot be checked this way at all: it looks correct at either value.

Check these on JLCPCB's Confirm Parts Placement preview. Their engineers also check polarity against the silkscreen and will email if they cannot judge it.

- C1, C2, C3, C4, C5, C6, J1, J2, J3, L1, L2

## Not in this packet

- No drill map or drill drawing. JLCPCB highly recommends one; the gerber exporter does not produce one yet.

## Conventions used

- Coordinates: the design origin, unshifted, matching the gerber image.
- Positions: the landpattern origin, which is the body centre for standard landpatterns but may not be for connectors.
- Rotation: degrees counter-clockwise. Bottom parts are negated against the design rotation, matching the KiCad plugin JLCPCB recommends.

