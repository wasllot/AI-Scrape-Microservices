"""
Writing Analyzers - Quality analysis tools for scripts

Provides analysis for:
- Readability (Flesch-Kincaid, Flesch Reading Ease)
- SEO metrics (keyword density, structure)
- Duration estimation
- Structure analysis
"""
import re
from typing import Dict, List, Optional
from collections import Counter


class ReadabilityAnalyzer:
    """Analyze readability metrics of text"""
    
    @staticmethod
    def count_syllables(word: str) -> int:
        """Count syllables in a word"""
        word = word.lower().strip()
        if len(word) <= 3:
            return 1
        
        vowels = "aeiouáéíóúü"
        syllable_count = 0
        prev_was_vowel = False
        
        for char in word:
            is_vowel = char in vowels
            if is_vowel and not prev_was_vowel:
                syllable_count += 1
            prev_was_vowel = is_vowel
        
        if word.endswith('e'):
            syllable_count -= 1
        
        return max(1, syllable_count)
    
    @staticmethod
    def flesch_kincaid_grade(text: str) -> float:
        """Calculate Flesch-Kincaid Grade Level"""
        sentences = ReadabilityAnalyzer._get_sentences(text)
        words = ReadabilityAnalyzer._get_words(text)
        
        if not sentences or not words:
            return 0.0
        
        total_syllables = sum(ReadabilityAnalyzer.count_syllables(w) for w in words)
        
        avg_sentence_length = len(words) / len(sentences)
        avg_syllables_per_word = total_syllables / len(words)
        
        grade = (0.39 * avg_sentence_length) + (11.8 * avg_syllables_per_word) - 15.59
        return round(max(0, min(grade, 18)), 1)
    
    @staticmethod
    def flesch_reading_ease(text: str) -> float:
        """Calculate Flesch Reading Ease score (0-100)"""
        sentences = ReadabilityAnalyzer._get_sentences(text)
        words = ReadabilityAnalyzer._get_words(text)
        
        if not sentences or not words:
            return 0.0
        
        total_syllables = sum(ReadabilityAnalyzer.count_syllables(w) for w in words)
        
        avg_sentence_length = len(words) / len(sentences)
        avg_syllables_per_word = total_syllables / len(words)
        
        score = 206.835 - (1.015 * avg_sentence_length) - (84.6 * avg_syllables_per_word)
        return round(max(0, min(score, 100)), 1)
    
    @staticmethod
    def interpret_readability(score: float) -> str:
        """Interpret Flesch Reading Ease score"""
        if score >= 90:
            return "Muy fácil - Nivel escolar 5º"
        elif score >= 80:
            return "Fácil - Nivel escolar 6º"
        elif score >= 70:
            return "Algo fácil - Nivel escolar 7º"
        elif score >= 60:
            return "Estándar - Nivel escolar 8-9º"
        elif score >= 50:
            return "Algo difícil - Nivel escolar 10-12º"
        elif score >= 30:
            return "Difícil - Universidad"
        else:
            return "Muy difícil - Pósgrado"
    
    @staticmethod
    def _get_sentences(text: str) -> List[str]:
        """Split text into sentences"""
        sentences = re.split(r'[.!?]+', text)
        return [s.strip() for s in sentences if s.strip()]
    
    @staticmethod
    def _get_words(text: str) -> List[str]:
        """Extract words from text"""
        words = re.findall(r'\b[a-zA-Záéíóúüñ]+\b', text.lower())
        return words
    
    @staticmethod
    def analyze(text: str) -> Dict:
        """Full readability analysis"""
        words = ReadabilityAnalyzer._get_words(text)
        sentences = ReadabilityAnalyzer._get_sentences(text)
        
        fk_grade = ReadabilityAnalyzer.flesch_kincaid_grade(text)
        fre_score = ReadabilityAnalyzer.flesch_reading_ease(text)
        
        return {
            "word_count": len(words),
            "sentence_count": len(sentences),
            "avg_words_per_sentence": round(len(words) / len(sentences), 1) if sentences else 0,
            "avg_characters_per_word": round(sum(len(w) for w in words) / len(words), 1) if words else 0,
            "flesch_kincaid_grade": fk_grade,
            "flesch_reading_ease": fre_score,
            "interpretation": ReadabilityAnalyzer.interpret_readability(fre_score)
        }


