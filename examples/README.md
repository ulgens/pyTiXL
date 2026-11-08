# Examples

Three runnable patches, from declarative basics to the procedural API.

| File | Shows |
| --- | --- |
| `01_hello_ascii.py` | Declarative class attributes, parameter setting, one full capture |
| `02_tinted_ascii.py` | A custom `Operator` subclass (`Tint`), explicit ports, a two-stage chain |
| `03_two_variants.py` | `patch.add(...)`, two sinks, switching the pinned output |

Run them from the repository root:

```bash
python examples/01_hello_ascii.py
python examples/02_tinted_ascii.py ~/Pictures/portrait.jpg
python examples/03_two_variants.py "Examples:images/t3-logo-alpha.png"
```

Each script:

1. attaches to a running TiXL debug bridge, or launches TiXL with
   `--debug-server` if none is listening;
2. creates a clean project and builds the patch;
3. writes captures to `examples/output/`.

An editor that was already running is reused and left running. Set `TIXL_EXE`
to point at a specific TiXL executable if auto-detection does not find it.

Captures:

- `01_hello_ascii_graph.png` and `01_hello_ascii.png`
- `02_tinted_ascii_graph.png` and `02_tinted_ascii.png`
- `03_dense_graph.png`, `03_dense.png`, and `03_sparse.png`

See the main [README](../README.md) for the full library API.
