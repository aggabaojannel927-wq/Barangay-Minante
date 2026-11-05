"""Collect source/schema evidence only; never export operational database rows."""
import ast
import hashlib
import json
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / 'barangay_system'
OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(APP))
from models import db


def collect():
    files, routes, tests, functions = [], [], [], []
    paths = sorted(p for p in APP.rglob('*') if p.is_file() and p.suffix in {'.py', '.html', '.css', '.js'}
                   and not {'instance', '__pycache__', 'audit-artifacts'}.intersection(p.parts))
    for p in paths:
        rel = p.relative_to(ROOT).as_posix()
        source = p.read_text(encoding='utf-8-sig')
        files.append({'path': rel, 'lines': len(source.splitlines()), 'sha256': hashlib.sha256(p.read_bytes()).hexdigest()})
        if p.suffix != '.py':
            continue
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                functions.append({'name': node.name, 'file': rel, 'line': node.lineno})
            if isinstance(node, ast.FunctionDef) and node.name.startswith('test_'):
                tests.append({'name': node.name, 'file': rel, 'line': node.lineno})
            if not isinstance(node, ast.FunctionDef):
                continue
            for dec in node.decorator_list:
                if isinstance(dec, ast.Call) and isinstance(dec.func, ast.Attribute) and isinstance(dec.func.value, ast.Name) and dec.func.value.id == 'app' and dec.func.attr in {'route','get','post'}:
                    methods = [dec.func.attr.upper()] if dec.func.attr != 'route' else ['GET']
                    for kw in dec.keywords:
                        if kw.arg == 'methods': methods = ast.literal_eval(kw.value)
                    routes.append({'path': ast.literal_eval(dec.args[0]), 'methods': methods, 'handler': node.name,
                                   'file': rel, 'line': node.lineno,
                                   'guards': [ast.unparse(d) for d in node.decorator_list if d is not dec]})
    schema = []
    database = APP / 'instance' / 'minante.db'
    con = sqlite3.connect(database.as_uri() + '?mode=ro', uri=True)
    try:
        tables = con.execute("SELECT name, sql FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name").fetchall()
        for name, ddl in tables:
            quoted = '"' + name.replace('"','""') + '"'
            columns = con.execute('PRAGMA table_info(' + quoted + ')').fetchall()
            keys = con.execute('PRAGMA foreign_key_list(' + quoted + ')').fetchall()
            indexes = []
            for row in con.execute('PRAGMA index_list(' + quoted + ')').fetchall():
                iq = '"' + row[1].replace('"','""') + '"'
                indexes.append({'name': row[1], 'unique': bool(row[2]), 'columns': [c[2] for c in con.execute('PRAGMA index_info('+iq+')')]})
            model = db.metadata.tables.get(name)
            schema.append({'name':name, 'ddl':ddl,
                'columns':[{'name':c[1],'type':c[2], 'nullable':not bool(c[3]),'default':c[4], 'pk':bool(c[5])} for c in columns],
                'foreign_keys':[{'column':k[3],'target_table':k[2],'target_column':k[4], 'on_delete':k[6]} for k in keys],
                'indexes':indexes,
                'model_foreign_keys':[{'column':fk.parent.name, 'target':fk.target_fullname} for fk in model.foreign_keys] if model is not None else []})
        integrity = con.execute('PRAGMA integrity_check').fetchone()[0]
        fk_count = len(con.execute('PRAGMA foreign_key_check').fetchall())
    finally:
        con.close()
    data={'review_date':'2026-10-07', 'source_scope':'Local working tree; no remote repository or operational rows exported',
          'python':sys.version.split()[0], 'sqlite':sqlite3.sqlite_version,
          'files':files, 'routes':sorted(routes,key=lambda x:x['path']), 'tests':tests, 'symbols':functions,
          'schema':schema, 'database_check':{'integrity':integrity,'foreign_key_violations':fk_count}}
    (OUT/'source_evidence.json').write_text(json.dumps(data,indent=2),encoding='utf-8')
    print(json.dumps({'source_files':len(files),'routes':len(routes),'tables':len(schema),'tests':len(tests),'integrity':integrity}))
    return data

if __name__ == '__main__': collect()
