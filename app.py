"""Interface do protótipo; uploads e resultados permanecem na sessão em memória."""
import hashlib
import json
import os
from pathlib import Path

import streamlit as st

from desafios.catalog import load_catalog, describe
from desafios.files import (load_xlsx, headers, suggested_columns, row_text,
                            export_xlsx, read_pdf, export_pdf_table, MAX_ROWS, prepare_table, export_csv)
from desafios.semantic import SemanticEngine

st.set_page_config(page_title='Desafios para inovação', page_icon='🌱', layout='wide')


@st.cache_resource(show_spinner=False)
def engine(version):
    catalog, current = load_catalog()
    if version != current:
        raise ValueError('A base mudou. Atualize a página.')
    return SemanticEngine(catalog, current)


def analyze_rows(items, cutoff, margin):
    model = engine(load_catalog()[1])
    results, details = {}, []
    progress = st.progress(0, text='Analisando linhas…')
    for count, (row_number, text) in enumerate(items, 1):
        result = model.rank(text, min_score=cutoff, min_margin=margin)[0]
        results[row_number] = describe(result)
        details.append({'linha': row_number, **result})
        progress.progress(count / len(items), text=f'Analisadas {count} de {len(items)} linhas')
    progress.empty()
    return results, details


def show_downloads(result, filename):
    if result.get('csv'):
        st.download_button('Baixar CSV com indicações', result['csv'],
                           file_name=f'{Path(filename).stem}_analisado.csv', mime='text/csv')
    if result.get('xlsx'):
        st.download_button('Baixar planilha com indicações', result['xlsx'],
                           file_name=f'{Path(filename).stem}_analisado.xlsx',
                           mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    st.download_button('Baixar relatório completo (JSON)',
                       json.dumps(result['details'], ensure_ascii=False, indent=2),
                       file_name=f'{Path(filename).stem}_analise.json', mime='application/json')


def main():
    st.title('Desafios para inovação')
    st.write('Encontre desafios relacionados a projetos, publicações, tecnologias, compromissos e soluções.')
    st.caption('Protótipo de pesquisa • Aderência temática sugerida; não comprova contribuição ou impacto.')
    st.info('Ambiente externo de demonstração: envie apenas documentos públicos ou exemplos sem informações internas.')
    catalog, version = load_catalog()
    cutoff = float(os.getenv('MIN_SIMILARITY', '0.35'))
    margin = float(os.getenv('MIN_MARGIN', '0.03'))
    if not 0 <= cutoff <= 1 or not 0 <= margin <= 0.5:
        raise ValueError('Configuração de análise inválida. Contate a pessoa responsável pelo aplicativo.')
    with st.sidebar:
        st.subheader('Sobre a análise')
        st.write(f'Seu texto será comparado com {len(catalog)} desafios para inovação da Embrapa.')
        st.write('Cada indicação inclui os vínculos com portfólio, objetivo, meta e ODS registrados na base de referência.')
        st.caption('Revise as sugestões antes de utilizá-las.')
        st.divider()
        st.subheader('Arquivos aceitos')
        st.caption('PDF, XLSX, XLS ou CSV · até 20 MB por arquivo')
        st.caption('PDF: até 150 páginas\n\nTabelas: até 2.000 linhas por análise')
        if st.button('Limpar sessão'):
            st.session_state.clear()
            st.rerun()
    mode = st.radio('O que deseja analisar?', ['Tabela por linha', 'Projeto em PDF'], horizontal=True)
    upload = st.file_uploader('Selecione o arquivo', type=['xlsx', 'xls', 'csv', 'pdf'] if mode == 'Tabela por linha' else ['pdf'])
    if upload is None:
        st.write('Para tabelas, você escolherá a aba, o cabeçalho e uma ou mais colunas de texto.')
        st.write('Para projetos, receberá até três desafios com trechos e páginas que apoiam a indicação.')
        return
    raw = upload.getvalue()
    identity = hashlib.sha256(raw).hexdigest() + mode + Path(upload.name).suffix.lower()
    if st.session_state.get('file_identity') != identity:
        st.session_state['file_identity'] = identity
        st.session_state.pop('result', None)
        st.session_state.pop('pdf', None)
    selection = [identity, cutoff, margin]
    if mode == 'Projeto em PDF':
        if st.button('Extrair texto do projeto'):
            st.session_state['pdf'] = read_pdf(raw)
            st.session_state.pop('result', None)
        if 'pdf' not in st.session_state:
            return
        pages, _, empty = st.session_state['pdf']
        if empty:
            st.warning(f'Páginas sem texto extraível: {empty}. A análise é parcial. Faça OCR para incluí-las.')
        with st.expander('Conferir texto extraído'):
            st.text_area('Prévia das primeiras páginas', '\n\n'.join(t for _, t in pages)[:12000], height=240, disabled=True)
        if st.button('Analisar projeto', type='primary'):
            with st.spinner('Carregando SBERT e comparando trechos…'):
                ranked = engine(version).rank('\n'.join(t for _, t in pages), top_k=3,
                                              min_score=cutoff, min_margin=margin, pages=pages)
            st.session_state['result'] = {'key': selection, 'details': {
                'tipo': 'projeto', 'paginas_sem_texto': empty, 'resultados': ranked,
                'similaridade_minima': cutoff, 'margem_minima': margin}}
        result = st.session_state.get('result')
        if result and result['key'] == selection:
            ranked = result['details']['resultados']
            if not ranked:
                st.warning('Nenhum desafio atingiu o critério configurado. Revise o texto e os critérios.')
            for position, item in enumerate(ranked, 1):
                st.subheader(f"{position}. {item['id_desafio']}")
                st.write(item['desafio'])
                st.text(describe(item))
                with st.expander('Trechos mais semelhantes'):
                    for evidence in item['evidence']:
                        st.caption(f"Página {evidence['page']} · similaridade {evidence['score']:.4f}")
                        st.text(evidence['text'])
            show_downloads(result, upload.name)
        return

    extension = Path(upload.name).suffix.lower()
    if extension in ('.xlsx', '.xls', '.csv'):
        delimiter, encoding = ';', 'utf-8-sig'
        if extension == '.csv':
            delimiter = st.selectbox('Separador do CSV', [';', ',', '\t', '|'],
                                     format_func=lambda v: {';': 'Ponto e vírgula (;)', ',': 'Vírgula (,)', '\t': 'Tabulação', '|': 'Barra vertical (|)'}[v])
            encoding = st.selectbox('Codificação do CSV', ['utf-8-sig', 'cp1252', 'utf-16'],
                                    format_func=lambda v: {'utf-8-sig': 'UTF-8', 'cp1252': 'Windows-1252 (Excel antigo)', 'utf-16': 'UTF-16'}[v])
            st.caption('Confira as colunas na prévia. O CSV de saída usa UTF-8 e o separador escolhido. Textos que possam ser interpretados como fórmulas recebem um apóstrofo de proteção.')
        elif extension == '.xls':
            st.info('O XLS será convertido para XLSX. Valores e abas serão mantidos; fórmulas serão substituídas pelos resultados salvos. Formatação, gráficos e macros não serão mantidos.')
        table_raw = prepare_table(raw, extension, delimiter, encoding)
        selection += [delimiter, encoding]
        values = load_xlsx(table_raw, data_only=True)
        formulas = load_xlsx(table_raw)
        sheet_name = st.selectbox('Aba a analisar', values.sheetnames)
        sheet = values[sheet_name]
        header = int(st.number_input('Linha do cabeçalho', min_value=1, max_value=max(1, sheet.max_row), value=1))
        labels = headers(sheet, header)
        options = list(range(len(labels)))
        columns = st.multiselect('Colunas que contêm o texto', options,
                                 default=suggested_columns(labels), format_func=lambda i: labels[i],
                                 key=f'cols_{identity}_{sheet_name}_{header}')
        preview = [{labels[c]: sheet.cell(r, c + 1).value for c in options}
                   for r in range(header + 1, min(sheet.max_row + 1, header + 11))]
        st.dataframe(preview, width='stretch')
        selection += [sheet_name, header, columns]
        items = [(r, row_text(sheet, r, [c + 1 for c in columns]))
                 for r in range(header + 1, sheet.max_row + 1)
                 if any(sheet.cell(r, c).value is not None or formulas[sheet_name].cell(r, c).value is not None
                        for c in range(1, sheet.max_column + 1))]
        missing_formula = any(formulas[sheet_name].cell(r, c + 1).data_type == 'f'
                              and sheet.cell(r, c + 1).value is None for r, _ in items for c in columns)
        if missing_formula:
            st.warning('Há fórmulas selecionadas sem resultado salvo. Recalcule e salve no Excel antes de analisar.')
        st.caption('Será acrescentada uma coluna na aba escolhida. Confira a cópia: objetos avançados do Excel podem não ser preservados.')
        if st.button('Analisar linhas', type='primary', disabled=not columns or not items or missing_formula):
            if len(items) > MAX_ROWS:
                raise ValueError('Selecione um arquivo com até 2.000 linhas de dados.')
            with st.spinner('Preparando análise…'):
                mapped, detail = analyze_rows(items, cutoff, margin)
                output = export_xlsx(table_raw, sheet_name, header, mapped)
            st.session_state['result'] = {'key': selection, 'xlsx': output,
                'csv': export_csv(output, sheet_name, delimiter) if extension == '.csv' else None,
                'details': {'aba': sheet_name, 'colunas': [labels[c] for c in columns],
                            'similaridade_minima': cutoff, 'margem_minima': margin, 'resultados': detail}}
    else:
        strategy = st.selectbox('Como identificar as tabelas?', ['lines', 'text'],
                                format_func=lambda s: 'Linhas e bordas' if s == 'lines' else 'Posição do texto')
        selection += [strategy]
        if st.button('Extrair tabelas'):
            st.session_state['pdf'] = (*read_pdf(raw, tables=True, strategy=strategy), strategy)
            st.session_state.pop('result', None)
        if 'pdf' not in st.session_state or st.session_state['pdf'][3] != strategy:
            return
        _, tables, empty, _ = st.session_state['pdf']
        if empty:
            st.warning(f'Páginas sem texto: {empty}. Tabelas nessas páginas podem ter sido omitidas; faça OCR.')
        if not tables:
            st.warning('Nenhuma tabela encontrada. Tente outra estratégia ou envie XLSX.')
            return
        chosen = st.selectbox('Tabela a analisar', range(len(tables)),
            format_func=lambda i: f"Página {tables[i]['page']} · tabela {tables[i]['table']}")
        rows = tables[chosen]['rows']
        header = int(st.number_input('Linha do cabeçalho na tabela', min_value=1, max_value=len(rows), value=1))
        rows = rows[header - 1:]
        labels = [f'{i + 1} — {v or "Sem título"}' for i, v in enumerate(rows[0])]
        columns = st.multiselect('Colunas de texto', range(len(labels)),
                                 default=suggested_columns(labels), format_func=lambda i: labels[i],
                                 key=f'pdfcols_{identity}_{chosen}_{header}_{strategy}')
        st.dataframe([{labels[i]: row[i] if i < len(row) else None for i in range(len(labels))}
                       for row in rows[1:11]], width='stretch')
        confirmed = st.checkbox('Conferi a extração: cada linha corresponde a um item.')
        selection += [chosen, header, columns, confirmed]
        items = [(r + 2, '\n'.join(str(row[c]) for c in columns if c < len(row) and row[c]))
                 for r, row in enumerate(rows[1:])]
        st.caption('Esta versão analisa uma tabela por vez e entrega XLSX; não altera o PDF original.')
        if st.button('Analisar tabela', type='primary', disabled=not confirmed or not columns or not items):
            if len(items) > MAX_ROWS or len(labels) >= 100:
                raise ValueError('Tabela excede o limite de linhas ou colunas.')
            with st.spinner('Preparando análise…'):
                mapped, detail = analyze_rows(items, cutoff, margin)
                output = export_pdf_table(rows, mapped)
            st.session_state['result'] = {'key': selection, 'xlsx': output,
                'details': {'pagina': tables[chosen]['page'], 'tabela': tables[chosen]['table'],
                            'colunas': [labels[c] for c in columns], 'resultados': detail,
                            'similaridade_minima': cutoff, 'margem_minima': margin}}
    result = st.session_state.get('result')
    if result and result['key'] == selection:
        detail = result['details']['resultados']
        st.success(f'{len(detail)} linhas processadas. Revise as indicações antes de utilizá-las.')
        st.dataframe([{'Linha': r['linha'], 'Desafio': r.get('id_desafio', ''),
                       'Similaridade': r.get('score'), 'Situação': r['status']} for r in detail],
                     width='stretch')
        show_downloads(result, upload.name)


try:
    main()
except ValueError as exc:
    st.error(str(exc))
except Exception:
    # Não exibir traceback ou conteúdo de uploads em logs/interface compartilhados.
    st.error('Não foi possível processar o arquivo ou carregar o modelo. Confira o formato e a conexão; tente novamente com um arquivo menor.')
