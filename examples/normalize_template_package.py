"""Normalize the invented artifact-tool export's XLSX content-type declarations.

No worksheet, value, formula, relationship or style is edited. This is only for
the generated example template, not for repairing uploaded user workbooks.
"""
from io import BytesIO
from pathlib import Path
import sys
import xml.etree.ElementTree as ET
import zipfile

MAIN = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml'
NS = 'http://schemas.openxmlformats.org/package/2006/content-types'


def normalize(path):
    path = Path(path)
    with zipfile.ZipFile(path) as archive:
        if 'xl/workbook.xml' not in archive.namelist():
            raise ValueError('Expected an XLSX workbook part.')
        raw = archive.read('[Content_Types].xml')
        types = ET.fromstring(raw)
        if types.tag != '{'+NS+'}Types':
            raise ValueError('Unexpected content-type namespace.')
        if any(any(marker in element.get('ContentType', '').lower()
                   for marker in ('macroenabled', 'vbaproject', 'activex', 'encrypted'))
               for element in types):
            raise ValueError('Only the macro-free invented template can be normalized.')
        existing = [e for e in types if e.tag == '{'+NS+'}Override'
                    and e.get('PartName') == '/xl/workbook.xml']
        if existing and (len(existing) != 1 or existing[0].get('ContentType') != MAIN):
            raise ValueError('Conflicting workbook declaration.')
        default = [e for e in types if e.tag == '{'+NS+'}Default' and e.get('Extension') == 'xml']
        if len(default) != 1 or default[0].get('ContentType') not in (MAIN, 'application/xml'):
            raise ValueError('Unexpected generated XML default.')
        default[0].set('ContentType', 'application/xml')
        if not existing:
            ET.SubElement(types, '{'+NS+'}Override', PartName='/xl/workbook.xml', ContentType=MAIN)
        ET.register_namespace('', NS)
        replacement = ET.tostring(types, encoding='utf-8', xml_declaration=True)
        stream = BytesIO()
        with zipfile.ZipFile(stream, 'w') as out:
            for info in archive.infolist():
                out.writestr(info, replacement if info.filename == '[Content_Types].xml' else archive.read(info.filename))
    with zipfile.ZipFile(BytesIO(stream.getvalue())) as out, zipfile.ZipFile(path) as original:
        assert out.namelist() == original.namelist()
        assert all(out.read(name) == original.read(name) for name in out.namelist() if name != '[Content_Types].xml')
    path.write_bytes(stream.getvalue())


if __name__ == '__main__':
    normalize(sys.argv[1])
