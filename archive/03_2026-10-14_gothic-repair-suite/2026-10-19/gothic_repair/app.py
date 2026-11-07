import argparse
from pathlib import Path

from .ui import run


def main(argv=None):
    parser = argparse.ArgumentParser(description="Launch the Gothic Repair Suite")
    parser.add_argument("--source", type=Path, help="image to open instead of the bundled Pass 7 original")
    parser.add_argument("--mask", type=Path, help="optional mask to preload")
    args = parser.parse_args(argv)
    root = Path.cwd()
    source = args.source or (root / "assets" / "Gothic_Relief_Pass_7_Original.png")
    mask = args.mask or (root / "assets" / "Pass7_Central_Legs_Inpaint_Mask.png")
    raise SystemExit(run(source if source.exists() else None, mask if mask.exists() else None))


if __name__ == "__main__":
    main()
