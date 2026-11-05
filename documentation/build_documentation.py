r"""Build editable Word and print PDF from reviewed narrative and schema metadata.

Run from repository root: .venv\Scripts\python.exe documentation/build_documentation.py
No operational row data is read; collect_evidence reads schema only.
"""
from __future__ import annotations
import html
import json
import os
import re
import shutil
import textwrap
from pathlib import Path

from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from PIL import Image as PILImage
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (BaseDocTemplate, Frame, PageTemplate, Paragraph, Spacer,
    PageBreak, Table, TableStyle, Image, Preformatted, KeepTogether)
from reportlab.platypus.tableofcontents import TableOfContents

from collect_evidence import collect
from content_data import TABLES, FUNCTIONS, DEFENSE, GLOSSARY, TEST_EXPECTATIONS

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
ASSETS = HERE/'assets'
NAME = 'Barangay_Minante_1_Integrated_Management_System_Full_Documentation'
TITLE = 'Barangay Minante 1 Integrated Management System'
SUBTITLE = 'Complete Capstone Research and Technical System Documentation'
FULL_TITLE = ('Development of an Integrated Barangay Permit, Event Approval, Blotter Management '
              'System with Notification and Scheduling Features for Barangay Minante 1, Cauayan City')
NAVY, GOLD, INK = '#082F5B', '#D4A62A', '#26384B'
DATE = 'October 7, 2026'


def mdtable(headers, rows):
    def clean(v): return str(v).replace('|','/').replace('\n','; ')
    return '\n'.join(['| '+' | '.join(headers)+' |','|'+'|'.join(['---']*len(headers))+'|']+
                     ['| '+' | '.join(clean(v) for v in row)+' |' for row in rows])


