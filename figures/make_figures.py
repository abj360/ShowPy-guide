#!/usr/bin/env python3

"""
make_figures.py --- draws the study guide's figures with ShowPy and matplotlib

Every number plotted comes from the library itself. Run from the repository root:

    uv run python figures/make_figures.py

Contains:
    FIGURES: lists every figure function, in the order they are drawn
    main(): draws every figure into figures
"""

import io
import math
from collections.abc import Callable
from pathlib import Path
from unittest import mock

import matplotlib as mpl

mpl.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import showpy.choreo.engine as engine_module
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from matplotlib.patches import Circle, FancyArrowPatch, FancyBboxPatch, Rectangle
from PIL import Image
from showpy.choreo.engine import PathEngine
from showpy.choreo.engine_compile import plan_progress
from showpy.choreo.forms import (
    arc_form,
    circle_form,
    generated_form,
    slot_poses,
    wedge_form,
)
from showpy.choreo.match import match, match_by_order
from showpy.choreo.models import (
    Easing,
    FacingMode,
    FacingSpec,
    MatchOptions,
    PathRow,
    PathStyle,
    Placement,
    Set,
    Waypoint,
)
from showpy.choreo.motion import DEFAULT_MOTIONS, ease
from showpy.choreo.routes import counter_march, follow_and_set_targets, make_route
from showpy.core.units import facing_vector
from showpy.examples import crossing_show, two_set_show, with_rows
from showpy.geo.affine import mirror_matrix, skew_matrix, transform_facing, transform_points
from showpy.geo.regions import region
from showpy.geo.shapes import bezier, curve_through, spiral, text_outline
from showpy.geo.spacing import (
    _bridson,
    block,
    concentric,
    distribute_on_points,
    fill,
    space_proportional,
)
from showpy.geo.svg import parse_path
from showpy.sheet.render import render_sheet
from showpy.sheet.templates import get_sheet
from showpy.time.clock import count_to_seconds, tempo_at
from showpy.time.models import Hold, TempoSection, Timeline, TimelineMode

OUT = Path(__file__).resolve().parent
DPI = 160
BLUE, RED, GREEN, GREY, ORANGE, PURPLE = (
    "#2c7fb8",
    "#c0392b",
    "#2e8b57",
    "#888888",
    "#e08e0b",
    "#7b4ea3",
)
SERIES = (BLUE, RED, GREEN, ORANGE, PURPLE, GREY, "#17becf", "#8c564b")
TICK = 0.45


def _style() -> None:
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 8.5,
            "axes.titlesize": 9.5,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.grid": True,
            "grid.color": "#e4e4e4",
            "grid.linewidth": 0.6,
            "legend.frameon": False,
            "legend.fontsize": 7.5,
        }
    )


def _save(fig: Figure, name: str) -> None:
    fig.tight_layout()
    fig.savefig(OUT / name, dpi=DPI)
    plt.close(fig)
    print(f"Drew {name}")


def _equal(ax: Axes) -> None:
    ax.set_aspect("equal", adjustable="datalim")


def _facing_ticks(ax: Axes, pts: np.ndarray, facings: list[float], color: str = "k") -> None:
    for (x, y), theta in zip(pts, facings, strict=True):
        fx, fy = facing_vector(theta)
        ax.plot([x, x + fx * TICK], [y, y + fy * TICK], color=color, lw=1.2)


