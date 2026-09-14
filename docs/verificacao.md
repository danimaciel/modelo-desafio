# Verificação da primeira versão

Executada em 14/09/2026, Windows, Python 3.12, PyTorch 2.8.0+cpu, Streamlit 1.49.1 e Sentence Transformers 5.1.0.

- Sete testes unitários passaram: integridade do catálogo; rejeição de IDs duplicados; segmentação que respeita o limite e inclui o fim do texto; preservação de fórmulas, formato básico e outras abas; isolamento entre linhas; exportação de texto sem execução de fórmulas; sugestão de colunas e sinalização de revisão.
- A interface inicial e a alternância de modo passaram no AppTest.
- Quatro descrições do próprio catálogo retornaram seus respectivos IDs como primeira indicação com o modelo real. É um teste funcional de autoconsulta, não uma medida de generalização.
- O teste de integração com modelo real passou para XLSX, projeto PDF, tabela PDF e PDF sem texto. Downloads foram gerados em memória e os XLSX reabertos para conferência.
- Os resultados antigos deixaram de aparecer após mudança nos critérios da análise.

Não avaliados nesta etapa: acurácia com documentos independentes rotulados; carga simultânea; OCR; todos os recursos avançados de Excel; build Docker e ambiente Linux de produção. A implantação no Streamlit requer entrada na conta responsável e validação no serviço.
