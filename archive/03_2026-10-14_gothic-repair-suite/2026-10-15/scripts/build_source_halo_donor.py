"""Build a deterministic halo candidate from the user's 2048 source pixels."""
from pathlib import Path

import cv2
import numpy as np


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets" / "references" / "Demiurge_Four_Panel_Restoration_Reference_2048.png"
DESTINATION = ROOT / "outputs" / "Pass7_Anatomy_Cleanup_v6.png"
SELECTION = ROOT / "assets" / "Pass7_v6_Source_Halos_Selection.png"
OUTPUT = ROOT / "assets" / "generated" / "Pass7_v6_Source_Halos_Donor_Candidate.png"


def warp_about_centers(
    source: np.ndarray,
    source_center: tuple[int, int],
    destination_center: tuple[int, int],
    scale: float,
    destination_shape: tuple[int, int],
) -> np.ndarray:
    matrix = np.array(
        [
            [scale, 0.0, destination_center[0] - scale * source_center[0]],
            [0.0, scale, destination_center[1] - scale * source_center[1]],
        ],
        dtype=np.float32,
    )
    return cv2.warpAffine(
        source,
        matrix,
        (destination_shape[1], destination_shape[0]),
        flags=cv2.INTER_LANCZOS4,
        borderMode=cv2.BORDER_REFLECT_101,
    )


def match_range(donor: np.ndarray, destination: np.ndarray, mask: np.ndarray) -> np.ndarray:
    chosen = mask > 0
    source_values = donor[chosen].astype(np.float32)
    destination_values = destination[chosen].astype(np.float32)
    source_low, source_high = np.percentile(source_values, (4, 96))
    dest_low, dest_high = np.percentile(destination_values, (4, 96))
    scale = (dest_high - dest_low) / max(source_high - source_low, 1.0)
    matched = (donor.astype(np.float32) - source_low) * scale + dest_low
    return np.clip(matched, 0, 255).astype(np.uint8)


def radial_mask(
    shape: tuple[int, int], center: tuple[int, int], inner: int, outer: int
) -> np.ndarray:
    yy, xx = np.ogrid[: shape[0], : shape[1]]
    distance_sq = (xx - center[0]) ** 2 + (yy - center[1]) ** 2
    return ((distance_sq >= inner**2) & (distance_sq <= outer**2)).astype(np.uint8) * 255


def main() -> None:
    source = cv2.imread(str(SOURCE), cv2.IMREAD_GRAYSCALE)
    destination = cv2.imread(str(DESTINATION), cv2.IMREAD_GRAYSCALE)
    selection = cv2.imread(str(SELECTION), cv2.IMREAD_GRAYSCALE)
    if source is None or destination is None or selection is None:
        raise FileNotFoundError("Source, destination, or halo selection is missing")

    shape = destination.shape
    upper_mask = cv2.bitwise_and(selection, radial_mask(shape, (529, 130), 34, 86))
    lower_mask = cv2.bitwise_and(selection, radial_mask(shape, (459, 207), 30, 91))

    upper = warp_about_centers(source, (858, 214), (529, 130), 0.905, shape)
    lower = warp_about_centers(source, (752, 340), (459, 207), 0.758, shape)
    upper = match_range(upper, destination, upper_mask)
    lower = match_range(lower, destination, lower_mask)

    candidate = destination.copy()
    candidate[upper_mask > 0] = upper[upper_mask > 0]
    # The radiating halo is foreground of the upper ring in the source.
    candidate[lower_mask > 0] = lower[lower_mask > 0]
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(OUTPUT), candidate, [cv2.IMWRITE_PNG_COMPRESSION, 3])
    print(OUTPUT)


if __name__ == "__main__":
    main()