def packages() -> None:
    """Draws the package layers and the direction of imports."""
    fig, ax = plt.subplots(figsize=(7.2, 3.9))
    ax.axis("off")
    layers = [
        ("core", "errors · ids · types · units · util · selection · validation", 0),
        ("geo", "curves · svg · shapes · spacing · affine · transforms · measure", 1),
        ("time", "timeline · clock · measures · validate", 1),
        ("cast", "groups · spots · select · rewrite", 2),
        ("sheet", "templates · coords · bounds · render", 2),
        ("notes", "anchors · notes · drafts", 2),
        ("choreo", "sets · forms · match · paths · motion · PathEngine · avoid", 3),
        ("show", "Show · manage · storage · history · collab · validate", 4),
        ("export", "video · print · data · pdf · publish", 5),
    ]
    rows: dict[int, list[tuple[str, str]]] = {}
    for name, detail, level in layers:
        rows.setdefault(level, []).append((name, detail))
    centers: dict[str, tuple[float, float]] = {}
    for level, items in rows.items():
        width = 10.0 / len(items)
        for i, (name, detail) in enumerate(items):
            x0, y0 = i * width + 0.12, level * 1.0
            ax.add_patch(
                FancyBboxPatch(
                    (x0, y0),
                    width - 0.24,
                    0.62,
                    boxstyle="round,pad=0.02,rounding_size=0.08",
                    fc="#eef3f8" if name != "choreo" else "#fdf1e3",
                    ec=BLUE,
                    lw=1.0,
                )
            )
            ax.text(x0 + 0.1, y0 + 0.42, name, weight="bold", fontsize=9, va="center")
            ax.text(x0 + 0.1, y0 + 0.17, detail, fontsize=6.0, va="center", color="#333")
            centers[name] = (x0 + (width - 0.24) / 2, y0)
    for upper, lower in [
        ("export", "show"),
        ("show", "choreo"),
        ("choreo", "cast"),
        ("choreo", "sheet"),
        ("choreo", "notes"),
        ("cast", "geo"),
        ("sheet", "geo"),
        ("geo", "core"),
        ("time", "core"),
    ]:
        (ux, uy), (lx, ly) = centers[upper], centers[lower]
        ax.add_patch(
            FancyArrowPatch(
                (ux, uy), (lx, ly + 0.62), arrowstyle="-|>", mutation_scale=8, color=GREY, lw=0.8
            )
        )
    ax.set_xlim(0, 10)
    ax.set_ylim(-0.1, 5.75)
    ax.text(10, 5.7, "arrows point from importer to imported", ha="right", fontsize=7, color=GREY)
    _save(fig, "fig_packages.png")


def coordinates() -> None:
    """Draws the stage-plane axes, the origin at front-center and four facings."""
    fig, ax = plt.subplots(figsize=(6.6, 3.6))
    w, d = 20.0, 12.0
    ax.add_patch(Rectangle((-w / 2, 0), w, d, fc="#f6f4ee", ec="k", lw=1))
    ax.annotate("", (3.5, 0), (0, 0), arrowprops={"arrowstyle": "-|>", "color": RED, "lw": 1.5})
    ax.annotate("", (0, 3.5), (0, 0), arrowprops={"arrowstyle": "-|>", "color": RED, "lw": 1.5})
    ax.text(3.6, 0.3, "+x (audience right)", color=RED, fontsize=7.5)
    ax.text(0.25, 3.6, "+y (upstage, away\nfrom the audience)", color=RED, fontsize=7.5)
    ax.plot(0, 0, "o", color=RED)
    ax.text(0.2, -0.9, "origin (0, 0) = front-center", color=RED, fontsize=7.5)
    ax.text(0, -2.4, "AUDIENCE", ha="center", weight="bold", color=GREY)
    ax.text(-w / 2, d + 0.3, f"x from -width/2 = {-w / 2:g}", fontsize=7.5)
    ax.text(w / 2, d + 0.3, f"to +width/2 = {w / 2:g}", fontsize=7.5, ha="right")
    for theta, (x, y) in zip(
        (0, 90, 180, 270), ((-7, 9), (-2.5, 9), (2.5, 9), (7, 9)), strict=True
    ):
        fx, fy = facing_vector(theta)
        ax.plot(x, y, "o", color=BLUE, ms=9)
        ax.annotate(
            "", (x + 1.6 * fx, y + 1.6 * fy), (x, y), arrowprops={"arrowstyle": "-|>", "lw": 1.4}
        )
        ax.text(
            x,
            y - 2.4,
            f"facing {theta}°\nvector ({fx + 0.0:.0f}, {fy + 0.0:.0f})",
            ha="center",
            fontsize=7,
        )
    ax.set_xlim(-11, 11)
    ax.set_ylim(-3, 13.5)
    ax.set_aspect("equal")
    ax.grid(False)
    _save(fig, "fig_coordinates.png")