def render_figures():
    os.environ['MPLCONFIGDIR'] = str(HERE/'.chart-cache')
    from matplotlib.figure import Figure
    from matplotlib.backends.backend_agg import FigureCanvasAgg
    from matplotlib.patches import FancyBboxPatch
    ASSETS.mkdir(exist_ok=True)

    def box(ax, x, y, w, h, label, dark=False, size=11):
        ax.add_patch(FancyBboxPatch((x,y), w,h, boxstyle='round,pad=0.012,rounding_size=0.018',
                     linewidth=1.2, edgecolor=NAVY, facecolor=NAVY if dark else '#F2F6FA'))
        ax.text(x+w/2,y+h/2,label,ha='center',va='center',fontsize=size,
                color='white' if dark else INK,linespacing=1.4)
    def arrow(ax,a,b,label=''):
        ax.annotate('',xy=b,xytext=a,arrowprops={'arrowstyle':'-|>','color':GOLD,'lw':2})
        if label: ax.text((a[0]+b[0])/2,(a[1]+b[1])/2+.018,label,ha='center',fontsize=8,color=INK)
    def save(fig,key):
        FigureCanvasAgg(fig);fig.savefig(ASSETS/(key+'.png'),dpi=170,bbox_inches='tight',facecolor='white')
    def flow(key,steps):
        fig=Figure(figsize=(9,max(3.6,len(steps)*.74)))
        ax=fig.subplots();ax.set_xlim(0,1);ax.set_ylim(0,1);ax.axis('off')
        gap=.96/len(steps); h=gap*.67
        for i,label in enumerate(steps):
            y=.97-(i+1)*gap
            box(ax,.08,y,.84,h,label,dark=i==0,size=11)
            if i: arrow(ax,(.5,y+gap),(.5,y+h+.012))
        save(fig,key)
    flow('architecture',['Resident / Staff / Administrator • Web browser',
        'Jinja HTML + custom CSS + JavaScript\nForms, navigation, charts and downloads',
        'Flask app.py + registered revision routes\nSession, CSRF, permissions and ownership',
        'Workflow + service functions\nValidation, review, reservation, payment and reporting',
        'SQLAlchemy → SQLite       |       Private filesystem\nRelated records and transactions       |       IDs, evidence, signatures',
        'Authorized outputs\nPages • DOCX • in-app notifications • audit records'])
    flow('ipo',['INPUT\nApplicant details • evidence • service choices • operator decisions',
        'PROCESS\nValidate → authorize → store → verify/review → approve → record outcome',
        'OUTPUT\nReferences • acknowledgments • approved documents • notifications • aggregates'])
    flows={
    'registration':['Applicant enters details, accepted ID and privacy consent','Pending registration + Pending ID/address verification',
                    'Administrator verifies both (or rejects with reason)','Administrator approves Pending account','Active approved account may log in'],
    'permit':['Select configured service → submit required evidence','Snapshot fee and requirements → acknowledgment',
              'Staff reviews evidence; correction returns to applicant','Verified required evidence → Endorsed to Admin',
              'Admin approval (or supported rejection)','Payment if required / Admin waiver / free service','Designated Admin signature → Ready for Pickup','Identity confirmed at counter → Completed + release record'],
    'event':['Choose active category, venue, date and interval','Serialize venue write and check overlapping reservations',
             'Available: reserve and submit\nConflict: recommend another day with private ten-minute hold',
             'Accept recommendation → recheck/reserve\nDecline or expiry → release hold','Staff review/endorsement → Admin decision','Rejected/Cancelled → release slot\nApproved → payment-eligible completion'],
    'blotter':['Complainant records respondent and incident','Filed → Under Review','For Investigation','For Hearing / Scheduled\nAppointment is a separate linked record','Admin Resolved → Closed\nResolution/officer editing is incomplete'],
    'walkin':['Staff/Admin searches existing Resident profile','Select permit service; capture purpose and requirements',
              'Save Resident ownership + encoder + fee/evidence snapshots','Create daily queue ticket','Print/download Walk-in Transaction Acknowledgment',
              'Continue normal permit review and decision workflow'],
    'release':['Resident arrives; operator locates Ready for Pickup permit','Check authorized operator and no Staff self-processing',
               'Check signature + Paid / Waived / Not Required','Operator confirms identity','Conditional status change → Completed','Store releaser/time → log and notification'],
    'payment':['Approved request with positive unpaid fee snapshot','Administrator or explicitly authorized Staff; never own payment',
               'Paid: exact Cash amount\nWaived: Admin only, zero amount and reason','Insert one linked payment decision; enforce database constraints',
               'Paid only → receipt and collection total\nPaid / Waived / Not Required → eligible for next service step'],
    'program':['Staff/Admin creates configurable Scholarship or Ayuda draft','Admin publishes program + linked dated announcement',
               'Approved applicant applies within dates; snapshot evidence','Per Resident / Household unique claim, or Repeatable',
               'Under Review → Needs Requirements / Qualified / Not Qualified','Qualified → Admin Approved / Waitlisted; slots checked','Admin confirms release/completion → Completed'],
    'announcement':['Staff draft or Administrator-approved notice','Approval with valid start and expiry','Before start: Scheduled, hidden from active feed',
                    'Start ≤ now < expiry: visible Published notice','At expiry: hidden; backend refresh persists Expired','History preserved; Admin Archive also preserves record'],
    }
    for key,steps in flows.items(): flow(key,steps)
    fig=Figure(figsize=(10,7.5));ax=fig.subplots();ax.set_xlim(0,1);ax.set_ylim(0,1);ax.axis('off')
    labels=[('Resident / Admin','1.0 User Management','Users / profiles / households'),('Resident / Staff / Admin','2.0 Permit Processing','Permits / requirements / payments'),
            ('Resident / Staff / Admin','3.0 Event Approval','Events / venues / reservations'),('Resident / Staff / Admin','4.0 Blotter Management','Blotter cases'),
            ('Users / operators','5.0 Schedules & Notices','Schedules / notifications / notices'),('Administrator','6.0 Reports & Monitoring','Aggregate reads / report metadata'),
            ('Instrumented routes','7.0 Activity Logging','Activity logs')]
    for i,(actor,process,data) in enumerate(labels):
        y=.88-i*.125
        box(ax,.01,y,.24,.07,actor,size=8.5);box(ax,.34,y,.31,.07,process,True,9);box(ax,.73,y,.26,.07,textwrap.fill(data,28),size=8)
        arrow(ax,(.26,y+.035),(.325,y+.035));arrow(ax,(.665,y+.035),(.715,y+.035))
    save(fig,'dfd')
    relationships={
      'erd_people':[('resident_profiles.user_id','users.id','0..1 profile per user'),('resident_profiles.resident_type_id','resident_types.id','many profiles to one type'),
        ('resident_profiles.accepted_id_type_id','accepted_id_types.id','many profiles to one type'),('household_members.resident_id','users.id','many membership records to user'),
        ('household_members.household_id','households.id','many members to household'),('households.head_resident_id','users.id','optional head reference')],
      'erd_permits':[('permit_applications.applicant_id','users.id','many permits per user'),('permit_applications.permit_type_id','permit_types.id','many permits per service'),
        ('service_requirements.permit_type_id','permit_types.id','many definitions per service'),('application_requirements.application_id','permit_applications.id','many snapshots per permit'),
        ('application_requirements.definition_id','service_requirements.id','definition link; copied fields retained'),('requirement_history.requirement_id','application_requirements.id','many history rows per item'),
        ('permit_signatories.permit_type_id','permit_types.id','one configured signatory per service'),('payments.permit_id','permit_applications.id','zero or one decision per permit'),
        ('queue_entries.permit_application_id','permit_applications.id','ticket links to permit'),('request_assignments.permit_application_id','permit_applications.id','assignment history'),
        ('resident_feedback.permit_application_id','permit_applications.id','feedback linked to completed permit')],
      'erd_operations':[('event_requests.requester_id','users.id','many event requests per user'),('event_requests.category_id','event_categories.id','category'),
        ('event_requests.venue_id','event_venues.id','venue'),('event_reservations.event_request_id','event_requests.id','optional unique link; holds may be unlinked'),
        ('payments.event_id','event_requests.id','zero or one payment decision'),('blotter_cases.complainant_id','users.id','many cases per complainant'),
        ('schedules.requested_by','users.id','owner; related transaction is logical'),('notifications.user_id','users.id','recipient'),('activity_logs.user_id','users.id','actor')],
      'erd_programs':[('program_applications.program_id','community_programs.id','many applications per program'),('program_applications.resident_id','users.id','applicant'),
        ('program_applications.household_id','households.id','optional household claim'),('program_application_history.application_id','program_applications.id','many prior evidence snapshots'),
        ('announcements.program_id','community_programs.id','optional program notice link')],
    }
    for key,rows in relationships.items():
        fig=Figure(figsize=(10,len(rows)*.67+.45));ax=fig.subplots();ax.set_xlim(0,1);ax.set_ylim(0,len(rows));ax.axis('off')
        # Separate relationship rows retain readable labels without crossing edges.
        for i,(child,parent,note) in enumerate(rows):
            y=len(rows)-i-.7
            ax.text(.01,y+.07,child,fontsize=9,bbox={'facecolor':'#F2F6FA','edgecolor':NAVY,'pad':6},va='center')
            ax.text(.99,y+.07,parent,fontsize=9,bbox={'facecolor':'#F2F6FA','edgecolor':NAVY,'pad':6},va='center',ha='right')
            ax.annotate('',xy=(.66,y+.08),xytext=(.44,y+.08),arrowprops={'arrowstyle':'-|>','color':GOLD,'lw':1.8})
            ax.text(.5,y-.25,note,ha='center',fontsize=8,color=INK)
        save(fig,key)
    shutil.copyfile(ROOT/'barangay_system/audit-artifacts/dashboard-1440.png',ASSETS/'dashboard.png')


