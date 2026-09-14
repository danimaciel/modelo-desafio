# Metodologia e validação

## Unidade de análise

A ideia desta proposta é comparar o conteúdo dos documentos com os desafios para inovação e apresentar sugestões que possam ser conferidas por quem conhece o tema. Abaixo, explico como a primeira versão faz essa comparação e o que ainda precisamos avaliar.

Cada linha representa um item. A pessoa confirma as colunas; seus textos são concatenados por linha com separação por quebra de linha. Nomes sugeridos ajudam a seleção, mas não substituem a confirmação. Autores, datas e códigos não entram automaticamente. Fórmulas são lidas pelo resultado salvo; ausência desse resultado bloqueia a análise da seleção.

Em projetos, o texto é extraído por página. Nenhuma seção recebe peso especial nesta versão: objetivos, justificativas, bibliografia e demais conteúdos extraídos participam da mesma regra. A ponderação de seções é uma melhoria a avaliar, não funcionalidade entregue.

## Segmentação e ranking

1. O sistema abre a base e confere se cada desafio tem um identificador único e uma descrição preenchida.
2. As descrições e os textos enviados são divididos em trechos que cabem no limite do modelo (`max_seq_length`). Há uma sobreposição de até 24 tokens entre trechos para manter parte do contexto. O texto original e sua posição ficam disponíveis para apresentar as evidências.
3. O SBERT transforma os trechos em representações numéricas normalizadas, chamadas embeddings. O processamento ocorre em CPU, em lotes de 16.
4. Cada trecho do documento é comparado aos trechos dos desafios. O cálculo usa o produto escalar, equivalente à similaridade de cosseno para esses vetores normalizados.
5. Para cada trecho do documento, o sistema guarda a maior similaridade encontrada com cada desafio.
6. A pontuação de um desafio é a média dos até três trechos do documento mais semelhantes a ele. Os desafios são ordenados por essa pontuação; em caso de empate exato, vale a ordem da base.
7. Para projetos, aparecem até três desafios que atingem o critério configurado. Para tabelas, aparece o primeiro candidato por linha, com aviso quando a similaridade é baixa.
8. Os vínculos são recuperados do registro do desafio. Quando falta ODS, o resultado informa “Não informado na base”. As marcações de metas encerradas são mantidas.

Essa agregação é uma hipótese inicial. Pode supervalorizar menções pontuais ou trechos sobrepostos. Não equivale a medir cobertura do projeto. Um reranker, ponderação de seções, sinônimos de domínio ou outro encoder só deve entrar após comparação com um conjunto validado.

## Revisão e rastreabilidade

Os limiares 0,35 e 0,03 são parâmetros experimentais. Texto com menos de oito palavras também é sinalizado para revisão. A diferença registrada é entre os dois primeiros candidatos do ranking geral. Não é uma margem específica de cada resultado.

Relatórios registram o identificador do modelo, a revisão resolvida dos pesos, SHA-256 do catálogo, critérios utilizados e evidências. A revisão padrão está fixada em `e8f8c211226b894fcb81acc59f3b34ba3efd5f42`. Defina `MODEL_REVISION` para testar outra revisão de forma explícita e reinicie o app. O catálogo e o código devem ser versionados juntos.

## Avaliação por especialistas

O próximo passo é reunir publicações, tecnologias, compromissos, soluções e projetos com um ou mais desafios indicados por especialistas. Também precisamos de exemplos sem aderência, textos curtos, temas parecidos, negações e siglas, para entender onde o modelo funciona bem e onde erra.

Uma parte dos exemplos será usada para ajustar os critérios, e outra para avaliar o resultado final. O mesmo documento, suas cópias ou versões não devem aparecer nos dois grupos, pois isso pode dar uma impressão de qualidade maior do que a real.

Formato JSONL para o script de ranking (somente exemplos com pelo menos um desafio válido):

```json
{"texto":"Descrição validada do item", "desafios":["D001"]}
```

O script `scripts/evaluate.py` mede o acerto da primeira indicação, a presença de pelo menos um desafio correto entre os três primeiros e a proporção média dos desafios esperados que aparecem nesses três resultados (recall). Essa avaliação não aplica o filtro de similaridade.

Precisamos avaliar separadamente os casos sem aderência, as indicações incorretas e os itens enviados para revisão. Comparar diferentes critérios ajudará a encontrar um equilíbrio entre oferecer sugestões e evitar associações frágeis. Os resultados serão mais úteis se forem apresentados por tipo de documento, além da média geral. Os testes de funcionamento com modelo simulado não substituem essa etapa.

## Atualização do catálogo

Para atualizar a base, execute `scripts/import_catalog.py` com uma planilha que tenha a aba `Desafios` e os seis cabeçalhos originais. Confira os registros incluídos ou removidos e suas relações antes de publicar a atualização, principalmente as metas encerradas. Quando faltar uma informação, ela deve permanecer ausente até que seja confirmada na fonte.
