# Protected evidence.csv integrity investigation

## Finding

No file was restored or regenerated.

| Check | Value |
|---|---|
| Protected file | `data/restructuring_v2/evidence.csv` |
| Expected SHA-256 | `0557f026a32e28c884c34c76d39d0d76630e375d500cffbbe80f532d682b5b4d` |
| Current SHA-256 | `e32c262d8abc4e9a4cefed7b7cbdd2041d0e7f550176b50c9c105d8d147a7f7f` |
| Last known-good commit | `eac7499a8ea659e126036675f773471a3d3451f6` |
| Rows before/current | 289 / 289 |
| Added/removed IDs | 0 / 0 |
| Changed rows | 81 |
| Changed fields | `parser_version` only |

All 81 differences change `pypdf-6.16.0+manual-1` to `pypdf-6.16.1+manual-1`. Byte length and line count are unchanged. No evidence text, extracted observation, direction, availability date, source hash, review status or prediction feature changed.

## Assessment

The drift is provenance/version metadata, not substantive analytical evidence. Existing scientific prediction values are not changed by this diff. However, the protected-file guard correctly fails because immutability is byte-level. Claims that all 12 protected artefacts verify must remain suspended until the founder explicitly authorises either restoration of the exact committed file or a separately governed correction. The current file was left untouched.
