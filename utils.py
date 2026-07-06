import os

def read_queries_from_file(filename):
    queries = {}
    
    try:
        if not os.path.exists(filename):
            return {}
        
        with open(filename, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                parts = line.split(' ', 1)
                if len(parts) >= 2:
                    query_id = parts[0].strip()
                    query_text = parts[1].strip()
                    queries[query_id] = query_text
        
        return queries
        
    except Exception as e:
        print(f"Erreur de lecture des requêtes: {e}")
        return {}

def save_boolean_results(results, filename):
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            for query_id, doc_ids in sorted(results.items(), key=lambda x: int(x[0])):
                for doc_id in sorted(doc_ids, key=lambda x: int(x)):
                    f.write(f"{query_id},{doc_id}\n")
        return True
    except Exception as e:
        print(f"Erreur de sauvegarde booléenne: {e}")
        return False

def save_ranked_results(results, filename):
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            for query_id, doc_scores in sorted(results.items(), key=lambda x: int(x[0])):
                for doc_id, score in doc_scores:
                    f.write(f"{query_id},{doc_id},{score:.4f}\n")
        return True
    except Exception as e:
        print(f"Erreur de sauvegarde ranking: {e}")
        return False