def expand_source(data):
    source=(HERE/'CAPSTONE_DOCUMENTATION.md').read_text(encoding='utf-8')
    catalog=mdtable(['Table','Purpose / module','Data created/updated by'],[(n,*TABLES[n]) for n in sorted(TABLES)])
    dictionary=[]
    for i,t in enumerate(data['schema'],1):
        name=t['name'];purpose,actors=TABLES[name]
        dictionary.extend([f'## A.{i} {name}',purpose+'.', '**Created/updated by:** '+actors+'.'])
        fk_by={f['column']:f for f in t['foreign_keys']}
        rows=[]
        for c in t['columns']:
            fk=fk_by.get(c['name'])
            key='PK' if c['pk'] else ''
            if fk: key+=(' / ' if key else '')+'FK → '+fk['target_table']+'.'+fk['target_column']
            default='—' if c['default'] is None else c['default']
            rows.append((c['name'],c['type'],key or '—','No (PK)' if c['pk'] else ('Yes' if c['nullable'] else 'No'),default))
        dictionary.append(mdtable(['Field','SQLite type','Key / reference','Nullable','SQL default'],rows))
        checks=re.findall(r'CHECK\s*\((.+)\)',t['ddl'])
        if checks: dictionary.append('**Stored CHECK clauses:** '+'; '.join(checks)+'.')
        unique=[', '.join(x['columns']) for x in t['indexes'] if x['unique']]
        dictionary.append('**Unique index keys:** '+('; '.join(unique) if unique else 'No additional unique index listed beyond the primary key')+'.')
        nonunique=[x['name']+' ('+', '.join(x['columns'])+')' for x in t['indexes'] if not x['unique']]
        dictionary.append('**Lookup indexes:** '+('; '.join(nonunique) if nonunique else 'No separate lookup index listed')+'.')
        if t['foreign_keys']:
            dictionary.append('**Relationships:** '+'; '.join(f['column']+' → '+f['target_table']+'.'+f['target_column']+' (on delete '+f['on_delete']+')' for f in t['foreign_keys'])+'.')
    functions=[]
    for n,file,inputs,outputs,database,security in FUNCTIONS:
        symbols=[s for s in data['symbols'] if s['name']==n and s['file']=='barangay_system/'+file]
        loc=f'barangay_system/{file}'+(':'+str(symbols[0]['line']) if symbols else '')
        functions.extend([f'### {n}',f'**Code:** `{loc}`. **Input:** {inputs}.',
            f'**Purpose / processing / output:** {outputs}. **SQLite interaction:** {database}.',f'**Permission / possible errors:** {security}.'])
    test_rows=[]
    raw=(HERE/'acceptance-run.txt').read_text(encoding='utf-16' if (HERE/'acceptance-run.txt').read_bytes().startswith(b'\xff\xfe') else 'utf-8-sig')
    for i,t in enumerate(data['tests'],1):
        key=t['name'].removeprefix('test_')
        expectation=TEST_EXPECTATIONS.get(key, key.replace('_',' ').capitalize()+'.')
        occurred=t['name'] in raw
        test_rows.append((f'T{i:02}',t['name'],expectation,'Recorded OK' if occurred and '\nOK' in raw else 'Not established in captured run'))
    test_rows.extend([('B01','Edge responsive audit','160 pages, four viewport widths, three roles; no recorded JS/overflow issues','Pass in saved browser audit'),
                      ('DB01','Isolated restart/integrity validator','Persistence across process restart, pragmas and DOCX checks','Pass in recorded SQLite validation'),
                      ('EXT01','Real Word/printer/email/SMS','Actual external rendering/printing/delivery','Not tested / transport absent')])
    tests=mdtable(['ID','Source scenario','Expected result','Actual / status'],test_rows)
    public={'index','favicon','healthz','login','register','privacy_notice','forgot_password','reset_password'}
    admin={'activity_logs','configuration','user_review','user_verification','user_approval','user_role','user_account_status',
           'reports','report_chart','report_export','approve_announcement','announcement_delete','review_resident_update',
           'payment_authority','program_requirements','publish_program','close_program'}
    operational={'front_desk','update_queue','release_walkin_permit','assign_permit','create_general_concern','route_general_concern',
                 'create_resident_update_request','manage_household','create_assistance_referral','review_permit_requirement','notification_send'}
    special={'payments':'Own financial view; Admin/authorized Staff records, except own',
             'payment_receipt':'Owner or payment-authorized operator; Paid only',
             'users':'Staff read-only; Administrator manages',
             'sign_approved_permit':'Designated Administrator for service',
             'resident_identification_document':'Owner or Administrator',
             'programs':'All approved users view; Staff/Admin draft',
             'program_detail':'Resident own application; Staff/Admin assist',
             'program_application':'Owner view/resubmit; non-owner operators review; Admin final steps',
             'program_file':'Owner or operational Staff/Admin',
             'program_acknowledgment':'Owner or operational Staff/Admin',
             'permit_requirement_file':'Non-owner Staff processor or Administrator',
             'resubmit_permit_requirement':'Eligible owner only',
             'schedule_status':'Staff/Admin allowed transitions; owner cannot act as Resident',
             'announcements':'All authorized view; Staff draft; Admin manages',
             'submit_permit_feedback':'Owner of Completed permit',
             'notification_read':'Recipient only','notifications_read_all':'Current recipient only',
             'accept_event_recommendation':'Owner of private hold','decline_event_recommendation':'Owner of private hold'}
    route_rows=[]
    for r in data['routes']:
        name=r['handler']
        access=special.get(name, 'Public' if name in public else 'Administrator' if name in admin else 'Staff/Admin operations' if name in operational else 'Authenticated; Resident records scoped to owner')
        purpose=name.replace('_',' ').capitalize()
        if name=='announcement_delete':purpose='Archive announcement, preserving row'
        if name in {'submission_receipt','walkin_claim_stub'}:purpose='Generate acknowledgment DOCX (legacy handler name)'
        route_rows.append((', '.join(r['methods']),r['path'],access,purpose+'; '+name+' at '+r['file'].split('/')[-1]+':'+str(r['line'])))
    routes=mdtable(['Method','Actual route','Role / boundary','Purpose / code'],route_rows)
    qparts=[];number=0
    for category,questions in DEFENSE.items():
        qparts.append('## '+category)
        for question,answer in questions:
            number+=1;qparts.append(f'**Q{number:02}. {question}**\n\n{answer}')
    glossary=mdtable(['Term','Meaning in this project'],sorted(GLOSSARY.items()))
    sources=mdtable(['Inspected source','Lines','Purpose'],[(f['path'],f['lines'],
        'Template/presentation' if f['path'].endswith('.html') else 'Browser presentation' if f['path'].endswith(('.js','.css')) else
        'Test/audit evidence' if '/tests/' in f['path'] else 'Application/service/data logic') for f in data['files']])
    result=re.search(r'Ran (\d+) tests in ([\d.]+)s',raw)
    assert result and re.search(r'^OK\s*$',raw,re.M), 'Acceptance run must finish successfully before generation'
    latest=f'The current captured acceptance run passed **{result[1]} tests in {result[2]} seconds (OK)**.'
    for key,value in {'LATEST_TEST_RESULT':latest,'TABLE_CATALOG':catalog,'DATA_DICTIONARY':'\n\n'.join(dictionary),'FUNCTION_REFERENCE':'\n\n'.join(functions),
        'TEST_CASES':tests,'ROUTE_INVENTORY':routes,'DEFENSE_QUESTIONS':'\n\n'.join(qparts),'GLOSSARY':glossary,'SOURCE_INDEX':sources}.items():
        source=source.replace('{{'+key+'}}',value)
    assert not re.search(r'\{\{[A-Z_]+\}\}',source)
    (HERE/'FULL_DOCUMENTATION.md').write_text(source,encoding='utf-8')
    return source