def angles() -> None:
    """Compares the facing convention with the math convention used for arcs."""
    fig, axes = plt.subplots(1, 2, figsize=(6.8, 3.3))
    for ax, title, fn in (
        (axes[0], "Facing: 0° = toward audience (-y), CCW", facing_vector),
        (
            axes[1],
            "Arc angle: 0° = +x, CCW (math)",
            lambda a: (math.cos(math.radians(a)), math.sin(math.radians(a))),
        ),
    ):
        ax.add_patch(Circle((0, 0), 1, fill=False, color=GREY, lw=0.8))
        for a in (0, 45, 90, 180, 270):
            vx, vy = fn(a)
            ax.annotate("", (vx, vy), (0, 0), arrowprops={"arrowstyle": "-|>", "color": BLUE})
            ax.text(1.22 * vx, 1.22 * vy, f"{a}°", ha="center", va="center", fontsize=8)
        ax.set_title(title, fontsize=8.5)
        ax.set_xlim(-1.5, 1.5)
        ax.set_ylim(-1.5, 1.5)
        ax.set_aspect("equal")
        ax.text(0, -1.45, "audience ↓", ha="center", fontsize=7, color=GREY)
    _save(fig, "fig_angles.png")


def arclength() -> None:
    """Shows Bézier samples at even native t versus even arc length s."""
    curve = bezier((0, 0), (0, 5), (1, 5), (7, 0))
    t = np.linspace(0, 1, 13)
    native = curve._native(t)
    even = curve.point_at(np.linspace(0, curve.length(), 13))
    fig, axes = plt.subplots(1, 2, figsize=(6.8, 2.6), sharey=True)
    dense = curve.point_at(np.linspace(0, curve.length(), 300))
    for ax, pts, title in (
        (axes[0], native, "13 points at even native t: bunched"),
        (axes[1], even, f"13 points at even arc length (L = {curve.length():.3f} m)"),
    ):
        ax.plot(dense[:, 0], dense[:, 1], color=GREY, lw=1)
        ax.plot(pts[:, 0], pts[:, 1], "o", color=BLUE, ms=4)
        ax.set_title(title, fontsize=8)
        _equal(ax)
    _save(fig, "fig_arclength.png")


def catmull() -> None:
    """Compares uniform, centripetal and chordal Catmull–Rom splines through the same points."""
    pts = ((0, 0), (1, 3), (1.6, 3.1), (5, 0), (6, 2.5))
    fig, ax = plt.subplots(figsize=(6.4, 3.0))
    for alpha, color, name in (
        (0.0, RED, "uniform alpha=0"),
        (0.5, BLUE, "centripetal alpha=0.5 (default)"),
        (1.0, GREEN, "chordal alpha=1"),
    ):
        c = curve_through(*pts, alpha=alpha)
        dense = c.point_at(np.linspace(0, c.length(), 600))
        ax.plot(dense[:, 0], dense[:, 1], color=color, lw=1.3, label=f"{name}: {c.length():.2f} m")
    xs, ys = zip(*pts, strict=True)
    ax.plot(xs, ys, "ks", ms=4, label="points the curve must pass")
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.12), ncol=2)
    _equal(ax)
    _save(fig, "fig_catmull.png")


def subdivision() -> None:
    """Shows to_polyline vertices of a spiral at two chord tolerances."""
    curve = spiral((0, 0), 0.5, 4.0, 2.0)
    fig, axes = plt.subplots(1, 2, figsize=(6.8, 3.2))
    dense = curve.point_at(np.linspace(0, curve.length(), 800))
    for ax, tol in zip(axes, (0.2, 0.02), strict=True):
        poly = curve.to_polyline(tol)
        ax.plot(dense[:, 0], dense[:, 1], color=GREY, lw=2.5, alpha=0.5)
        ax.plot(poly[:, 0], poly[:, 1], "-o", color=BLUE, ms=2.5, lw=0.9)
        ax.set_title(f"tol = {tol} m: {len(poly)} vertices", fontsize=8.5)
        _equal(ax)
    _save(fig, "fig_subdivision.png")


