"""Avaliação com exemplos JSONL: {"texto": "...", "desafios": ["D001"]}."""
import argparse
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from desafios.catalog import load_catalog
from desafios.semantic import SemanticEngine


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('examples', type=Path)
    args = parser.parse_args()
    rows = [json.loads(line) for line in args.examples.read_text(encoding='utf-8').splitlines() if line.strip()]
    if not rows:
        raise ValueError('Conjunto de avaliação vazio.')
    catalog, version = load_catalog()
    valid = {r['id_desafio'] for r in catalog}
    for row in rows:
        if not row.get('texto', '').strip() or not row.get('desafios') or not set(row['desafios']) <= valid:
            raise ValueError('Exemplo sem texto, sem rótulo ou com desafio inexistente.')
    model = SemanticEngine(catalog, version)
    top1, hit3, recall3 = 0, 0, 0.0
    for row in rows:
        expected = set(row['desafios'])
        results = model.rank(row['texto'], top_k=3, min_score=-1)
        predicted = [r['id_desafio'] for r in results]
        top1 += predicted[0] in expected
        hit3 += bool(expected.intersection(predicted))
        recall3 += len(expected.intersection(predicted)) / len(expected)
    print(json.dumps({'exemplos': len(rows), 'acerto_primeira_indicacao': top1 / len(rows),
                      'presenca_de_ao_menos_um_correto_top3': hit3 / len(rows),
                      'recall_medio_top3': recall3 / len(rows), 'base_sha256': version,
                      'model_revision': model.revision}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
