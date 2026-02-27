"""Parse Yosys stat output for area, cell count."""
import re


def parse_yosys_stat(stdout: str) -> dict:
    """
    Parse Yosys 'stat' output.
    Returns dict with chip_area, num_cells, num_wires, etc. if found.
    """
    metrics = {}
    # Example stat output:
    #   Chip area for module '\top': 123.45
    #   Number of cells: 42
    area_match = re.search(r"Chip area[^:]*:\s*([\d.]+)", stdout, re.MULTILINE)
    if area_match:
        metrics["chip_area"] = float(area_match.group(1))

    cells_match = re.search(r"Number of cells:\s*(\d+)", stdout, re.MULTILINE)
    if cells_match:
        metrics["num_cells"] = int(cells_match.group(1))

    wires_match = re.search(r"Number of wires:\s*(\d+)", stdout, re.MULTILINE)
    if wires_match:
        metrics["num_wires"] = int(wires_match.group(1))

    # Yosys stat -tech cmos gives transistor count
    # Also look for "cells" in generic stat
    cells_alt = re.search(r"(\d+)\s+cells?\s+", stdout, re.IGNORECASE)
    if cells_alt and "num_cells" not in metrics:
        metrics["num_cells"] = int(cells_alt.group(1))

    return metrics
