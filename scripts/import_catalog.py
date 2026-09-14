"""python scripts/import_catalog.py fonte.xlsx --output data/desafios.json"""
import argparse
import hashlib
import json
from datetime import date
from pathlib import Path
import openpyxl


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('source', type=Path)
    parser.add_argument('--output', type=Path, default=Path('data/desafios.json'))
    args = parser.parse_args()
    workbook = openpyxl.load_workbook(args.source, read_only=True, data_only=True)
    sheet = workbook['Desafios']
    values = iter(sheet.values)
    expected = ['id_desafio', 'Portfólio', 'Desafio para Inovação', 'Objetivo Estratégico', 'Meta Estratégica', 'ODS']
    if list(next(values)) != expected:
        raise ValueError('Cabeçalhos diferentes do formato esperado. Consulte a documentação.')
    keys = ['id_desafio', 'portfolio', 'desafio', 'objetivo', 'meta', 'ods']
    rows = [dict(zip(keys, row)) for row in values if any(v is not None for v in row)]
    ids = [r['id_desafio'] for r in rows]
    if not rows or len(ids) != len(set(ids)) or any(not r['id_desafio'] or not r['desafio'] for r in rows):
        raise ValueError('Base vazia ou com identificadores duplicados/vazios ou descrições ausentes.')
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    args.output.with_name('proveniencia.json').write_text(json.dumps({
        'arquivo_fonte': args.source.name, 'sha256_fonte': hashlib.sha256(args.source.read_bytes()).hexdigest(),
        'data_importacao': date.today().isoformat(), 'aba': sheet.title, 'registros': len(rows),
        'relacoes': 'Reproduzidas da planilha fornecida; não validadas externamente.'
    }, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f'{len(rows)} desafios importados. Revise o diff antes de publicar.')


if __name__ == '__main__':
    main()
