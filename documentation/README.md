# Current capstone documentation

The current package documents the inspected local implementation, including partial workflows. It supersedes historical research descriptions for current behavior. It does not claim a remotely verified GitHub revision or institutional approval.

- [Editable full documentation](../Barangay_Minante_1_Integrated_Management_System_Full_Documentation.docx)
- [Full PDF](../Barangay_Minante_1_Integrated_Management_System_Full_Documentation.pdf)
- [Three-page defense cheat sheet, PDF](../Barangay_Minante_1_Defense_Cheat_Sheet.pdf)
- [Editable cheat sheet](../Barangay_Minante_1_Defense_Cheat_Sheet.docx)
- [Reviewed narrative source](CAPSTONE_DOCUMENTATION.md)
- [Expanded source, including generated appendices](FULL_DOCUMENTATION.md)
- [Validation results](validation_summary.json)

The full package includes 13 chapters, all 35 inspected SQLite tables and columns, all 72 declared routes (plus the explanation of Flask's static route), 17 figures, role permissions, user manuals, 82 defense questions, limitations, and test evidence. Text and tables in Word are editable; diagrams/screenshots are images. The PDF has a populated table of contents and bookmarks. Word has clickable contents links; regenerate a page-numbered contents list in Word if your institution requires it after editing.

## Regeneration

From the repository root, using the project's environment:

```powershell
.\.venv\Scripts\python.exe -m pip install -r documentation\requirements.txt
.\.venv\Scripts\python.exe documentation\build_documentation.py
.\.venv\Scripts\python.exe documentation\validate_documentation.py
```

Application dependencies must already be installed. The PDF build uses Windows Arial fonts. `collect_evidence.py` reads Python/template/static source and SQLite schema metadata with a read-only connection. It does not query/export operational resident records. The checked database location is the default local `barangay_system/instance/minante.db`; update the evidence collector deliberately for another schema source.

Before regeneration after code changes, review and update the narrative and explanatory content. Automatic inventory regeneration does not automatically rewrite workflow claims. Refresh `acceptance-run.txt` from an isolated test run if asserting a newer result. Generated source fingerprints let the validator detect source drift.

Screenshots are copied from the saved synthetic browser audit, not private production records. Rendered inspection pages under `preview/` are review artifacts. Microsoft Word application rendering and physical printing were not verified; structural checks do not replace them.
