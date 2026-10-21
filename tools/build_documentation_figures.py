"""Build a mathematical illustration; never modifies archived analysis results."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "figures"
INK, TEAL, AMBER, MUTED = "#203449", "#007F7B", "#B87824", "#596773"


def describe_svg(path: Path, title: str, description: str) -> None:
    ET.register_namespace("", "http://www.w3.org/2000/svg")
    ET.register_namespace("xlink", "http://www.w3.org/1999/xlink")
    tree = ET.parse(path)
    root = tree.getroot()
    root.insert(0, ET.Element("{http://www.w3.org/2000/svg}title"))
    root[0].text = title
    root.insert(1, ET.Element("{http://www.w3.org/2000/svg}desc"))
    root[1].text = description
    tree.write(path, encoding="utf-8", xml_declaration=True)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 12,
                         "text.color": INK, "axes.labelcolor": INK,
                         "xtick.color": MUTED, "ytick.color": MUTED,
                         "svg.fonttype": "none", "svg.hashsalt": "enzyme-documentation-v1"})
    fig, axes = plt.subplots(1, 2, figsize=(9.2, 4.8))
    for ax, maximum, title in zip(axes, (0.15, 12),
                                  ("A. A narrow view near zero", "B. A wider concentration range")):
        substrate = np.linspace(0, maximum, 400)
        for vmax, km, color, style, label in (
            (1.0, 1.0, TEAL, "-", "Curve A: Vmax = 1, Km = 1"),
            (2.0, 2.0, AMBER, "--", "Curve B: Vmax = 2, Km = 2"),
        ):
            ax.plot(substrate, vmax * substrate / (km + substrate), color=color,
                    linestyle=style, linewidth=2.8, label=label)
        ax.set(xlabel="Substrate (arbitrary units)", ylabel="Rate (arbitrary units)", title=title)
        ax.set_xlim(0, maximum)
        ax.set_ylim(0, 0.16 if maximum < 1 else 2.12)
        ax.spines[["top", "right"]].set_visible(False)
        ax.grid(axis="y", color="#DCE4E9", linewidth=0.7)
        ax.set_axisbelow(True)
    axes[1].axhline(1, color=TEAL, linewidth=1, alpha=0.6)
    axes[1].axhline(2, color=AMBER, linestyle="--", linewidth=1, alpha=0.6)
    axes[1].text(11.8, 1.04, "A's limiting rate", ha="right", color=TEAL, fontsize=10)
    axes[1].text(11.8, 2.04, "B's limiting rate", ha="right", color=AMBER, fontsize=10)
    fig.suptitle("Similar low-concentration slopes can hide different limiting rates", fontsize=16, x=0.5, y=0.98)
    fig.text(0.5, 0.89, "Illustrative model curves — not Puromycin measurements", ha="center", color=MUTED)
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", bbox_to_anchor=(0.5, 0.005), ncol=2,
               frameon=False, fontsize=10)
    fig.subplots_adjust(left=0.09, right=0.98, bottom=0.22, top=0.78, wspace=0.34)
    path = OUT / "concentration-range-illustration.svg"
    fig.savefig(path, metadata={"Date": None})
    plt.close(fig)
    describe_svg(path, "Illustrative Michaelis–Menten curves across two concentration ranges",
                 "Curve A has Vmax=1 and Km=1; curve B has Vmax=2 and Km=2. Both have slope 1 at zero. "
                 "The curves are close over 0 to 0.15 but approach different limiting rates over 0 to 12. "
                 "All quantities are arbitrary mathematical units, not archived experimental data.")
    manifest = {"kind": "illustrative mathematical scenario", "equation": "v = Vmax*S/(Km+S)",
                "parameters": [{"curve": "A", "Vmax": 1, "Km": 1}, {"curve": "B", "Vmax": 2, "Km": 2}],
                "ranges": [[0, 0.15], [0, 12]], "randomness": "none",
                "output_sha256": {path.name: hashlib.sha256(path.read_bytes()).hexdigest()}}
    (OUT / "figure-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")


if __name__ == "__main__":
    main()
