from pathlib import Path
import logging

try:
    from docx import Document
    from docx.shared import RGBColor, Pt
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False

try:
    from PyPDF2 import PdfReader
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

try:
    from openpyxl import load_workbook
    OPENPYXL_AVAILABLE = True
except ImportError:
    OPENPYXL_AVAILABLE = False

try:
    import xlrd
    XLRD_AVAILABLE = True
except ImportError:
    XLRD_AVAILABLE = False

logger = logging.getLogger(__name__)


def extract_text_content(file_path):
    file_path = Path(file_path)
    
    if not file_path.exists() or not file_path.is_file():
        return ''
    
    ext = file_path.suffix.lower()
    text_parts = []
    
    try:
        if ext == '.docx':
            if not DOCX_AVAILABLE:
                return ''
            doc = Document(file_path)
            for para in doc.paragraphs:
                if para.text.strip():
                    text_parts.append(para.text)
            for table in doc.tables:
                for row in table.rows:
                    row_text = []
                    for cell in row.cells:
                        if cell.text.strip():
                            row_text.append(cell.text)
                    if row_text:
                        text_parts.append(' '.join(row_text))
        
        elif ext == '.doc':
            try:
                import pypandoc
                text = pypandoc.convert_file(str(file_path), 'plain', format='doc')
                text_parts.append(text)
            except:
                return ''
        
        elif ext == '.pdf':
            if not PDF_AVAILABLE:
                return ''
            reader = PdfReader(file_path)
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    text_parts.append(text)
        
        elif ext == '.rtf':
            try:
                import pypandoc
                text = pypandoc.convert_file(str(file_path), 'plain', format='rtf')
                text_parts.append(text)
            except:
                try:
                    import striprtf
                    with open(file_path, 'rb') as f:
                        rtf_content = f.read()
                    text = striprtf.RTF(rtf_content).plain
                    text_parts.append(text)
                except ImportError:
                    try:
                        with open(file_path, 'rb') as f:
                            rtf_content = f.read()
                        
                        import re
                        
                        # Пробуем разные кодировки
                        text = None
                        for encoding in ['utf-8', 'cp1251', 'latin-1']:
                            try:
                                text = rtf_content.decode(encoding, errors='ignore')
                                break
                            except:
                                continue
                        
                        if not text:
                            text = rtf_content.decode('utf-8', errors='ignore')
                        
                        # Удаляем RTF заголовок
                        text = re.sub(r'\\rtf\d*\s*', '', text)
                        
                        # Удаляем команды
                        text = re.sub(r'\\[a-z]+\d*\s*', ' ', text)
                        text = re.sub(r'\\[^a-z\s{}]', '', text)
                        
                        # Удаляем группы, сохраняя текст
                        def clean_group(match):
                            content = match.group(1)
                            if re.search(r'[а-яА-Яa-zA-Z0-9]{2,}', content):
                                cleaned = re.sub(r'\\[a-z]+\d*\s*', ' ', content)
                                cleaned = re.sub(r'\\[^a-z\s{}]', '', cleaned)
                                return cleaned
                            return ''
                        
                        max_iterations = 20
                        iteration = 0
                        while '{' in text and iteration < max_iterations:
                            new_text = re.sub(r'\{([^{}]*)\}', clean_group, text)
                            if new_text == text:
                                break
                            text = new_text
                            iteration += 1
                        
                        text = text.replace('{', '').replace('}', '')
                        text = text.replace('\\par', '\n')
                        text = text.replace('\\line', '\n')
                        text = text.replace('\\tab', '\t')
                        text = re.sub(r'Width\d+Width\d+', '', text)
                        text = re.sub(r'[ \t]+', ' ', text)
                        text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
                        
                        lines = []
                        for line in text.split('\n'):
                            line = line.strip()
                            if line and re.search(r'[а-яА-Яa-zA-Z0-9]{2,}', line):
                                lines.append(line)
                        
                        text = '\n'.join(lines).strip()
                        text_parts.append(text)
                    except:
                        return ''
                except:
                    return ''
        
        elif ext == '.txt':
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    text_parts.append(f.read())
            except:
                return ''
        
        elif ext == '.xlsx':
            if not OPENPYXL_AVAILABLE:
                return ''
            wb = load_workbook(file_path, data_only=True)
            for sheet_name in wb.sheetnames:
                sheet = wb[sheet_name]
                if sheet.max_row > 0 and sheet.max_column > 0:
                    for row in sheet.iter_rows(min_row=1, max_row=sheet.max_row, min_col=1, max_col=sheet.max_column):
                        row_text = []
                        for cell in row:
                            if cell.value is not None:
                                row_text.append(str(cell.value))
                        if row_text:
                            text_parts.append(' '.join(row_text))
        
        elif ext == '.xls':
            if not XLRD_AVAILABLE:
                return ''
            wb = xlrd.open_workbook(file_path)
            for sheet_name in wb.sheet_names():
                sheet = wb.sheet_by_name(sheet_name)
                for row_idx in range(sheet.nrows):
                    row_text = []
                    for col_idx in range(sheet.ncols):
                        cell = sheet.cell(row_idx, col_idx)
                        if cell.value:
                            row_text.append(str(cell.value))
                    if row_text:
                        text_parts.append(' '.join(row_text))
        
        full_text = ' '.join(text_parts)
        return full_text.lower()  # Возвращаем в нижнем регистре для поиска
        
    except Exception as e:
        logger.error(f'Ошибка извлечения текста из файла {file_path}: {e}')
        return ''


