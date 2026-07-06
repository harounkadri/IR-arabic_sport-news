import math
from collections import defaultdict

class RankedProcessor:
    def __init__(self, preprocessor, position_indexer):
        self.preprocessor = preprocessor
        self.position_indexer = position_indexer
        self.documents = position_indexer.documents
        self.total_docs = position_indexer.total_docs
        
        self._prepare_all_data()
    
    def _prepare_all_data(self):
        self.tf_matrix = defaultdict(lambda: defaultdict(int))
        
        for term, doc_dict in self.position_indexer.index.items():
            for doc_id, positions in doc_dict.items():
                self.tf_matrix[doc_id][term] = len(positions)
        
        self.df_dict = defaultdict(int)
        for term, doc_dict in self.position_indexer.index.items():
            self.df_dict[term] = len(doc_dict)
        
        self.doc_lengths = {}
        for doc_id in self.documents:
            total = sum(self.tf_matrix[doc_id].values())
            self.doc_lengths[doc_id] = total
        
        self.tfidf_matrix = defaultdict(lambda: defaultdict(float))
        
        for doc_id in self.documents:
            for term, tf in self.tf_matrix[doc_id].items():
                df = self.df_dict[term]
                if df > 0 and self.total_docs > 0:
                    tf_weight = 1 + math.log10(tf) if tf > 0 else 0
                    idf = math.log10(self.total_docs / df)
                    self.tfidf_matrix[doc_id][term] = tf_weight * idf
        
        self.doc_norms = {}
        for doc_id in self.documents:
            sum_squares = sum(w * w for w in self.tfidf_matrix[doc_id].values())
            self.doc_norms[doc_id] = math.sqrt(sum_squares) if sum_squares > 0 else 1.0
    
    def _process_query(self, query_text):
        query_terms = self.preprocessor.preprocess_text(
            query_text, 
            stem=True, 
            protect_words=True
        )
        
        if not query_terms:
            return {}, 0.0
        
        query_tf = defaultdict(int)
        for term in query_terms:
            query_tf[term] += 1
        
        query_vector = {}
        
        for term, tf in query_tf.items():
            df = self.df_dict.get(term, 0)
            
            if df > 0 and self.total_docs > 0:
                tf_weight = 1 + math.log10(tf) if tf > 0 else 0
                idf = math.log10(self.total_docs / df)
                query_vector[term] = tf_weight * idf
        
        norm_sq = sum(w * w for w in query_vector.values())
        norm = math.sqrt(norm_sq) if norm_sq > 0 else 1.0
        
        return query_vector, norm
    
    def search_with_cosine_similarity(self, query, top_k=50):
        query_vector, query_norm = self._process_query(query)
        
        if not query_vector or query_norm == 0:
            return []
        
        scores = []
        
        for doc_id in self.documents:
            dot_product = 0.0
            doc_vector = self.tfidf_matrix[doc_id]
            
            for term, q_weight in query_vector.items():
                if term in doc_vector:
                    dot_product += q_weight * doc_vector[term]
            
            doc_norm = self.doc_norms[doc_id]
            
            if doc_norm > 0 and query_norm > 0:
                cosine = dot_product / (query_norm * doc_norm)
                
                if cosine > 0:
                    scores.append((doc_id, min(1.0, max(0.0, cosine))))
        
        scores.sort(key=lambda x: x[1], reverse=True)
        
        if scores and scores[0][1] > 0:
            max_score = scores[0][1]
            if max_score > 0:
                normalized = [(doc_id, score/max_score) for doc_id, score in scores]
                return normalized[:top_k]
        
        return scores[:top_k]
    
    def search_with_bm25(self, query, top_k=50, k1=1.2, b=0.75):
        query_terms = self.preprocessor.preprocess_text(
            query, 
            stem=True, 
            protect_words=True
        )
        
        if not query_terms:
            return []
        
        total_length = sum(self.doc_lengths.values())
        avgdl = total_length / self.total_docs if self.total_docs > 0 else 0
        
        scores = defaultdict(float)
        
        for doc_id in self.documents:
            doc_score = 0.0
            doc_length = self.doc_lengths[doc_id]
            
            for term in query_terms:
                tf = self.tf_matrix[doc_id].get(term, 0)
                
                if tf == 0:
                    continue
                
                df = self.df_dict.get(term, 0)
                
                if df == 0:
                    continue
                
                idf = math.log((self.total_docs - df + 0.5) / (df + 0.5) + 1)
                
                tf_component = (tf * (k1 + 1)) / (tf + k1 * (1 - b + b * (doc_length / avgdl)))
                
                doc_score += idf * tf_component
            
            if doc_score > 0:
                scores[doc_id] = doc_score
        
        sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        
        return sorted_scores[:top_k]