def svg_arcs() -> None:
    """Draws the four SVG arcs that join the same two points with the same radii."""
    fig, ax = plt.subplots(figsize=(5.6, 3.6))
    for (large, sweep), color in zip(((0, 0), (0, 1), (1, 0), (1, 1)), SERIES, strict=False):
        (sub,) = parse_path(f"M 0 0 A 2 1.4 0 {large} {sweep} 3 1")
        piece = sub.pieces[0]
        pts = piece.evaluate(np.linspace(0, 1, 300))
        ax.plot(
            pts[:, 0], pts[:, 1], color=color, lw=1.4, label=f"large-arc={large}, sweep={sweep}"
        )
    ax.plot([0, 3], [0, 1], "ko", ms=4)
    ax.text(0.1, -0.25, "P1 (0, 0)", fontsize=7)
    ax.text(3.1, 1.0, "P2 (3, 1)", fontsize=7)
    ax.legend(loc="upper left", fontsize=7)
    ax.set_title(
        "A 2 1.4 0 <large> <sweep> from P1 to P2 (SVG y down, plotted as stored)", fontsize=8
    )
    _equal(ax)
    _save(fig, "fig_svg_arc.png")


def poisson() -> None:
    """Shows every Bridson sample in an area and the 30 kept by farthest-point selection."""
    area = region([(0, 0), (14, 0), (14, 9), (7, 12), (0, 9)])
    candidates = _bridson(area, 1.5, 0)
    kept = distribute_on_points(candidates, 30)
    fig, ax = plt.subplots(figsize=(5.4, 4.0))
    x, y = area.exterior.xy
    ax.plot(x, y, color="k", lw=1)
    ax.plot(
        candidates[:, 0],
        candidates[:, 1],
        ".",
        color=GREY,
        ms=4,
        label=f"{len(candidates)} Bridson samples (gap ≥ 1.5 m)",
    )
    ax.plot(kept[:, 0], kept[:, 1], "o", color=RED, ms=5, label="30 kept by farthest-point")
    ax.legend(loc="lower center", bbox_to_anchor=(0.5, -0.32), ncol=1)
    _equal(ax)
    _save(fig, "fig_poisson.png")


def spacing() -> None:
    """Shows a block, a hex fill, concentric rings and proportional spacing on letters."""
    fig, axes = plt.subplots(1, 4, figsize=(7.4, 2.4))
    b = block((0, 0), 3, 4, 1.0, facing=30.0)
    axes[0].plot(b[:, 0], b[:, 1], "o", color=BLUE, ms=4)
    axes[0].plot(b[:4, 0], b[:4, 1], "o", color=RED, ms=4)
    axes[0].set_title("block 3 x 4, facing 30°\n(front row red)", fontsize=7.5)
    square = region([(0, 0), (5, 0), (5, 5), (0, 5)])
    h = fill(square, 1.0, "hex")
    axes[1].plot(*square.exterior.xy, color="k", lw=0.8)
    axes[1].plot(h[:, 0], h[:, 1], "o", color=GREEN, ms=3)
    axes[1].set_title(f"fill hex, 1 m: {len(h)} spots", fontsize=7.5)
    for ring, color in zip(concentric((0, 0), [1.0, 2.0, 3.0], [4, 8, 12]), SERIES, strict=False):
        axes[2].plot(ring[:, 0], ring[:, 1], "o", color=color, ms=3.5)
    axes[2].set_title("concentric 4, 8, 12", fontsize=7.5)
    strokes = text_outline("SHOW", "simplex", 3.0, (0, 0))
    for s in strokes:
        axes[3].plot(s.to_polyline()[:, 0], s.to_polyline()[:, 1], color="#cccccc", lw=1)
    for pts in space_proportional(strokes, 48):
        axes[3].plot(pts[:, 0], pts[:, 1], "o", color=PURPLE, ms=2.2)
    axes[3].set_title("text_outline + space_proportional\n48 spots", fontsize=7.5)
    for ax in axes:
        _equal(ax)
        ax.tick_params(labelsize=6)
    _save(fig, "fig_spacing.png")


