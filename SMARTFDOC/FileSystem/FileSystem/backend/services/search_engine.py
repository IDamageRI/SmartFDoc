import re
from difflib import SequenceMatcher
from typing import List, Dict, Tuple


def calculate_relevance_score(query: str, document: Dict) -> float:
    query_lower = query.lower().strip()
    if not query_lower:
        return 0.0
    
    is_external = document.get('category') == 'external'
    external_penalty = 0.3 if is_external else 1.0
    
    score = 0.0
    max_score = 0.0
    
    file_name = (document.get('file_name') or '').lower()
    title = (document.get('title') or '').lower()
    
    if file_name:
        max_score += 3.0
        if query_lower in file_name:
            if file_name == query_lower:
                score += 3.0
            elif file_name.startswith(query_lower):
                score += 2.5
            else:
                score += 2.0
        
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
    
    description = (document.get('description') or '').lower()
    if description:
        max_score += 1.0
        if query_lower in description:
            score += 1.0
        similarity = SequenceMatcher(None, query_lower, description).ratio()
        score += similarity * 0.5
    
    doc_type = (document.get('document_type_name') or '').lower()
    if doc_type:
        max_score += 0.5
        if query_lower in doc_type:
            score += 0.5
    
    department = (document.get('department_name') or '').lower()
    if department:
        max_score += 0.5
        if query_lower in department:
            score += 0.5
    
    if max_score > 0:
        normalized_score = min(score / max_score, 1.0)
    else:
        normalized_score = 0.0
    
    normalized_score *= external_penalty
    
    return normalized_score


def rank_search_results(query: str, documents: List[Dict]) -> List[Dict]:
    if not query or not query.strip():
        internal_docs = [d for d in documents if d.get('category') != 'external']
        external_docs = [d for d in documents if d.get('category') == 'external']
        return internal_docs + external_docs
    
    query = query.strip()
    
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
    
    internal_docs.sort(key=lambda x: x.get('_relevance_score', 0.0), reverse=True)
    external_docs.sort(key=lambda x: x.get('_relevance_score', 0.0), reverse=True)
    
    return internal_docs + external_docs


def fuzzy_search(query: str, text: str) -> bool:
    if not query or not text:
        return False
    
    query_lower = query.lower()
    text_lower = text.lower()
    
    if query_lower in text_lower:
        return True
    
    query_words = query_lower.split()
    text_words = text_lower.split()
    
    for q_word in query_words:
        for t_word in text_words:
            if q_word in t_word or t_word in q_word:
                return True
    
    similarity = SequenceMatcher(None, query_lower, text_lower).ratio()
    if similarity > 0.6:
        return True
    
    return False

