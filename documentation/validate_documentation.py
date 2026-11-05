"""Check generated document structure, coverage, source drift and PDF bounds."""
import hashlib
import json
import re
import zipfile
from pathlib import Path
import pymupdf as fitz
from docx import Document
from pypdf import PdfReader
from content_data import DEFENSE

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
NAME='Barangay_Minante_1_Integrated_Management_System_Full_Documentation'

def validate():
    data=json.loads((HERE/'source_evidence.json').read_text(encoding='utf-8'))
    source=(HERE/'FULL_DOCUMENTATION.md').read_text(encoding='utf-8')
    assert '{{' not in source, 'Unexpanded template marker'
    drift=[f['path'] for f in data['files'] if hashlib.sha256((ROOT/f['path']).read_bytes()).hexdigest()!=f['sha256']]
    assert not drift, drift
    doc=Document(ROOT/(NAME+'.docx'));pdf=PdfReader(ROOT/(NAME+'.pdf'))
    text='\n'.join(p.extract_text() or '' for p in pdf.pages)
    compact=re.sub(r'\s+','',text)
    missing=[t['name'] for t in data['schema'] if t['name'] not in compact]
    assert not missing, missing
    for chapter in range(1,14): assert f'Chapter {chapter}' in text
    questions=sum(map(len,DEFENSE.values()));assert questions>=75
    for n in range(1,questions+1):assert f'Q{n:02}.' in text
    assert len(doc.tables)>=35 and len(doc.inline_shapes)==17
    assert len(doc.paragraphs)>500
    with zipfile.ZipFile(ROOT/(NAME+'.docx')) as archive:
        xml=archive.read('word/document.xml').decode('utf-8')
        assert '<w:tbl>' in xml and '<w:bookmarkStart' in xml and '<w:hyperlink' in xml
        assert len([n for n in archive.namelist() if n.startswith('word/media/')])>=17
    cheat=PdfReader(ROOT/'Barangay_Minante_1_Defense_Cheat_Sheet.pdf')
    assert 2<=len(cheat.pages)<=4
    blank=[i+1 for i,p in enumerate(pdf.pages) if len((p.extract_text() or '').strip())<60]
    assert not blank, blank
    rendered=fitz.open(ROOT/(NAME+'.pdf'));bounds=[]
    for i,page in enumerate(rendered):
        for b in page.get_text('blocks'):
            if b[0]<-1 or b[1]<-1 or b[2]>page.rect.width+1 or b[3]>page.rect.height+1:bounds.append(i+1)
    assert not bounds, bounds
    preview=HERE/'preview';preview.mkdir(exist_ok=True)
    page_choices={0}
    for target in ['Figure 14. Resident','A.1 accepted_id_types','Q01. What is the system?','Table 1.','Chapter 4 — Complete','B. Route Inventory']:
        candidates=[i for i,p in enumerate(rendered) if target in p.get_text()]
        if candidates:page_choices.add(candidates[-1])
    # Render cover, body/table/ERD/question examples plus every cheat-sheet page.
    for i in sorted(page_choices):rendered[i].get_pixmap(matrix=fitz.Matrix(1.1,1.1)).save(preview/f'full-{i+1:03}.png')
    short=fitz.open(ROOT/'Barangay_Minante_1_Defense_Cheat_Sheet.pdf')
    for i,p in enumerate(short):p.get_pixmap(matrix=fitz.Matrix(1,1)).save(preview/f'cheat-{i+1}.png')
    summary={'full_pdf_pages':len(pdf.pages),'cheat_sheet_pages':len(cheat.pages),'word_tables':len(doc.tables),
             'word_figures':len(doc.inline_shapes),'defense_questions':questions,'sqlite_tables':len(data['schema']),
             'source_declared_routes':len(data['routes']),'source_files':len(data['files']),
             'blank_pdf_pages':blank,'out_of_page_text_blocks':bounds,'source_drift':drift,
             'editable_word_content':'Native paragraphs/tables; diagrams and screenshots are pictures',
             'unverified':'Installed Microsoft Word rendering and physical printing',
             'files':[{ 'name':p.name,'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in
                      [ROOT/(NAME+'.docx'),ROOT/(NAME+'.pdf'),ROOT/'Barangay_Minante_1_Defense_Cheat_Sheet.docx',ROOT/'Barangay_Minante_1_Defense_Cheat_Sheet.pdf']]}
    (HERE/'validation_summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
    print(json.dumps(summary,indent=2))

if __name__=='__main__':validate()
