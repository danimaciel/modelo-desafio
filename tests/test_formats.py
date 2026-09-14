import csv
import unittest
from io import BytesIO, StringIO
import xlwt
from desafios.files import prepare_table, load_xlsx, export_xlsx, export_csv


class FormatTests(unittest.TestCase):
    def test_csv_roundtrip(self):
        raw = 'Título;Resumo;Código\r\n"Tecnologia; solo";"Descrição\ncom acento";0012\r\n'.encode('cp1252')
        converted = prepare_table(raw, '.csv', ';', 'cp1252')
        sheet = load_xlsx(converted).active
        self.assertEqual(sheet['A2'].value, 'Tecnologia; solo')
        self.assertEqual(sheet['B2'].value, 'Descrição\ncom acento')
        self.assertEqual(sheet['C2'].value, '0012')
        output = export_xlsx(converted, 'Dados', 1, {2: {'id_desafio': 'D001', 'desafio': 'Teste', 'portfolio': 'P', 'objetivo': 'O', 'meta': 'Meta\nteste', 'ods': 'ODS'}})
        rows = list(csv.reader(StringIO(export_csv(output, 'Dados', ';').decode('utf-8-sig')), delimiter=';'))
        self.assertEqual(rows[1], ['Tecnologia; solo', 'Descrição\ncom acento', '0012', 'D001 — Teste', 'P', 'O', 'Meta\nteste', 'ODS'])

    def test_csv_bad_encoding_and_formula_text(self):
        with self.assertRaises(ValueError):
            prepare_table('Descrição'.encode('cp1252'), '.csv')
        converted = prepare_table(b'Titulo,Resumo\n=1+1,solo', '.csv', ',')
        self.assertEqual(load_xlsx(converted).active['A2'].data_type, 's')
        self.assertIn("'=1+1", export_csv(converted, 'Dados', ',').decode('utf-8-sig'))

    def test_xls_sheets_and_values(self):
        source = xlwt.Workbook()
        sheet = source.add_sheet('Tecnologias')
        sheet.write(0, 0, 'Descrição')
        sheet.write(1, 0, 'Solo e água')
        sheet.write(1, 1, 12.5)
        source.add_sheet('Outra').write(0, 0, 'Preservado')
        stream = BytesIO()
        source.save(stream)
        result = load_xlsx(prepare_table(stream.getvalue(), '.xls'))
        self.assertEqual(result.sheetnames, ['Tecnologias', 'Outra'])
        self.assertEqual(result.active['A2'].value, 'Solo e água')
        self.assertEqual(result.active['B2'].value, 12.5)
        self.assertEqual(result['Outra']['A1'].value, 'Preservado')
