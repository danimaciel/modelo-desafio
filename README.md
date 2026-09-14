# Modelo Desafio

### Formatos de planilha

Além de XLSX, são aceitos **XLS e CSV**, com a mesma seleção de aba, cabeçalho e colunas de texto.

- **XLS:** o resultado é entregue em XLSX. A conversão mantém os valores e as abas, mas substitui fórmulas pelos resultados salvos e não preserva formatação, gráficos ou macros.
- **CSV:** o separador e a codificação são selecionados na interface. Há suporte a ponto e vírgula, vírgula, tabulação e barra vertical; as codificações disponíveis são UTF-8, Windows-1252 e UTF-16. A prévia permite conferir a leitura. O resultado pode ser baixado em CSV (UTF-8 com BOM, usando o separador escolhido) ou XLSX. Textos que possam ser interpretados como fórmulas recebem um apóstrofo de proteção na saída CSV.

Os limites de tamanho e quantidade de linhas também se aplicam a esses formatos.

Aplicação para facilitar a identificação dos desafios para inovação da Embrapa mais relacionados a um projeto, publicação, tecnologia, compromisso ou solução. A ideia é que o usuário envie um arquivo e receba sugestões de desafios, acompanhadas de suas relações com portfólios, objetivos estratégicos, metas e ODS.

O projeto usa o modelo SBERT para comparar o significado semântico dos textos. Nesta primeira versão, a interface foi construída com Streamlit. O código e a documentação ficam neste repositório para permitir ajustes, avaliação e uma futura hospedagem na infraestrutura da Embrapa.

Esta é uma proposta em desenvolvimento. 

## Como funciona

- **Planilhas XLSX:** usuário escolhe a aba, a linha do cabeçalho e as colunas que contêm o texto. O sistema analisa cada linha e acrescenta uma coluna com o desafio sugerido e seus vínculos. Depois, o usuário baixa a cópia da planilha com os resultados.
- **Projetos em PDF:** o sistema lê o texto e apresenta até três desafios relacionados, com os trechos e as páginas que apoiam cada indicação.
- **Tabelas em PDF:** usuário confere a tabela extraída e escolhe as colunas de texto. O resultado é disponibilizado em XLSX, uma tabela por vez.

Também é possível baixar um relatório JSON com os detalhes da análise. Linhas sem texto ficam sem classificação. Textos curtos, baixa similaridade ou resultados muito próximos recebem um aviso de revisão.

As relações com portfólios, objetivos, metas e ODS vêm da base de referência. O modelo sugere o desafio; os vínculos são os que já estão registrados para ele.

## Executar localmente

Recomendado: Python 3.12, CPU e conexão para baixar o modelo na primeira execução.

```bash
python -m venv .venv
# Windows PowerShell:
.venv\Scripts\Activate.ps1
# Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

O navegador abrirá a interface local. As dependências fixam PyTorch CPU para Windows/Linux (Python 3.12); em macOS use a distribuição compatível de PyTorch e remova o sufixo `+cpu`. Não é necessário contratar API de inferência: os pesos são executados no servidor que hospeda o aplicativo. Hospedagem, memória e disponibilidade são limitações separadas.

## Base e metodologia

Para esta primeira versão, usou-se uma planilha com 107 desafios, associados a 9 portfólios, 7 objetivos e 25 textos distintos de metas. Em 44 registros, a meta está marcada como encerrada; um registro não informa ODS. Mantive essas informações como estavam na planilha.

A base está em `data/desafios.json`. O arquivo `data/proveniencia.json` registra sua origem e uma identificação digital do arquivo original, que permite conferir qual versão foi utilizada.

O modelo utilizado é o `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`, com licença Apache 2.0. Ele compara os textos enviados com a descrição de cada desafio. Textos longos são divididos em trechos, e a classificação considera os até três trechos mais semelhantes a cada desafio. A [documentação da metodologia](docs/metodologia.md) explica o cálculo e a avaliação prevista.

**Os critérios iniciais 0,35 (similaridade) e 0,03 (diferença entre primeiros candidatos) são experimentais, não calibrados.** A pontuação não é probabilidade de acerto. Não há treinamento com exemplos da Embrapa nesta versão.

## Limitações conhecidas

- Sem OCR: PDFs digitalizados devem ser reconhecidos externamente e reenviados. Páginas sem texto são sinalizadas; a análise pode ser parcial.
- Tabelas complexas, células mescladas e continuação entre páginas exigem conferência; o protótipo não une tabelas automaticamente.
- XLSX: se as colunas escolhidas contêm fórmulas, recalcule e salve o arquivo no Excel antes de enviá-lo. O aplicativo usa os resultados salvos. Nos testes, a formatação comum, as fórmulas e as outras abas foram preservadas; recursos avançados do Excel ainda precisam de conferência na cópia gerada.
- Uma aba ou tabela por execução. Limites: 20 MB, 150 páginas, 2.000 linhas analisadas, 100 colunas de entrada (99 para acrescentar resultado), 100 MB descompactados e 2.000 trechos por item/projeto. Divida arquivos maiores.
- A similaridade temática não comprova contribuição, entrega, impacto nem associação oficial. Textos curtos, siglas, negações e descrições genéricas podem produzir indicações incorretas.
- Sem garantia de disponibilidade ou capacidade para muitos acessos simultâneos no serviço gratuito.

## Estrutura

```text
app.py                 Interface Streamlit
desafios/catalog.py    Catálogo, versão e formatação dos resultados
desafios/semantic.py   SBERT, segmentação e ranking
desafios/files.py      Leitura PDF/XLSX e exportação em memória
data/                  Catálogo e proveniência
scripts/               Importação de catálogo e avaliação
tests/                 Testes automatizados sem download do modelo
docs/                  Método, implantação e migração
Dockerfile             Execução em servidor próprio
```

## Testar e atualizar

```bash
python -m unittest discover -s tests -v
python scripts/import_catalog.py "caminho/Desafios.xlsx"
python scripts/evaluate.py "caminho/exemplos_validados.jsonl"
```

Teste de integração opcional (baixa os pesos na primeira execução, usa arquivos sintéticos em memória):

```bash
pip install -r requirements-dev.txt
python scripts/smoke_test.py
```

Esse teste percorre os principais caminhos da aplicação: planilhas, projetos e tabelas em PDF. Também confere fórmulas, linhas vazias e atualização dos resultados quando os critérios mudam. Ele verifica o funcionamento; a qualidade das sugestões e o desempenho com muitos usuários precisam de avaliações próprias.

Para avaliar a qualidade das indicações, o próximo passo é reunir exemplos com desafios definidos por especialistas. Esses documentos podem ficar fora do repositório, especialmente quando forem internos. Ao atualizar a base, ajuste também as contagens nos testes e na documentação e reinicie o aplicativo.

## Referências técnicas

- [Modelo e arquitetura](https://huggingface.co/sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2)
- [Sentence Transformers](https://sbert.net/docs/package_reference/sentence_transformer/model.html)
- [Streamlit Community Cloud](https://docs.streamlit.io/deploy/streamlit-community-cloud)
- [pdfplumber](https://github.com/jsvine/pdfplumber)