def affine_facing() -> None:
    """Shows facings carried through a skew and a mirror by vector_facing(M · v)."""
    pts = np.array([[x, y] for y in (0.0, 1.5) for x in (0.0, 1.5, 3.0)])
    facings = [0.0, 30.0, 60.0, 90.0, 135.0, 200.0]
    fig, axes = plt.subplots(1, 3, figsize=(7.2, 2.4))
    for ax, (title, m) in zip(
        axes,
        (
            ("original", np.eye(3)),
            ("skew 35° in x", skew_matrix(35.0, 0.0, (0, 0))),
            ("mirror across x = 1.5", mirror_matrix((1.5, 0), (1.5, 1))),
        ),
        strict=True,
    ):
        moved = transform_points(pts, m)
        mapped = [transform_facing(f, m) for f in facings]
        ax.plot(moved[:, 0], moved[:, 1], "o", color=BLUE, ms=7)
        _facing_ticks(ax, moved, mapped, RED)
        for (x, y), f in zip(moved, mapped, strict=True):
            ax.text(x + 0.1, y + 0.25, f"{f:.0f}°", fontsize=6.5)
        ax.set_title(title, fontsize=8.5)
        ax.set_xlim(-1.0, 5.5)
        ax.set_ylim(-1.0, 2.6)
        ax.set_aspect("equal")
    _save(fig, "fig_affine_facing.png")


def tempo_ramp() -> None:
    """Plots tempo and seconds against counts for a ramp followed by a hold."""
    ramp = TempoSection(at_count=0.0, counts_per_minute=120.0, ramp_to=180.0, ramp_counts=32.0)
    steady = TempoSection(at_count=48.0, counts_per_minute=90.0)
    tl = Timeline(
        mode=TimelineMode.COUNTS, tempos=(ramp, steady), holds=(Hold(at_count=40.0, seconds=3.0),)
    )
    counts = np.linspace(0, 64, 641)
    fig, axes = plt.subplots(1, 2, figsize=(7.0, 2.8))
    axes[0].plot(counts, [tempo_at(tl, c) for c in counts], color=BLUE)
    axes[0].set_xlabel("count")
    axes[0].set_ylabel("tempo (counts per minute)")
    axes[0].set_title("ramp 120→180 over 32 counts, 90 from 48", fontsize=8)
    secs = [count_to_seconds(tl, c) for c in counts]
    axes[1].plot(counts, secs, color=RED, label="seconds(count)")
    axes[1].plot(counts, counts * 0.5, color=GREY, ls="--", lw=0.8, label="steady 120 cpm")
    axes[1].axvline(40, color=ORANGE, lw=0.8, ls=":")
    axes[1].text(41, 4, "3 s hold\nat count 40", fontsize=7, color=ORANGE)
    axes[1].set_xlabel("count")
    axes[1].set_ylabel("show seconds")
    axes[1].legend(loc="upper left")
    _save(fig, "fig_tempo.png")


def easings() -> None:
    """Plots every easing kind as distance share against time share."""
    u = np.linspace(0, 1, 801)
    kinds = [
        Easing(kind="linear"),
        Easing(kind="ease_in", strength=2),
        Easing(kind="ease_out", strength=2),
        Easing(kind="ease_in_out", strength=3),
        Easing(kind="hold_then_burst", strength=2),
        Easing(kind="burst_then_settle", strength=3),
        Easing(kind="steps", strength=4),
        Easing(kind="custom", points=((0, 0), (0.3, 0.6), (0.7, 0.6), (1, 1))),
    ]
    fig, axes = plt.subplots(2, 4, figsize=(7.2, 3.8), sharex=True, sharey=True)
    for ax, e in zip(axes.ravel(), kinds, strict=True):
        ax.plot(u, ease(e, u), color=BLUE, lw=1.4)
        ax.plot([0, 1], [0, 1], color=GREY, lw=0.6, ls="--")
        label = e.kind if e.kind in ("linear", "custom") else f"{e.kind} ({e.strength:g})"
        ax.set_title(label, fontsize=7.5)
    for ax in axes[1]:
        ax.set_xlabel("time share u")
    for ax in axes[:, 0]:
        ax.set_ylabel("distance share")
    _save(fig, "fig_easing.png")