class SEOAnalyzer:
    """Analyze SEO metrics of text"""
    
    def __init__(self, text: str, keywords: Optional[List[str]] = None):
        self.text = text
        self.keywords = keywords or []
        self.words = self._extract_words()
    
    def _extract_words(self) -> List[str]:
        """Extract all words from text"""
        return re.findall(r'\b[a-zA-Záéíóúüñ]+\b', self.text.lower())
    
    def keyword_density(self) -> Dict:
        """Calculate keyword density"""
        if not self.keywords or not self.words:
            return {}
        
        total_words = len(self.words)
        density = {}
        
        for keyword in self.keywords:
            keyword_lower = keyword.lower()
            count = self.words.count(keyword_lower)
            density[keyword] = {
                "count": count,
                "density": round((count / total_words) * 100, 2) if total_words > 0 else 0
            }
        
        return density
    
    def heading_structure(self) -> Dict:
        """Analyze heading structure"""
        lines = self.text.split('\n')
        
        h1_count = sum(1 for line in lines if line.strip().startswith('# '))
        h2_count = sum(1 for line in lines if line.strip().startswith('## '))
        h3_count = sum(1 for line in lines if line.strip().startswith('### '))
        
        has_h1 = h1_count > 0
        has_h2 = h2_count > 0
        
        return {
            "h1_count": h1_count,
            "h2_count": h2_count,
            "h3_count": h3_count,
            "has_h1": has_h1,
            "has_h2": has_h2,
            "structure_score": "good" if (has_h1 and has_h2) else "needs_improvement"
        }
    
    def meta_description_readiness(self) -> Dict:
        """Check if content is ready for meta description"""
        sentences = ReadabilityAnalyzer._get_sentences(self.text)
        
        first_sentences = sentences[:2] if len(sentences) >= 2 else sentences
        preview_text = ' '.join(first_sentences)
        
        length = len(preview_text)
        
        return {
            "recommended_length": "150-160 caracteres",
            "current_length": length,
            "status": "too_short" if length < 100 else "good" if length <= 160 else "too_long",
            "suggested_meta": preview_text[:160] + "..." if length > 160 else preview_text
        }
    
    def analyze(self) -> Dict:
        """Full SEO analysis"""
        return {
            "keyword_density": self.keyword_density(),
            "heading_structure": self.heading_structure(),
            "meta_description": self.meta_description_readiness()
        }


class DurationEstimator:
    """Estimate reading and speaking duration"""
    
    READING_WPM = 200
    SPEAKING_WPM = 150
    
    @staticmethod
    def estimate_reading_time(text: str, wpm: int = None) -> float:
        """Estimate reading time in minutes"""
        words = len(re.findall(r'\b[a-zA-Záéíóúüñ]+\b', text))
        speed = wpm or DurationEstimator.READING_WPM
        return round(words / speed, 1)
    
    @staticmethod
    def estimate_speaking_time(text: str, wpm: int = None) -> float:
        """Estimate speaking time in minutes"""
        words = len(re.findall(r'\b[a-zA-Záéíóúüñ]+\b', text))
        speed = wpm or DurationEstimator.SPEAKING_WPM
        return round(words / speed, 1)
    
    @staticmethod
    def analyze(text: str) -> Dict:
        """Full duration analysis"""
        reading_min = DurationEstimator.estimate_reading_time(text)
        speaking_min = DurationEstimator.estimate_speaking_time(text)
        
        return {
            "reading_minutes": reading_min,
            "speaking_minutes": speaking_min,
            "word_count": len(re.findall(r'\b[a-zA-Záéíóúüñ]+\b', text))
        }


