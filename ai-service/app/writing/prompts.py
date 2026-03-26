"""
Writing Prompts - Specialized prompts for script improvement

Contains prompt templates for different writing techniques and operations.
"""
from typing import Dict, Optional
from enum import Enum


class WritingTechnique(str, Enum):
    """Available writing techniques for structure improvement"""
    STORYTELLING = "storytelling"
    AIDA = "aida"
    PAS = "pas"
    HERO_JOURNEY = "hero_journey"
    THREE_ACT = "three_act"
    INVERTED_PYRAMID = "inverted_pyramid"
    RULE_OF_THREE = "rule_of_three"


class ToneType(str, Enum):
    """Available tone types"""
    FORMAL = "formal"
    PROFESSIONAL = "professional"
    CASUAL = "casual"
    DYNAMIC = "dynamic"
    FRIENDLY = "friendly"
    AUTHORITATIVE = "authoritative"


class FormatType(str, Enum):
    """Available output formats"""
    GENERAL = "general"
    VIDEO = "video"
    PODCAST = "podcast"
    LINKEDIN = "linkedin"
    PRESENTATION = "presentation"


class LengthPreference(str, Enum):
    """Length preferences"""
    SHORT = "short"
    MEDIUM = "medium"
    LONG = "long"


class WritingPrompts:
    """Collection of specialized prompts for writing operations"""
    
    BASE_SYSTEM = """Eres un experto redactor de guiones profesionales con más de 15 años de experiencia.
Tu especialidad es crear contenido único, engaging y memorable que captura la atención del lector/oyente desde el primer momento.

Principios que sigues:
1. NUNCA sigues patrones predecibles - cada guión es único
2. Usas técnicas narrativas avanzadas para maximizar retención
3. Adaptas el tono y estilo al público objetivo
4. Creas flujo natural entre secciones sin transiciones forzadas
5. Evitas clichés y frases gastadas
6. Tus guiones se sienten humanos, no generados por IA"""

    @staticmethod
    def get_improve_prompt(
        content: str,
        tone: str = "professional",
        target_audience: str = "general",
        purpose: Optional[str] = None
    ) -> str:
        """Generate improvement prompt"""
        purpose_text = f"\nPropósito del guión: {purpose}" if purpose else ""
        return f"""{WritingPrompts.BASE_SYSTEM}

CONTEXTO:
- Tono deseado: {tone}
- Audiencia objetivo: {target_audience}{purpose_text}

GUION ORIGINAL:
---
{content}
---

INSTRUCCIONES:
1. Mejora la fluidez y naturalidad del texto
2. Corrige errores gramaticales y ortográficos
3. Haz el contenido más engaging y memorable
4. Mantén el mensaje original pero enriquece la expresión
5. Evita patrones repetitivos comunes en guiones generados por IA
6. Haz cada oración única - evita estructuras repetitivas

GUION MEJORADO:"""

    @staticmethod
    def get_structure_prompt(
        content: str,
        technique: str,
        tone: str = "professional",
        target_audience: str = "general"
    ) -> str:
        """Generate structure improvement prompt with specific technique"""
        
        techniques = {
            "storytelling": """Usa la técnica de Storytelling con:
- Un protagonista claro con el que la audiencia se identifique
- Un conflicto o desafío central
- Arco emocional con altibajos
- Clímax emocional
- Resolución satisfactoria
- Lecciones aprendidasimplícitas
- Voz en primera persona o narrativa cercana""",

            "aida": """Usa la fórmula AIDA (Atención-Interés-Deseo-Acción):
- ATENCIÓN: Hook explosivo en los primeros segundos/párrafos
- INTERÉS: Desarrolla el problema/oportunidad con detalles
- DESEO: Muestra beneficios tangibles y transformación
- ACCIÓN: CTA claro, específico y urgente""",

            "pas": """Usa la fórmula PAS (Problema-Agitación-Solución):
- PROBLEMA: Identifica claramente el dolor del lector
- AGITACIÓN: Amplifica las consecuencias de no actuar
- SOLUCIÓN: Presenta tu solución como el camino inevitable""",

            "hero_journey": """Usa el Viaje del Héroe (12 pasos):
1. Mundo ordinario (establecer contexto)
2. Llamado a la aventura
3. Resistencia/inicio del viaje
4. Encuentros con mentores/aliados
5. Prueba suprema (el desafío)
6.回头 (punto más oscuro)
7. Recompensa (victoria/insight)
8. Camino de regreso
9. Renacimiento
10. Retorno con el(elixir)
11. Maestro de dos mundos
12. Vida nueva""",

            "three_act": """Usa estructura de 3 actos:
- ACTO 1 (Setup - 25%): Introduce personajes, contexto, y el detonante
- ACTO 2 (Confrontation - 50%): Desarrollo con obstáculos, tensiones crecientes, punto de giro
- ACTO 3 (Resolution - 25%): Clímax, resolución, mensaje final""",

            "inverted_pyramid": """Usa Pirámide Invertida:
- Conclusión primero (la respuesta principal al inicio)
- Información más importante inmediatamente
- Detalles de soporte en orden de importancia
- Contexto mínimo al final
- Ideal para SEO y lectores impacientes""",

            "rule_of_three": """Usa Regla de Tres:
- Organiza ideas en tríos memorables
- Tres puntos clave por sección
- Tres ejemplos cuando sea necesario
- Ritmo: punto-punto-punto (climax)
- Evita listas de más de 3 elementos
- Cada "tres" debe ser completo y autosuficiente"""
        }
        
        technique_instruction = techniques.get(technique, techniques["storytelling"])
        
        return f"""{WritingPrompts.BASE_SYSTEM}

TÉCNICA A APLICAR:
{technique_instruction}

CONTEXTO:
- Tono: {tone}
- Audiencia: {target_audience}

GUION ORIGINAL:
---
{content}
---

INSTRUCCIONES:
1. Reescribe el guión aplicando la técnica especificada
2. Haz que el resultado sea ÚNICO y memorable - NO sigas patrones predecibles
3. Integra la técnica de forma natural, no forzada
4. Mantén el mensaje core pero mejora la estructura
5. Cada sección debe fluir naturalmente a la siguiente
6. Evita frases de transición genéricas ("En primer lugar", "En conclusión")

GUION REESTRUCTURADO:"""

    @staticmethod
    def get_tone_prompt(content: str, tone: str) -> str:
        """Generate tone change prompt"""
        tone_guidance = {
            "formal": "Usa lenguaje profesional, evitando contracciones, con estructura pulida y vocabulario sofisticado pero accesible.",
            "professional": "Tono de negocio, directo, confiado, orientado a resultados. Evita jerga innecesaria.",
            "casual": "Lenguaje coloquial pero no vulgar. Como si hablaras con un amigo interesante. Usa contracciones.",
            "dynamic": "Energético, apasionado, motivador. Oraciones vary length. Usa verbos de acción poderosos.",
            "friendly": "Cálido, cercano, empático. Haz que el lector se sienta understood y valorado.",
            "authoritative": "Experto, seguro, con evidencia. Tono de líder de opinión. Datos y convictos."
        }
        
        guidance = tone_guidance.get(tone, tone_guidance["professional"])
        
        return f"""{WritingPrompts.BASE_SYSTEM}

CAMBIO DE TONO: {tone}
{guidance}

GUION ORIGINAL:
---
{content}
---

 Reescribe el guión con el nuevo tono manteniendo:
1. El mensaje y contenido original
2. La estructura lógica
3. Engagement del lector
4. Naturalidad - no forzar palabras

GUION CON NUEVO TONO:"""

    @staticmethod
    def get_expand_prompt(content: str, factor: str = "medium") -> str:
        """Generate expansion prompt"""
        factor_guide = {
            "short": "Expande aproximadamente un 30%. Sé conciso pero añade detalles clave.",
            "medium": "Expande aproximadamente un 50%. Añade ejemplos, explicaciones y contexto.",
            "long": "Expande significativamente (75-100%). Desarrolla cada punto profundamente, añade historias, datos y transiciones elaboradas."
        }
        
        guide = factor_guide.get(factor, factor_guide["medium"])
        
        return f"""{WritingPrompts.BASE_SYSTEM}

INSTRUCCIONES DE EXPANSIÓN:
{guide}

GUION ORIGINAL:
---
{content}
---

INSTRUCCIONES:
1. Expande el guión manteniendo su esencia
2. Añade detalles, ejemplos y contexto donde sea apropiado
3. Desarrolla transiciones naturales entre secciones
4. Evita redundancia - cada palabra debe aportar valor
5. Mantén el tono y estilo consistentes
6. NO repitas información - profundiza

GUION EXPANDIDO:"""

    @staticmethod
    def get_summarize_prompt(content: str, length: str = "medium") -> str:
        """Generate summarization prompt"""
        length_guide = {
            "short": "Resumen ultra-conciso: máximo 20% del original. Solo puntos esenciales.",
            "medium": "Resumen balanceado: 30-40% del original. Ideas principales con algo de contexto.",
            "long": "Resumen detallado: 50% del original. Mantén estructura y suficiente detalle."
        }
        
        guide = length_guide.get(length, length_guide["medium"])
        
        return f"""{WritingPrompts.BASE_SYSTEM}

INSTRUCCIONES DE RESUMEN:
{guide}

GUION ORIGINAL:
---
{content}
---

INSTRUCCIONES:
1. Extrae los puntos más importantes
2. Mantén la esencia y mensaje central
3. Conserva estructura lógica
4. Resume, no parafrasees - ve directo al punto
5. Cada oración debe justificar su existencia

RESUMEN:"""

    @staticmethod
    def get_adapt_format_prompt(
        content: str,
        format_type: str,
        target_audience: str = "general"
    ) -> str:
        """Generate format adaptation prompt"""
        
        format_guidance = {
            "video": """Adaptación para VIDEO:
- Hook en los primeros 3-5 segundos (frase que capture atención inmediata)
- Secciones cortas (máximo 2-3 minutos por bloque)
- Transiciones dinámicas entre temas
- Puntos visuales claros para cada sección
- CTAs visuales (llamados a la acción)
- Ritmo rápido pero no precipitado
- Preguntas retóricas para mantener engagement""",

            "podcast": """Adaptación para PODCAST:
- Apertura conversacional (saludo + qué tratarán)
- Tono más íntimo y natural, como hablando con un amigo
- Pistas de audio indicated [música], [pausa], [sonido]
- Preguntas directas al oyente para mantener conexión
- Historias y ejemplos extensos (el formato lo permite)
- Cierre con resumen + CTA para seguir escuchando
- Evita texto muy largo sin pausas""",

            "linkedin": """Adaptación para LINKEDIN:
- Primera línea CRÍTICA (lo que aparece antes de "ver más")
- Emojis estratégicos para romper texto
- Líneas cortas (máximo 1-2 oraciones por párrafo)
- Espacios visuales entre bloques
- Máximo 3000 caracteres (idealmente menos)
- 3-5 puntos clave con bullet points
- CTA al final (comentario, compartir, conectar)
- Hashtags relevantes (máximo 3-5)
- Tono profesional pero personal""",

            "presentation": """Adaptación para PRESENTACIÓN:
- Slides: solo puntos clave + visuales
- Notas del speaker: texto completo y detallado
- Estructura: Slide título → Contenido mínimo → Notas extensas
- 每 slide: 1 idea principal, máximo 6 bullets
- Transiciones claras entre secciones
- Tiempo estimado por sección
- hooks para mantener atención entre slides"""
        }
        
        guidance = format_guidance.get(format_type, format_guidance["general"])
        
        return f"""{WritingPrompts.BASE_SYSTEM}

FORMATO DESTINO: {format_type}
AUDIENCIA: {target_audience}

{guidance}

GUION ORIGINAL:
---
{content}
---

ADAPTA el guión al formato especificado:
1. Respeta las características del formato
2. Mantén el mensaje core
3. Optimiza para la experiencia del usuario final
4. Incluye notas específicas del formato si aplica

GUION ADAPTADO:"""

    @staticmethod
    def get_analysis_prompt(content: str) -> str:
        """Generate analysis prompt for quality metrics"""
        return f"""{WritingPrompts.BASE_SYSTEM}

Analiza el siguiente guión y proporciona un análisis detallado en formato JSON:

GUION A ANALIZAR:
---
{content}
---

PROPORCIONA un JSON con esta estructura exacta:
{{
    "word_count": número total de palabras,
    "character_count": número de caracteres,
    "sentence_count": número de oraciones,
    "avg_words_per_sentence": promedio de palabras por oración,
    "avg_characters_per_word": promedio de caracteres por palabra,
    "readability": {{
        "flesch_kincaid_grade": nivel de lectura (1-12),
        "flesch_reading_ease": puntuación (0-100),
        "interpretation": "descripción del nivel de legibilidad"
    }},
    "structure": {{
        "has_intro": true/false,
        "has_development": true/false,
        "has_conclusion": true/false,
        "transition_count": número de transiciones,
        "section_balance": "balanceado/desbalanceado"
    }},
    "engagement": {{
        "hook_strength": "fuerte/medio/debil",
        "cta_present": true/false,
        "questions_count": número de preguntas,
        "emotional_appeal": "alto/medio/bajo"
    }},
    "quality_flags": {{
        "has_redundancy": true/false,
        "has_cliches": true/false,
        "too_passive": true/false,
        "suggestions": ["lista de sugerencias específicas"]
    }},
    "estimated_duration": {{
        "reading_minutes": minutos de lectura,
        "speaking_minutes": minutos de lectura en voz alta (150-200 ppm)
    }}
}}

JSON:"""
