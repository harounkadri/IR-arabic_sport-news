import re
import os
from nltk.stem.isri import ISRIStemmer

class ArabicPreprocessor:
    def __init__(self, stopwords_file, protected_words_file=None):
        self.stopwords = self._load_stopwords(stopwords_file)
        self.protected_words = self._load_protected_words(protected_words_file) if protected_words_file else set()
        self.stemmer = ISRIStemmer()
        
        print(f"✓ Préprocesseur arabe initialisé")
        print(f"  - Stemmer: ISRIStemmer")
        print(f"  - Stopwords: {len(self.stopwords)} mots")
        print(f"  - Mots protégés: {len(self.protected_words)} mots")
    
    def _load_stopwords(self, stopwords_file):
        stopwords_set = set()
        
        try:
            if not os.path.exists(stopwords_file):
                raise FileNotFoundError(f"Fichier stopwords requis: {stopwords_file}")
            
            with open(stopwords_file, 'r', encoding='utf-8') as f:
                for line in f:
                    word = line.strip()
                    if word and not word.startswith('#'):
                        normalized_word = self._remove_al_prefix(word)
                        stopwords_set.add(normalized_word)
            
            print(f"  {len(stopwords_set)} stopwords chargés")
            return stopwords_set
            
        except Exception as e:
            print(f"✗ Erreur chargement stopwords: {e}")
            raise
    
    def _load_protected_words(self, protected_words_file):
        protected_set = set()
        
        try:
            if not os.path.exists(protected_words_file):
                print(f"⚠️ Fichier mots protégés non trouvé: {protected_words_file}")
                return protected_set
            
            with open(protected_words_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        clean_word = self._remove_al_prefix(line)
                        clean_word = self.normalize_arabic(clean_word)
                        if clean_word:
                            protected_set.add(clean_word)
            
            print(f"  {len(protected_set)} mots protégés chargés")
            
            if protected_set:
                sample = list(protected_set)[:5]
                print(f"  Exemples: {sample}")
            
            return protected_set
            
        except Exception as e:
            print(f"✗ Erreur chargement mots protégés: {e}")
            return set()
    
    def _clean_term(self, term):
        if not term:
            return term
        
        term = term.strip()
        term = self.normalize_arabic(term)
        
        return term
    
    def _remove_al_prefix(self, word):
        if not word or len(word) < 2:
            return word
        
        word_str = str(word)
        
        prefixes = ['ال', 'إل', 'أل', 'لل']
        
        for prefix in prefixes:
            if word_str.startswith(prefix) and len(word_str) > len(prefix):
                return word_str[len(prefix):]
        
        if word_str.startswith('ل') and len(word_str) > 1 and word_str[1] == 'ا':
            return word_str[2:] if len(word_str) > 2 else word_str
        
        return word_str
    
    def normalize_arabic(self, text):
        if not text or not isinstance(text, str):
            return ""
        
        text = text.strip()
        
        text = text.replace('إ', 'ا').replace('أ', 'ا').replace('آ', 'ا')
        text = text.replace('ى', 'ي')
        
        tashkeel = re.compile(r'[\u064B-\u065F\u0670]')
        text = tashkeel.sub('', text)
        
        text = text.replace('ـ', '')
        
        text = re.sub(r'[0-9]', '', text)
        
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def tokenize(self, text):
        normalized = self.normalize_arabic(text)
        
        arabic_punctuation = r'[\u060C\u061B\u061F\u061E\u0640\u0021-\u002F\u003A-\u0040\u005B-\u0060\u007B-\u007E\u066A\u066B\u066C]'
        cleaned_text = re.sub(arabic_punctuation, ' ', normalized)
        
        cleaned_text = re.sub(r'\s+', ' ', cleaned_text).strip()
        
        tokens = re.findall(r'[\u0600-\u06FF]+', cleaned_text)
        
        cleaned_tokens = []
        for token in tokens:
            without_al = self._remove_al_prefix(token)
            if without_al:
                cleaned_tokens.append(without_al)
        
        return cleaned_tokens
    
    def remove_stopwords(self, tokens):
        return [token for token in tokens if token not in self.stopwords]
    
    def is_protected(self, word):
        normalized_word = self.normalize_arabic(self._remove_al_prefix(word))
        return normalized_word in self.protected_words
    
    def stem_with_protection(self, tokens):
        stemmed_tokens = []
        
        for token in tokens:
            if not token or token in self.stopwords:
                continue
            
            if self.is_protected(token):
                stemmed_tokens.append(token)
                continue
            
            try:
                stemmed = self.stemmer.stem(token)
                if stemmed and len(stemmed) >= 2:
                    stemmed_tokens.append(stemmed)
                else:
                    stemmed_tokens.append(token)
                    
            except Exception:
                stemmed_tokens.append(token)
        
        return stemmed_tokens
    
    def preprocess_text(self, text, stem=True, protect_words=True):
        tokens = self.tokenize(text)
        
        if not tokens:
            return []
        
        tokens = self.remove_stopwords(tokens)
        
        if stem and tokens:
            if protect_words and self.protected_words:
                tokens = self.stem_with_protection(tokens)
            else:
                stemmed_tokens = []
                for token in tokens:
                    try:
                        stemmed = self.stemmer.stem(token)
                        if stemmed:
                            stemmed_tokens.append(stemmed)
                        else:
                            stemmed_tokens.append(token)
                    except:
                        stemmed_tokens.append(token)
                tokens = stemmed_tokens
        
        return tokens
    
    def preprocess_for_indexing(self, text):
        return self.preprocess_text(text, stem=True, protect_words=True)
    
    def preprocess_for_query(self, text):
        return self.preprocess_text(text, stem=True, protect_words=True)