"""
Сервис для парсинга содержимого файлов различных форматов
"""
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


def parse_docx(file_path):
    """Парсит DOCX файл и возвращает HTML с форматированием"""
    try:
        from docx import Document
        from docx.shared import RGBColor, Pt
        from docx.enum.text import WD_ALIGN_PARAGRAPH
        
        doc = Document(file_path)
        html_parts = ['<div class="document-content">']
        
        for para in doc.paragraphs:
            if not para.text.strip():
                html_parts.append('<p>&nbsp;</p>')
                continue
            
            # Определяем стили параграфа
            style_parts = []
            alignment = para.alignment
            if alignment:
                if alignment == 1:  # CENTER
                    style_parts.append('text-align: center;')
                elif alignment == 2:  # RIGHT
                    style_parts.append('text-align: right;')
                elif alignment == 3:  # JUSTIFY
                    style_parts.append('text-align: justify;')
            
            para_html = '<p'
            if style_parts:
                para_html += f' style="{"; ".join(style_parts)}"'
            para_html += '>'
            
            # Обрабатываем runs (части текста с разным форматированием)
            for run in para.runs:
                text = run.text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                if not text:
                    continue
                
                run_styles = []
                if run.bold:
                    run_styles.append('font-weight: bold;')
                if run.italic:
                    run_styles.append('font-style: italic;')
                if run.underline:
                    run_styles.append('text-decoration: underline;')
                
                if run.font and run.font.size:
                    size_pt = run.font.size.pt
                    run_styles.append(f'font-size: {size_pt}pt;')
                
                if run.font and run.font.color and run.font.color.rgb:
                    rgb = run.font.color.rgb
                    color = f'#{rgb:06x}'
                    run_styles.append(f'color: {color};')
                
                if run_styles:
                    para_html += f'<span style="{"; ".join(run_styles)}">{text}</span>'
                else:
                    para_html += text
            
            para_html += '</p>'
            html_parts.append(para_html)
        
        # Обрабатываем таблицы
        for table in doc.tables:
            html_parts.append('<table style="border-collapse: collapse; width: 100%; margin: 10px 0;">')
            for row in table.rows:
                html_parts.append('<tr>')
                for cell in row.cells:
                    cell_text = cell.text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                    html_parts.append(f'<td style="border: 1px solid #ddd; padding: 8px;">{cell_text}</td>')
                html_parts.append('</tr>')
            html_parts.append('</table>')
        
        html_parts.append('</div>')
        return ''.join(html_parts)
        
    except Exception as e:
        logger.error(f'Ошибка парсинга DOCX: {e}')
        raise


def parse_doc(file_path):
    """Парсит старый формат DOC (через конвертацию)"""
    try:
        # Для старых DOC файлов используем pypandoc или просто возвращаем сообщение
        import pypandoc
        html = pypandoc.convert_file(str(file_path), 'html', format='doc')
        return f'<div class="document-content">{html}</div>'
    except Exception as e:
        logger.error(f'Ошибка парсинга DOC: {e}')
        # Если pypandoc не работает, возвращаем сообщение
        return '<div class="document-content"><p>Парсинг старых DOC файлов требует установки pandoc. Пожалуйста, скачайте файл для просмотра.</p></div>'


def parse_pdf(file_path):
    """Парсит PDF файл и возвращает HTML с форматированием"""
    try:
        from PyPDF2 import PdfReader
        
        reader = PdfReader(file_path)
        html_parts = ['<div class="document-content">']
        
        for page_num, page in enumerate(reader.pages, 1):
            html_parts.append(f'<div class="pdf-page" style="page-break-after: always; margin-bottom: 20px;">')
            html_parts.append(f'<h3 style="color: #666; font-size: 14px; margin-bottom: 10px;">Страница {page_num}</h3>')
            
            text = page.extract_text()
            if text:
                # Разбиваем на параграфы
                paragraphs = text.split('\n\n')
                for para in paragraphs:
                    para = para.strip()
                    if para:
                        para_html = para.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                        html_parts.append(f'<p style="margin: 5px 0; line-height: 1.6;">{para_html}</p>')
            
            html_parts.append('</div>')
        
        html_parts.append('</div>')
        return ''.join(html_parts)
        
    except Exception as e:
        logger.error(f'Ошибка парсинга PDF: {e}')
        raise


