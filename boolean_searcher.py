import re

class BooleanSearcher:
    def __init__(self, indexer, preprocessor):
        self.indexer = indexer
        self.preprocessor = preprocessor
    
    def search(self, query):
        query = query.strip()
        if not query:
            return []
            
        try:
            postfix = self._parse_to_postfix(query)
            result_docs = self._evaluate_postfix(postfix)
            return sorted(list(result_docs), key=lambda x: int(x) if x.isdigit() else x)
        except Exception as e:
            print(f"Erreur d'évaluation booléenne: {e}")
            return []

    def _parse_to_postfix(self, query):
        pattern = r'(#\d+\([^)]+\)|"[^"]+"|(?i)\bAND\b|(?i)\bOR\b|(?i)\bNOT\b|\(|\)|[^\s()"]+)'
        tokens = [t for t in re.findall(pattern, query) if t.strip()]
        
        precedence = {'NOT': 3, 'AND': 2, 'OR': 1, '(': 0}
        output = []
        operators = []
        
        for token in tokens:
            upper_tok = token.upper()
            if upper_tok in ['AND', 'OR', 'NOT']:
                while operators and precedence.get(operators[-1], 0) >= precedence[upper_tok]:
                    if upper_tok == 'NOT' and operators[-1] == 'NOT':
                        break
                    output.append(operators.pop())
                operators.append(upper_tok)
            elif upper_tok == '(':
                operators.append('(')
            elif upper_tok == ')':
                while operators and operators[-1] != '(':
                    output.append(operators.pop())
                if operators:
                    operators.pop()
            else:
                output.append(token)
                
        while operators:
            output.append(operators.pop())
            
        return output

    def _evaluate_postfix(self, postfix):
        stack = []
        all_docs = set(self.indexer.documents.keys())
        
        for token in postfix:
            upper_tok = token.upper()
            if upper_tok == 'AND':
                if len(stack) < 2: return set()
                right = stack.pop()
                left = stack.pop()
                stack.append(left & right)
            elif upper_tok == 'OR':
                if len(stack) < 2: return set()
                right = stack.pop()
                left = stack.pop()
                stack.append(left | right)
            elif upper_tok == 'NOT':
                if not stack: return set()
                operand = stack.pop()
                stack.append(all_docs - operand)
            else:
                if token.startswith('"') and token.endswith('"'):
                    docs = set(self._phrase_search(token[1:-1]))
                elif token.startswith('#'):
                    docs = set(self._proximity_search(token))
                else:
                    docs = set(self._simple_search(token))
                stack.append(docs)
                
        return stack[0] if stack else set()
    
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
        
        return list(all_docs)
    
    def _phrase_search(self, phrase):
        terms = self.preprocessor.preprocess_text(
            phrase, 
            stem=True, 
            protect_words=True
        )
        
        if len(terms) < 1:
            return []
        
        if len(terms) == 1:
            return self.indexer.get_documents_with_term(terms[0])
        
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
        
        return results
    
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
        
        return list(all_docs)
    
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