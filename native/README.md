# Built to Last? — JavaScript app

The final student-facing activity is served only under `/js/` in this repository. Seven local HTML/CSS/JavaScript files replace runtime Python, Streamlit and Pyodide loading. No external services, storage, installation or redirects are added. The original server app and published stlite root remain unchanged.

`export.py` captures the unchanged Python teaching renderers at all 26 reached positions and 96 variants. Acquisition, upkeep, partial-year straight-line depreciation, disposal, intangible assets, performance analysis, every explanation/hint, account/statement effect, table and debrief answer remain. Depreciation, disposal and ratio reasoning are visible only after their calculations are correct. JavaScript calculations and exact CPython option shuffles are checked against independent Python outcomes, including 63-bit seeds and ties-to-even currency rounding.

Back is strictly read-only and Forward stops at the earned page. Calculation checks and the ordinary validated Continue/Complete controls earn new work. Numeric fields lock after correct calculation; reasoning is a separate checkpoint. Built to Last counts every submitted numeric recheck, including unchanged wrong amounts, as the original does. Choice and numeric drafts clear on submission. Tables, expansion and CSV downloads do not mutate progress. Native controls preserve visible keyboard focus and 44-pixel boxed arrow targets.

Original version-3 Python/stlite saved links restore after changing their path to `/js/`, preserving query parameters, review position, choice/numeric drafts, seed, answers, attempts and first-pass scoring. The original migration for the retired `exchange` disposal decision remains: its obsolete draft/score is removed and active completed disposal work resumes at intangibles, exactly as Python. Ordinary native snapshots retain the same version-3 schema and are accepted by Python. More than 50 practice attempts upgrades a snapshot to native version 4, retaining full scoring and refreshability; such extended links require the JavaScript app. Bounded anonymous numeric text in a separate `draft` query parameter preserves unfinished formatting and invalid numeric input. Future work is rejected and future views are clamped. Reset starts fresh, and independent tabs/contexts do not share state.

```sh
PY=/workspace/.cloud-setup/venvs/main/bin/python
"$PY" native/export.py
node --test native/tests/*.test.mjs
"$PY" -m unittest discover -s tests -v
"$PY" native/build.py
"$PY" native/tests/browser.py
```

Serve `native/dist/` over HTTP/HTTPS. Build copies only `js/` runtime files and a SHA-256 manifest; Python/Node remain development tools. Publication adds `/js/` to the existing static branch after checking remote refs and proving the rest of the site is byte unchanged. See [validation](VALIDATION.md) and `review/`. A current browser needs ES modules, BigInt, Web Crypto and Compression Streams.