def parse(source):
    lines=source.splitlines();blocks=[];i=0;table_count=0;context='Reference'
    while i<len(lines):
        line=lines[i].strip()
        if not line: i+=1;continue
        if line.startswith('```'):
            code=[];i+=1
            while i<len(lines) and not lines[i].startswith('```'): code.append(lines[i]);i+=1
            blocks.append(('code','\n'.join(code)));i+=1;continue
        m=re.match(r'^(#{1,3}) (.+)',line)
        if m:
            context=m[2];blocks.append(('heading',(len(m[1]),m[2])));i+=1;continue
        m=re.match(r'!\[(.*?)\]\((.*?)\)',line)
        if m: blocks.append(('image',(m[1],HERE/m[2])));i+=1;continue
        if line.startswith('|'):
            rows=[]
            while i<len(lines) and lines[i].strip().startswith('|'):
                cells=[x.strip() for x in lines[i].strip().strip('|').split('|')]
                if not all(re.fullmatch(r':?-+:?',c) for c in cells): rows.append(cells)
                i+=1
            table_count+=1;caption=f'Table {table_count}. {context}'
            blocks.append(('table',(caption,rows)));continue
        if line=='<!-- pagebreak -->': blocks.append(('break',None));i+=1;continue
        m=re.match(r'^(?:- |\d+\. )(.+)',line)
        if m: blocks.append(('list',line));i+=1;continue
        parts=[line];i+=1
        while i<len(lines) and lines[i].strip() and not re.match(r'^(#|\||```|!\[|- |\d+\. |<!--)',lines[i]): parts.append(lines[i].strip());i+=1
        blocks.append(('text',' '.join(parts)))
    return blocks


