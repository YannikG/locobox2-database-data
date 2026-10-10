from __future__ import annotations

import shutil
import subprocess
from pathlib import Path


def run_pdftotext_layout(pdf: Path, out_txt: Path) -> None:
    bin_path = shutil.which("pdftotext")
    if not bin_path:
        raise RuntimeError("pdftotext not found (install poppler)")
    out_txt.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [bin_path, "-layout", str(pdf), str(out_txt)],
        check=True,
    )