def parse_docx(file_path):
    if not DOCX_AVAILABLE:
        raise ImportError('Библиотека python-docx не установлена. Установите: pip install python-docx')
    
    try:
        doc = Document(file_path)
        html_parts = ['<div class="document-content">']
        
        for para in doc.paragraphs:
            if not para.text.strip():
                html_parts.append('<p>&nbsp;</p>')
                continue
            
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
                
                if run.font and run.font.color:
                    try:
                        if hasattr(run.font.color, 'rgb') and run.font.color.rgb:
                            rgb = run.font.color.rgb
                            if isinstance(rgb, int):
                                color = f'#{rgb:06x}'
                            else:
                                try:
                                    color = f'#{int(rgb):06x}'
                                except:
                                    color = None
                            if color:
                                run_styles.append(f'color: {color};')
                    except (ValueError, TypeError, AttributeError):
                        pass
                
                try:
                    if hasattr(run.font, 'highlight_color'):
                        highlight = run.font.highlight_color
                        if highlight is not None:
                            try:
                                highlight_val = int(highlight) if not isinstance(highlight, int) else highlight
                                if highlight_val and highlight_val != 0:  # 0 = None в docx
                                    highlight_colors = {
                                        1: '#FFFF00',  # Yellow
                                        2: '#00FF00',  # Bright Green
                                        3: '#00FFFF',  # Cyan
                                        4: '#FF00FF',  # Magenta
                                        5: '#0000FF',  # Blue
                                        6: '#FF0000',  # Red
                                        7: '#000080',  # Dark Blue
                                        8: '#008000',  # Dark Green
                                        9: '#008080',  # Dark Cyan
                                        10: '#800080', # Dark Magenta
                                        11: '#800000', # Dark Red
                                        12: '#808000', # Dark Yellow
                                        13: '#808080', # Dark Gray
                                        14: '#C0C0C0', # Light Gray
                                        15: '#000000', # Black
                                    }
                                    bg_color = highlight_colors.get(highlight_val, '#FFFF00')
                                    run_styles.append(f'background-color: {bg_color};')
                            except (ValueError, TypeError, AttributeError):
                                pass
                except (ValueError, TypeError, AttributeError):
                    pass
                
                if run_styles:
                    para_html += f'<span style="{"; ".join(run_styles)}">{text}</span>'
                else:
                    para_html += text
            
            para_html += '</p>'
            html_parts.append(para_html)
        
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
    try:
        import pypandoc
        html = pypandoc.convert_file(str(file_path), 'html', format='doc')
        return f'<div class="document-content">{html}</div>'
    except Exception as e:
        logger.error(f'Ошибка парсинга DOC: {e}')
        return '<div class="document-content"><p>Парсинг старых DOC файлов требует установки pandoc. Пожалуйста, скачайте файл для просмотра.</p></div>'


