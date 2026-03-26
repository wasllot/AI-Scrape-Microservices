"""
Writing Formatters - Format adaptation for different outputs

Provides formatters for:
- Video scripts
- Podcast scripts
- LinkedIn posts
- Presentation slides
"""
from typing import Dict, List, Optional
from dataclasses import dataclass


@dataclass
class FormatResult:
    """Result of format adaptation"""
    formatted_content: str
    format_type: str
    notes: List[str]


class VideoFormatter:
    """Format content for video scripts"""
    
    @staticmethod
    def format(content: str) -> FormatResult:
        """Format content as video script"""
        lines = content.split('\n')
        formatted_lines = []
        notes = []
        
        formatted_lines.append("=" * 50)
        formatted_lines.append("SCRIPT PARA VIDEO")
        formatted_lines.append("=" * 50)
        formatted_lines.append("")
        
        formatted_lines.append("[APERTURA - 3-5 segundos]")
        formatted_lines.append("🎬 Hook inicial - Frase que captura atención inmediata")
        formatted_lines.append("")
        
        in_body = False
        section_count = 0
        
        for i, line in enumerate(lines):
            if line.strip():
                if not in_body:
                    section_count += 1
                    formatted_lines.append(f"\n[BLOQUE {section_count} - 2-3 minutos]")
                
                formatted_lines.append(line)
                in_body = True
            else:
                if in_body:
                    formatted_lines.append("")
                    formatted_lines.append("[TRANSICIÓN]")
                    formatted_lines.append("→ Переход к следующей теме")
                    formatted_lines.append("")
                in_body = False
        
        formatted_lines.append("")
        formatted_lines.append("[CIERRE - 30 segundos]")
        formatted_lines.append("📢 Resumen + CTA final")
        formatted_lines.append("")
        
        notes.extend([
            "Duración estimada: 5-15 minutos por bloque",
            "Cada bloque termina con pregunta retórica",
            "Visuales sugeridos entre secciones"
        ])
        
        return FormatResult(
            formatted_content='\n'.join(formatted_lines),
            format_type="video",
            notes=notes
        )


class PodcastFormatter:
    """Format content for podcast scripts"""
    
    @staticmethod
    def format(content: str) -> FormatResult:
        """Format content as podcast script"""
        lines = content.split('\n')
        formatted_lines = []
        notes = []
        
        formatted_lines.append("=" * 50)
        formatted_lines.append("SCRIPT PARA PODCAST")
        formatted_lines.append("=" * 50)
        formatted_lines.append("")
        
        formatted_lines.append("[INTRO - 30-60 segundos]")
        formatted_lines.append("🎙️ Saludo + presentación del tema")
        formatted_lines.append("💡 Qué van a aprender los oyentes")
        formatted_lines.append("")
        
        formatted_lines.append("[MÚSICA DE TRANSICIÓN]")
        formatted_lines.append("")
        
        in_topic = False
        topic_count = 0
        
        for line in lines:
            if line.strip():
                if not in_topic:
                    topic_count += 1
                    formatted_lines.append(f"\n🎯 TEMA {topic_count}:")
                
                formatted_lines.append(f"   {line}")
                in_topic = True
            else:
                if in_topic:
                    formatted_lines.append("")
                    formatted_lines.append("   [Pregunta al oyente: ¿esto te ha pasado?]")
                    formatted_lines.append("")
                in_topic = False
        
        formatted_lines.append("")
        formatted_lines.append("[CIERRE - 1-2 minutos]")
        formatted_lines.append("📝 Resumen de puntos clave")
        formatted_lines.append("🔗 CTA: Suscribirse, comentar, compartir")
        formatted_lines.append("")
        
        notes.extend([
            "Tono conversacional y cercano",
            "Pausas indicadas con [pausa]",
            "Sonidos ambiente entre secciones",
            "Duración: 20-45 minutos ideal"
        ])
        
        return FormatResult(
            formatted_content='\n'.join(formatted_lines),
            format_type="podcast",
            notes=notes
        )


