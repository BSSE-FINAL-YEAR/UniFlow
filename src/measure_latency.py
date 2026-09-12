"""Measure real latency from your location. Owner: Swale Sebabe (Model Selection Note).

    python src/measure_latency.py --n 10
"""
import argparse, statistics, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from llm_client import generate

PROMPT = ('Design 3 test cases for this rule and return raw JSON only: '
          '"Maximum course load is 6 units in Year 1." '
          'Schema: {"test_cases":[{"id":"","title":"","expected_result":""}]}')

ap = argparse.ArgumentParser(); ap.add_argument("--n", type=int, default=10)
n = ap.parse_args().n

lat, tok, fails = [], [], 0
for i in range(n):
    r = generate(user=PROMPT, system="You reply only with raw JSON.")
    if r.error:
        fails += 1; print(f"  {i+1}/{n}  ERROR {r.error[:70]}"); continue
    lat.append(r.latency_ms)
    if r.prompt_tokens and r.completion_tokens:
        tok.append(r.prompt_tokens + r.completion_tokens)
    print(f"  {i+1}/{n}  {r.latency_ms:>6}ms  tokens={r.prompt_tokens}/{r.completion_tokens}")

if not lat:
    raise SystemExit("All calls failed — check your API key before writing the note.")

s = sorted(lat)
print(f"\n--- Paste these MEASURED numbers into the Model Selection Note ---")
print(f"Successful calls : {len(lat)}/{n}" + (f"  ({fails} failed)" if fails else ""))
print(f"Median latency   : {s[len(s)//2]} ms")
print(f"p95 latency      : {s[int(len(s)*0.95)-1] if len(s)>1 else s[0]} ms")
print(f"Min / Max        : {s[0]} / {s[-1]} ms")
if len(lat) > 1:
    print(f"Std deviation    : {statistics.stdev(lat):.0f} ms")
if tok:
    print(f"Mean tokens/call : {statistics.mean(tok):.0f}")
    print(f"\nWeek 7 estimate  : 30 scenarios x 5 re-runs x {statistics.mean(tok):.0f} tokens "
          f"= ~{30*5*statistics.mean(tok):,.0f} tokens total")
