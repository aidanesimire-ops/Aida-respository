"""
validate.py — recalc a workbook with the `formulas` engine (no LibreOffice),
scan every cell for Excel errors, and print requested QA cells.

Usage: python3 validate.py ../Shahidi_Assemblage_Model.xlsx "Sheet!C115" ...
"""
import sys, re, warnings
warnings.filterwarnings("ignore")
import numpy as np
import formulas

ERR_TOKENS = ("#REF!", "#VALUE!", "#DIV/0!", "#N/A", "#NAME?", "#NULL!",
              "#NUM!", "#ERROR", "#CIRC")

def cellval(v):
    """Unwrap a formulas Ranges/ndarray value to a scalar or string."""
    try:
        arr = v.value
    except AttributeError:
        arr = v
    a = np.asarray(arr, dtype=object).ravel()
    if a.size == 0:
        return None
    return a[0]

def main():
    path = sys.argv[1]
    xl = formulas.ExcelModel().loads(path).finish()
    sol = xl.calculate()
    fname = path.split("/")[-1]   # original case kept by engine

    errors = []
    for key, val in sol.items():
        # key like "'[FILE.XLSX]SHEET NAME'!C115"
        try:
            sval = cellval(val)
        except Exception:
            continue
        if isinstance(sval, str):
            for t in ERR_TOKENS:
                if t in sval:
                    errors.append((key, sval)); break

    print(f"=== recalc engine: formulas ; cells solved: {len(sol)}")
    print(f"=== formula errors: {len(errors)}")
    for k, v in errors[:80]:
        print("   ERR", k, "=", v)

    # requested QA cells
    for spec in sys.argv[2:]:
        sh, co = spec.split("!")
        want = f"'[{fname}]{sh.upper()}'!{co.upper()}"
        got = None
        for key, val in sol.items():
            if key == want:
                got = cellval(val); break
        print(f"   {spec} = {got}")

if __name__ == "__main__":
    main()
