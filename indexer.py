from collections import defaultdict
import re

class PositionalIndexer:
    def __init__(self, preprocessor):
        self.preprocessor = preprocessor
        self.index = defaultdict(lambda: defaultdict(list))
        self.documents = {}
        self.total_docs = 0
        
    def build_index(self, documents):
        print("Construction de l'index...")
        
        for doc in documents:
            doc_id = doc['id']
            self.documents[doc_id] = doc
            
            tokens = self.preprocessor.preprocess_text(doc['full_text'], stem=True)
            
            for position, token in enumerate(tokens):
                self.index[token][doc_id].append(position)
        
        self.total_docs = len(self.documents)
        
        problem_count = self._check_index_problems()
        
        print(f"✓ Index construit: {len(self.index)} termes, {self.total_docs} documents")
        if problem_count > 0:
            print(f"⚠️  {problem_count} problèmes détectés dans l'index")
        
        if self.index:
            sample = list(self.index.keys())[:5]
            print(f"Exemples de termes: {sample}")
        
        return self.index
    
    def _check_index_problems(self):
        problem_count = 0
        problematic_terms = []
        
        for term in list(self.index.keys()):
            if self._has_non_arabic(term):
                problem_count += 1
                problematic_terms.append(term)
                
                if len(problematic_terms) <= 5:
                    df = len(self.index[term])
                    print(f"  Problème: '{term}' (dans {df} docs)")
        
        if problematic_terms and len(problematic_terms) > 5:
            print(f"  ... et {len(problematic_terms) - 5} autres termes problématiques")
        
        return problem_count
    
    def _has_non_arabic(self, text):
        arabic_pattern = re.compile(r'^[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]+$')
        return not arabic_pattern.match(text)
    
    def filter_arabic_only(self):
        print("Filtrage des termes arabes seulement...")
        
        arabic_pattern = re.compile(r'^[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]+$')
        arabic_index = {}
        
        terms_removed = []
        terms_kept = []
        
        for term, doc_dict in self.index.items():
            if arabic_pattern.match(term):
                arabic_index[term] = doc_dict
                terms_kept.append(term)
            else:
                terms_removed.append(term)
        
        old_count = len(self.index)
        self.index = arabic_index
        new_count = len(self.index)
        
        print(f"✓ Index filtré: {old_count} → {new_count} termes")
        print(f"  Termes supprimés (non-arabes): {len(terms_removed)}")
        print(f"  Termes conservés (arabes): {len(terms_kept)}")
        
        if terms_removed:
            print(f"  Exemples de termes supprimés: {terms_removed[:10]}")
        if terms_kept:
            print(f"  Exemples de termes conservés: {terms_kept[:10]}")
        
        return terms_removed
    
    def get_document_frequency(self, term):
        if term in self.index:
            return len(self.index[term])
        return 0
    
    def get_term_frequency(self, term, doc_id):
        if term in self.index and doc_id in self.index[term]:
            return len(self.index[term][doc_id])
        return 0
    
    def get_documents_with_term(self, term):
        if term in self.index:
            return list(self.index[term].keys())
        return []
    
    def get_positions(self, term, doc_id):
        if term in self.index and doc_id in self.index[term]:
            return self.index[term][doc_id]
        return []
    
    def save_index(self, filename):
        try:
            sorted_terms = sorted(self.index.keys())
            
            with open(filename, 'w', encoding='utf-8') as f:
                for term in sorted_terms:
                    df = len(self.index[term])
                    f.write(f"{term}:{df}\n")
                    
                    for doc_id in sorted(self.index[term].keys(), key=lambda x: int(x) if x.isdigit() else x):
                        positions = self.index[term][doc_id]
                        sorted_positions = sorted(positions)
                        positions_str = ','.join(map(str, sorted_positions))
                        f.write(f"\t{doc_id}: {positions_str}\n")
            
            print(f"✓ Index sauvegardé: {filename}")
            print(f"  - {len(sorted_terms)} termes")
            print(f"  - {self.total_docs} documents")
            
            return True
            
        except Exception as e:
            print(f"✗ Erreur sauvegarde: {e}")
            return False
    
    def print_stats(self):
        print(f"\n=== Statistiques de l'Index ===")
        print(f"Documents: {self.total_docs}")
        print(f"Termes uniques: {len(self.index)}")
        
        total_terms_in_docs = 0
        for doc_id in self.documents:
            doc_terms = set()
            for term, doc_dict in self.index.items():
                if doc_id in doc_dict:
                    doc_terms.add(term)
            total_terms_in_docs += len(doc_terms)
        
        if self.total_docs > 0:
            avg_terms_per_doc = total_terms_in_docs / self.total_docs
            print(f"Termes moyens par document: {avg_terms_per_doc:.1f}")
        
        term_freqs = [(term, len(docs)) for term, docs in self.index.items()]
        term_freqs.sort(key=lambda x: x[1], reverse=True)
        
        print("\nTop 10 termes (par fréquence document):")
        for i, (term, freq) in enumerate(term_freqs[:10], 1):
            percentage = (freq / self.total_docs) * 100 if self.total_docs > 0 else 0
            print(f"  {i:2d}. {term:20s} ({freq:4d} docs, {percentage:5.1f}%)")
        
        print("\n10 termes les plus rares (par fréquence document):")
        rare_terms = [t for t in term_freqs if t[1] == 1]
        if rare_terms:
            for i, (term, freq) in enumerate(rare_terms[:10], 1):
                print(f"  {i:2d}. {term}")
            if len(rare_terms) > 10:
                print(f"  ... et {len(rare_terms) - 10} autres termes uniques")
        else:
            print("  Aucun terme unique")
        
        if term_freqs:
            avg_term_length = sum(len(term) for term, _ in term_freqs) / len(term_freqs)
            print(f"\nLongueur moyenne des termes: {avg_term_length:.1f} caractères")