def plain(s): return re.sub(r'\*\*|`','',s)
def rich(s):
    s=html.escape(str(s))
    s=re.sub(r'\*\*(.+?)\*\*',r'<b>\1</b>',s)
    s=re.sub(r'`(.+?)`',r'<font name="Courier">\1</font>',s)
    return s


def fonts():
    for name,filename in [('DocBody','arial.ttf'),('DocBold','arialbd.ttf'),('DocItalic','ariali.ttf')]:
        pdfmetrics.registerFont(TTFont(name,'C:/Windows/Fonts/'+filename))
    pdfmetrics.registerFontFamily('DocBody',normal='DocBody',bold='DocBold',italic='DocItalic',boldItalic='DocBold')


class PDFDocument(BaseDocTemplate):
    def __init__(self,path,title=TITLE):
        super().__init__(str(path),pagesize=A4,leftMargin=19*mm,rightMargin=19*mm,topMargin=20*mm,bottomMargin=19*mm,
                         title=title,author='Project documentation',subject=SUBTITLE)
        self.addPageTemplates(PageTemplate(id='main',frames=[Frame(self.leftMargin,self.bottomMargin,self.width,self.height,id='body')],onPage=self.page))
    def page(self,c,doc):
        c.saveState()
        if doc.page>1:
            c.setStrokeColor(colors.HexColor(GOLD));c.line(19*mm,283*mm,191*mm,283*mm)
            c.setFont('DocBody',7);c.setFillColor(colors.HexColor(INK));c.drawString(19*mm,286*mm,'BARANGAY MINANTE 1 • TECHNICAL DOCUMENTATION')
        c.setFont('DocBody',7);c.drawString(19*mm,11*mm,DATE);c.drawRightString(191*mm,11*mm,str(doc.page));c.restoreState()
    def afterFlowable(self,flowable):
        if isinstance(flowable,Paragraph) and hasattr(flowable,'outline'):
            level,key=flowable.outline
            self.canv.bookmarkPage(key);self.canv.addOutlineEntry(flowable.getPlainText(),key,level,False)
            if level<2:self.notify('TOCEntry',(level,flowable.getPlainText(),self.page,key))


