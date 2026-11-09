# pyTiXL


> [!CAUTION]
> The project is at very early stage and almost all components are generated using LLMs (DeepSeek <3), following best practices from [ulgens/python-anything](https://github.com/ulgens/python-anything/).
>
> The current version is just a development dump and not ready for any serious usage.


A small, Pythonic library for building [TiXL](https://tixl.app) patches and capturing
their graph and rendered output.

```python
from pytixl import AsciiRender, LoadImage, Patch


class MyPatch(Patch):
    # Create an image input.
    image = LoadImage("Examples:images/t3-logo-alpha.png")

    # Create a filter and set its parameters.
    ascii = AsciiRender()
    ascii.filter_characters = "@%#*+=-:. "

    # Connect the image input to the filter.
    image >> ascii


patch = MyPatch()
patch.screenshot(path="out/logo.png")
```

The library launches TiXL with its debug bridge if no editor is listening, creates a
clean project, materializes the operators, connects them, tidies the graph, and writes
the screenshots.

## Install

```bash
uv venv
uv pip install -e .
```

With the lint hooks:

```bash
uv pip install -e '.[dev]'
prek install
```

Requires Python 3.10+ and TiXL 4.4 with the debug bridge.

## Defining patches

Operators are declared as class attributes. Connections use `>>`, which connects an
operator's default output to the first compatible input of another operator:

```python
class MyPatch(Patch):
    image = LoadImage("~/Pictures/portrait.jpg")
    ascii = AsciiRender()
    image >> ascii
```

For explicit ports, use the port attributes:

```python
image.texture >> ascii.image
```

Inputs use Pythonic snake_case names and map to TiXL's actual input names. Values can
also be passed as constructor arguments:

```python
class MyPatch(Patch):
    image = LoadImage(path="Examples:images/t3-logo-alpha.png", cache_resources=True)
    ascii = AsciiRender(
        filter_characters="@%#*+=-:. ",
        mix_in_colors=0.2,
    )
    image >> ascii
```

Procedural patches use `add` instead:

```python
from pytixl import AsciiRender, LoadImage, Patch

patch = Patch()
image = patch.add(LoadImage("Examples:images/t3-logo-alpha.png"), "image")
ascii = patch.add(AsciiRender(), "ascii")
ascii.image = image
patch.set_output(ascii)
```

### Custom operators

Any TiXL symbol can be wrapped by subclassing `Operator` and declaring its ports:

```python
from pytixl import Operator, Port


class Blur(Operator):
    symbol = "Blur"
    input_ports = {
        "image": Port("Image", "texture"),
        "radius": Port("Radius", "float"),
    }
    output_ports = {"texture": Port("Output", "texture")}


class MyPatch(Patch):
    image = LoadImage("...")
    blur = Blur(radius=4.0)
    image >> blur
```

Port types are used to pick an input automatically: `texture`, `path`, `string`, `float`,
`int`, `bool`, `vec2`, `int2`, and `color`. Local file paths are resolved to absolute
paths before they are sent to TiXL; resource paths such as `Examples:...` pass through
unchanged.

## Capturing

`Patch.screenshot()` builds the patch lazily and returns a `Capture` with the files it
wrote:

```python
capture = patch.screenshot()
print(capture.graph)  # .../tixl_20261108_101500/patch_graph.png
print(capture.output)  # .../tixl_20261108_101500/patch_output.png
```

`path` can be a directory or an image path:

```python
patch.screenshot("captures")  # captures/patch_graph.png + patch_output.png
patch.screenshot("captures/logo.png")  # captures/logo_graph.png + captures/logo.png
patch.screenshot("captures/logo.png", target="graph")  # graph only
```

Graph screenshots use TiXL's own focus-selection framing (the behaviour behind `F`),
then crop the editor UI to the graph canvas on platforms without native graph capture.

## Lifecycle

`Patch` is a context manager. It shuts down TiXL only if it launched the editor itself;
an editor that was already running is left alone.

```python
with MyPatch() as patch:
    patch.screenshot("captures")

# same, without a context manager
patch = MyPatch()
try:
    patch.screenshot("captures")
finally:
    patch.close()
```

Constructor options:

| Option       | Description                                                        |
| ------------ | ------------------------------------------------------------------ |
| `project`    | Open an existing TiXL project instead of creating one              |
| `name`       | Short name for a newly created project                             |
| `namespace`  | Namespace for a newly created project (default `user.<name>`)      |
| `clean`      | `True`/`False` override for deleting existing nodes                 |
| `port`       | Debug bridge port (default `9042`)                                 |
| `executable` | Path to the TiXL executable (auto-detected by default)             |
| `window`     | Editor window size as `WxH` (default: full available screen)       |
| `session`    | Reuse an existing `EditorSession`                                  |
| `keep_open`  | Leave a launched editor running after `close()`                    |

Existing projects are not cleaned by default. New projects have their tutorial nodes
removed unless `clean=False`.

## CLI

The original command-line workflow remains available:

```bash
pytixl-ascii
pytixl-ascii --image ~/Pictures/portrait.jpg
pytixl-ascii --image "Lib:images/basic/perlin-noise.jpg"
pytixl-ascii --out ./captures --keep-open
pytixl-ascii --project my_project
pytixl-ascii --help
```

It is implemented on top of the library and writes `patch_graph.png` and
`patch_output.png`.

## Examples

Three runnable patches live in [`examples/`](examples/README.md):

- `01_hello_ascii.py` — declarative class attributes and a full capture.
- `02_tinted_ascii.py` — a custom `Operator` subclass (`Tint`) and a two-stage chain.
- `03_two_variants.py` — the procedural API with two outputs and `set_output()`.

```bash
python examples/01_hello_ascii.py
python examples/02_tinted_ascii.py ~/Pictures/portrait.jpg
python examples/03_two_variants.py
```

## HTTP API

The optional `api` extra exposes the debug bridge as a typed HTTP service with
Swagger UI. It attaches to an already-running editor; it never launches TiXL.

```bash
uv sync --extra api
pytixl-api --tixl-port 9042            # http://127.0.0.1:8787/docs
```

Every TiXL protocol method has its own endpoint under `/api`, with Pydantic
request and response models:

```text
GET /api/getVersion
GET /api/getGraphState
POST /api/setInput
POST /api/addOp
POST /api/connect
DELETE /api/deleteOp
POST /api/screenshot
POST /api/newProject
...
```

Query parameters and request and response bodies use TiXL's camelCase spelling.
Python fields stay snake_case, and Swagger shows both the schema and examples.

```bash
curl -s http://127.0.0.1:8787/api/getVersion
curl -s 'http://127.0.0.1:8787/api/getGraphState?includeDefaults=true'
curl -s -X POST http://127.0.0.1:8787/api/setInput \
  -H 'content-type: application/json' \
  -d '{"childId": "...", "inputName": "Path", "value": "Examples:images/t3-logo-alpha.png"}'
```

`GET /health` reports whether the bridge is connected; protocol endpoints return
`503` until TiXL is listening. The bridge reconnects automatically. `GET
/api/methods` lists the typed methods, and `GET /api/status` shows the
connection and capture counters.

### Captures

Screenshots are written to `./captures` by default:

```bash
# Metadata + a /files URL
curl -s -X POST http://127.0.0.1:8787/api/screenshot \
  -H 'content-type: application/json' -d '{"target": "output"}'

# Image bytes
curl -s -X POST 'http://127.0.0.1:8787/api/screenshot?inline=true' \
  -H 'content-type: application/json' -d '{"target": "ui"}' -o ui.png

# Or send Accept: image/png
curl -s -X POST http://127.0.0.1:8787/api/screenshot \
  -H 'accept: image/png' -H 'content-type: application/json' \
  -d '{"target": "output"}' -o output.png
```

Relative paths stay inside the captures folder. Absolute paths are allowed and
are served at `/files/<name>` only when they are inside it. Use
`--captures-dir` to change the location.

### Security and operation

The server binds `127.0.0.1` by default. Binding elsewhere requires a token:

```bash
TIXL_API_TOKEN=secret pytixl-api --host 0.0.0.0 --port 8787
```

When `TIXL_API_TOKEN` (or `--token`) is set, every request needs
`Authorization: Bearer <token>`. CORS is disabled unless `--cors-origin` is
given. Run a single uvicorn worker: TiXL serializes requests on one TCP
connection, and multiple workers would create competing connections.

Errors use a stable body:

```json
{
  "code": "NOT_FOUND",
  "message": "getOutput failed: NOT_FOUND - Instance has no matching output",
  "method": "getOutput",
  "tixlCode": "NOT_FOUND",
  "detail": "Instance has no matching output"
}
```

Protocol codes map to `422` for invalid input, `404` for missing state, `409`
for refused operations, `503` when the bridge is unavailable, and `504` on
timeouts.

### API options

| Option | Description |
| --- | --- |
| `--host` / `--port` | HTTP bind address and port (default `127.0.0.1:8787`) |
| `--tixl-host` / `--tixl-port` | TiXL debug bridge (default `127.0.0.1:9042`) |
| `--captures-dir` | Capture directory (default `./captures`) |
| `--token` | Bearer token; also read from `TIXL_API_TOKEN` |
| `--cors-origin` | Allowed CORS origin; repeat for several |
| `--log-level` | uvicorn log level (default `info`) |

Long-running methods use per-method timeouts: `newProject` 900 s, `openProject`
and `reload` 300 s, `pumpFrames` 300 s, and everything else 120 s.

## Development

```bash
prek run --all-files
```
