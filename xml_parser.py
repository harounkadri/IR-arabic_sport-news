import xml.etree.ElementTree as ET
import re

class XMLParser:
    def __init__(self, xml_file):
        self.xml_file = xml_file
    
    def parse(self):
        documents = []
        try:
            context = ET.iterparse(self.xml_file, events=('end',))
            for event, elem in context:
                if elem.tag == 'Article':
                    doc = self._extract_article(elem)
                    if doc and doc['id'] and doc['full_text'].strip():
                        documents.append(doc)
                    elem.clear()
            
            print(f"✓ {len(documents)} documents parsés depuis {self.xml_file} (iterparse)")
            return documents
            
        except ET.ParseError:
            print("⚠️ Fichier XML malformé, utilisation du parseur de secours (en mémoire)...")
            return self._parse_fallback()
        except Exception as e:
            print(f"✗ Erreur parsing XML: {e}")
            return []

    def _parse_fallback(self):
        documents = []
        try:
            with open(self.xml_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            content = self._clean_xml(content)
            root = ET.fromstring(content)
            
            for article in root.findall('.//Article'):
                doc = self._extract_article(article)
                if doc and doc['id'] and doc['full_text'].strip():
                    documents.append(doc)
            
            print(f"✓ {len(documents)} documents parsés depuis {self.xml_file} (fallback)")
            return documents
            
        except Exception as e:
            print(f"✗ Erreur parsing XML fallback: {e}")
            return []
    
    def _clean_xml(self, content):
        content = re.sub(r'<!--.*?-->', '', content, flags=re.DOTALL)
        
        if not content.strip().startswith('<?xml'):
            content = '<?xml version="1.0" encoding="UTF-8"?>\n<root>\n' + content + '\n</root>'
        
        return content
    
    def _extract_article(self, article):
        try:
            id_elem = article.find('ID')
            doc_id = id_elem.text.strip() if id_elem is not None and id_elem.text else None
            
            if not doc_id:
                return None
            
            headline_elem = article.find('HEADLINE')
            headline = headline_elem.text.strip() if headline_elem is not None and headline_elem.text else ""
            
            text_elem = article.find('TEXT')
            text = text_elem.text.strip() if text_elem is not None and text_elem.text else ""
            
            full_text = headline + " " + text
            
            if not full_text.strip():
                return None
            
            return {
                'id': doc_id,
                'headline': headline,
                'text': text,
                'full_text': full_text
            }
            
        except Exception as e:
            print(f"✗ Erreur extraction article: {e}")
            return None