def pdf_styles():
    return {
        'body':ParagraphStyle('Body',fontName='DocBody',fontSize=9.4,leading=13.4,spaceAfter=7,textColor=colors.HexColor(INK)),
        'h1':ParagraphStyle('H1',fontName='DocBold',fontSize=18,leading=22,spaceAfter=13,textColor=colors.HexColor(NAVY),keepWithNext=True),
        'h2':ParagraphStyle('H2',fontName='DocBold',fontSize=12,leading=16,spaceBefore=9,spaceAfter=7,textColor=colors.HexColor(NAVY),keepWithNext=True),
        'h3':ParagraphStyle('H3',fontName='DocBold',fontSize=10.5,leading=14,spaceBefore=8,spaceAfter=6,textColor=colors.HexColor(NAVY),keepWithNext=True),
        'cell':ParagraphStyle('Cell',fontName='DocBody',fontSize=7.6,leading=10,wordWrap='CJK',textColor=colors.HexColor(INK)),
        'cap':ParagraphStyle('Caption',fontName='DocBold',fontSize=8.5,leading=11,spaceBefore=7,spaceAfter=6,textColor=colors.HexColor(NAVY),keepWithNext=True),
        'center':ParagraphStyle('Center',fontName='DocBody',fontSize=12,leading=19,alignment=TA_CENTER,spaceAfter=16,textColor=colors.HexColor(INK)),
        'cover':ParagraphStyle('Cover',fontName='DocBold',fontSize=27,leading=35,alignment=TA_CENTER,spaceAfter=24,textColor=colors.HexColor(NAVY)),
        'code':ParagraphStyle('Code',fontName='Courier',fontSize=7.4,leading=10,spaceAfter=9,backColor=colors.HexColor('#F2F6FA')),
    }


