# Amu Cut SFX

Place reusable short sound effects in this directory. Use semantic filenames such as ui-click.mp3, whoosh-soft.mp3, and impact-light.mp3.

## Matching

engine/src/match_sfx.py combines filename tokens and subtitle keywords for automatic matching. A project can override the result in audio-mix.json with an explicit scene, file, and time.

## Rules

- Sound effects support speech rhythm and visual changes.
- Keep speech clear. The default acceptance target for approved effects is about -2.3 dBTP.
- User-provided effects enter the matching pool first.
- Full talking-head reference tracks in ../references/ are style references and are not mixed into the final video as complete tracks.
