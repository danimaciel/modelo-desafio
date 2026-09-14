import json
import re
import unittest
from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory

import numpy as np
import openpyxl

from desafios.catalog import load_catalog, describe
from desafios.files import export_xlsx, load_xlsx, row_text, suggested_columns, export_pdf_table
from desafios.semantic import token_chunks, SemanticEngine


class Tokenizer:
    def num_special_tokens_to_add(self, pair=False):
        return 2

    def __call__(self, text, **kwargs):
        return {'offset_mapping': [(m.start(), m.end()) for m in re.finditer(r'\S+', text)]}


class Model:
    tokenizer = Tokenizer()
    max_seq_length = 20

    def encode(self, texts, **kwargs):
        vectors = np.array([[1 + t.lower().count('solo'), 1 + t.lower().count('leite')]
                            for t in texts], dtype=float)
        return vectors / np.linalg.norm(vectors, axis=1, keepdims=True)


class CoreTests(unittest.TestCase):
    def test_catalog_integrity_and_missing_ods(self):
        rows, version = load_catalog()
        self.assertEqual(len(rows), 107)
        self.assertEqual(len({r['id_desafio'] for r in rows}), 107)
        self.assertEqual(sum(not r['ods'] for r in rows), 1)
        self.assertEqual(sum('META ENCERRADA' in r['meta'] for r in rows), 44)
        self.assertEqual(len(version), 64)

    def test_duplicate_catalog_is_rejected(self):
        rows, _ = load_catalog()
        with TemporaryDirectory() as temp:
            path = Path(temp) / 'base.json'
            path.write_text(json.dumps([rows[0], rows[0]]), encoding='utf-8')
            with self.assertRaises(ValueError):
                load_catalog(path)

    def test_chunking_keeps_tail_and_obeys_limit(self):
        text = ' '.join(f'token{i}' for i in range(100))
        chunks = token_chunks(text, Tokenizer(), 20)
        self.assertIn('token99', chunks[-1])
        self.assertTrue(all(len(c.split()) <= 18 for c in chunks))
        self.assertEqual(set(text.split()), set(' '.join(chunks).split()))

    def test_no_cross_row_leakage_and_formula_preservation(self):
        workbook = openpyxl.Workbook()
        sheet = workbook.active
        sheet.title = 'Itens'
        sheet.append(['Título', 'Resumo', 'Cálculo'])
        sheet.append(['Solo', 'Recuperação', '=1+2'])
        sheet.append(['Leite', 'Qualidade', None])
        sheet['A2'].font = openpyxl.styles.Font(bold=True)
        workbook.create_sheet('Outra')['B2'] = 'preservado'
        raw = BytesIO()
        workbook.save(raw)
        self.assertEqual(row_text(sheet, 2, [1, 2]), 'Solo\nRecuperação')
        result = export_xlsx(raw.getvalue(), 'Itens', 1, {2: '=texto', 3: 'D002'})
        exported = load_xlsx(result)
        self.assertEqual(exported['Itens']['C2'].value, '=1+2')
        self.assertEqual(exported['Itens']['D2'].data_type, 's')
        self.assertEqual(exported['Itens']['D3'].value, 'D002')
        self.assertTrue(exported['Itens']['A2'].font.bold)
        self.assertEqual(exported['Outra']['B2'].value, 'preservado')
        repeated = load_xlsx(export_xlsx(result, 'Itens', 1, {2: 'novo'}))
        self.assertEqual(repeated['Itens']['E1'].value, 'Enquadramento sugerido (2)')

    def test_pdf_table_is_text(self):
        output = load_xlsx(export_pdf_table([['Título'], ['=1+1']], {2: 'D001'}))
        self.assertEqual(output.active['A2'].data_type, 's')

    def test_suggests_text_columns(self):
        self.assertEqual(suggested_columns(['A — Autor', 'B — Título', 'C — Descrição']), [1, 2])

    def test_ranking_blank_abstention_and_linked_metadata(self):
        records = [{'id_desafio': 'A', 'desafio': 'solo solo solo', 'portfolio': 'P1',
                    'objetivo': 'O1', 'meta': 'META ENCERRADA', 'ods': None},
                   {'id_desafio': 'B', 'desafio': 'leite leite leite', 'portfolio': 'P2',
                    'objetivo': 'O2', 'meta': 'M2', 'ods': 'ODS2'}]
        model = SemanticEngine(records, 'version', Model())
        self.assertNotIn('id_desafio', model.rank(' ')[0])
        result = model.rank('solo solo solo')[0]
        self.assertEqual(result['id_desafio'], 'A')
        self.assertEqual(result['portfolio'], 'P1')
        self.assertIn('Não informado', describe(result))
        self.assertIn('META ENCERRADA', describe(result))
        self.assertEqual(model.rank('outro assunto', top_k=3, min_score=0.99), [])
        self.assertIn('baixa similaridade', model.rank('outro assunto', min_score=0.99)[0]['status'])


if __name__ == '__main__':
    unittest.main()
