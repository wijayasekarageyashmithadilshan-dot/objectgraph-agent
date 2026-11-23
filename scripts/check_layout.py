"""Layout check for the paper PDFs: flags a heading in the last two lines of a column and columns
that end early (possible blank gaps; figures and the last page need a visual look).
  python scripts/check_layout.py paper.pdf
"""
import sys, re, subprocess
from xml.etree import ElementTree as ET
pdf=sys.argv[1]
xml=subprocess.run(['pdftotext','-bbox-layout',pdf,'-'],capture_output=True,text=True).stdout
xml=re.sub(r'<!DOCTYPE[^>]*>','',xml); xml=xml.replace('xmlns="http://www.w3.org/1999/xhtml"',''); xml=re.sub(r'&(?!amp;|lt;|gt;|quot;|apos;|#)','&amp;',xml)
xml=re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]','',xml)
root=ET.fromstring(xml)
head=re.compile(r'^([IVX]+\.\s+[A-Z]|[A-H]\.\s+[A-Z][A-Z]|\d+(\.\d+)?\s+[A-Z][a-z]|APPENDIX|REFERENCES|ACKNOWLEDG|TABLE [IVX]+$|Table \d+)')
for pi,page in enumerate(root.iter('page'),1):
    W=float(page.get('width')); H=float(page.get('height'))
    lines=[]
    for ln in page.iter('line'):
        words=[w.text or '' for w in ln.iter('word')]
        x=float(ln.get('xMin')); y=float(ln.get('yMax'))
        lines.append((x,y,' '.join(words)))
    for col,(lo,hi) in enumerate([(0,W/2),(W/2,W)]):
        L=[l for l in lines if lo<=l[0]<hi and l[1]<H*0.93 and l[1]>H*0.06]
        if not L: continue
        L.sort(key=lambda t:t[1])
        tail=L[-2:]
        for x,y,t in tail:
            if head.match(t.strip()) and len(t)<70:
                print(f'page {pi} col {col+1}: heading near bottom -> {t!r} (y={y:.0f}/{H:.0f})')

    for col,(lo,hi) in enumerate([(0,W/2),(W/2,W)]):
        L=[l for l in lines if lo<=l[0]<hi and H*0.06<l[1]<H*0.93]
        if L and max(l[1] for l in L) < H*0.78:
            print(f'page {pi} col {col+1}: text ends at {max(l[1] for l in L)/H:.0%} of page height (check for a blank gap)')