def matching() -> None:
    """Compares by-order, min-sum and bottleneck matchings on one small problem."""
    starts = np.array([[4.1, 0.7], [3.5, 0.8], [4.0, 1.2], [3.3, 0.6], [3.0, 0.0]])
    slots = np.array([[3.2, 3.1], [4.4, 3.8], [2.3, 4.4], [2.4, 3.8], [2.1, 4.1]])
    ids = [str(i) for i in range(5)]
    results = (
        (
            "by order",
            match_by_order(
                ids,
                slots,
                Set(
                    id="a",
                    counts=0,
                    placements=tuple(
                        Placement(entity=e, x=float(p[0]), y=float(p[1]))
                        for e, p in zip(ids, starts, strict=True)
                    ),
                ),
            ),
        ),
        ("sum", match(starts, slots, options=MatchOptions(objective="sum", keep_groups=False))),
        (
            "sum_squares",
            match(starts, slots, options=MatchOptions(objective="sum_squares", keep_groups=False)),
        ),
        ("bottleneck_then_sum", match(starts, slots, options=MatchOptions(keep_groups=False))),
    )
    fig, axes = plt.subplots(1, 4, figsize=(7.4, 3.0))
    for ax, (name, r) in zip(axes, results, strict=True):
        targets = r.target_points()
        for i, e in enumerate(r.entities):
            s = starts[int(e)]
            ax.plot([s[0], targets[i][0]], [s[1], targets[i][1]], color=SERIES[int(e)], lw=1.2)
        ax.plot(starts[:, 0], starts[:, 1], "o", color="k", ms=4)
        ax.plot(slots[:, 0], slots[:, 1], "s", mfc="white", mec="k", ms=5)
        ax.set_title(
            f"{name}\nmax {r.max_distance:.2f}, total {r.total_distance:.2f}, "
            f"crossings {r.crossings}",
            fontsize=6.8,
        )
        ax.set_xlim(1.8, 4.7)
        ax.set_ylim(-0.3, 4.7)
        ax.set_aspect("equal")
    _save(fig, "fig_matching.png")


def engine_time() -> None:
    """Plots distance travelled against counts for a delayed, eased move with a timed waypoint."""
    row = PathRow(
        entity="T1",
        style=PathStyle.POLYLINE,
        start=1.0,
        end=7.0,
        waypoints=(Waypoint(x=3.0, y=5.0, at=3.0),),
        easing=Easing(kind="ease_in_out", strength=2),
    )
    show = with_rows({"T1": row})
    plan = PathEngine(show).compile(("1", "2")).plans["T1"]
    tau = np.linspace(0, 8, 801)
    fig, ax = plt.subplots(figsize=(6.4, 2.9))
    ax.plot(
        tau, plan_progress(plan, tau), color=BLUE, lw=1.6, label="arc length s(τ) used for position"
    )
    ax.plot(
        plan.knots_t,
        plan.knots_s,
        "o--",
        color=RED,
        ms=5,
        lw=0.8,
        label="time-map knots (piecewise linear)",
    )
    for k in plan.window:
        ax.axvline(k, color=GREY, lw=0.6, ls=":")
    ax.set_xlabel("local count τ")
    ax.set_ylabel("meters along the path")
    ax.set_title(
        "window 1–7, waypoint at count 3, ease_in_out applied to the whole window", fontsize=8
    )
    ax.legend(loc="upper left")
    _save(fig, "fig_engine_time.png")


