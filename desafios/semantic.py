import os
import threading
import numpy as np

MODEL_NAME = 'sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2'
MODEL_REVISION = 'e8f8c211226b894fcb81acc59f3b34ba3efd5f42'


def token_chunks(text, tokenizer, limit):
    """Preserva o texto original e respeita o limite de tokens com sobreposição."""
    if not text or not text.strip():
        return []
    budget = limit - tokenizer.num_special_tokens_to_add(pair=False)
    if budget < 8:
        raise ValueError('Limite de tokens inválido.')
    encoded = tokenizer(text, add_special_tokens=False, return_offsets_mapping=True,
                        truncation=False, verbose=False)
    offsets = encoded['offset_mapping']
    chunks = []
    step = max(1, budget - min(24, budget // 4))
    start = 0
    while start < len(offsets):
        end = min(start + budget, len(offsets))
        chunks.append(text[offsets[start][0]:offsets[end - 1][1]])
        if end == len(offsets):
            break
        start += step
    return chunks


class SemanticEngine:
    def __init__(self, catalog, catalog_version, model=None):
        self.catalog = catalog
        self.catalog_version = catalog_version
        self.lock = threading.Lock()
        if model is None:
            from sentence_transformers import SentenceTransformer
            import torch
            torch.set_num_threads(max(1, int(os.getenv('TORCH_NUM_THREADS', '2'))))
            model = SentenceTransformer(MODEL_NAME, device='cpu',
                                       revision=os.getenv('MODEL_REVISION') or MODEL_REVISION)
        self.model = model
        try:
            self.revision = str(model[0].auto_model.config._commit_hash or 'não resolvida')
        except (AttributeError, TypeError, KeyError):
            self.revision = 'não resolvida'
        texts, self.owners = [], []
        for index, row in enumerate(catalog):
            # Só o desafio define o ranking; relações institucionais são recuperadas depois.
            parts = self.chunks(row['desafio'])
            texts.extend(parts)
            self.owners.extend([index] * len(parts))
        self.vectors = self.encode(texts)

    def chunks(self, text):
        return token_chunks(text, self.model.tokenizer, self.model.max_seq_length)

    def encode(self, texts):
        with self.lock:
            return np.asarray(self.model.encode(texts, batch_size=16,
                              normalize_embeddings=True, convert_to_numpy=True,
                              show_progress_bar=False))

    def rank(self, text, top_k=1, min_score=0.35, min_margin=0.03, pages=None):
        if not text or not text.strip():
            return [{'status': 'Sem texto nas colunas selecionadas; não analisado.'}]
        source = pages if pages is not None else [(None, text)]
        chunks, locations = [], []
        for page, content in source:
            parts = self.chunks(content)
            chunks.extend(parts)
            locations.extend([page] * len(parts))
        if len(chunks) > 2000:
            raise ValueError('Texto excede 2.000 trechos. Divida o documento e tente novamente.')
        if not chunks:
            return [{'status': 'Sem texto extraível; não analisado.'}]
        similarities = self.encode(chunks) @ self.vectors.T
        per_challenge = np.column_stack([
            similarities[:, np.array(self.owners) == i].max(axis=1)
            for i in range(len(self.catalog))
        ])
        # Média dos até três trechos mais aderentes. Heurística a validar por especialistas.
        scores = np.sort(per_challenge, axis=0)[-min(3, len(chunks)):].mean(axis=0)
        order = np.argsort(-scores, kind='stable')
        margin = float(scores[order[0]] - scores[order[1]]) if len(order) > 1 else 1.0
        results = []
        for index in order[:max(1, min(top_k, 3))]:
            score = float(scores[index])
            if top_k > 1 and score < min_score:
                continue
            short = len(text.split()) < 8
            flags = []
            if score < min_score:
                flags.append('baixa similaridade')
            if margin < min_margin:
                flags.append('primeiros candidatos próximos')
            if short:
                flags.append('texto curto')
            status = 'Requer revisão: ' + '; '.join(flags) if flags else 'Sugestão preliminar; validar com especialista'
            best = np.argsort(-per_challenge[:, index], kind='stable')[:3]
            results.append({**self.catalog[index], 'score': score, 'margin': margin,
                            'status': status, 'model': MODEL_NAME, 'revision': self.revision,
                            'catalog_version': self.catalog_version,
                            'evidence': [{'page': locations[j], 'text': chunks[j],
                                          'score': float(per_challenge[j, index])} for j in best]})
        return results
