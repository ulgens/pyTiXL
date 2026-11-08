"""Operator specifications used to describe a patch declaratively.

A patch class declares operators as class attributes and connects them with
``>>``::

    class MyPatch(Patch):
        image = LoadImage("Examples:images/t3-logo-alpha.png")
        ascii = AsciiRender(filter_characters="@%#*+=-:. ")
        image >> ascii

Each operator mirrors one TiXL symbol. Parameters are exposed with Pythonic
snake_case names (``ascii.filter_characters``) and map to the symbol's actual
input names (``FilterCharacters``).
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Any, ClassVar

__all__ = [
    "AsciiRender",
    "InputRef",
    "LoadImage",
    "Operator",
    "OutputRef",
    "Port",
]


@dataclass(frozen=True)
class Port:
    """A TiXL input or output and the value type it carries."""

    name: str
    type: str = "any"


@dataclass(frozen=True)
class _Link:
    source: Operator
    output: str
    input: str


class InputRef:
    """A reference to one input of an operator, e.g. ``ascii.image``."""

    __slots__ = ("name", "owner")

    def __init__(self, owner: Operator, name: str):
        self.owner = owner
        self.name = name

    @property
    def port(self) -> Port:
        return self.owner.input_ports[self.name]

    @property
    def value(self) -> Any:
        return self.owner.values.get(self.name)

    def __repr__(self) -> str:
        return f"{self.owner.label or type(self.owner).__name__}.{self.name}"


class OutputRef:
    """A reference to one output of an operator, e.g. ``image.texture``."""

    __slots__ = ("name", "owner")

    def __init__(self, owner: Operator, name: str):
        self.owner = owner
        self.name = name

    @property
    def port(self) -> Port:
        return self.owner.output_ports[self.name]

    def __rshift__(self, other: Operator | InputRef):
        return _connect(self, other)

    def __repr__(self) -> str:
        return f"{self.owner.label or type(self.owner).__name__}.{self.name}"


class Operator:
    """Base class for one TiXL operator in a patch.

    Subclasses declare the symbol name and its ports::

        class Blur(Operator):
            symbol = "Blur"
            input_ports = {
                "image": Port("Image", "texture"),
                "radius": Port("Radius", "float"),
            }
            output_ports = {"texture": Port("Output", "texture")}
    """

    symbol: ClassVar[str] = ""
    input_ports: ClassVar[dict[str, Port]] = {}
    output_ports: ClassVar[dict[str, Port]] = {}

    def __init__(self, **params: Any):
        object.__setattr__(self, "values", {})
        object.__setattr__(self, "links", [])
        object.__setattr__(self, "position", None)
        object.__setattr__(self, "label", None)
        if params:
            self.set(**params)

    # -- parameters -----------------------------------------------------

    def set(self, **params: Any) -> Operator:
        """Set one or more input values and return the operator."""
        for name, value in params.items():
            if name == "position":
                object.__setattr__(self, "position", _coerce_position(value))
                continue
            if name not in self.input_ports:
                raise AttributeError(
                    f"{type(self).__name__} has no input {name!r}; "
                    f"available inputs: {', '.join(self.input_ports) or 'none'}"
                )
            self.values[name] = _coerce(value, self.input_ports[name])
        return self

    def __setattr__(self, name: str, value: Any) -> None:
        if name in {"values", "links", "position", "label"} or name.startswith("_"):
            object.__setattr__(self, name, value)
            return

        if name in self.input_ports:
            if isinstance(value, (Operator, OutputRef)):
                self.connect_from(value, input_name=name)
            else:
                self.values[name] = _coerce(value, self.input_ports[name])
            return

        raise AttributeError(
            f"{type(self).__name__} has no writable input {name!r}; "
            f"available inputs: {', '.join(self.input_ports) or 'none'}"
        )

    def __getattr__(self, name: str) -> Any:
        if name in self.input_ports:
            return InputRef(self, name)
        if name in self.output_ports:
            return OutputRef(self, name)
        raise AttributeError(f"{type(self).__name__} has no port {name!r}")

    # -- connections ----------------------------------------------------

    def connect_from(
        self,
        source: Operator | OutputRef,
        *,
        input_name: str | None = None,
        output: str | None = None,
    ) -> Operator:
        """Connect ``source`` to one of this operator's inputs."""
        source_operator, output_name = _resolve_source(source, output)
        if output_name not in source_operator.output_ports:
            raise AttributeError(f"{source_operator!r} has no output {output_name!r}")

        input_name = input_name or self._free_input_for(source_operator.output_ports[output_name].type)
        if input_name not in self.input_ports:
            raise AttributeError(f"{self!r} has no input {input_name!r}")

        self.links = [link for link in self.links if link.input != input_name]
        self.links.append(_Link(source_operator, output_name, input_name))
        return self

    def _free_input_for(self, value_type: str) -> str:
        candidates = [name for name, port in self.input_ports.items() if port.type == value_type]
        if not candidates:
            candidates = list(self.input_ports)
        if not candidates:
            raise TypeError(f"{self!r} has no inputs to connect to")

        connected = {link.input for link in self.links}
        for name in candidates:
            if name not in connected:
                return name
        raise TypeError(f"{self!r} already has every {value_type!r} input connected; connect an explicit port instead")

    @property
    def default_output(self) -> OutputRef:
        if len(self.output_ports) != 1:
            raise TypeError(
                f"{self!r} has {len(self.output_ports)} outputs; use an explicit one such as source.output_name"
            )
        return OutputRef(self, next(iter(self.output_ports)))

    def __rshift__(self, other: Operator | InputRef):
        return _connect(self, other)

    def __repr__(self) -> str:
        label = self.label or type(self).__name__
        if not self.values:
            return label
        params = ", ".join(f"{key}={value!r}" for key, value in self.values.items())
        return f"{label}({params})"


