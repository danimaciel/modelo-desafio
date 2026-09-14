# Implantação e migração

## Demonstração no Streamlit

Minha proposta é começar pelo Streamlit Community Cloud e, quando houver estrutura disponível, levar a aplicação para um servidor da Embrapa. O mesmo código pode ser usado nos dois ambientes.

Para publicar no Streamlit, selecione o repositório `danimaciel/modelo-desafio`, a branch `main`, o arquivo `app.py` e Python 3.12. A base de desafios já está no repositório. Na primeira análise, o aplicativo baixa o modelo do Hugging Face e passa a executá-lo no próprio servidor, sem contratar uma API de inferência.

A primeira carga precisa de conexão com o Hugging Face. Como o modelo ocupa memória e disco, vamos avaliar o tempo de resposta e o consumo com arquivos representativos antes de ampliar o grupo de usuários.

O serviço gratuito pode suspender aplicativos inativos e não garante disponibilidade contínua. Configure o compartilhamento para o grupo de participantes nas opções da plataforma. O aplicativo ainda não possui login próprio; nesta demonstração, serão usados documentos públicos ou exemplos sem conteúdo interno.

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

Os arquivos são processados no servidor de hospedagem, e não apenas no navegador de quem os envia. O aplicativo não controla os registros e os prazos de liberação de memória da plataforma. Por isso, esta demonstração deve receber apenas arquivos públicos ou exemplos sem dados pessoais ou confidenciais. O relatório JSON inclui trechos do documento e precisa do mesmo cuidado que o arquivo original.

## Servidor próprio

```bash
docker build -t modelo-desafio .
docker run --rm -p 8501:8501 modelo-desafio
```

Para os primeiros testes de capacidade, a estimativa é usar 2 vCPUs e 4 GB de RAM. Essa configuração ainda precisa ser avaliada com o volume real de uso. O Dockerfile prepara a execução em CPU.

Na migração, a equipe de infraestrutura precisará configurar HTTPS e login institucional na entrada do serviço. Essa integração ainda não faz parte do aplicativo. Também será necessário restringir o acesso direto à porta 8501 e definir monitoramento, atualização de dependências e registros técnicos que não incluam o conteúdo dos documentos.

Se o servidor não tiver acesso à internet, baixe previamente a versão validada do modelo e disponibilize seus arquivos no cache do Hugging Face usado pelo contêiner. Configure `HF_HUB_OFFLINE=1`, `HF_HOME` e `MODEL_REVISION` e teste a inicialização sem internet. As dependências Python também devem estar instaladas na imagem Docker.

O módulo `desafios/semantic.py` funciona independentemente do Streamlit. Isso permite manter a interface atual ou, no futuro, criar outra forma de acesso ao modelo. Se houver muitos usuários simultâneos, será preciso avaliar uma fila de processamento. Nesta versão, o aplicativo controla o acesso ao modelo para evitar execuções simultâneas do encoder, mas ainda não distribui trabalhos entre servidores.

## O que validar antes do uso institucional

- Conjunto rotulado por especialistas e limiares calibrados por tipo de documento.
- Capacidade, latência e isolamento entre sessões sob acessos simultâneos.
- Integridade de planilhas reais, principalmente objetos e recursos avançados.
- Autenticação, autorização, HTTPS, retenção e revisão do tratamento de dados pela equipe responsável.
- Atualização do catálogo e decisão explícita sobre apresentação de metas históricas.
- Build Docker e execução no sistema operacional de destino. Testes em Windows não comprovam implantação Linux.