def facing_phases() -> None:
    """Plots facing over a transition: before, during (blended) and after the window."""
    a = Placement(entity="T1", x=0.0, y=5.0, facing=0.0)
    row = PathRow(entity="T1", start=2.0, end=6.0, facing_mode=FacingMode.TRAVEL, turn_counts=1.5)
    base = two_set_show()
    first = base.sets[0].with_placements({"T1": a})
    second = base.sets[1].with_placements({"T1": {"x": 4.0, "y": 9.0, "facing": 270.0}})
    show = with_rows({"T1": row}, show=base.model_copy(update={"sets": (first, second)}))
    engine = PathEngine(show)
    tau = np.linspace(0, 8, 641)
    facing = [engine.facing_at("T1", t, local=("1", "2")) for t in tau]
    fig, ax = plt.subplots(figsize=(6.4, 2.6))
    ax.plot(tau, facing, color=BLUE, lw=1.6)
    notes = (
        (1.0, 205, "before:\nprevious facing 0°"),
        (4.0, 205, "during: TRAVEL (135°)\nblended in over 1.5"),
        (7.1, 60, "after: next facing\n270°, blended\nover 1.5"),
    )
    for x, y, text in notes:
        ax.text(x, y, text, ha="center", fontsize=7)
    for k in (2.0, 6.0):
        ax.axvline(k, color=GREY, ls=":", lw=0.8)
    ax.set_ylim(-10, 290)
    ax.set_xlabel("local count τ")
    ax.set_ylabel("facing (degrees)")
    _save(fig, "fig_facing_phases.png")


def segments() -> None:
    """Shows the aliasing bug that easing breaks fixed: steps easing, with and without breaks."""
    row = PathRow(entity="T1", easing=Easing(kind="steps", strength=4))
    show = with_rows({"T1": row})
    tau = np.linspace(0, 8, 801)
    fig, axes = plt.subplots(1, 2, figsize=(7.0, 2.8), sharey=True)
    true_y = [PathEngine(show).position("T1", t, local=("1", "2"))[1] for t in tau]
    for ax, label, patch in (
        (axes[0], "without easing breaks (the old bug)", True),
        (axes[1], "with easing breaks (current)", False),
    ):
        if patch:
            with mock.patch.object(engine_module, "easing_breaks", return_value=[]):
                segs = PathEngine(show).entity_segments("T1", ("1", "2"), tol=0.02)
        else:
            segs = PathEngine(show).entity_segments("T1", ("1", "2"), tol=0.02)
        ax.plot(tau, true_y, color=GREY, lw=3, alpha=0.5, label="true y(τ)")
        xs = [segs[0].t0, *(s.t1 for s in segs)]
        ys = [segs[0].p0[1], *(s.p1[1] for s in segs)]
        ax.plot(xs, ys, "-o", color=RED, ms=3, lw=1, label=f"{len(segs)} segments")
        ax.set_title(label, fontsize=8)
        ax.set_xlabel("local count τ")
        ax.legend(loc="upper left")
    axes[0].set_ylabel("y (m)")
    _save(fig, "fig_segments.png")


def closest() -> None:
    """Draws two moving spots, their positions per count and the closest approach."""
    show = crossing_show()
    engine = PathEngine(show)
    tau = np.linspace(0, 8, 9)
    fig, ax = plt.subplots(figsize=(5.0, 3.4))
    for e, color in (("T1", BLUE), ("T2", RED)):
        pts = np.array([engine.position(e, t, local=("1", "2")) for t in tau])
        ax.plot(pts[:, 0], pts[:, 1], "-o", color=color, ms=3.5, label=f"{e} at counts 0..8")
    ax.plot(2, 7, "*", color="k", ms=12, label="closest approach: count 4, 0 m")
    ax.legend(loc="lower center", bbox_to_anchor=(0.5, -0.42))
    _equal(ax)
    _save(fig, "fig_closest.png")


