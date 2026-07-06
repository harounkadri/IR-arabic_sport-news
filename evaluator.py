import os
import argparse
from collections import defaultdict

def load_qrels(qrels_file):
    """Loads relevance judgments from a TREC format file.
    Format: query_id iter doc_id relevance
    Returns: dict[query_id][doc_id] = relevance_score (int)
    """
    qrels = defaultdict(dict)
    try:
        if not os.path.exists(qrels_file):
            return {}
            
        with open(qrels_file, 'r', encoding='utf-8') as f:
            for line in f:
                parts = line.strip().split()
                if len(parts) >= 4:
                    qid, _, doc_id, rel = parts[:4]
                    qrels[qid][doc_id] = int(rel)
        return qrels
    except Exception as e:
        print(f"Erreur chargement qrels: {e}")
        return {}

def load_results(results_file):
    """Loads system results.
    Format Boolean: query_id,doc_id
    Format Ranked: query_id,doc_id,score
    """
    results = defaultdict(list)
    try:
        if not os.path.exists(results_file):
            return {}
            
        with open(results_file, 'r', encoding='utf-8') as f:
            for line in f:
                parts = line.strip().split(',')
                if len(parts) >= 2:
                    qid = parts[0].strip()
                    doc_id = parts[1].strip()
                    score = float(parts[2].strip()) if len(parts) > 2 else 1.0
                    results[qid].append((doc_id, score))
                    
        for qid in results:
            results[qid].sort(key=lambda x: x[1], reverse=True)
            
        return results
    except Exception as e:
        print(f"Erreur chargement résultats: {e}")
        return {}

def evaluate(qrels, results, k=10):
    metrics = {
        'MAP': 0.0,
        'MRR': 0.0,
        f'P@{k}': 0.0,
        f'R@{k}': 0.0
    }
    
    if not qrels or not results:
        return metrics
        
    num_queries = len(qrels)
    
    total_ap = 0.0
    total_rr = 0.0
    total_p_at_k = 0.0
    total_r_at_k = 0.0
    
    for qid, relevant_docs in qrels.items():
        rel_set = set(doc_id for doc_id, rel in relevant_docs.items() if rel > 0)
        num_rel = len(rel_set)
        
        if num_rel == 0:
            num_queries -= 1
            continue
            
        retrieved = results.get(qid, [])
        retrieved_docs = [doc_id for doc_id, _ in retrieved]
        
        # RR
        rr = 0.0
        for i, doc_id in enumerate(retrieved_docs):
            if doc_id in rel_set:
                rr = 1.0 / (i + 1)
                break
        total_rr += rr
        
        # AP
        ap = 0.0
        hits = 0
        for i, doc_id in enumerate(retrieved_docs):
            if doc_id in rel_set:
                hits += 1
                ap += hits / (i + 1)
        if num_rel > 0:
            ap /= num_rel
        total_ap += ap
        
        # P@K and R@K
        retrieved_k = retrieved_docs[:k]
        hits_k = sum(1 for doc_id in retrieved_k if doc_id in rel_set)
        
        total_p_at_k += hits_k / k
        total_r_at_k += hits_k / num_rel if num_rel > 0 else 0
        
    if num_queries > 0:
        metrics['MAP'] = total_ap / num_queries
        metrics['MRR'] = total_rr / num_queries
        metrics[f'P@{k}'] = total_p_at_k / num_queries
        metrics[f'R@{k}'] = total_r_at_k / num_queries
        
    return metrics

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Évaluateur de système IR (Précision, Rappel, MAP, MRR)")
    parser.add_argument('--qrels', type=str, default='data/qrels.txt', help='Fichier de pertinence (TREC format: qid 0 docid rel)')
    parser.add_argument('--results', type=str, default='outputs/results.ranked.txt', help='Fichier de résultats du système (CSV)')
    parser.add_argument('--k', type=int, default=10, help='Seuil k pour P@k et R@k')
    
    args = parser.parse_args()
    
    print(f"Évaluation des résultats : {args.results}")
    print(f"Fichier de référence (Qrels) : {args.qrels}")
    
    qrels = load_qrels(args.qrels)
    results = load_results(args.results)
    
    if not qrels:
        print("\n⚠️ Le fichier qrels n'existe pas ou est vide.")
        print("👉 Créez un fichier 'data/qrels.txt' au format 'query_id 0 doc_id relevance' pour pouvoir évaluer votre système.")
    elif not results:
        print("\n⚠️ Le fichier de résultats n'existe pas ou est vide. Exécutez d'abord une recherche.")
    else:
        metrics = evaluate(qrels, results, args.k)
        print("\n=== RÉSULTATS DE L'ÉVALUATION ===")
        print(f"Requêtes évaluées : {len([q for q in qrels if any(r > 0 for r in qrels[q].values())])}")
        print(f"MAP   : {metrics['MAP']:.4f}")
        print(f"MRR   : {metrics['MRR']:.4f}")
        print(f"P@{args.k}  : {metrics[f'P@{args.k}']:.4f}")
        print(f"R@{args.k}  : {metrics[f'R@{args.k}']:.4f}")
        print("=================================")
