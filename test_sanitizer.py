"""Test: comprehensive report with input sanitization, name influence, signature"""
import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from core.input_sanitizer import sanitize_name, validate_date, name_stroke_element, compute_signature, make_id

# ── Test 1: name sanitization ──
tests = [
    ("罗展程", "罗展程"),
    ("  罗展程  ", "罗展程"),
    ("罗展程 ", "罗展程"),
    ("罗 展程", "罗 展程"),  # space in name
    ("", ""),
    ("  ", ""),
    ("啊啊啊啊", ""),  # repeated char
    ("A", ""),
    ("Albert Einstein", "Albert Einstein"),
]
print("=== Name sanitization ===")
for raw, expected in tests:
    cleaned, err = sanitize_name(raw)
    ok = "PASS" if (cleaned == expected or err and not expected) else "FAIL"
    print(f"  '{raw}' -> '{cleaned}' (err={err}) {ok}")

# ── Test 2: name stroke analysis ──
print("\n=== Name 五行 analysis ===")
for n in ["罗展程", "毛泽东", "爱因斯坦", "张三"]:
    nse = name_stroke_element(n)
    print(f"  {n}: strokes={[s['stroke'] for s in nse['chars']]} total={nse['total_strokes']} element={nse['dominant_element']}")

# ── Test 3: date validation ──
print("\n=== Date validation ===")
date_tests = [
    (1997, 6, 22, 1, True),
    (1997, 2, 29, 1, False),  # not leap year
    (2025, 1, 1, 12, False),  # too young
    (1800, 1, 1, 12, False),  # too old
    (1997, 13, 1, 12, False), # bad month
    (1997, 0, 1, 12, False),  # bad month
]
for y, m, d, h, expected in date_tests:
    valid, err = validate_date(y, m, d, h)
    ok = "PASS" if valid == expected else "FAIL"
    print(f"  {y}-{m}-{d} h={h}: valid={valid} ({err}) {ok}")

# ── Test 4: signature uniqueness ──
print("\n=== Signature uniqueness ===")
sigs = []
for name in ["罗展程", "罗展程 ", " 罗展程", "张三", "李四"]:
    sig = compute_signature(name, 1997, 6, 22, 1, "丁丑 己亥 辛巳 庚丑")
    repeated = sig in sigs
    sigs.append(sig)
    print(f"  '{name}': {sig} {'DUPE!' if repeated else 'unique'}")

# ── Test 5: input_id deterministic ──
print("\n=== Input ID ===")
for name in ["罗展程", "罗展程 ", "张三", "李四"]:
    clean = sanitize_name(name)[0]
    iid = make_id(clean, 1997, 6, 22, 1)
    print(f"  '{name}' -> '{clean}' -> {iid}")

print("\nAll tests done.")
