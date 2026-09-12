"""
Улучшенный поисковый движок с ранжированием результатов
"""
import re
from difflib import SequenceMatcher
from typing import List, Dict, Tuple


def calculate_relevance_score(query: str, document: Dict) -> float:
    """
    Вычисляет релевантность документа запросу
    
    Args:
        query: Поисковый запрос
        document: Словарь с данными документа
    
    Returns:
        float: Оценка релевантности (0.0 - 1.0)
    """
    query_lower = query.lower().strip()
    if not query_lower:
        return 0.0
    
    # Внешние документы имеют минимальный приоритет
    is_external = document.get('category') == 'external'
    external_penalty = 0.3 if is_external else 1.0
    
    score = 0.0
    max_score = 0.0
    
    # Проверяем название файла (самый высокий приоритет)
    file_name = (document.get('file_name') or '').lower()
    title = (document.get('title') or '').lower()
    
    if file_name:
        max_score += 3.0
        if query_lower in file_name:
            # Точное совпадение в названии файла
            if file_name == query_lower:
                score += 3.0
            elif file_name.startswith(query_lower):
                score += 2.5
            else:
                score += 2.0
        
        # Частичное совпадение
        similarity = SequenceMatcher(None, query_lower, file_name).ratio()
        score += similarity * 1.0
    
    if title:
        max_score += 2.5
        if query_lower in title:
            if title == query_lower:
                score += 2.5
            elif title.startswith(query_lower):
                score += 2.0
            else:
                score += 1.5
        
        similarity = SequenceMatcher(None, query_lower, title).ratio()
        score += similarity * 0.8
    
    # Проверяем описание
    description = (document.get('description') or '').lower()
    if description:
        max_score += 1.0
        if query_lower in description:
            score += 1.0
        similarity = SequenceMatcher(None, query_lower, description).ratio()
        score += similarity * 0.5
    
    # Проверяем тип документа
    doc_type = (document.get('document_type_name') or '').lower()
    if doc_type:
        max_score += 0.5
        if query_lower in doc_type:
            score += 0.5
    
    # Проверяем отдел
    department = (document.get('department_name') or '').lower()
    if department:
        max_score += 0.5
        if query_lower in department:
            score += 0.5
    
    # Нормализуем оценку
    if max_score > 0:
        normalized_score = min(score / max_score, 1.0)
    else:
        normalized_score = 0.0
    
    # Применяем штраф для внешних документов
    normalized_score *= external_penalty
    
    return normalized_score


def rank_search_results(query: str, documents: List[Dict]) -> List[Dict]:
    """
    Ранжирует результаты поиска по релевантности
    
    Args:
        query: Поисковый запрос
        documents: Список документов
    
    Returns:
        List[Dict]: Отсортированный список документов с оценкой релевантности
    """
    if not query or not query.strip():
        # Если запроса нет, сортируем: сначала внутренние, потом внешние
        internal_docs = [d for d in documents if d.get('category') != 'external']
        external_docs = [d for d in documents if d.get('category') == 'external']
        return internal_docs + external_docs
    
    query = query.strip()
    
    # Разделяем на внутренние и внешние документы
    internal_docs = []
    external_docs = []
    
    for doc in documents:
        score = calculate_relevance_score(query, doc)
        doc_with_score = doc.copy()
        doc_with_score['_relevance_score'] = score
        
        if doc.get('category') == 'external':
            external_docs.append(doc_with_score)
        else:
            internal_docs.append(doc_with_score)
    
    # Сортируем каждую группу по релевантности
    internal_docs.sort(key=lambda x: x.get('_relevance_score', 0.0), reverse=True)
    external_docs.sort(key=lambda x: x.get('_relevance_score', 0.0), reverse=True)
    
    # Возвращаем сначала внутренние, потом внешние
    return internal_docs + external_docs


def fuzzy_search(query: str, text: str) -> bool:
    """
    Нечеткий поиск в тексте
    
    Args:
        query: Поисковый запрос
        text: Текст для поиска
    
    Returns:
        bool: True если найдено совпадение
    """
    if not query or not text:
        return False
    
    query_lower = query.lower()
    text_lower = text.lower()
    
    # Точное совпадение
    if query_lower in text_lower:
        return True
    
    # Частичное совпадение (слова)
    query_words = query_lower.split()
    text_words = text_lower.split()
    
    for q_word in query_words:
        for t_word in text_words:
            if q_word in t_word or t_word in q_word:
                return True
    
    # Нечеткое совпадение
    similarity = SequenceMatcher(None, query_lower, text_lower).ratio()
    if similarity > 0.6:
        return True
    
    return False

