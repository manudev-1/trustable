import re
from typing import List, Dict, Tuple
from collections import Counter
import math

from model.Review import Review
from model.DetectedPattern import DetectedTemplate


class TemplateDetector:
    """
    FASE 2.3: Rilevazione di template pattern con slot variabili.
    
    Identifica pattern come: "[PAROLA] [WILDCARD] [PAROLA] [PAROLA]"
    e calcola l'entropia dei filler per ogni slot.
    
    Entropia bassa (<2.0) indica pattern rigido e potenzialmente automatizzato.
    """
    
    TEMPLATE_ENTROPY_THRESHOLD = 2.0
    MIN_SLOT_OCCURRENCES = 3
    
    def __init__(self):
        pass
    
    def _extract_sentences(self, text: str) -> List[str]:
        """
        Estrae frasi da un testo.
        
        Args:
            text: Testo sorgente
        
        Returns:
            Lista di frasi
        """
        sentences = re.split(r'[.!?;]', text)
        return [s.strip() for s in sentences if len(s.strip()) > 10]
    
    def _tokenize_for_templates(self, text: str) -> List[str]:
        """
        Tokenizza un testo preservando più informazioni per i template.
        """
        text = text.lower()

        text = re.sub(r'[^\w\s\'àèéìòù]', ' ', text)
        tokens = text.split()
        return [t for t in tokens if len(t) > 1]
    
    def analyze_window(
        self,
        reviews: List[Review],
        window_review_ids: List[str]
    ) -> List[DetectedTemplate]:
        """
        Analizza una finestra per pattern template.
        
        Args:
            reviews: Lista di tutte le review
            window_review_ids: ID delle review nella finestra
        
        Returns:
            Lista di DetectedTemplate trovati
        """
        window_reviews = [r for r in reviews if r.review_id in window_review_ids]
        
        if not window_reviews:
            return []

        all_sentences = []
        for review in window_reviews:
            if review.text:
                sentences = self._extract_sentences(review.text)
                all_sentences.extend(sentences)
        
        if not all_sentences:
            return []
        
        templates = self._discover_templates(all_sentences)
        
        return templates
    
    def _discover_templates(self, sentences: List[str]) -> List[DetectedTemplate]:
        """
        Scopre template pattern da una lista di frasi.
        
        Algoritmo:
        1. Per ogni frase, genera una "signature" mantenendo parole anchor
        2. Raggruppa frasi con signature simile
        3. Calcola entropia dei slot variabili
        4. Segnala template con bassa entropia
        
        Args:
            sentences: Lista di frasi
        
        Returns:
            Lista di template trovati
        """
        if not sentences or len(sentences) < self.MIN_SLOT_OCCURRENCES:
            return []
        
        tokenized = [self._tokenize_for_templates(s) for s in sentences]

        tokenized = [t for t in tokenized if 4 <= len(t) <= 20]
        
        if not tokenized:
            return []
        
        templates_found = []
        processed_signatures = set()
        
        for i, tokens in enumerate(tokenized):
            if len(tokens) < 4:
                continue

            signature = tuple([
                (j, tokens[j] if j < len(tokens) else '*')
                for j in range(len(tokens))
                if j % 2 == 0 or j == len(tokens) - 1
            ])
            
            if signature in processed_signatures:
                continue
            
            similar_sentences = self._find_similar_sentences(
                tokens, tokenized
            )
            
            if len(similar_sentences) >= self.MIN_SLOT_OCCURRENCES:
                template_str, slot_fillers, entropy = self._extract_template_info(
                    similar_sentences
                )
                
                if entropy < self.TEMPLATE_ENTROPY_THRESHOLD:
                    template = DetectedTemplate(
                        template=template_str,
                        slot_fillers=slot_fillers,
                        entropy=entropy,
                        occurrences=len(similar_sentences)
                    )
                    templates_found.append(template)
                    processed_signatures.add(signature)
        
        return self._deduplicate_templates(templates_found)
    
    def _find_similar_sentences(
        self,
        tokens: List[str],
        all_tokenized: List[List[str]]
    ) -> List[List[str]]:
        """
        Trova frasi simili a quella data.
        
        Criteri di somiglianza:
        - Stessa lunghezza
        - Stesse parole nelle posizioni pari
        """
        similar = [tokens]
        length = len(tokens)
        
        for other in all_tokenized:
            if len(other) == length:
                match_score = sum(
                    1 for j in range(0, length, 2)
                    if j < len(other) and tokens[j] == other[j]
                )
                
                if match_score >= max(2, length // 3):
                    similar.append(other)
        
        return similar
    
    def _extract_template_info(
        self,
        similar_sentences: List[List[str]]
    ) -> Tuple[str, Dict[str, List[str]], float]:
        """
        Estrae il template e calcola l'entropia.
        
        Returns:
            (template_string, slot_fillers_dict, entropy)
        """
        if not similar_sentences:
            return "", {}, 0
        
        length = len(similar_sentences[0])

        template_parts = []
        slot_fillers = {}
        entropies = []
        
        for pos in range(length):
            words_at_pos = [s[pos] for s in similar_sentences if pos < len(s)]
            word_counts = Counter(words_at_pos)
            
            if len(word_counts) == 1:
                word = list(word_counts.keys())[0]
                template_parts.append(word)
            else:
                slot_name = f"slot_{pos}"
                template_parts.append(f"[{slot_name}]")
                slot_fillers[slot_name] = list(word_counts.keys())
                
                total = sum(word_counts.values())
                entropy = 0.0
                for count in word_counts.values():
                    p = count / total
                    entropy -= p * math.log2(p + 1e-9)

                max_entropy = math.log2(len(word_counts))
                if max_entropy > 0:
                    entropy = entropy / max_entropy * 4
                
                entropies.append(entropy)
        
        avg_entropy = sum(entropies) / len(entropies) if entropies else 0
        
        template_str = " ".join(template_parts)
        
        return template_str, slot_fillers, avg_entropy
    
    @staticmethod
    def _deduplicate_templates(templates: List[DetectedTemplate]) -> List[DetectedTemplate]:
        """
        Rimuove template duplicati o molto simili.
        """
        if not templates:
            return []
        
        sorted_templates = sorted(templates, key=lambda t: t.entropy)
        
        kept = []
        
        for template in sorted_templates:
            normalized = template.template.lower()
            
            is_duplicate = False
            for kept_template in kept:
                kept_norm = kept_template.template.lower()
                if TemplateDetector._template_similarity(normalized, kept_norm) > 0.8:
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                kept.append(template)
        
        return kept
    
    @staticmethod
    def _template_similarity(t1: str, t2: str) -> float:
        """Calcola somiglianza tra due template string (0-1)."""
        t1_parts = set(t1.split())
        t2_parts = set(t2.split())
        
        if not t1_parts and not t2_parts:
            return 1.0
        
        intersection = len(t1_parts & t2_parts)
        union = len(t1_parts | t2_parts)
        
        if union == 0:
            return 0
        
        return intersection / union
