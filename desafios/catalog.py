import hashlib
import json
from pathlib import Path

FIELDS = ('id_desafio', 'portfolio', 'desafio', 'objetivo', 'meta', 'ods')
DEFAULT_PATH = Path(__file__).resolve().parents[1] / 'data' / 'desafios.json'


def load_catalog(path=DEFAULT_PATH):
    raw = Path(path).read_bytes()
    rows = json.loads(raw)
    if not rows:
        raise ValueError('O catálogo está vazio.')
    ids = set()
    for row in rows:
        if any(key not in row for key in FIELDS):
            raise ValueError('O catálogo não contém todos os campos obrigatórios.')
        if not row['id_desafio'] or row['id_desafio'] in ids or not row['desafio']:
            raise ValueError('Identificador duplicado/vazio ou desafio sem descrição.')
        ids.add(row['id_desafio'])
    return rows, hashlib.sha256(raw).hexdigest()


def describe(result):
    if not result.get('id_desafio'):
        return result['status']
    return '\n'.join([
        f"{result['id_desafio']} — {result['desafio']}",
        f"Portfólio: {result['portfolio']}",
        f"Objetivo: {result['objetivo']}",
        f"Meta: {result['meta']}",
        f"ODS: {result['ods'] or 'Não informado na base'}",
        f"Similaridade: {result['score']:.4f} (não é probabilidade)",
        f"Situação: {result['status']}",
        f"Modelo: {result['model']}",
        f"Versão do modelo: {result['revision']}",
        f"Base SHA-256: {result['catalog_version']}",
    ])