def parse_pdf(file_path):
    if not PDF_AVAILABLE:
        raise ImportError('Библиотека PyPDF2 не установлена. Установите: pip install PyPDF2')
    
    try:
        reader = PdfReader(file_path)
        html_parts = ['<div class="document-content">']
        
        for page_num, page in enumerate(reader.pages, 1):
            html_parts.append(f'<div class="pdf-page" style="page-break-after: always; margin-bottom: 20px;">')
            html_parts.append(f'<h3 style="color: #666; font-size: 14px; margin-bottom: 10px;">Страница {page_num}</h3>')
            
            text = page.extract_text()
            if text:
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
    try:
        import pypandoc
        html = pypandoc.convert_file(str(file_path), 'html', format='rtf')
        return f'<div class="document-content">{html}</div>'
    except Exception as e:
        logger.error(f'Ошибка парсинга RTF через pypandoc: {e}')
        try:
            import striprtf
            with open(file_path, 'rb') as f:
                rtf_content = f.read()
            text = striprtf.RTF(rtf_content).plain
            # Дополнительная очистка текста от служебной информации
            import re
            # Удаляем служебные строки
            lines = []
            for line in text.split('\n'):
                line = line.strip()
                # Пропускаем строки с только служебной информацией
                if line and not re.match(r'^(Width|Times New Roman|Tahoma|Normal|Default|Microsoft|HYPERLINK)', line, re.IGNORECASE):
                    if re.search(r'[а-яА-Яa-zA-Z0-9]{3,}', line):
                        lines.append(line)
            text = '\n'.join(lines)
            html_content = text.replace('\n', '<br>').replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            return f'<div class="document-content"><pre style="white-space: pre-wrap; font-family: Arial, sans-serif; line-height: 1.6;">{html_content}</pre></div>'
        except ImportError:
            logger.warning('striprtf не установлен, используем базовый парсинг')
        except Exception as e:
            logger.error(f'Ошибка парсинга RTF через striprtf: {e}')
        
        try:
            with open(file_path, 'rb') as f:
                rtf_content = f.read()
            
            import re
            
            # Пробуем разные кодировки для декодирования
            text = None
            for encoding in ['utf-8', 'cp1251', 'latin-1']:
                try:
                    text = rtf_content.decode(encoding, errors='ignore')
                    break
                except:
                    continue
            
            if not text:
                text = rtf_content.decode('utf-8', errors='ignore')
            
            # Извлекаем и декодируем шестнадцатеричные последовательности ДО удаления RTF команд
            # Это важно, так как текст может быть закодирован в hex
            def decode_hex_text(match):
                hex_str = match.group(1)
                # Обрабатываем только последовательности из четного количества символов (байты)
                if len(hex_str) % 2 != 0:
                    return ''
                # Минимум 4 символа (2 байта) для декодирования
                if len(hex_str) < 4:
                    return ''
                try:
                    hex_bytes = bytes.fromhex(hex_str)
                    # Пробуем Windows-1251 (для русского текста) - приоритет для кириллицы
                    decoded = hex_bytes.decode('cp1251', errors='ignore')
                    # Проверяем, что получился читаемый текст (минимум 2 буквы)
                    if re.search(r'[а-яА-Яa-zA-Z0-9\s]{2,}', decoded):
                        return decoded
                except:
                    pass
                try:
                    # Пробуем UTF-8
                    decoded = hex_bytes.decode('utf-8', errors='ignore')
                    if re.search(r'[а-яА-Яa-zA-Z0-9\s]{2,}', decoded):
                        return decoded
                except:
                    pass
                return ''
            
            # Декодируем шестнадцатеричные последовательности (от 4 до 200 символов, четное количество)
            # Ищем последовательности, которые могут быть закодированным текстом
            text = re.sub(r'\b([0-9a-fA-F]{4,200})\b', decode_hex_text, text)
            
            # Также обрабатываем последовательности без границ слов (внутри текста)
            # Но только если они достаточно длинные (от 8 символов)
            text = re.sub(r'([0-9a-fA-F]{8,200})', decode_hex_text, text)
            
            # Удаляем RTF заголовок и команды
            text = re.sub(r'\\rtf\d*\s*', '', text)
            text = re.sub(r'\\[a-z]+\d*\s*', ' ', text)
            text = re.sub(r'\\[^a-z\s{}]', '', text)
            
            # Удаляем информацию о шрифтах и форматировании
            text = re.sub(r'Times New Roman[^;]*;?', '', text, flags=re.IGNORECASE)
            text = re.sub(r'Tahoma[^;]*;?', '', text, flags=re.IGNORECASE)
            text = re.sub(r'Width\d+Width\d+', '', text)
            text = re.sub(r'Width\d+', '', text)
            text = re.sub(r'WidthB\d+', '', text)
            text = re.sub(r'Normal[^;]*;?', '', text, flags=re.IGNORECASE)
            text = re.sub(r'Default Paragraph Font[^;]*;?', '', text, flags=re.IGNORECASE)
            text = re.sub(r'Microsoft Word[^;]*;?', '', text, flags=re.IGNORECASE)
            text = re.sub(r'HYPERLINK[^"]*"[^"]*"', '', text, flags=re.IGNORECASE)
            text = re.sub(r'Document Map[^;]*;?', '', text, flags=re.IGNORECASE)
            text = re.sub(r'Hyperlink[^;]*;?', '', text, flags=re.IGNORECASE)
            
            # Удаляем длинные числовые последовательности (коды)
            text = re.sub(r'\b[0-9]{8,}\b', '', text)
            
            # Удаляем группы в фигурных скобках, сохраняя текст
            def clean_group(match):
                content = match.group(1)
                # Если внутри есть читаемый текст, сохраняем его
                if re.search(r'[а-яА-Яa-zA-Z0-9]{2,}', content):
                    cleaned = re.sub(r'\\[a-z]+\d*\s*', ' ', content)
                    cleaned = re.sub(r'\\[^a-z\s{}]', '', cleaned)
                    return cleaned
                return ''
            
            # Многократно удаляем вложенные группы
            max_iterations = 20
            iteration = 0
            while '{' in text and iteration < max_iterations:
                new_text = re.sub(r'\{([^{}]*)\}', clean_group, text)
                if new_text == text:
                    break
                text = new_text
                iteration += 1
            
            # Удаляем оставшиеся фигурные скобки
            text = text.replace('{', '').replace('}', '')
            
            # Заменяем RTF команды
            text = text.replace('\\par', '\n')
            text = text.replace('\\line', '\n')
            text = text.replace('\\tab', '\t')
            text = text.replace('\\emdash', '—')
            text = text.replace('\\endash', '–')
            
            # Удаляем служебные команды и символы
            text = re.sub(r'[0-9]{10,}', '', text)  # Удаляем длинные числовые последовательности
            text = re.sub(r'[{}]', '', text)
            
            # Удаляем оставшиеся шестнадцатеричные последовательности
            text = re.sub(r'\b[0-9a-fA-F]{6,}\b', '', text)
            
            # Очистка пробелов
            text = re.sub(r'[ \t]+', ' ', text)
            text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
            
            # Разбиваем на строки и фильтруем
            lines = []
            for line in text.split('\n'):
                line = line.strip()
                # Пропускаем строки без читаемого текста
                if line and re.search(r'[а-яА-Яa-zA-Z0-9]{3,}', line):
                    # Удаляем оставшиеся служебные символы
                    line = re.sub(r'[0-9]{6,}', '', line)  # Удаляем длинные числа
                    line = re.sub(r'\b[0-9a-fA-F]{4,}\b', '', line)  # Удаляем hex последовательности
                    line = re.sub(r'^[^а-яА-Яa-zA-Z0-9]+', '', line)  # Удаляем начало без букв
                    line = re.sub(r'[^а-яА-Яa-zA-Z0-9\s.,;:!?()-]+$', '', line)  # Удаляем конец без букв
                    # Удаляем строки, состоящие в основном из цифр и служебных символов
                    if line.strip() and len(line.strip()) > 2:
                        # Проверяем, что в строке достаточно букв
                        letters = len(re.findall(r'[а-яА-Яa-zA-Z]', line))
                        if letters >= 3:
                            lines.append(line.strip())
            
            text = '\n'.join(lines).strip()
            
            if not text or len(text) < 3:
                return '<div class="document-content"><p>Не удалось извлечь текст из RTF файла. Пожалуйста, скачайте файл для просмотра.</p></div>'
            
            html_content = text.replace('\n', '<br>').replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            return f'<div class="document-content"><pre style="white-space: pre-wrap; font-family: Arial, sans-serif; line-height: 1.6;">{html_content}</pre></div>'
        except Exception as e:
            logger.error(f'Ошибка базового парсинга RTF: {e}')
            return '<div class="document-content"><p>Не удалось распарсить RTF файл. Пожалуйста, скачайте файл для просмотра.</p></div>'


