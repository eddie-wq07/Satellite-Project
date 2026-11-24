# ABB IRB1600 X-120 asset provenance

Downloaded from https://github.com/work-r-labs/robots at revision
`ab6aa489855256de07ba46c7b45887fdbc42b607`. `source.json` records each exact raw URL,
byte length and SHA-256. `LICENSE` is the repository's MIT license, preserved verbatim.
The downloaded binary USD, physics, sensor and geometry layers are unchanged.
The URDF is retained for reference; the scene loads the supplied USD, not a new URDF conversion.
The URDF's separate STL references are not used by this project and are not downloaded.

Visual identification: candidate ABB IRB1600 family based on the flat upright link cover,
paired cover fasteners, slender branded forearm and circular wrist. The provided stills do not
show a model plate or reliable dimension scale. Exact variant, reach and payload are unverified.
The ABB IRB2600 product photo was also inspected; its upright housing differs visibly.

Project overrides live in `../../environments/factory.usda`: joint drives, added multi-contact
head, estimated tool-loaded wrist mass/inertia, cables and scene placement. Source link masses
and collision approximations otherwise remain the upstream model's estimates; they have not
been identified from the real factory. Do not treat this as calibrated hardware dynamics.
