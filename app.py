"""Interface do protótipo; uploads e resultados permanecem na sessão em memória."""
import hashlib
import json
from pathlib import Path

import streamlit as st

from desafios.catalog import load_catalog, describe
from desafios.files import (load_xlsx, headers, suggested_columns, row_text,
                            export_xlsx, read_pdf, export_pdf_table, MAX_ROWS)
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
    with st.sidebar:
        st.subheader('Sobre a análise')
        st.write(f'{len(catalog)} desafios na base fornecida.')
        st.caption(f'Base: {version[:12]}')
        st.write('As relações com portfólios, objetivos, metas e ODS são reproduzidas da base.')
        st.caption('Há metas encerradas e um ODS não informado. Essas situações são preservadas.')
        with st.expander('Critérios experimentais'):
            st.caption('Valores iniciais sem calibração. Similaridade não é percentual de certeza.')
            cutoff = st.slider('Similaridade mínima', 0.0, 1.0, 0.35, 0.01)
            margin = st.slider('Diferença mínima entre os dois primeiros', 0.0, 0.5, 0.03, 0.01)
        st.caption('Limites: 20 MB; 150 páginas; até 2.000 linhas analisadas por vez.')
        if st.button('Limpar sessão'):
            st.session_state.clear()
            st.rerun()
    mode = st.radio('O que deseja analisar?', ['Tabela por linha', 'Projeto em PDF'], horizontal=True)
    upload = st.file_uploader('Selecione o arquivo', type=['xlsx', 'pdf'] if mode == 'Tabela por linha' else ['pdf'])
    if upload is None:
        st.write('Para tabelas, você escolherá a aba, o cabeçalho e uma ou mais colunas de texto.')
        st.write('Para projetos, receberá até três desafios com trechos e páginas que apoiam a indicação.')
        return
    raw = upload.getvalue()
    identity = hashlib.sha256(raw).hexdigest() + mode
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

    if upload.name.lower().endswith('.xlsx'):
        values = load_xlsx(raw, data_only=True)
        formulas = load_xlsx(raw)
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
                output = export_xlsx(raw, sheet_name, header, mapped)
            st.session_state['result'] = {'key': selection, 'xlsx': output,
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
