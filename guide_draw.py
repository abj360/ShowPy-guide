#!/usr/bin/env python3

"""
guide_draw.py --- draws pictures of library results from inside the guide's code snippets

A snippet calls one of these functions, for example `sketch.points(pts)`; the picture is saved
under figures/snippets and appears under the snippet's output in the PDF. Run outside the
build, the functions still save the PNG and print nothing, so snippets stay runnable.

Contains:
    Sketch: draws points, curves, moves, plots, sheets and engine frames as figure files
    sketch: the shared Sketch the snippets use
"""

import io
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import matplotlib as mpl

mpl.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.figure import Figure
from PIL import Image, ImageDraw
from showpy.choreo.engine import PathEngine
from showpy.core.units import facing_vector
from showpy.export.video import render_frame
from showpy.sheet.render import SheetCanvas, render_sheet

SNIPPET_DIR = Path(__file__).resolve().parent / "figures" / "snippets"
DPI = 150
COLORS = ("#2c7fb8", "#c0392b", "#2e8b57", "#e08e0b", "#7b4ea3", "#888888", "#17becf")
TICK_SHARE = 0.06
FRAME_MARGIN_M = 3.0
FRAME_PX_PER_M = 14.0
FRAME_GAP_PX = 10
LABEL_PX = 24


