import time
import os
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
from config import *
from xml_parser import XMLParser
from preprocessor import ArabicPreprocessor
from indexer import PositionalIndexer
from boolean_searcher import BooleanSearcher
from ranked_processor import RankedProcessor
from utils import read_queries_from_file, save_boolean_results, save_ranked_results

class SearchSystemGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("🔍 Système de Recherche Arabe (ISRIStemmer)")
        self.root.geometry("1100x750")
        
        self.documents = []
        self.indexer = None
        self.preprocessor = None
        self.boolean_searcher = None
        self.ranked_processor = None
        
        self.search_type = tk.StringVar(value="boolean")
        self.ranking_algorithm = tk.StringVar(value="cosine")
        
        self.protect_words = tk.BooleanVar(value=True)
        
        self._create_interface()
        
        self.root.after(100, self._initialize_system)
    
    def _create_interface(self):
        main_frame = tk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        title_frame = tk.Frame(main_frame)
        title_frame.pack(fill=tk.X, pady=(0, 20))
        
        tk.Label(title_frame, text="🔍 SYSTÈME DE RECHERCHE ARABE", 
                font=("Arial", 20, "bold"), fg="#2c3e50").pack()
        
        tk.Label(title_frame, text="Recherche booléenne et ranking avec ISRIStemmer - Termes arabes seulement", 
                font=("Arial", 11), fg="#7f8c8d").pack()
        
        control_frame = tk.LabelFrame(main_frame, text="Paramètres de recherche", 
                                     font=("Arial", 11, "bold"), padx=15, pady=15)
        control_frame.pack(fill=tk.X, pady=(0, 15))
        
        row0 = tk.Frame(control_frame)
        row0.pack(fill=tk.X, pady=(0, 10))
        
        tk.Checkbutton(row0, text="Protéger les noms propres et termes spécifiques",
                      variable=self.protect_words,
                      font=("Arial", 10)).pack(side=tk.LEFT)
        
        tk.Label(row0, text="(Empêche le stemming des mots dans protected_words.txt)",
                font=("Arial", 9), fg="gray").pack(side=tk.LEFT, padx=(10, 0))
        
        row1 = tk.Frame(control_frame)
        row1.pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(row1, text="Type:", font=("Arial", 10)).pack(side=tk.LEFT, padx=(0, 10))
        
        tk.Radiobutton(row1, text="Booléenne (exact)", variable=self.search_type,
                      value="boolean", font=("Arial", 10),
                      command=self._on_search_type_changed).pack(side=tk.LEFT, padx=5)
        
        tk.Radiobutton(row1, text="Ranking (pertinence)", variable=self.search_type,
                      value="ranked", font=("Arial", 10),
                      command=self._on_search_type_changed).pack(side=tk.LEFT, padx=5)
        
        self.algorithm_frame = tk.Frame(control_frame)
        self.algorithm_frame.pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(self.algorithm_frame, text="Algorithme:", font=("Arial", 10)).pack(side=tk.LEFT, padx=(0, 10))
        
        tk.Radiobutton(self.algorithm_frame, text="Cosine Similarity", 
                      variable=self.ranking_algorithm, value="cosine", 
                      font=("Arial", 10)).pack(side=tk.LEFT, padx=5)
        
        tk.Radiobutton(self.algorithm_frame, text="BM25 (meilleur)", 
                      variable=self.ranking_algorithm, value="bm25", 
                      font=("Arial", 10)).pack(side=tk.LEFT, padx=5)
        
        row3 = tk.Frame(control_frame)
        row3.pack(fill=tk.X)
        
        tk.Label(row3, text="Requête:", font=("Arial", 10)).pack(side=tk.LEFT, padx=(0, 10))
        
        self.query_var = tk.StringVar()
        self.query_entry = tk.Entry(row3, textvariable=self.query_var, 
                                   font=("Arial", 12), width=50)
        self.query_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        self.query_entry.bind('<Return>', lambda e: self._execute_search())
        
        search_btn = tk.Button(row3, text="🔍 Rechercher", font=("Arial", 11, "bold"),
                              bg="#3498db", fg="white", padx=25,
                              command=self._execute_search)
        search_btn.pack(side=tk.LEFT)
        
        results_frame = tk.LabelFrame(main_frame, text="Résultats de recherche", 
                                     font=("Arial", 11, "bold"), padx=15, pady=15)
        results_frame.pack(fill=tk.BOTH, expand=True)
        
        self._create_results_table(results_frame)
        
        self.status_bar = tk.Label(self.root, text="Initialisation...", 
                                  bd=1, relief=tk.SUNKEN, anchor=tk.W,
                                  font=("Arial", 10), bg="#f8f9fa")
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        log_frame = tk.LabelFrame(self.root, text="Logs et vérifications", 
                                 font=("Arial", 10, "bold"), padx=10, pady=10)
        log_frame.pack(fill=tk.X, padx=20, pady=(0, 10))
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=6, 
                                                 font=("Courier", 9))
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        self.query_entry.config(state='disabled')
        self._hide_algorithm_frame()
    
    def _on_search_type_changed(self):
        if self.search_type.get() == "ranked":
            self._show_algorithm_frame()
        else:
            self._hide_algorithm_frame()
        
        self._recreate_results_table()
    
    def _hide_algorithm_frame(self):
        self.algorithm_frame.pack_forget()
    
    def _show_algorithm_frame(self):
        self.algorithm_frame.pack(fill=tk.X, pady=(0, 10))
    
    def _create_results_table(self, parent):
        scroll_frame = tk.Frame(parent)
        scroll_frame.pack(fill=tk.BOTH, expand=True)
        
        self.results_tree = ttk.Treeview(scroll_frame)
        
        vsb = ttk.Scrollbar(scroll_frame, orient="vertical", command=self.results_tree.yview)
        hsb = ttk.Scrollbar(scroll_frame, orient="horizontal", command=self.results_tree.xview)
        
        self.results_tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        self.results_tree.grid(column=0, row=0, sticky='nsew')
        vsb.grid(column=1, row=0, sticky='ns')
        hsb.grid(column=0, row=1, sticky='ew')
        
        scroll_frame.grid_columnconfigure(0, weight=1)
        scroll_frame.grid_rowconfigure(0, weight=1)
        
        self._setup_table_columns()
    
    def _setup_table_columns(self):
        if self.search_type.get() == "ranked":
            columns = ['Rang', 'Document', 'Score', 'Confiance', 'Détails']
            self.results_tree['columns'] = columns
            
            for col in columns:
                self.results_tree.heading(col, text=col)
                if col == 'Rang':
                    self.results_tree.column(col, width=50, anchor='center')
                elif col == 'Document':
                    self.results_tree.column(col, width=100, anchor='center')
                elif col == 'Score':
                    self.results_tree.column(col, width=80, anchor='center')
                elif col == 'Confiance':
                    self.results_tree.column(col, width=100, anchor='center')
                else:
                    self.results_tree.column(col, width=200)
        else:
            columns = ['Document', 'Termes trouvés', 'Occurrences totales']
            self.results_tree['columns'] = columns
            
            for col in columns:
                self.results_tree.heading(col, text=col)
                if col == 'Document':
                    self.results_tree.column(col, width=100, anchor='center')
                elif col == 'Termes trouvés':
                    self.results_tree.column(col, width=150)
                else:
                    self.results_tree.column(col, width=100, anchor='center')
    
    def _recreate_results_table(self):
        for item in self.results_tree.get_children():
            self.results_tree.delete(item)
        
        for col in self.results_tree['columns']:
            self.results_tree.heading(col, text='')
        
        self._setup_table_columns()
    
    def _execute_search(self):
        query = self.query_var.get().strip()
        
        if not query:
            messagebox.showwarning("Requête vide", "Veuillez entrer une requête.")
            return
        
        for item in self.results_tree.get_children():
            self.results_tree.delete(item)
        
        if not self.boolean_searcher or not self.ranked_processor:
            messagebox.showerror("Système non initialisé", 
                               "Le système n'est pas encore prêt. Patientez...")
            return
        
        try:
            start_time = time.time()
            
            if self.search_type.get() == "boolean":
                results = self._execute_boolean_search(query)
            else:
                results = self._execute_ranked_search(query)
            
            elapsed = time.time() - start_time
            
            self.status_bar.config(text=f"Recherche: {len(results)} résultats en {elapsed:.3f}s")
            
        except Exception as e:
            self._log(f"❌ ERREUR: {str(e)}")
            messagebox.showerror("Erreur", f"Erreur de recherche:\n{str(e)}")
    
    def _execute_boolean_search(self, query):
        results = self.boolean_searcher.search(query)
        
        if not results:
            self.results_tree.insert('', 'end', values=("Aucun", "Aucun", "0"))
            self._log(f"Booléen: '{query}' → 0 documents")
            return []
        
        original_terms = self.preprocessor.preprocess_text(
            query, 
            stem=True, 
            protect_words=self.protect_words.get()
        )
        
        for doc_id in results:
            found_count = 0
            total_occurrences = 0
            
            for term in original_terms:
                positions = self.indexer.get_positions(term, doc_id)
                if positions:
                    found_count += 1
                    total_occurrences += len(positions)
            
            terms_str = f"{found_count} terme(s) trouvé(s)"
            if found_count > 0 and len(original_terms) > 0:
                terms_str = ", ".join(original_terms[:3])
                if len(original_terms) > 3:
                    terms_str += f"... (+{len(original_terms)-3})"
            
            self.results_tree.insert('', 'end', 
                                   values=(doc_id, terms_str, total_occurrences))
        
        self._log(f"Booléen: '{query}' → {len(results)} documents")
        self._log(f"  Protection activée: {self.protect_words.get()}")
        self._log(f"  Termes recherchés: {original_terms}")
        
        return results
    
    def _execute_ranked_search(self, query):
        if self.ranking_algorithm.get() == "cosine":
            results = self.ranked_processor.search_with_cosine_similarity(query, TOP_K_RESULTS)
            algo_name = "Cosine"
        else:
            results = self.ranked_processor.search_with_bm25(query, TOP_K_RESULTS)
            algo_name = "BM25"
        
        if not results:
            self.results_tree.insert('', 'end', 
                                   values=(1, "Aucun", "0.0000", "-", "Aucun résultat"))
            self._log(f"{algo_name}: '{query}' → 0 documents")
            return []
        
        for i, (doc_id, score) in enumerate(results[:15], 1):
            if score > 0.8:
                confidence = "🟢 Excellente"
                color = "green"
            elif score > 0.5:
                confidence = "🟡 Bonne"
                color = "orange"
            elif score > 0.2:
                confidence = "🟠 Faible"
                color = "#FFA500"
            else:
                confidence = "🔴 Très faible"
                color = "red"
            
            details = f"Score: {score:.4f}"
            
            self.results_tree.insert('', 'end', 
                                   values=(i, doc_id, f"{score:.4f}", confidence, details))
            
            self.results_tree.tag_configure(f"score_{i}", background=color)
            self.results_tree.item(self.results_tree.get_children()[-1], 
                                 tags=(f"score_{i}",))
        
        if len(results) > 15:
            self.results_tree.insert('', 'end', 
                                   values=("...", f"+{len(results)-15}", "", "", ""))
        
        self._log(f"{algo_name}: '{query}' → {len(results)} documents")
        self._log(f"  Protection activée: {self.protect_words.get()}")
        self._log(f"  Meilleur score: {results[0][1]:.4f} (doc {results[0][0]})")
        self._log(f"  Score moyenne: {sum(s for _, s in results)/len(results):.4f}")
        
        return results
    
    def _log(self, message):
        self.root.after(0, self._log_ui, message)
        
    def _log_ui(self, message):
        timestamp = time.strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
        self.root.update_idletasks()
    
    def _initialize_system(self):
        import threading
        threading.Thread(target=self._initialize_worker, daemon=True).start()
        
    def _initialize_worker(self):
        self.root.after(0, lambda: self.status_bar.config(text="Initialisation du système..."))
        self._log("=" * 70)
        self._log("INITIALISATION DU SYSTÈME DE RECHERCHE")
        self._log("=" * 70)
        
        try:
            self._log("📁 Vérification des fichiers...")
            if not os.path.exists(DATA_FILE):
                self._log(f"❌ FICHIER MANQUANT: {DATA_FILE}")
                self.root.after(0, lambda: messagebox.showerror("Fichier manquant", 
                                   f"Le fichier {DATA_FILE} est requis."))
                return
            
            self._log("🔧 Initialisation du préprocesseur...")
            
            protected_file = PROTECTED_WORDS_FILE if os.path.exists(PROTECTED_WORDS_FILE) else None
            
            self.preprocessor = ArabicPreprocessor(
                STOPWORDS_FILE, 
                protected_file
            )
            
            if protected_file:
                self._log(f"✓ Préprocesseur avec protection des mots initialisé")
                self._log(f"  Mots protégés chargés: {len(self.preprocessor.protected_words)}")
            else:
                self._log("⚠️ Préprocesseur sans protection (fichier protected_words.txt manquant)")
            
            self._log("📄 Chargement des documents...")
            parser = XMLParser(DATA_FILE)
            self.documents = parser.parse()
            
            if not self.documents:
                self._log("❌ Aucun document trouvé!")
                return
            
            self._log(f"✓ {len(self.documents)} documents chargés")
            
            self._log("🔨 Construction de l'index...")
            self.indexer = PositionalIndexer(self.preprocessor)
            self.indexer.build_index(self.documents)
            
            self._log("🧹 Filtrage des termes arabes seulement...")
            removed_terms = self.indexer.filter_arabic_only()
            self._log(f"  Termes non-arabes supprimés: {len(removed_terms)}")
            
            self._log("🚀 Initialisation des moteurs...")
            self.boolean_searcher = BooleanSearcher(self.indexer, self.preprocessor)
            self.ranked_processor = RankedProcessor(self.preprocessor, self.indexer)
            
            self._log("💾 Sauvegarde des index...")
            self.indexer.save_index(INDEX_FILE)
            
            self._log("📝 Traitement des requêtes prédéfinies...")
            self._process_predefined_queries()
            
            self._log("=" * 70)
            self._log("✅ SYSTÈME PRÊT POUR LA RECHERCHE")
            self._log(f"   Documents: {len(self.documents)}")
            self._log(f"   Termes uniques: {len(self.indexer.index)}")
            self._log(f"   Mots protégés: {len(self.preprocessor.protected_words)}")
            self._log(f"   Protection activée dans GUI: {self.protect_words.get()}")
            self._log("=" * 70)
            
            self.root.after(0, self._on_init_success)
            
        except Exception as e:
            self._log(f"❌ ERREUR D'INITIALISATION: {str(e)}")
            import traceback
            self._log(traceback.format_exc())
            self.root.after(0, lambda err=e: messagebox.showerror("Erreur", f"Erreur d'initialisation:\n{str(err)}"))
            
    def _on_init_success(self):
        self.query_entry.config(state='normal')
        self.status_bar.config(text=f"✅ Prêt! {len(self.documents)} documents indexés")
        protection_status = "activée" if self.preprocessor.protected_words and self.protect_words.get() else "désactivée"
        messagebox.showinfo("Système prêt", 
                          f"Système initialisé avec succès!\n\n"
                          f"• Documents: {len(self.documents)}\n"
                          f"• Termes uniques: {len(self.indexer.index)}\n"
                          f"• Mots protégés: {len(self.preprocessor.protected_words)}\n"
                          f"• Protection des mots: {protection_status}\n\n"
                          f"Vous pouvez maintenant effectuer des recherches.")
    
    def _process_predefined_queries(self):
        bool_queries = read_queries_from_file(QUERIES_BOOLEAN)
        if bool_queries:
            results = {}
            for qid, qtext in bool_queries.items():
                results[qid] = self.boolean_searcher.search(qtext)
                self._log(f"  Bool Q{qid}: {len(results[qid])} résultats")
            
            save_boolean_results(results, RESULTS_BOOLEAN_FILE)
        
        ranked_queries = read_queries_from_file(QUERIES_RANKED)
        if ranked_queries:
            results = {}
            for qid, qtext in ranked_queries.items():
                results[qid] = self.ranked_processor.search_with_cosine_similarity(qtext, 10)
                if results[qid]:
                    self._log(f"  Rank Q{qid}: meilleur score {results[qid][0][1]:.4f}")
            
            save_ranked_results(results, RESULTS_RANKED_FILE)
    
    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    try:
        import nltk
        nltk.data.find('tokenizers/punkt')
    except Exception:
        print("Installation de NLTK...")
        nltk.download('punkt', quiet=True)
    
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    app = SearchSystemGUI()
    app.run()