class LinkedInFormatter:
    """Format content for LinkedIn posts"""
    
    MAX_LENGTH = 3000
    
    @staticmethod
    def format(content: str) -> FormatResult:
        """Format content for LinkedIn"""
        lines = content.split('\n')
        formatted_lines = []
        notes = []
        
        formatted_lines.append("=" * 50)
        formatted_lines.append("POST PARA LINKEDIN")
        formatted_lines.append("=" * 50)
        formatted_lines.append("")
        
        first_line = lines[0].strip() if lines else ""
        formatted_lines.append(first_line[:200])
        
        if len(first_line) > 200:
            formatted_lines.append("... [ver más]")
        
        formatted_lines.append("")
        
        bullet_points = []
        rest_content = []
        
        for line in lines[1:]:
            stripped = line.strip()
            if stripped.startswith(('- ', '• ', '* ', '1.', '2.', '3.')):
                bullet_points.append(stripped)
            elif stripped:
                rest_content.append(stripped)
        
        if bullet_points:
            formatted_lines.append("📌 PUNTOS CLAVE:")
            for bp in bullet_points[:7]:
                formatted_lines.append(f"   {bp}")
            formatted_lines.append("")
        
        if rest_content:
            formatted_lines.append("📝 DESARROLLO:")
            for rc in rest_content[:5]:
                if len('\n'.join(formatted_lines)) < LinkedInFormatter.MAX_LENGTH - 200:
                    formatted_lines.append(rc)
                    formatted_lines.append("")
        
        formatted_lines.append("")
        formatted_lines.append("💬 ¿Qué opinas? Comenta 👇")
        formatted_lines.append("")
        formatted_lines.append("#Professional #Industry #Thoughts")
        
        total_length = len('\n'.join(formatted_lines))
        notes.extend([
            f"Longitud actual: {total_length} caracteres",
            "Ideal: menos de 3000 caracteres",
            "Primera línea es crucial (lo que aparece antes de 'ver más')",
            "Usa líneas cortas y espacios visuales",
            "3-5 hashtags máximo"
        ])
        
        return FormatResult(
            formatted_content='\n'.join(formatted_lines),
            format_type="linkedin",
            notes=notes
        )


class PresentationFormatter:
    """Format content for presentation slides"""
    
    @staticmethod
    def format(content: str) -> FormatResult:
        """Format content as presentation slides"""
        lines = content.split('\n')
        formatted_lines = []
        notes = []
        
        formatted_lines.append("=" * 60)
        formatted_lines.append("PRESENTACIÓN - SLIDES + NOTAS DEL SPEAKER")
        formatted_lines.append("=" * 60)
        
        sections = PresentationFormatter._split_into_sections(lines)
        
        for i, section in enumerate(sections, 1):
            formatted_lines.append(f"\n{'='*60}")
            formatted_lines.append(f"SLIDE {i}")
            formatted_lines.append(f"{'='*60}")
            
            section_lines = [l for l in section['content'] if l.strip()]
            
            if section_lines:
                formatted_lines.append("\n📊 TÍTULO DEL SLIDE:")
                formatted_lines.append(section_lines[0])
                
                formatted_lines.append("\n📋 CONTENIDO (máx 6 bullets):")
                for bullet in section_lines[1:7]:
                    formatted_lines.append(f"  • {bullet}")
                
                formatted_lines.append("\n🎤 NOTAS DEL SPEAKER:")
                speaker_notes = section_lines[1:] if len(section_lines) > 1 else []
                for note in speaker_notes:
                    formatted_lines.append(f"   {note}")
                
                formatted_lines.append(f"\n estimado: ⏱️ Tiempo2-3 minutos")
        
        formatted_lines.append("\n" + "="*60)
        formatted_lines.append("CIERRE")
        formatted_lines.append("="*60)
        formatted_lines.append("📊 Resumen final")
        formatted_lines.append("🎯 CTA: preguntas o siguiente paso")
        
        notes.extend([
            "Cada slide: 1 idea principal",
            "Máximo 6 bullets por slide",
            "Notas del speaker extensas para guiar presentación",
            "Transiciones claras entre slides",
            "Duración total: 15-30 minutos"
        ])
        
        return FormatResult(
            formatted_content='\n'.join(formatted_lines),
            format_type="presentation",
            notes=notes
        )
    
    @staticmethod
    def _split_into_sections(lines: List[str]) -> List[Dict]:
        """Split content into logical sections"""
        sections = []
        current_section = {'title': 'Introduction', 'content': []}
        
        section_keywords = ['introducción', 'tema', 'punto', 'sección', 'parte', 'conclusión']
        
        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue
            
            is_new_section = False
            for kw in section_keywords:
                if kw in stripped.lower() and len(stripped) < 50:
                    is_new_section = True
                    break
            
            if is_new_section and current_section['content']:
                sections.append(current_section)
                current_section = {'title': stripped, 'content': []}
            
            current_section['content'].append(stripped)
        
        if current_section['content']:
            sections.append(current_section)
        
        if not sections:
            sections = [{'title': 'Content', 'content': lines}]
        
        return sections


class GeneralFormatter:
    """General formatting without specific adaptation"""
    
    @staticmethod
    def format(content: str) -> FormatResult:
        """Return content as-is with notes"""
        return FormatResult(
            formatted_content=content,
            format_type="general",
            notes=["Formato general sin adaptaciones específicas"]
        )


class FormatAdapter:
    """Main adapter to select appropriate formatter"""
    
    FORMATTERS = {
        "video": VideoFormatter,
        "podcast": PodcastFormatter,
        "linkedin": LinkedInFormatter,
        "presentation": PresentationFormatter,
        "general": GeneralFormatter
    }
    
    @classmethod
    def format(cls, content: str, format_type: str) -> FormatResult:
        """Format content using specified formatter"""
        formatter_class = cls.FORMATTERS.get(format_type, GeneralFormatter)
        return formatter_class.format(content)
    
    @classmethod
    def get_available_formats(cls) -> List[str]:
        """Get list of available format types"""
        return list(cls.FORMATTERS.keys())
