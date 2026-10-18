"""Resolve the explicit inventory of files included in the research release."""
import json
from pathlib import Path

def release_paths(root):
 root=Path(root).resolve()
 cfg=json.loads((root/'configs/submission_files.json').read_text(encoding='utf-8'))
 paths={root/name for name in cfg['files']}
 snapshots=json.loads((root/'data/raw/alfred_vintages/manifest.json').read_text(encoding='utf-8'))
 paths.update(root/f"data/raw/alfred_vintages/{r['vintage']}/{r['series']}.csv" for r in snapshots['records'])
 for pattern in cfg['patterns']:paths.update(p for p in root.glob(pattern) if p.is_file())
 for p in paths:
  assert p.is_file(),f'Required release file missing: {p.relative_to(root)}'
  assert p.resolve().is_relative_to(root),f'Path escapes release: {p}'
 return sorted(paths)
