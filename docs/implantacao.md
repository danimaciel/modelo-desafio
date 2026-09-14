# Implantação e migração

## Demonstração no Streamlit

Usar `app.py`, branch `main`, Python 3.12. O catálogo acompanha o repositório; os pesos são baixados do Hugging Face Hub na primeira análise, sem API de inferência paga. A conectividade com o Hub é necessária para a primeira carga. Dependências e pesos ocupam memória e disco; limites do Community Cloud podem provocar reinício. Medir tempo e consumo com arquivos representativos antes de ampliar o grupo de usuários.

O serviço gratuito pode suspender apps inativos. O protótipo não oferece SLA. Escolher compartilhamento restrito nas configurações da plataforma; a interface não inclui autenticação própria. Não confundir repositório público com autorização para publicar documentos internos.

## Tratamento dos arquivos

### Configuração administrativa da análise

Os critérios não aparecem como controles para o usuário. A pessoa responsável pela hospedagem pode definir `MIN_SIMILARITY` (padrão `0.35`, entre 0 e 1) e `MIN_MARGIN` (padrão `0.03`, entre 0 e 0.5) nas variáveis de ambiente. No Streamlit Community Cloud, podem ser definidos como chaves de primeiro nível em **Settings → Secrets**, que são expostas como variáveis de ambiente. Reinicie o aplicativo após a alteração. Esses valores continuam experimentais e precisam de calibração. Os critérios usados ficam registrados no relatório JSON. Não versione o arquivo `secrets.toml`.

```toml
MIN_SIMILARITY = "0.35"
MIN_MARGIN = "0.03"
```

O identificador técnico da base permanece nos relatórios para rastreabilidade, sem aparecer na barra lateral. Metas encerradas e ODS não informado são apresentados nos resultados em que se aplicam.

### Sessão e processamento

Uploads, texto extraído, embeddings das entradas e resultados são processados em memória. A aplicação não salva uploads em disco nem os envia ao GitHub ou a APIs generativas. Apenas o modelo e o catálogo usam cache compartilhado. Resultados ficam no estado da sessão para permitir downloads, até a limpeza ou encerramento da sessão; a plataforma controla a liberação final de memória. O botão “Limpar sessão” remove o estado da aplicação e os widgets.

Arquivos atravessam e são processados no servidor de hospedagem. Não prometer execução somente no navegador, exclusão instantânea de toda infraestrutura ou ausência de logs da plataforma. Não colocar dados pessoais, confidenciais ou não autorizados na demonstração. Os relatórios JSON contêm trechos do documento e devem receber o mesmo tratamento do original.

## Servidor próprio

```bash
docker build -t modelo-desafio .
docker run --rm -p 8501:8501 modelo-desafio
```

Começar a avaliação de capacidade com 2 vCPUs e 4 GB de RAM como estimativa, não mínimo validado. O Dockerfile usa CPU. Colocar HTTPS e autenticação institucional no proxy de entrada. Validar a integração com o provedor institucional; ela não está implementada. Restringir acesso direto à porta 8501 e configurar limites de tráfego, logs sem conteúdo de documentos, atualização de dependências e monitoramento conforme a infraestrutura disponível.

Em ambiente sem internet, preparar previamente os pesos da revisão validada no cache Hugging Face e disponibilizá-los ao usuário do contêiner; configurar `HF_HUB_OFFLINE=1`, `HF_HOME` e `MODEL_REVISION`. Testar a carga offline antes da implantação. As dependências Python também precisam estar disponíveis na imagem já construída.

O módulo `desafios/semantic.py` não depende de Streamlit, permitindo futura API. A interface atual pode continuar sendo usada sem reescrever o mecanismo semântico. Para concorrência elevada, avaliar fila de trabalhos e processamento separado; nesta versão o acesso ao encoder é protegido por lock e não há fila distribuída.

## O que validar antes do uso institucional

- Conjunto rotulado por especialistas e limiares calibrados por tipo de documento.
- Capacidade, latência e isolamento entre sessões sob acessos simultâneos.
- Integridade de planilhas reais, principalmente objetos e recursos avançados.
- Autenticação, autorização, HTTPS, retenção e revisão do tratamento de dados pela equipe responsável.
- Atualização do catálogo e decisão explícita sobre apresentação de metas históricas.
- Build Docker e execução no sistema operacional de destino. Testes em Windows não comprovam implantação Linux.
