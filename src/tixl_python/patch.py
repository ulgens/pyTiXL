"""
Declarative patches for TiXL.
"""

from __future__ import annotations

import atexit
import contextlib
import copy
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Any, ClassVar

from tixl_python.capture import (
    Capture,
    capture_graph,
    capture_output,
    resolve_capture_paths,
)
from tixl_python.client import TixlClient, TixlError
from tixl_python.config import (
    DEFAULT_PORT,
    PROJECT_CREATE_TIMEOUT_SECONDS,
)
from tixl_python.editor import EditorSession
from tixl_python.operators import Operator

log = logging.getLogger(__name__)

__all__ = (
    "Patch",
    "PatchMeta",
)


class PatchMeta(type):
    """Collect operators declared as class attributes."""

    def __new__(mcls, name: str, bases: tuple[type, ...], namespace: dict[str, Any]):
        cls = super().__new__(mcls, name, bases, namespace)

        declared: dict[str, Operator] = {}
        for base in bases:
            declared.update(getattr(base, "_declared_nodes", {}))
        for key, value in namespace.items():
            if isinstance(value, Operator):
                object.__setattr__(value, "label", key)
                declared[key] = value

        cls._declared_nodes = declared
        return cls


class Patch(metaclass=PatchMeta):
    """A patch made of operators, built in TiXL on demand.

    Operators can be declared as class attributes and connected with ``>>``::

        class MyPatch(Patch):
            image = LoadImage("Examples:images/t3-logo-alpha.png")
            ascii = AsciiRender()
            image >> ascii

        patch = MyPatch()
        patch.screenshot("out")

    They can also be created procedurally with :meth:`add`::

        patch = Patch()
        image = patch.add(LoadImage("..."), "image")
        ascii = patch.add(AsciiRender(), "ascii")
        ascii.image = image

    Building happens lazily on the first call to :meth:`build` or
    :meth:`screenshot`. Use the patch as a context manager to ensure a TiXL
    instance launched by it is shut down again.
    """

    _declared_nodes: ClassVar[dict[str, Operator]] = {}

    def __init__(
        self,
        *,
        project: str | None = None,
        name: str | None = None,
        namespace: str | None = None,
        clean: bool | None = None,
        port: int = DEFAULT_PORT,
        executable: str | Path | None = None,
        window: str | None = None,
        session: EditorSession | None = None,
        keep_open: bool = False,
    ):
        self._project_hint = project
        self._name = name
        self._namespace = namespace
        self._clean = clean
        self._keep_open = keep_open

        self._owns_session = session is None
        self._session = session or EditorSession(
            port=port,
            executable=executable,
            window=window,
        )

        self._nodes: dict[str, Operator] = {}
        self._output: Operator | None = None
        self._built = False
        self._child_ids: dict[str, str] = {}

        self.project: str | None = None
        self.created = False
        self.removed_nodes = 0

        self._copy_declared_nodes()
        self.setup()

        atexit.register(self.close)

    # -- definition -----------------------------------------------------

    def setup(self) -> None:
        """Hook for procedural patches; override in subclasses."""

    def _copy_declared_nodes(self) -> None:
        declared = type(self)._declared_nodes
        if not declared:
            return

        copied = copy.deepcopy(tuple(declared.values()))
        for name, node in zip(declared, copied, strict=True):
            self.add(node, name)

    def add(self, operator: Operator, name: str | None = None) -> Operator:
        """Add an operator to the patch and return it."""
        if not isinstance(operator, Operator):
            raise TypeError(f"Expected an Operator, got {operator!r}")

        name = name or self._unique_name(operator)
        if name in self._nodes:
            raise ValueError(f"An operator named {name!r} already exists")

        operator.label = name
        self._nodes[name] = operator
        object.__setattr__(self, name, operator)
        return operator

    def _unique_name(self, operator: Operator) -> str:
        base = re.sub(r"(?<!^)(?=[A-Z])", "_", type(operator).__name__).lower()
        name = base
        index = 2
        while name in self._nodes:
            name = f"{base}_{index}"
            index += 1
        return name

    def set_output(self, operator: Operator | str | None) -> Patch:
        """Choose which operator is pinned to the output window."""
        if operator is None:
            self._output = None
            return self

        if isinstance(operator, str):
            try:
                operator = self._nodes[operator]
            except KeyError as error:
                raise KeyError(f"No operator named {operator!r}") from error

        self._require_registered(operator)
        self._output = operator
        return self

    @property
    def nodes(self) -> dict[str, Operator]:
        """The patch operators, keyed by their attribute name."""
        return dict(self._nodes)

    @property
    def output(self) -> Operator | None:
        """The explicitly chosen output, or the last sink in the patch."""
        if self._output is not None:
            return self._output
        sinks = self._sinks()
        return sinks[-1] if sinks else None

    def _sinks(self) -> list[Operator]:
        sources = {id(link.source) for node in self._nodes.values() for link in node.links}
        sinks = [node for node in self._nodes.values() if id(node) not in sources]
        return sinks or list(self._nodes.values())

    def _require_registered(self, operator: Operator) -> None:
        name = operator.label
        if name not in self._nodes or self._nodes[name] is not operator:
            raise ValueError(f"{operator!r} is not part of this patch; add it first")

    # -- building -------------------------------------------------------

    def build(self) -> Patch:
        """Create the project in TiXL and materialize the patch."""
        if self._built:
            return self
        if not self._nodes:
            raise RuntimeError("The patch has no operators")

        client = self._session.open()
        self.project, self.created = self._open_project(client)

        should_clean = (self.created and self._clean is not False) or self._clean is True
        if should_clean:
            self.removed_nodes = _clean_composition(client)

        self._child_ids = self._add_operators(client)
        self._apply_values(client)
        self._apply_connections(client)
        client.pump(10)

        # The debug bridge edits the symbol directly, which does not notify the
        # MagGraph view. Reopening makes it rebuild its layout from the symbol.
        log.info("Refreshing the graph view...")
        with contextlib.suppress(TixlError):
            client.call("openProject", timeout=180, name=self.project)
            client.pump(30)

        self._layout(client)
        self._pin_output(client)

        self._built = True
        return self

    def _open_project(self, client: TixlClient) -> tuple[str, bool]:
        if self._project_hint:
            log.info("Opening existing project: %s", self._project_hint)
            client.call("openProject", timeout=120, name=self._project_hint)
            client.pump(30)
            return self._project_hint, False

        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        short_name = self._name or f"{self._default_name()}_{stamp}"
        namespace = self._namespace or f"user.{short_name}"

        log.info("Creating project: %s (compiling, this can take a while)", namespace)
        created = client.call(
            "newProject",
            timeout=PROJECT_CREATE_TIMEOUT_SECONDS,
            name=namespace,
        )
        display_name = created.get("displayName") or short_name
        log.info("Opening created project: %s", display_name)
        client.call("openProject", timeout=120, name=display_name)
        client.pump(45)
        return display_name, True

    def _default_name(self) -> str:
        return re.sub(r"(?<!^)(?=[A-Z])", "_", type(self).__name__).lower()

    def _add_operators(self, client: TixlClient) -> dict[str, str]:
        child_ids: dict[str, str] = {}
        for name, node in self._nodes.items():
            if not node.symbol:
                raise RuntimeError(f"{type(node).__name__} has no TiXL symbol name")
            params: dict[str, Any] = {"symbolName": node.symbol}
            if node.position is not None:
                params["posX"], params["posY"] = node.position
            log.info("Adding %s (%s)...", name, node.symbol)
            child_ids[name] = client.call("addOp", **params)["childId"]
        return child_ids

    def _apply_values(self, client: TixlClient) -> None:
        for name, node in self._nodes.items():
            for alias, value in node.values.items():
                port = node.input_ports[alias]
                log.info("  %s.%s = %r", name, alias, value)
                client.call(
                    "setInput",
                    childId=self._child_ids[name],
                    inputName=port.name,
                    value=value,
                )

    def _apply_connections(self, client: TixlClient) -> None:
        for name, node in self._nodes.items():
            for link in node.links:
                self._require_registered(link.source)
                source_port = link.source.output_ports[link.output].name
                target_port = node.input_ports[link.input].name
                log.info(
                    "Connecting %s.%s -> %s.%s...",
                    link.source.label,
                    source_port,
                    name,
                    target_port,
                )
                client.call(
                    "connect",
                    sourceChildId=self._child_ids[link.source.label],
                    sourceOutput=source_port,
                    targetChildId=self._child_ids[name],
                    targetInput=target_port,
                )

    def _layout(self, client: TixlClient) -> None:
        sink_ids = [self._child_ids[node.label] for node in self._sinks()]
        log.info("Laying out the patch inputs...")
        client.call("select", childIds=sink_ids)
        with contextlib.suppress(TixlError):
            client.call("layoutSelection")
        client.pump(10)

    def _pin_output(self, client: TixlClient) -> None:
        output = self.output
        if output is None:
            return

        with contextlib.suppress(TixlError):
            client.call("openWindow", name="OutputWindow")
        with contextlib.suppress(TixlError):
            client.call("pin", childId=self._child_ids[output.label])
            client.pump(45)

    # -- capture --------------------------------------------------------

    def screenshot(
        self,
        path: str | Path | None = None,
        *,
        target: str = "all",
        crop_scale: str = "auto",
    ) -> Capture:
        """Build the patch if needed and save graph/output screenshots.

        ``path`` may be a directory or a ``.png``/``.jpg`` base path. Passing a
        file path treats it as the output image and writes the graph next to it
        with a ``_graph`` suffix.
        """
        if target not in {"all", "graph", "output"}:
            raise ValueError("target must be 'all', 'graph', or 'output'")
        self.build()

        paths = resolve_capture_paths(path, target=target)
        client = self._session.open()
        child_ids = list(self._child_ids.values())

        graph = None
        if target in {"all", "graph"}:
            graph = capture_graph(
                client,
                paths.graph,
                child_ids,
                crop_scale=crop_scale,
                ui_path=paths.ui,
            )

        output = None
        output_node = self.output
        if target in {"all", "output"} and output_node is not None:
            output = capture_output(
                client,
                paths.output,
                self._child_ids[output_node.label],
            )

        ui = paths.ui if paths.ui.exists() else None
        return Capture(graph=graph, output=output, ui=ui)

    # -- state ----------------------------------------------------------

    def graph_state(self, *, include_defaults: bool = True) -> dict[str, Any]:
        """Return the focused composition's graph state from TiXL."""
        self.build()
        return self._session.open().call(
            "getGraphState",
            includeDefaults=include_defaults,
        )

    @property
    def client(self) -> TixlClient:
        """The underlying debug-bridge client, opening the editor if needed."""
        return self._session.open()

    @property
    def log_path(self) -> Path | None:
        """The editor log file, when this session launched TiXL."""
        return self._session.log_path

    # -- lifecycle ------------------------------------------------------

    def close(self) -> None:
        """Close the TiXL connection, shutting down an editor we launched."""
        if self._owns_session:
            self._session.close(keep_open=self._keep_open)

    def __enter__(self) -> Patch:
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()


def _clean_composition(client: TixlClient) -> int:
    """Delete every existing child so the generated patch is the only content."""
    state = client.call("getGraphState")
    children = state.get("children") or []
    removed = 0
    for child in children:
        child_id = child.get("childId")
        if not child_id:
            continue
        try:
            client.call("deleteOp", childId=child_id)
            removed += 1
        except TixlError as error:
            log.warning("Could not delete %s: %s", child.get("symbolName", child_id), error)
    if removed:
        client.pump(20)
    return removed
