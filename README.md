# Modelo Desafio

Protótipo de aplicação web baseada em SBERT para sugerir a aderência temática de projetos, publicações, tecnologias, compromissos e soluções aos desafios para inovação da Embrapa. Proposta de pesquisa, sem caráter de enquadramento institucional oficial.

## Funcionalidades

- **XLSX:** escolha de aba, linha do cabeçalho e uma ou mais colunas de texto; uma indicação por linha, em uma nova coluna, com portfólio, objetivo, meta e ODS. Cópia para download e relatório JSON com evidências.
- **PDF de projeto:** extração por página, comparação de trechos e até três desafios acima do critério configurado, com páginas e evidências. Relatório JSON para download.
- **PDF com tabelas:** extração por bordas ou posição do texto, prévia e confirmação das colunas. Uma tabela por análise, exportada em XLSX.
- Textos vazios não são classificados; pontuações baixas, textos curtos e candidatos próximos exigem revisão.
- Relações institucionais são recuperadas por identificador, sem geração ou inferência de novos vínculos.

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

## Publicar no Streamlit Community Cloud

1. Entre em https://share.streamlit.io/ com a conta que acessa este repositório.
2. Crie um aplicativo a partir de `danimaciel/modelo-desafio`.
3. Selecione branch `main`, arquivo principal `app.py` e Python **3.12** nas configurações avançadas.
4. Aguarde instalação e inicialização. A primeira análise baixa o modelo.
5. Teste com documentos públicos. Configure compartilhamento restrito aos participantes quando essa opção estiver disponível na conta.

Não há login institucional implementado neste protótipo. Publicar o app não cria restrição a funcionários da Embrapa. A camada de acesso é da plataforma, até a migração institucional. Não versionar segredos ou uploads.

As instruções acima estão preparadas para implantação; criar o repositório não publica automaticamente o aplicativo. Consulte [implantação e migração](docs/implantacao.md).

## Base e metodologia

`data/desafios.json` contém 107 desafios da planilha fornecida pela responsável pela proposta. São 9 portfólios, 7 objetivos, 25 textos distintos de metas; 44 registros mencionam meta encerrada e um não informa ODS. Não houve atualização externa ou correção dos vínculos. `data/proveniencia.json` registra a origem e o hash do arquivo fonte.

Modelo: `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` (Apache 2.0). O catálogo é indexado por descrição do desafio; textos extensos são divididos por tokens. A similaridade usa cosseno de vetores normalizados; o ranking agrega os três trechos mais aderentes. Leia [metodologia e validação](docs/metodologia.md) antes de interpretar os resultados.

**Os critérios iniciais 0,35 (similaridade) e 0,03 (diferença entre primeiros candidatos) são experimentais, não calibrados.** A pontuação não é probabilidade de acerto. Não há treinamento com exemplos da Embrapa nesta versão.

## Limitações conhecidas

- Sem OCR: PDFs digitalizados devem ser reconhecidos externamente e reenviados. Páginas sem texto são sinalizadas; a análise pode ser parcial.
- Tabelas complexas, células mescladas e continuação entre páginas exigem conferência; o protótipo não une tabelas automaticamente.
- XLSX: fórmulas selecionadas precisam de valores calculados salvos pelo Excel. A biblioteca não recalcula fórmulas. Formatação comum, fórmulas e outras abas são preservadas em testes; objetos avançados podem ser alterados pelo leitor/escritor. Não promete preservação binária perfeita.
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

O teste cobre autoconsultas ao catálogo, upload simulado na interface, XLSX com fórmulas e outra aba, linhas vazias, invalidação de resultados quando critérios mudam, PDF de projeto, tabela em PDF e rejeição de PDF sem texto. Não substitui teste de acurácia com exemplos independentes ou teste de carga.

Os testes unitários verificam funcionamento, não acurácia do SBERT. O avaliador exige exemplos rotulados por especialistas; não publique documentos internos no repositório. Ao atualizar o catálogo, revise também as contagens de referência nos testes e na documentação, e reinicie o app.

## Referências técnicas

- [Modelo e arquitetura](https://huggingface.co/sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2)
- [Sentence Transformers](https://sbert.net/docs/package_reference/sentence_transformer/model.html)
- [Streamlit Community Cloud](https://docs.streamlit.io/deploy/streamlit-community-cloud)
- [pdfplumber](https://github.com/jsvine/pdfplumber)