def parse_rtf(file_path):
    """Парсит RTF файл"""
    try:
        import pypandoc
        html = pypandoc.convert_file(str(file_path), 'html', format='rtf')
        return f'<div class="document-content">{html}</div>'
    except Exception as e:
        logger.error(f'Ошибка парсинга RTF: {e}')
        # Если pypandoc не работает, пытаемся прочитать как текст
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                # Простая обработка RTF (удаляем RTF команды)
                import re
                content = re.sub(r'\\[a-z]+\d*\s?', '', content)
                content = re.sub(r'\{[^}]*\}', '', content)
                content = content.replace('\\par', '\n')
                html_content = content.replace('\n', '<br>').replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                return f'<div class="document-content"><pre style="white-space: pre-wrap; font-family: Arial, sans-serif;">{html_content}</pre></div>'
        except:
            return '<div class="document-content"><p>Не удалось распарсить RTF файл. Пожалуйста, скачайте файл для просмотра.</p></div>'


def parse_xlsx(file_path):
    """Парсит XLSX файл и возвращает HTML таблицу"""
    try:
        from openpyxl import load_workbook
        from openpyxl.styles import Font, PatternFill, Alignment
        
        wb = load_workbook(file_path, data_only=True)
        html_parts = ['<div class="document-content">']
        
        for sheet_name in wb.sheetnames:
            sheet = wb[sheet_name]
            html_parts.append(f'<h3 style="margin-top: 20px; margin-bottom: 10px;">Лист: {sheet_name}</h3>')
            html_parts.append('<table style="border-collapse: collapse; width: 100%; margin: 10px 0;">')
            
            # Получаем размеры данных
            if sheet.max_row > 0 and sheet.max_column > 0:
                for row in sheet.iter_rows(min_row=1, max_row=sheet.max_row, min_col=1, max_col=sheet.max_column):
                    html_parts.append('<tr>')
                    for cell in row:
                        # Получаем стили ячейки
                        cell_styles = ['border: 1px solid #ddd;', 'padding: 8px;']
                        
                        if cell.font:
                            if cell.font.bold:
                                cell_styles.append('font-weight: bold;')
                            if cell.font.italic:
                                cell_styles.append('font-style: italic;')
                            if cell.font.color and cell.font.color.rgb:
                                color = f'#{cell.font.color.rgb:06x}'
                                cell_styles.append(f'color: {color};')
                        
                        if cell.fill and cell.fill.start_color and cell.fill.start_color.rgb:
                            bg_color = f'#{cell.fill.start_color.rgb:06x}'
                            cell_styles.append(f'background-color: {bg_color};')
                        
                        if cell.alignment:
                            if cell.alignment.horizontal:
                                cell_styles.append(f'text-align: {cell.alignment.horizontal};')
                        
                        cell_value = str(cell.value) if cell.value is not None else ''
                        cell_value = cell_value.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                        
                        style_str = ' '.join(cell_styles)
                        html_parts.append(f'<td style="{style_str}">{cell_value}</td>')
                    
                    html_parts.append('</tr>')
            
            html_parts.append('</table>')
        
        html_parts.append('</div>')
        return ''.join(html_parts)
        
    except Exception as e:
        logger.error(f'Ошибка парсинга XLSX: {e}')
        raise


def parse_file(file_path):
    """
    Парсит файл и возвращает HTML с содержимым
    
    Args:
        file_path: Путь к файлу
        
    Returns:
        dict: {
            'success': bool,
            'html': str,  # HTML содержимое
            'error': str  # Сообщение об ошибке (если есть)
        }
    """
    file_path = Path(file_path)
    
    if not file_path.exists():
        return {
            'success': False,
            'html': '',
            'error': 'Файл не найден'
        }
    
    if not file_path.is_file():
        return {
            'success': False,
            'html': '',
            'error': 'Указанный путь не является файлом'
        }
    
    ext = file_path.suffix.lower()
    
    try:
        if ext == '.docx':
            html = parse_docx(file_path)
        elif ext == '.doc':
            html = parse_doc(file_path)
        elif ext == '.pdf':
            html = parse_pdf(file_path)
        elif ext == '.rtf':
            html = parse_rtf(file_path)
        elif ext in ['.xlsx', '.xls']:
            html = parse_xlsx(file_path)
        else:
            return {
                'success': False,
                'html': '',
                'error': f'Неподдерживаемый формат файла: {ext}'
            }
        
        return {
            'success': True,
            'html': html,
            'error': None
        }
        
    except Exception as e:
        logger.error(f'Ошибка парсинга файла {file_path}: {e}')
        return {
            'success': False,
            'html': '',
            'error': f'Ошибка парсинга: {str(e)}'
        }

