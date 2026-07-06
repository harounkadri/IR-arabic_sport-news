import re

class BooleanSearcher:
    def __init__(self, indexer, preprocessor):
        self.indexer = indexer
        self.preprocessor = preprocessor
    
    def search(self, query):
        query = query.strip()
        
        if not query:
            return []
        
        if query.startswith('"') and query.endswith('"'):
            return self._phrase_search(query[1:-1])
        elif query.startswith('#'):
            return self._proximity_search(query)
        elif "AND NOT" in query.upper():
            return self._boolean_and_not(query)
        elif "AND" in query.upper():
            return self._boolean_and(query)
        elif "OR" in query.upper():
            return self._boolean_or(query)
        else:
            return self._simple_search(query)
    
    def _simple_search(self, query_text):
        terms = self.preprocessor.preprocess_text(
            query_text, 
            stem=True, 
            protect_words=True
        )
        
        if not terms:
            return []
        
        all_docs = set()
        for term in terms:
            docs = self.indexer.get_documents_with_term(term)
            if docs:
                all_docs.update(docs)
        
        return sorted(list(all_docs), key=lambda x: int(x))
    
    def _boolean_and(self, query):
        parts = re.split(r'\s+AND\s+', query, flags=re.IGNORECASE)
        
        if len(parts) < 2:
            return self._simple_search(query)
        
        doc_sets = []
        
        for part in parts:
            terms = self.preprocessor.preprocess_text(
                part.strip(), 
                stem=True, 
                protect_words=True
            )
            
            if not terms:
                return []
            
            docs = set()
            for term in terms:
                term_docs = self.indexer.get_documents_with_term(term)
                if term_docs:
                    docs.update(term_docs)
            
            doc_sets.append(docs)
        
        if not doc_sets:
            return []
        
        result = set(doc_sets[0])
        for doc_set in doc_sets[1:]:
            result &= doc_set
        
        return sorted(list(result), key=lambda x: int(x))
    
    def _boolean_or(self, query):
        parts = re.split(r'\s+OR\s+', query, flags=re.IGNORECASE)
        
        if len(parts) < 2:
            return self._simple_search(query)
        
        all_docs = set()
        
        for part in parts:
            terms = self.preprocessor.preprocess_text(
                part.strip(), 
                stem=True, 
                protect_words=True
            )
            
            if terms:
                for term in terms:
                    docs = self.indexer.get_documents_with_term(term)
                    if docs:
                        all_docs.update(docs)
        
        return sorted(list(all_docs), key=lambda x: int(x))
    
    def _boolean_and_not(self, query):
        pattern = r'\s+AND\s+NOT\s+'
        parts = re.split(pattern, query, flags=re.IGNORECASE)
        
        if len(parts) < 2:
            return self._simple_search(query)
        
        terms_a = self.preprocessor.preprocess_text(
            parts[0].strip(), 
            stem=True, 
            protect_words=True
        )
        
        if not terms_a:
            return []
        
        docs_a = set()
        for term in terms_a:
            docs = self.indexer.get_documents_with_term(term)
            if docs:
                docs_a.update(docs)
        
        if not docs_a:
            return []
        
        terms_b = self.preprocessor.preprocess_text(
            parts[1].strip(), 
            stem=True, 
            protect_words=True
        )
        
        docs_b = set()
        if terms_b:
            for term in terms_b:
                docs = self.indexer.get_documents_with_term(term)
                if docs:
                    docs_b.update(docs)
        
        result = docs_a - docs_b
        
        return sorted(list(result), key=lambda x: int(x))
    
    def _phrase_search(self, phrase):
        terms = self.preprocessor.preprocess_text(
            phrase, 
            stem=True, 
            protect_words=True
        )
        
        if len(terms) < 1:
            return []
        
        if len(terms) == 1:
            docs = self.indexer.get_documents_with_term(terms[0])
            return sorted(docs, key=lambda x: int(x))
        
        common_docs = None
        
        for term in terms:
            docs = set(self.indexer.get_documents_with_term(term))
            if not docs:
                return []
            
            if common_docs is None:
                common_docs = docs
            else:
                common_docs &= docs
            
            if not common_docs:
                return []
        
        results = []
        for doc_id in common_docs:
            if self._check_exact_phrase_order(terms, doc_id):
                results.append(doc_id)
        
        return sorted(results, key=lambda x: int(x))
    
    def _check_exact_phrase_order(self, terms, doc_id):
        positions = []
        for i, term in enumerate(terms):
            term_positions = self.indexer.get_positions(term, doc_id)
            if not term_positions:
                return False
            if i == 0:
                positions.append(sorted(term_positions))
            else:
                positions.append(set(term_positions))
        
        for start_pos in positions[0]:
            match = True
            current_pos = start_pos
            
            for i in range(1, len(terms)):
                if (current_pos + 1) not in positions[i]:
                    match = False
                    break
                current_pos += 1
            
            if match:
                return True
        
        return False
    
    def _proximity_search(self, query):
        match = re.match(r'#(\d+)\(([^,]+),\s*([^)]+)\)', query)
        if not match:
            return []
        
        distance = int(match.group(1))
        term1_text = match.group(2).strip()
        term2_text = match.group(3).strip()
        
        terms1 = self.preprocessor.preprocess_text(
            term1_text, 
            stem=True, 
            protect_words=True
        )
        terms2 = self.preprocessor.preprocess_text(
            term2_text, 
            stem=True, 
            protect_words=True
        )
        
        if not terms1 or not terms2:
            return []
        
        all_docs = set()
        
        for t1 in terms1:
            for t2 in terms2:
                docs1 = set(self.indexer.get_documents_with_term(t1))
                docs2 = set(self.indexer.get_documents_with_term(t2))
                common_docs = docs1 & docs2
                
                for doc_id in common_docs:
                    if self._check_proximity(t1, t2, doc_id, distance):
                        all_docs.add(doc_id)
        
        return sorted(list(all_docs), key=lambda x: int(x))
    
    def _check_proximity(self, term1, term2, doc_id, max_distance):
        pos1 = self.indexer.get_positions(term1, doc_id)
        pos2 = self.indexer.get_positions(term2, doc_id)
        
        if not pos1 or not pos2:
            return False
        
        pos1.sort()
        pos2.sort()
        
        i, j = 0, 0
        while i < len(pos1) and j < len(pos2):
            dist = abs(pos1[i] - pos2[j])
            
            if dist <= max_distance:
                return True
            
            if pos1[i] < pos2[j]:
                i += 1
            else:
                j += 1
        
        return False