def create_pdf(blocks,path,front=True):
    s=pdf_styles();story=[];doc=PDFDocument(path)
    if front:
        story.extend([Spacer(1,40*mm),Paragraph(TITLE,s['cover']),Paragraph(SUBTITLE,s['center']),Spacer(1,12*mm),
            Paragraph(FULL_TITLE,s['center']),Spacer(1,20*mm),Paragraph('Source-grounded local implementation edition<br/>'+DATE,s['center']),PageBreak(),
            Paragraph('Document Information',s['h1']),Paragraph('Purpose: capstone research, defense preparation, user training, technical handover and maintenance.',s['body']),
            Paragraph('Prepared from the local source and read-only SQLite schema. No institutional approval, author identity or sign-off is asserted. The project team should complete its required institutional cover/approval forms separately.',s['body']),
            Paragraph('Evidence: prior October 5 audit plus the current captured acceptance run. Current capabilities and partial workflows are distinguished throughout. Repository identity is supplied by the project owner; no remote commit is certified.',s['body']),
            Paragraph('Editable counterpart: '+NAME+'.docx. Narrative source, schema evidence, generation scripts and validation summary are included in documentation/.',s['body']),PageBreak(),
            Paragraph('Table of Contents',s['h1'])])
        toc=TableOfContents();toc.levelStyles=[ParagraphStyle('TOC0',fontName='DocBold',fontSize=9,leading=14,spaceBefore=5),ParagraphStyle('TOC1',fontName='DocBody',fontSize=8,leading=12,leftIndent=12)]
        story.extend([toc,PageBreak(),Paragraph('List of Figures',s['h1'])])
        for kind,value in blocks:
            if kind=='image':story.append(Paragraph(html.escape(value[0]),s['body']))
        story.extend([PageBreak(),Paragraph('List of Tables',s['h1'])])
        for kind,value in blocks:
            if kind=='table':story.append(Paragraph(html.escape(value[0]),s['body']))
    counter=0
    for kind,value in blocks:
        if kind=='heading':
            level,label=value;counter+=1
            if level==1 and story:story.append(PageBreak())
            para=Paragraph(rich(label),s['h'+str(level)]);para.outline=(min(level-1,1),f'h{counter}') if level<=2 else (2,f'h{counter}')
            # Word function subsections do not create broken PDF outline jumps.
            if level==3: del para.outline
            story.append(para)
        elif kind in {'text','list'}:story.append(Paragraph(rich(value),s['body']))
        elif kind=='code':story.append(Preformatted('\n'.join(textwrap.fill(line,103,replace_whitespace=False,drop_whitespace=False) if len(line)>103 else line for line in value.splitlines()),s['code']))
        elif kind=='break':story.append(PageBreak())
        elif kind=='image':
            caption,file=value
            with PILImage.open(file) as im:w,h=im.size
            scale=min(doc.width/w,450/h)
            story.append(KeepTogether([Image(str(file),width=w*scale,height=h*scale),Paragraph(html.escape(caption),s['cap'])]))
        elif kind=='table':
            caption,rows=value;n=len(rows[0]);widths=[doc.width/n]*n
            if n==3:widths=[doc.width*.23,doc.width*.39,doc.width*.38]
            if n==4:widths=[doc.width*.09,doc.width*.29,doc.width*.40,doc.width*.22] if rows[0][0]=='ID' else [doc.width*.13,doc.width*.33,doc.width*.27,doc.width*.27]
            if n==5:widths=[doc.width*.27,doc.width*.17,doc.width*.30,doc.width*.11,doc.width*.15]
            rendered=[[Paragraph(rich(c),s['cell']) for c in row] for row in rows]
            table=Table(rendered,colWidths=widths,repeatRows=1,hAlign='LEFT')
            table.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#E6EEF6')),('VALIGN',(0,0),(-1,-1),'TOP'),
                ('GRID',(0,0),(-1,-1),.35,colors.HexColor('#C9D4E0')),('LEFTPADDING',(0,0),(-1,-1),5),('RIGHTPADDING',(0,0),(-1,-1),5),
                ('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5)]))
            story.extend([Paragraph(html.escape(caption),s['cap']),table,Spacer(1,9)])
    doc.multiBuild(story)


def word_text(paragraph,text):
    for part in re.split(r'(\*\*.*?\*\*|`.*?`)',str(text)):
        run=paragraph.add_run(part[2:-2] if part.startswith('**') else part[1:-1] if part.startswith('`') else part)
        if part.startswith('**'):run.bold=True
        if part.startswith('`'):run.font.name='Consolas';run.font.size=Pt(8)


def create_docx(blocks,path,front=True):
    doc=Document();sec=doc.sections[0];sec.page_width=Inches(8.27);sec.page_height=Inches(11.69)
    sec.top_margin=sec.bottom_margin=Inches(.75);sec.left_margin=sec.right_margin=Inches(.75)
    normal=doc.styles['Normal'];normal.font.name='Arial';normal.font.size=Pt(10);normal.paragraph_format.space_after=Pt(7)
    for level,size in [(1,18),(2,13),(3,11)]:
        style=doc.styles[f'Heading {level}'];style.font.name='Arial';style.font.size=Pt(size);style.font.color.rgb=RGBColor.from_string('082F5B')
    footer=sec.footer.paragraphs[0];footer.text=DATE+'  •  ';footer.alignment=2
    field=OxmlElement('w:fldSimple');field.set(qn('w:instr'),'PAGE');footer._p.append(field)
    header=sec.header.paragraphs[0];header.text='BARANGAY MINANTE 1 • TECHNICAL DOCUMENTATION';header.style='Caption'
    headings=[(v[0],v[1]) for k,v in blocks if k=='heading']
    if front:
        doc.add_paragraph('\n\n');doc.add_heading(TITLE,0);doc.add_paragraph(SUBTITLE,'Subtitle');doc.add_paragraph(FULL_TITLE)
        doc.add_paragraph('\nSource-grounded local implementation edition\n'+DATE);doc.add_page_break()
        doc.add_heading('Document Information',1)
        doc.add_paragraph('Purpose: capstone research, defense preparation, user training, technical handover and maintenance. Based on local source and read-only schema; no institutional approval or author identity is fabricated.')
        doc.add_paragraph('Project team/institution approval forms should be completed by the responsible authors and institution. This editable version contains native Word text and tables; figures are embedded images.')
        doc.add_paragraph('The table of contents below links to document headings. Use Word’s References tools if a page-numbered contents field is required after editing. The PDF includes a populated page-numbered contents list.')
        doc.add_page_break();doc.add_heading('Table of Contents',1)
        for i,(level,label) in enumerate(headings,1):
            if level>2:continue
            p=doc.add_paragraph();p.paragraph_format.left_indent=Inches(.15 if level==2 else 0)
            link=OxmlElement('w:hyperlink');link.set(qn('w:anchor'),f'h{i}');run=OxmlElement('w:r');t=OxmlElement('w:t');t.text=label;run.append(t);link.append(run);p._p.append(link)
        doc.add_page_break();doc.add_heading('List of Figures',1)
        for kind,value in blocks:
            if kind=='image':doc.add_paragraph(value[0])
        doc.add_page_break();doc.add_heading('List of Tables',1)
        for kind,value in blocks:
            if kind=='table':doc.add_paragraph(value[0])
    counter=0
    for kind,value in blocks:
        if kind=='heading':
            level,label=value;counter+=1
            if level==1 and (front or counter>1):doc.add_page_break()
            p=doc.add_heading(label,level);start=OxmlElement('w:bookmarkStart');start.set(qn('w:id'),str(counter));start.set(qn('w:name'),f'h{counter}')
            end=OxmlElement('w:bookmarkEnd');end.set(qn('w:id'),str(counter));p._p.insert(0,start);p._p.append(end)
        elif kind in {'text','list'}:
            p=doc.add_paragraph();word_text(p,value)
        elif kind=='break':doc.add_page_break()
        elif kind=='code':
            p=doc.add_paragraph();r=p.add_run(value);r.font.name='Consolas';r.font.size=Pt(8)
        elif kind=='image':
            caption,file=value
            with PILImage.open(file) as im:w,h=im.size
            width=min(6.6,7.4*w/h);doc.add_picture(str(file),width=Inches(width));doc.add_paragraph(caption,'Caption')
        elif kind=='table':
            caption,rows=value;p=doc.add_paragraph(caption,'Caption');p.paragraph_format.keep_with_next=True
            table=doc.add_table(rows=0,cols=len(rows[0]));table.style='Table Grid'
            for idx,row in enumerate(rows):
                cells=table.add_row().cells
                for cell,text in zip(cells,row):
                    p=cell.paragraphs[0];word_text(p,text)
                    for run in p.runs:run.font.size=Pt(8);run.bold=idx==0 or run.bold
                if idx==0:
                    repeat=OxmlElement('w:tblHeader');table.rows[0]._tr.get_or_add_trPr().append(repeat)
            doc.add_paragraph()
    doc.core_properties.title=TITLE;doc.core_properties.subject=SUBTITLE;doc.core_properties.author='Project documentation'
    doc.save(path)


def main():
    fonts();data=collect();render_figures();source=expand_source(data);blocks=parse(source)
    create_docx(blocks,ROOT/(NAME+'.docx'));create_pdf(blocks,ROOT/(NAME+'.pdf'))
    cheat=parse((HERE/'DEFENSE_CHEAT_SHEET.md').read_text(encoding='utf-8'))
    create_docx(cheat,ROOT/'Barangay_Minante_1_Defense_Cheat_Sheet.docx',False)
    create_pdf(cheat,ROOT/'Barangay_Minante_1_Defense_Cheat_Sheet.pdf',False)
    print(json.dumps({'docx':NAME+'.docx','pdf':NAME+'.pdf','figures':sum(k=='image' for k,v in blocks),
                     'tables':sum(k=='table' for k,v in blocks),'defense_questions':sum(map(len,DEFENSE.values()))}))

if __name__=='__main__':main()
