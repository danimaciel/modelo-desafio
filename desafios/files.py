from copy import copy
from io import BytesIO
from zipfile import ZipFile, BadZipFile
import unicodedata

import openpyxl
import pdfplumber

MAX_BYTES = 20 * 1024 * 1024
MAX_ROWS = 2000
MAX_COLUMNS = 100
MAX_PAGES = 150


def validate_bytes(raw):
    if not raw or len(raw) > MAX_BYTES:
        raise ValueError('Envie um arquivo não vazio de até 20 MB.')


def load_xlsx(raw, data_only=False):
    validate_bytes(raw)
    try:
        with ZipFile(BytesIO(raw)) as archive:
            if sum(x.file_size for x in archive.infolist()) > 100 * 1024 * 1024:
                raise ValueError('Planilha descompactada excede 100 MB.')
            names = archive.namelist()
            if any('vbaProject' in n or n.startswith('xl/embeddings/') for n in names):
                raise ValueError('Remova macros e objetos incorporados antes de enviar.')
        workbook = openpyxl.load_workbook(BytesIO(raw), data_only=data_only, keep_links=True)
    except (BadZipFile, KeyError) as exc:
        raise ValueError('O arquivo não é uma planilha XLSX válida.') from exc
    for sheet in workbook:
        if sheet.max_row > MAX_ROWS + 100 or sheet.max_column > MAX_COLUMNS:
            raise ValueError('Limite: 2.100 linhas e 100 colunas por aba, incluindo formatação.')
    return workbook


def headers(sheet, row):
    return [f'{openpyxl.utils.get_column_letter(i)} — {sheet.cell(row, i).value or "Sem título"}'
            for i in range(1, sheet.max_column + 1)]


def suggested_columns(labels):
    words = ('titulo', 'resumo', 'descricao', 'palavra', 'objetivo', 'resultado',
             'compromisso', 'solucao', 'tecnologia', 'publicacao')
    return [i for i, label in enumerate(labels) if any(w in unicodedata.normalize(
        'NFKD', label.lower()).encode('ascii', 'ignore').decode() for w in words)]


def row_text(sheet, row, columns):
    return '\n'.join(str(sheet.cell(row, col).value).strip() for col in columns
                     if sheet.cell(row, col).value is not None
                     and str(sheet.cell(row, col).value).strip())


def export_xlsx(raw, sheet_name, header_row, results):
    """Edita a cópia em memória; preserva fórmulas e outras abas com openpyxl."""
    workbook = load_xlsx(raw)
    sheet = workbook[sheet_name]
    column = sheet.max_column + 1
    if column > MAX_COLUMNS:
        raise ValueError('Não há espaço para a coluna de resultado no limite do protótipo.')
    existing = {str(c.value) for c in sheet[header_row]}
    title = 'Enquadramento sugerido'
    suffix = 2
    while title in existing:
        title = f'Enquadramento sugerido ({suffix})'
        suffix += 1
    sheet.cell(header_row, column, title)
    sheet.cell(header_row, column).font = copy(sheet.cell(header_row, 1).font)
    sheet.column_dimensions[openpyxl.utils.get_column_letter(column)].width = 65
    for row, value in results.items():
        cell = sheet.cell(row, column)
        cell.value = value
        cell.data_type = 's'
        cell.alignment = openpyxl.styles.Alignment(wrap_text=True, vertical='top')
    output = BytesIO()
    workbook.save(output)
    return output.getvalue()


def read_pdf(raw, tables=False, strategy='lines'):
    validate_bytes(raw)
    pages, found, empty = [], [], []
    with pdfplumber.open(BytesIO(raw)) as pdf:
        if len(pdf.pages) > MAX_PAGES:
            raise ValueError('Limite de 150 páginas por PDF.')
        for number, page in enumerate(pdf.pages, 1):
            content = page.extract_text() or ''
            if not content.strip():
                empty.append(number)
            pages.append((number, content))
            if tables:
                settings = {'vertical_strategy': strategy, 'horizontal_strategy': strategy}
                for table_number, table in enumerate(page.extract_tables(settings), 1):
                    if table:
                        found.append({'page': number, 'table': table_number, 'rows': table})
            page.close()
    if not any(text.strip() for _, text in pages):
        raise ValueError('PDF sem texto extraível. Faça OCR e envie novamente; OCR não está incluído nesta versão.')
    return pages, found, empty


def export_pdf_table(rows, results):
    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.title = 'Tabela analisada'
    for row in rows:
        sheet.append([str(v) if v is not None else '' for v in row])
    # Conteúdo extraído é texto, nunca fórmula executável.
    for row in sheet:
        for cell in row:
            cell.data_type = 's'
    output = BytesIO()
    workbook.save(output)
    return export_xlsx(output.getvalue(), sheet.title, 1, results)
