# Built to Last?

Built to Last? is a holistic Streamlit activity for introductory accounting. Students follow one fictional company's long-lived assets from acquisition through later expenditures, straight-line depreciation, disposal, intangible assets, financial-statement presentation, and return-on-assets analysis.

The activity is framed through account increases and decreases, ending account balances, and financial-statement effects. Students work with one connected asset lifecycle rather than a collection of unrelated questions.

## Interaction design

- Student-facing labels describe the case rather than the course or chapter number.
- Case decisions follow the business timeline; answer order is randomized once per student and remains stable after refresh.
- Unsubmitted choices and calculation drafts survive refresh without collecting identifying information.
- Incorrect work receives a targeted hint and can be revised immediately on the same screen without revealing the answer.
- Navigation returns students to the top of each new decision.
- Depreciation and disposal include before-and-after balance bridges that connect the calculations to assets, liabilities, equity, and net income.

## Student flow

1. Determine the historical cost of land, land improvements, buildings, and equipment.
2. Separate ordinary repairs from additions and improvements.
3. Calculate straight-line depreciation, accumulated depreciation, and book value, including a partial year.
4. Update balances through the disposal date and determine the gain or loss.
5. Account for patents, copyrights, trademarks, franchises, goodwill, and research and development.
6. Present long-lived assets and analyze profit margin, asset turnover, and return on assets.

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
streamlit run streamlit_app.py
```

## Verify

```bash
python -m unittest discover -s tests -v
python -m py_compile streamlit_app.py built_to_last/*.py
```

## Privacy and progress

The app requires no login, database, secrets, or student name. It stores only compact answer selections, unfinished non-written drafts, numeric responses, activity position, a randomization seed, and scoring flags in a validated URL parameter so browser refreshes can restore progress. No written response or identifying information is included.

## Deployment

The project is structured for GitHub-based Streamlit Community Cloud deployment with `streamlit_app.py` as the application file.