class StructureAnalyzer:
    """Analyze structure of text"""
    
    INTRO_KEYWORDS = ['introducción', 'present', 'bienvenido', 'hola', 'en este', 'hoy vamos', 'quiero', 'vamos a']
    CONCLUSION_KEYWORDS = ['conclusión', 'resumen', 'finalmente', 'en conclusión', 'para terminar', 'recapitul', 'en resumen']
    
    @staticmethod
    def has_intro(text: str) -> bool:
        """Check if text has introduction"""
        text_lower = text.lower()
        first_section = text_lower[:min(500, len(text_lower))]
        return any(kw in first_section for kw in StructureAnalyzer.INTRO_KEYWORDS)
    
    @staticmethod
    def has_conclusion(text: str) -> bool:
        """Check if text has conclusion"""
        text_lower = text.lower()
        last_section = text_lower[max(0, len(text_lower)-500):]
        return any(kw in last_section for kw in StructureAnalyzer.CONCLUSION_KEYWORDS)
    
    @staticmethod
    def has_development(text: str) -> bool:
        """Check if text has development/body"""
        return len(text) > 500
    
    @staticmethod
    def transition_count(text: str) -> int:
        """Count transitions in text"""
        transitions = [
            'además', 'también', 'asimismo', 'por otro lado', 'sin embargo',
            'por lo tanto', 'en consecuencia', 'finalmente', 'en primer lugar',
            'en segundo lugar', 'por una parte', 'por otra parte', 
            'a continuación', 'a pesar de', 'por supuesto', 'de hecho',
            'en otras palabras', 'es decir', 'por ejemplo', 'tal como'
        ]
        
        text_lower = text.lower()
        count = sum(1 for t in transitions if t in text_lower)
        return count
    
    @staticmethod
    def section_balance(text: str) -> str:
        """Analyze if sections are balanced"""
        third = len(text) // 3
        
        intro_section = text[:third]
        dev_section = text[third:2*third]
        conc_section = text[2*third:]
        
        lengths = [len(intro_section), len(dev_section), len(conc_section)]
        avg = sum(lengths) / 3
        variance = max(lengths) - min(lengths)
        
        if variance < avg * 0.3:
            return "balanceado"
        elif variance < avg * 0.6:
            return "ligeramente desbalanceado"
        else:
            return "desbalanceado"
    
    @staticmethod
    def analyze(text: str) -> Dict:
        """Full structure analysis"""
        return {
            "has_intro": StructureAnalyzer.has_intro(text),
            "has_development": StructureAnalyzer.has_development(text),
            "has_conclusion": StructureAnalyzer.has_conclusion(text),
            "transition_count": StructureAnalyzer.transition_count(text),
            "section_balance": StructureAnalyzer.section_balance(text)
        }


class QualityAnalyzer:
    """Comprehensive quality analysis combining all analyzers"""
    
    def __init__(self, text: str, keywords: Optional[List[str]] = None):
        self.text = text
        self.keywords = keywords
    
    def analyze(self) -> Dict:
        """Full quality analysis"""
        readability = ReadabilityAnalyzer.analyze(self.text)
        structure = StructureAnalyzer.analyze(self.text)
        duration = DurationEstimator.analyze(self.text)
        
        seo = None
        if self.keywords:
            seo = SEOAnalyzer(self.text, self.keywords).analyze()
        
        quality_flags = self._detect_quality_issues()
        
        return {
            "readability": readability,
            "structure": structure,
            "duration": duration,
            "seo": seo,
            "quality_flags": quality_flags
        }
    
    def _detect_quality_issues(self) -> Dict:
        """Detect common quality issues"""
        text_lower = self.text.lower()
        
        cliches = [
            'en primer lugar', 'por último', 'en conclusión', 'a modo de',
            'es importante mencionar', 'hay que destacar', 'cabe señalar',
            'debe tenerse en cuenta', 'sin lugar a dudas', 'a nivel de'
        ]
        
        has_cliches = any(c in text_lower for c in cliches)
        
        sentences = ReadabilityAnalyzer._get_sentences(self.text)
        passive_pattern = r'\b(está|siendo|fue|ser|son|están)\s+\w+ado\b'
        too_passive = bool(re.search(passive_pattern, self.text)) and len(sentences) > 0
        
        words = text_lower.split()
        word_counts = Counter(words)
        duplicates = {w: c for w, c in word_counts.items() if c > 3 and len(w) > 6}
        has_redundancy = len(duplicates) > 0
        
        suggestions = []
        if has_cliches:
            suggestions.append("Evita clichés y frases hechas")
        if too_passive:
            suggestions.append("Usa más voz activa")
        if has_redundancy:
            suggestions.append("Revisa repeticiones innecesarias")
        
        return {
            "has_redundancy": has_redundancy,
            "has_cliches": has_cliches,
            "too_passive": too_passive,
            "suggestions": suggestions
        }