def routes() -> None:
    """Draws a follow-the-leader route and a counter-march, with every spot's path."""
    show = two_set_show()
    route = make_route(
        show, ("1", "2"), "T4", [(10.0, 9.0), (10.0, 14.0)], ["T4", "T3", "T2", "T1"]
    )
    followed = follow_and_set_targets(show, ("1", "2"), route)
    cm = counter_march(show, ("1", "2"), ["T4", "T3", "T2", "T1"], (10.0, 5.0))
    fig, axes = plt.subplots(1, 2, figsize=(7.0, 2.9))
    for ax, s, title in (
        (axes[0], followed, "follow the leader (T4 leads)"),
        (axes[1], cm, "counter-march, turning at (10, 5)"),
    ):
        engine = PathEngine(s)
        for i, e in enumerate(("T1", "T2", "T3", "T4")):
            g = engine.path_geometry(e, ("1", "2"))
            ax.plot(g[:, 0], g[:, 1], color=SERIES[i], lw=1.2, label=e)
            a, b = s.set("1").get(e).point, s.set("2").get(e).point
            ax.plot(*a, "o", color=SERIES[i], ms=4)
            ax.plot(*b, "s", color=SERIES[i], ms=4, mfc="white")
        ax.set_title(title, fontsize=8)
        _equal(ax)
    axes[0].legend(loc="upper left", ncol=2)
    _save(fig, "fig_routes.png")


def motions() -> None:
    """Draws the four built-in custom motions from (0, 0) to (8, 0)."""
    u = np.linspace(0, 1, 400)
    fig, axes = plt.subplots(1, 4, figsize=(7.4, 2.1))
    for ax, name in zip(axes, ("weave", "zigzag", "figure_eight", "spiral"), strict=True):
        pts = DEFAULT_MOTIONS.get(name)(u, (0.0, 0.0), (8.0, 0.0), {})
        ax.plot(pts[:, 0], pts[:, 1], color=BLUE)
        ax.plot([0, 8], [0, 0], "o", color=RED, ms=3)
        ax.set_title(name, fontsize=8)
        _equal(ax)
    _save(fig, "fig_motions.png")


def forms() -> None:
    """Draws slots and facings of several form kinds."""
    examples = [
        (
            "arc_form, facing normal",
            arc_form("a", [], (0, 0), 5.0, 30.0, 120.0, facing=FacingSpec(mode="normal"), n=7),
        ),
        ("circle_form (outward)", circle_form("c", [], (0, 0), 3.0, n=10)),
        ("wedge_form 90°", wedge_form("w", [], (0, 0), 4.0, 90.0, n=9)),
        ("generated rose", generated_form("r", [], "rose", n=20)),
        ("generated spiral", generated_form("s", [], "spiral", n=14)),
    ]
    fig, axes = plt.subplots(1, 5, figsize=(7.6, 2.0))
    for ax, (title, form) in zip(axes, examples, strict=True):
        pts, facings = slot_poses(form)
        ax.plot(pts[:, 0], pts[:, 1], "o", color=BLUE, ms=3.5)
        _facing_ticks(ax, pts, facings, RED)
        ax.set_title(title, fontsize=7)
        _equal(ax)
        ax.tick_params(labelsize=6)
    _save(fig, "fig_forms.png")


def sheets() -> None:
    """Tiles render_sheet PNGs of the field, the stage and the gym floor."""
    images = [
        Image.open(io.BytesIO(render_sheet(get_sheet(ref), "png", px_per_m=px)))
        for ref, px in (
            ("sheet:hs-football", 6.0),
            ("sheet:proscenium-stage", 26.0),
            ("sheet:gym-basketball", 18.0),
        )
    ]
    height = max(i.size[1] for i in images)
    width = sum(i.size[0] for i in images) + 20 * (len(images) - 1)
    tile = Image.new("RGB", (width, height), "white")
    x = 0
    for i in images:
        tile.paste(i, (x, height - i.size[1]))
        x += i.size[0] + 20
    tile.save(OUT / "fig_sheets.png")
    print("Drew fig_sheets.png")


FIGURES: tuple[Callable[[], None], ...] = (
    packages,
    coordinates,
    angles,
    arclength,
    catmull,
    subdivision,
    svg_arcs,
    poisson,
    spacing,
    affine_facing,
    tempo_ramp,
    easings,
    matching,
    engine_time,
    facing_phases,
    segments,
    closest,
    routes,
    motions,
    forms,
    sheets,
)


def main() -> None:
    """Draws every figure into the figures folder."""
    _style()
    for draw in FIGURES:
        draw()


if __name__ == "__main__":
    main()