@dataclass
class Sketch:
    """Saves pictures of snippet results and remembers them for the guide build.

    Attributes:
        prefix: File name stem for the next pictures; the build sets it per snippet.
        pending: (path, caption) pairs drawn since the build last collected them.
        count: Pictures drawn under the current prefix.
    """

    prefix: str = "scratch"
    pending: list[tuple[Path, str]] = field(default_factory=list)
    count: int = 0

    def start(self, prefix: str) -> None:
        """Begins naming pictures for a new snippet."""
        self.prefix, self.count = prefix, 0

    def collect(self) -> list[tuple[Path, str]]:
        """Returns and forgets the pictures drawn since the last call."""
        done, self.pending = self.pending, []
        return done

    def _path(self) -> Path:
        SNIPPET_DIR.mkdir(parents=True, exist_ok=True)
        self.count += 1
        return SNIPPET_DIR / f"{self.prefix}-{self.count}.png"

    def _keep(self, fig: Figure, caption: str) -> None:
        path = self._path()
        fig.tight_layout()
        fig.savefig(path, dpi=DPI)
        plt.close(fig)
        self.pending.append((path, caption))

    def points(
        self,
        *groups: Any,
        labels: tuple[str, ...] = (),
        curves: tuple[Any, ...] = (),
        facings: tuple[Any, ...] = (),
        numbered: bool = False,
        caption: str = "",
    ) -> None:
        """Draws point groups (N, 2), optional curves under them and optional facing ticks."""
        fig, ax = plt.subplots(figsize=(5.4, 3.2))
        for curve in curves:
            dense = curve.point_at(np.linspace(0.0, curve.length(), 400))
            ax.plot(dense[:, 0], dense[:, 1], color="#bbbbbb", lw=2.0, zorder=1)
        span = 1.0
        for i, group in enumerate(groups):
            pts = np.asarray(group, dtype=float).reshape(-1, 2)
            span = max(span, float(np.ptp(pts, axis=0).max()) if len(pts) > 1 else 1.0)
            label = labels[i] if i < len(labels) else None
            ax.plot(pts[:, 0], pts[:, 1], "o", color=COLORS[i % len(COLORS)], ms=5, label=label)
            if numbered:
                for k, (x, y) in enumerate(pts):
                    ax.annotate(str(k), (x, y), textcoords="offset points", xytext=(3, 3), size=7)
        for i, angles in enumerate(facings):
            pts = np.asarray(groups[i], dtype=float).reshape(-1, 2)
            for (x, y), theta in zip(pts, angles, strict=True):
                fx, fy = facing_vector(float(theta))
                tick = TICK_SHARE * span
                ax.plot([x, x + fx * tick], [y, y + fy * tick], color="black", lw=1.1)
        if labels:
            ax.legend(fontsize=7, frameon=False)
        ax.set_aspect("equal", adjustable="datalim")
        ax.grid(color="#eeeeee")
        ax.set_xlabel("x (m)")
        ax.set_ylabel("y (m)")
        self._keep(fig, caption or "The points the snippet computed, in meters.")

    def moves(self, starts: Any, targets: Any, caption: str = "") -> None:
        """Draws straight moves from starts (dots) to targets (squares)."""
        a, b = np.asarray(starts, dtype=float), np.asarray(targets, dtype=float)
        fig, ax = plt.subplots(figsize=(5.0, 3.2))
        for i, (p, q) in enumerate(zip(a, b, strict=True)):
            color = COLORS[i % len(COLORS)]
            ax.annotate("", q, p, arrowprops={"arrowstyle": "-|>", "color": color, "lw": 1.2})
            ax.plot(*p, "o", color=color, ms=5)
            ax.plot(*q, "s", color=color, mfc="white", ms=6)
        ax.set_aspect("equal", adjustable="datalim")
        ax.grid(color="#eeeeee")
        self._keep(fig, caption or "Straight moves from start (dot) to target (square).")

    def plot(
        self,
        x: Any,
        *ys: Any,
        labels: tuple[str, ...] = (),
        xlabel: str = "",
        ylabel: str = "",
        caption: str = "",
    ) -> None:
        """Draws one or more y series against x."""
        fig, ax = plt.subplots(figsize=(5.4, 2.8))
        for i, y in enumerate(ys):
            label = labels[i] if i < len(labels) else None
            ax.plot(x, y, color=COLORS[i % len(COLORS)], lw=1.5, label=label)
        if labels:
            ax.legend(fontsize=7, frameon=False)
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        ax.grid(color="#eeeeee")
        self._keep(fig, caption or "The values the snippet computed.")

    def sheet(self, sheet: Any, px_per_m: float = 8.0, caption: str = "") -> None:
        """Saves render_sheet()'s PNG of a sheet."""
        path = self._path()
        path.write_bytes(render_sheet(sheet, "png", px_per_m=px_per_m))
        self.pending.append((path, caption or f"render_sheet() of {sheet.ref}."))

    def frames(
        self, show: Any, counts: tuple[float, ...], crop: Any = None, caption: str = ""
    ) -> None:
        """Renders the show with render_frame() at several global counts, side by side."""
        engine = PathEngine(show)
        canvas = crop or _fit(show, engine, counts)
        images = [render_frame(show, engine.sample(t), canvas) for t in counts]
        width, height = images[0].size
        pitch = width + FRAME_GAP_PX
        strip = Image.new("RGB", (pitch * len(images) - FRAME_GAP_PX, height + LABEL_PX), "white")
        draw = ImageDraw.Draw(strip)
        for i, (t, image) in enumerate(zip(counts, images, strict=True)):
            strip.paste(image, (i * pitch, LABEL_PX))
            draw.text((i * pitch + 4, 4), f"count {t:g}", fill="black", font_size=16)
        path = self._path()
        strip.save(path)
        shown = ", ".join(f"{t:g}" for t in counts)
        self.pending.append((path, caption or f"render_frame() at counts {shown}."))

    def image(self, data: bytes, caption: str = "") -> None:
        """Saves PNG bytes the library produced."""
        path = self._path()
        Image.open(io.BytesIO(data)).save(path)
        self.pending.append((path, caption or "The image the library returned."))


def _fit(show: Any, engine: PathEngine, counts: tuple[float, ...]) -> SheetCanvas:
    pts = np.array([engine.positions(t) for t in counts]).reshape(-1, 2)
    lo, hi = pts.min(axis=0) - FRAME_MARGIN_M, pts.max(axis=0) + FRAME_MARGIN_M
    side = max(hi - lo)
    px = min(FRAME_PX_PER_M, 520.0 / max(side, 1.0))
    return SheetCanvas(
        min_x=float(lo[0]), min_y=float(lo[1]), max_x=float(hi[0]), max_y=float(hi[1]), px_per_m=px
    )


sketch = Sketch()
