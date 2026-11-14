#!/usr/bin/env python3

"""
t10_export.py --- tutorial step 10: renders frames and a video, prints sheets and exports data

Contains:
    FIGURES: names the folder the rendered frames are written to
    save_frames(): renders the tutorial show at several counts and tiles them in a grid
    main(): renders, exports and prints a summary of every output
"""

from pathlib import Path

from PIL import Image, ImageDraw
from showpy.choreo.engine import PathEngine
from showpy.export.data import export_frames_csv, export_json, import_json, to_text
from showpy.export.pdf import to_pdf
from showpy.export.print_sheets import coordinate_sheet, cue_sheet
from showpy.export.video import export_video, render_frame
from showpy.sheet.render import SheetCanvas, render_sheet
from showpy.show.models import Show
from showpy.time.models import Marker, MarkerKind
from showpy.time.timeline import add_marker

from t05_paths import build_tutorial_show
from t08_notes_validate import add_notes

FIGURES = Path(__file__).resolve().parent.parent / "figures"
FRAME_COUNTS = (0.0, 8.0, 16.0, 24.0, 32.0)
FRAME_GAP_PX = 10
GRID_COLUMNS = 3
LABEL_PX = 24
CROP = SheetCanvas(min_x=-16.0, min_y=8.0, max_x=16.0, max_y=36.0, px_per_m=14.0)


def save_frames(show: Show) -> Path:
    """Renders the show at FRAME_COUNTS over a cropped canvas and tiles the frames in a grid."""
    engine = PathEngine(show)
    frames = [render_frame(show, engine.sample(t), CROP) for t in FRAME_COUNTS]
    width, height = frames[0].size
    cell_w, cell_h = width + FRAME_GAP_PX, height + LABEL_PX + FRAME_GAP_PX
    rows = -(-len(frames) // GRID_COLUMNS)
    strip = Image.new("RGB", (cell_w * GRID_COLUMNS, cell_h * rows), "white")
    draw = ImageDraw.Draw(strip)
    for i, (t, frame) in enumerate(zip(FRAME_COUNTS, frames, strict=True)):
        x, y = (i % GRID_COLUMNS) * cell_w, (i // GRID_COLUMNS) * cell_h
        strip.paste(frame, (x, y + LABEL_PX))
        draw.text((x + 4, y + 4), f"count {t:g}", fill="black", font_size=16)
    path = FIGURES / "tutorial_frames.png"
    strip.save(path)
    return path


def main() -> None:
    """Writes the frame strip and the field PNG, then summarizes video, data and print outputs."""
    show = add_notes(build_tutorial_show())
    hit = Marker(label="block hit", at_count=16.0, kind=MarkerKind.REHEARSAL)
    show = show.model_copy(update={"timeline": add_marker(show.timeline, hit)})
    strip = save_frames(show)
    print("frame strip:", strip.name, Image.open(strip).size)
    (FIGURES / "tutorial_field.png").write_bytes(render_sheet(show.sheet, "png", px_per_m=8.0))
    video = export_video(show, (0.0, 4.0), fps=6, px_per_m=4.0)
    print("video:", len(video) > 0, "MP4 box", video[4:8])
    document = export_json(show)
    print("json schema:", document["schema"], "round trip equal:", import_json(document) == show)
    print("\n".join(export_frames_csv(show).splitlines()[:3]))
    print(to_text(coordinate_sheet(show, "T4", precision=0.1)))
    print(to_text(cue_sheet(show)))
    print("coordinate sheet PDF starts with", to_pdf(coordinate_sheet(show, "T4"))[:8])


if __name__ == "__main__":
    main()
