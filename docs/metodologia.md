# Metodologia e validação

## Unidade de análise

Cada linha representa um item. A pessoa confirma as colunas; seus textos são concatenados por linha com separação por quebra de linha. Nomes sugeridos ajudam a seleção, mas não substituem a confirmação. Autores, datas e códigos não entram automaticamente. Fórmulas são lidas pelo resultado salvo; ausência desse resultado bloqueia a análise da seleção.

Em projetos, o texto é extraído por página. Nenhuma seção recebe peso especial nesta versão: objetivos, justificativas, bibliografia e demais conteúdos extraídos participam da mesma regra. A ponderação de seções é uma melhoria a avaliar, não funcionalidade entregue.

## Segmentação e ranking

1. Carregar o catálogo validando identificadores únicos e descrições não vazias.
2. Segmentar descrições de desafios e entradas em janelas limitadas pelo tokenizer e `max_seq_length` do modelo. Reservar os tokens especiais e usar sobreposição de até 24 tokens. Preservar offsets e o texto original para evidências.
3. Gerar embeddings normalizados em CPU, em lotes de 16.
4. Comparar cada trecho de entrada com os trechos dos desafios por produto escalar, equivalente ao cosseno para vetores normalizados.
5. Para cada trecho de entrada, selecionar a maior similaridade entre os trechos de cada desafio.
6. Para cada desafio, calcular a média dos até três trechos de entrada com maior similaridade. Ordenar de forma estável, usando a ordem da base como desempate técnico.
7. Em projetos, retornar até três desafios que atingem o critério. Em tabelas, retornar o primeiro candidato, sinalizando baixa similaridade quando aplicável; não tratar isso como enquadramento definitivo.
8. Recuperar os vínculos exatamente pelo registro classificado. Campo ODS vazio recebe “Não informado na base”; textos de metas encerradas permanecem intactos.

Essa agregação é uma hipótese inicial. Pode supervalorizar menções pontuais ou trechos sobrepostos. Não equivale a medir cobertura do projeto. Um reranker, ponderação de seções, sinônimos de domínio ou outro encoder só deve entrar após comparação com um conjunto validado.

## Revisão e rastreabilidade

Os limiares 0,35 e 0,03 são parâmetros experimentais. Texto com menos de oito palavras também é sinalizado para revisão. A diferença registrada é entre os dois primeiros candidatos do ranking geral. Não é uma margem específica de cada resultado.

Relatórios registram o identificador do modelo, a revisão resolvida dos pesos, SHA-256 do catálogo, critérios utilizados e evidências. A revisão padrão está fixada em `e8f8c211226b894fcb81acc59f3b34ba3efd5f42`. Defina `MODEL_REVISION` para testar outra revisão de forma explícita e reinicie o app. O catálogo e o código devem ser versionados juntos.

## Avaliação por especialistas

Criar exemplos de publicações, tecnologias, compromissos, soluções e projetos, com um ou mais desafios aceitáveis definidos por avaliadores. Incluir itens sem aderência, textos curtos, temas parecidos, negações e siglas. Separar conjuntos para escolher parâmetros e para medir qualidade final, sem duplicatas ou versões do mesmo documento entre eles.

Formato JSONL para o script de ranking (somente exemplos com pelo menos um desafio válido):

```json
{"texto":"Descrição validada do item", "desafios":["D001"]}
```

`scripts/evaluate.py` mede acerto do primeiro candidato, presença de pelo menos um correto entre três e recall médio entre três, sem filtro de similaridade. Não mede sozinho a qualidade de abstenção. Avaliar separadamente os exemplos sem aderência, a taxa de recomendações indevidas, os casos enviados para revisão e cobertura versus erro em diferentes limiares. Relatar os resultados por tipo de item e não apenas a média geral. Os testes com modelo simulado não substituem essa avaliação.

## Atualização do catálogo

Executar `scripts/import_catalog.py` com planilha cuja aba `Desafios` tenha os seis cabeçalhos originais. Valores ausentes não devem ser completados por inferência. Conferir registros adicionados/removidos e vínculos, especialmente metas encerradas, antes de publicar. O programa não recebe instruções executáveis do catálogo ou dos documentos; eles são dados de entrada.