def _connect(source: Operator | OutputRef, target: Operator | InputRef) -> Operator:
    if isinstance(target, InputRef):
        target.owner.connect_from(source, input_name=target.name)
        return target.owner
    if isinstance(target, Operator):
        target.connect_from(source)
        return target
    raise TypeError(f"Can't connect {source!r} to {target!r}")


def _resolve_source(source: Operator | OutputRef, output: str | None) -> tuple[Operator, str]:
    if isinstance(source, OutputRef):
        return source.owner, output or source.name
    if isinstance(source, Operator):
        return source, output or source.default_output.name
    raise TypeError(f"Expected an operator or output, got {source!r}")


def _coerce(value: Any, port: Port) -> Any:
    if port.type == "path":
        return _coerce_path(value)
    if isinstance(value, Path):
        return str(value)
    if port.type == "string":
        return value if isinstance(value, str) else str(value)
    if port.type == "float":
        return float(value)
    if port.type == "int":
        return int(value)
    if port.type == "bool":
        return bool(value)
    if port.type in {"vec2", "int2", "color", "vec4"}:
        if isinstance(value, dict):
            return value
        components = tuple(value)
        if port.type == "vec2":
            x, y = components
            return {"X": float(x), "Y": float(y)}
        if port.type == "int2":
            x, y = components
            return {"X": int(x), "Y": int(y)}
        x, y, z, *rest = components
        return {
            "X": float(x),
            "Y": float(y),
            "Z": float(z),
            "W": float(rest[0]) if rest else 1.0,
        }
    return value


def _coerce_path(value: Any) -> str:
    """Resolve existing local files; leave TiXL resource paths untouched.

    TiXL resolves relative paths against its own working directory, so local
    files are made absolute here. Resource paths such as
    ``Examples:images/t3-logo-alpha.png`` do not exist on disk and pass through.
    """
    path = Path(value).expanduser()
    if path.is_file():
        return str(path.resolve())
    return str(value)


def _coerce_position(value: Any) -> tuple[float, float]:
    x, y = value
    return float(x), float(y)


class LoadImage(Operator):
    """Load an image from a file path or a TiXL resource path."""

    symbol = "LoadImage"
    input_ports: ClassVar[dict[str, Port]] = {
        "path": Port("Path", "path"),
        "cache_resources": Port("CacheResources", "bool"),
    }
    output_ports: ClassVar[dict[str, Port]] = {"texture": Port("Texture", "texture")}

    def __init__(self, path: str | Path | None = None, **params: Any):
        if path is not None:
            params = {"path": path, **params}
        super().__init__(**params)


class AsciiRender(Operator):
    """Render an image as ASCII characters."""

    symbol = "AsciiRender"
    input_ports: ClassVar[dict[str, Port]] = {
        "image": Port("ImageA", "texture"),
        "fill": Port("Fill", "color"),
        "background": Port("Background", "color"),
        "mix_in_colors": Port("MixInColors", "float"),
        "scale_factor": Port("ScaleFactor", "float"),
        "offset": Port("Offset", "vec2"),
        "font_char_size": Port("FontCharSize", "int2"),
        "gain_and_bias": Port("GainAndBias", "vec2"),
        "randomize": Port("Randomize", "float"),
        "font_file_path": Port("FontFilePath", "path"),
        "filter_characters": Port("FilterCharacters", "string"),
        "generate_mips": Port("GenerateMips", "bool"),
        "resolution": Port("Resolution", "int2"),
    }
    output_ports: ClassVar[dict[str, Port]] = {"texture": Port("Output", "texture")}
