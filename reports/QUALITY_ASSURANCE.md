# Quality assurance

The report contains 12 pages. The presentation contains 10 slides, eight native editable charts and eight embedded Excel workbooks. Its 908-word English script is synchronized with slide notes. Estimated delivery with pauses is 6–8 minutes; no timed rehearsal is claimed.

All report pages and presentation slides were rendered and visually reviewed. Chart numerical values and embedded workbook data were preserved during presentation wording updates. Native PowerPoint execution has not been checked.

Offline replay recalculates 15 original model specifications, six sensitivity specifications, the 40-month media and 44-month macro comparisons, and the retrospective extensions. It checks 1,005 source snapshots. The supplied suite contains 50 tests. Current checks are recorded in reports/final_gpt_v3/FINAL_QA.json, reports/final_gpt_v3/dashboard_verification.json and output/checks/verification.json after package verification.

Dashboard JavaScript logic, filters, fixed economic-gap calculation, validation and event panels, SVG geometry and 40-row CSV export were checked locally. The available browser tool did not support the local file URL; browser layout and native interaction were not inspected.

Statistical replay uses public categorical data and archived releases. It does not re-extract private text, rerun semantic coding or independently authenticate original human annotation. Uncertainty, missing labels and exploratory analyses remain documented. No new paid inference is required.
