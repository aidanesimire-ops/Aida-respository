"""preview.py — text dump of a sheet's non-empty cells, row by row (structure QA)."""
import sys, openpyxl
wb = openpyxl.load_workbook(sys.argv[1])
ws = wb[sys.argv[2]]
for row in ws.iter_rows(min_row=int(sys.argv[3]) if len(sys.argv) > 3 else 1,
                        max_row=int(sys.argv[4]) if len(sys.argv) > 4 else ws.max_row):
    cells = [(c.coordinate, c.value) for c in row if c.value not in (None, "")]
    if cells:
        parts = []
        for coord, v in cells:
            sv = str(v)
            if len(sv) > 40: sv = sv[:37] + "..."
            parts.append(f"{coord}={sv}")
        print(" | ".join(parts))