def parse_xlsx(file_path):
    file_path = Path(file_path)
    ext = file_path.suffix.lower()
    
    try:
        html_parts = ['<div class="document-content">']
        
        if ext == '.xlsx':
            if not OPENPYXL_AVAILABLE:
                raise ImportError('Библиотека openpyxl не установлена. Установите: pip install openpyxl')
            wb = load_workbook(file_path, data_only=True)
            
            for sheet_name in wb.sheetnames:
                sheet = wb[sheet_name]
                html_parts.append(f'<h3 style="margin-top: 20px; margin-bottom: 10px;">Лист: {sheet_name}</h3>')
                html_parts.append('<table style="border-collapse: collapse; width: 100%; margin: 10px 0;">')
                
                if sheet.max_row > 0 and sheet.max_column > 0:
                    for row in sheet.iter_rows(min_row=1, max_row=sheet.max_row, min_col=1, max_col=sheet.max_column):
                        html_parts.append('<tr>')
                        for cell in row:
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
                            
                            if cell.alignment and cell.alignment.horizontal:
                                cell_styles.append(f'text-align: {cell.alignment.horizontal};')
                            
                            cell_value = str(cell.value) if cell.value is not None else ''
                            cell_value = cell_value.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                            
                            style_str = ' '.join(cell_styles)
                            html_parts.append(f'<td style="{style_str}">{cell_value}</td>')
                        
                        html_parts.append('</tr>')
                
                html_parts.append('</table>')
        
        elif ext == '.xls':
            if not XLRD_AVAILABLE:
                try:
                    import pypandoc
                    html = pypandoc.convert_file(str(file_path), 'html', format='xls')
                    return f'<div class="document-content">{html}</div>'
                except:
                    return '<div class="document-content"><p>Для просмотра старых XLS файлов требуется установка библиотеки xlrd. Пожалуйста, скачайте файл для просмотра.</p></div>'
            
            try:
                wb = xlrd.open_workbook(file_path)
                
                for sheet_name in wb.sheet_names():
                    sheet = wb.sheet_by_name(sheet_name)
                    html_parts.append(f'<h3 style="margin-top: 20px; margin-bottom: 10px;">Лист: {sheet_name}</h3>')
                    html_parts.append('<table style="border-collapse: collapse; width: 100%; margin: 10px 0;">')
                    
                    for row_idx in range(sheet.nrows):
                        html_parts.append('<tr>')
                        for col_idx in range(sheet.ncols):
                            cell = sheet.cell(row_idx, col_idx)
                            cell_value = str(cell.value) if cell.value else ''
                            cell_value = cell_value.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                            
                            cell_styles = ['border: 1px solid #ddd;', 'padding: 8px;']
                            
                            if cell.ctype == xlrd.XL_CELL_NUMBER:
                                cell_styles.append('text-align: right;')
                            
                            style_str = ' '.join(cell_styles)
                            html_parts.append(f'<td style="{style_str}">{cell_value}</td>')
                        
                        html_parts.append('</tr>')
                    
                    html_parts.append('</table>')
            except Exception as e:
                logger.error(f'Ошибка парсинга XLS: {e}')
                raise
        
        else:
            raise ValueError(f'Неподдерживаемый формат Excel: {ext}')
        
        html_parts.append('</div>')
        return ''.join(html_parts)
        
    except Exception as e:
        logger.error(f'Ошибка парсинга Excel: {e}')
        raise


def parse_file(file_path):
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

