import argparse
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from tifffile import imread

parser = argparse.ArgumentParser(description="Find CT rotation axis from 0° and 180° projections.")
parser.add_argument("-flats", type=str, help="Path to raw data folder")
parser.add_argument("-darks", type=str, help="Path to raw data folder")
parser.add_argument("-tomo", type=str, help="Path to raw data folder")
parser.add_argument("-SAVE", type=str, help="Path to rec data folder")
parser.add_argument("-shiftmin", type=int, default=-100)
parser.add_argument("-shiftmax", type=int, default=100)
parser.add_argument("-crop", type=int, default=10, help="Pixels to crop from each side (default: 10)")
parser.add_argument("-plot", action="store_true")
args = parser.parse_args()

def find_rotation_axis(proj_0, proj_180, shift_range, crop=10, epsilon=1e-6):
    """
    Search for the rotation axis by minimizing stdev of proj_0 / flipped(proj_180)
    over a range of horizontal shifts.

    Returns best_shift, shifts array, stdevs array.
    """
    proj_180_flipped = np.fliplr(proj_180)

    shifts = np.arange(shift_range[0], shift_range[1] + 1)
    stdevs = np.zeros(len(shifts))

    for i, shift in enumerate(shifts):
        shifted = np.roll(proj_180_flipped, shift, axis=1)
        ratio = proj_0 / (shifted + epsilon)
        stdevs[i] = ratio[:, crop:-crop].std()

    best_shift = shifts[np.argmin(stdevs)]
    return best_shift, shifts, stdevs


def fit_parabola(shifts, stdevs, best_shift, half_window=5):
    """
    Fit a parabola around the minimum for sub-pixel accuracy.
    Returns the sub-pixel shift at the parabola vertex, or falls back to
    the integer best_shift if the fit doesn't produce a proper minimum.
    """
    mask = (shifts >= best_shift - half_window) & (shifts <= best_shift + half_window)
    coeffs = np.polyfit(shifts[mask].astype(np.float64), stdevs[mask], 2)

    if coeffs[0] <= 0:
        return float(best_shift)

    return -coeffs[1] / (2 * coeffs[0])


flats_dir = Path(args.flats)
darks_dir = Path(args.darks)
tomo_dir  = Path(args.tomo)

flat_files = sorted(flats_dir.glob("*.tif*"))
dark_files = sorted(darks_dir.glob("*.tif*"))
tomo_files = sorted(tomo_dir.glob("*.tif*"))

if not flat_files:
    raise FileNotFoundError(f"No TIFF files found in {flats_dir}")
if not dark_files:
    raise FileNotFoundError(f"No TIFF files found in {darks_dir}")
if len(tomo_files) < 2:
    raise FileNotFoundError(f"Need at least 2 TIFF files in {tomo_dir}")

print("Loading images...")
print(f"  Flat fields : {len(flat_files)} image(s) from {flats_dir}")
print(f"  Dark fields : {len(dark_files)} image(s) from {darks_dir}")
# load flats
flat = np.stack([imread(p).astype(np.float32) for p in flat_files]).mean(axis=0)
# load darks
dark = np.stack([imread(p).astype(np.float32) for p in dark_files]).mean(axis=0)
flat_dark = flat - dark

print(f"  0°  projection : {tomo_files[0].name}")
print(f"  180° projection : {tomo_files[-1].name}")
p0   = (imread(tomo_files[0] ).astype(np.float32) - dark) / flat_dark
p180 = (imread(tomo_files[-1]).astype(np.float32) - dark) / flat_dark

print(f"  Image shape : {p0.shape}")

# --- Search for rotation axis ---
shift_range = (args.shiftmin, args.shiftmax)
print(f"Searching shifts from {shift_range[0]} to {shift_range[1]} pixels...")

best_shift, shifts, stdevs = find_rotation_axis(p0, p180, shift_range, args.crop)
subpixel_shift = fit_parabola(shifts, stdevs, best_shift)

width = p0.shape[1]
print(f"\nResults:")
print(f"  Image width          : {width} px")
print(f"  Best integer shift   : {best_shift} px")
print(f"  Sub-pixel shift      : {subpixel_shift:.3f} px")
print(f"  Rotation axis (int)  : {width / 2 + best_shift / 2:.1f} px")
print(f"  Rotation axis (sub)  : {width / 2 + subpixel_shift / 2:.3f} px")

if args.plot:
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.plot(shifts, stdevs, "o-", markersize=3, label="stdev")
    ax.axvline(best_shift, color="tab:orange", linestyle="--", label=f"integer minimum ({best_shift} px)")
    ax.axvline(subpixel_shift, color="tab:red", linestyle=":", label=f"sub-pixel minimum ({subpixel_shift:.2f} px)")
    ax.set_xlabel("Shift (pixels)")
    ax.set_ylabel("Std dev of ratio image")
    ax.set_title("Rotation axis search")
    ax.legend()
    plt.tight_layout()

    save_path = Path(args.SAVE) / "correlate-first-last"
    save_path.mkdir(parents=True, exist_ok=True)
    fig.savefig(save_path / "rotation_axis.png", dpi=150)
    cor_value = width / 2 + subpixel_shift / 2
    with open(save_path / "rotation_axis.txt", "w") as f:
        f.write(f"{cor_value:.3f}\n")
    plt.close(fig)
