# Perfil Profesional y Filosofía Técnica

## Resumen Ejecutivo
Soy un desarrollador de software apasionado por la construcción de sistemas escalables y mantenibles. Mi enfoque combina una sólida base en principios de ingeniería de software con la pragmática necesaria para entregar valor rápidamente. Me especializo en arquitectura de microservicios, desarrollo backend y devops.

## Stack Tecnológico y Experiencia

| Categoría | Tecnologías | Años de Experiencia |
| :--- | :--- | :--- |
| **Lenguajes** | PHP, Python, JavaScript, HTML5, CSS3 | 8 años |
| **Backend** | Laravel, Django | 8 años |
| **Frontend** | Vue.js, React, Next.js, Tailwind | 4+ años |
| **Mobile/Modern JS** | TypeScript, Next.js, NestJS | 4+ años |
| **Bases de Datos** | MySQL, SQL Server, PostgreSQL, MongoDB, Firebase | 8 años |
| **DevOps** | Git, Docker, Gestión de Servidores (WHM/GCP) | 8 años |
| **E-commerce** | PrestaShop, WordPress | 4+ años |

## Filosofía Técnica

### Clean Code y SOLID
Creo firmemente que el código se lee muchas más veces de las que se escribe. Aplico principios SOLID no como dogma, sino como herramientas para gestionar la complejidad.
- **S (Single Responsibility)**: Cada módulo debe tener una única razón para cambiar.
- **O (Open/Closed)**: Extiendo funcionalidad sin modificar código existente, usando polimorfismo y patrones de diseño.
- **Pruebas Automatizadas**: "Si no está probado, está roto". Desarrollo con TDD cuando es posible y siempre aseguro una buena cobertura de tests unitarios y de integración.

### Microservicios vs Monolito
No hay una "bala de plata".
- **Monolito Modular**: Mi preferencia para empezar. Fácil de desplegar, testear y refactorizar.
- **Microservicios**: Solo cuando la complejidad del dominio o los requisitos de escalabilidad organizacional lo demandan. Requieren una madurez en DevOps (observabilidad, CI/CD) que no debe subestimarse.

## Historias de Proyectos (Metodología STAR)

### Proyecto: Migración de E-commerce Legado
**Situación**: Un sistema e-commerce de 10 años en PHP monolítico, sin tests, con despliegues manuales que tomaban horas y causaban caídas.
**Tarea**: Modernizar la plataforma para soportar el Black Friday (5x tráfico) sin reescribir todo desde cero.
**Acción**:
- Implementé patrón "Strangler Fig" para extraer funcionalidades críticas (búsqueda, checkout) a microservicios en Go y Node.js.
- Automaticé el pipeline de CI/CD con GitHub Actions y Docker.
- Introduje tests de integración Cypress para flujos críticos.
**Resultado**: Despliegues en 15 minutos, cero downtime durante Black Friday, y aumento del 20% en conversión gracias a la mejora en performance de búsqueda.

### Proyecto: Sistema de Gestión de Flotas en Tiempo Real
**Situación**: Necesidad de trackear 5000+ vehículos en tiempo real y detectar anomalías.
**Tarea**: Diseñar una arquitectura capaz de ingerir miles de eventos por segundo.
**Acción**:
- Diseñé una arquitectura orientada a eventos usando Kafka para la ingesta.
- Usé Redis para cache de última posición y PostgreSQL con TimescaleDB para histórico.
- Implementé servicios en Python (FastAPI) para el procesamiento de datos.
**Resultado**: Latencia de actualización menor a 200ms. El sistema escaló horizontalmente para soportar el doble de flota en 6 meses.

## Habilidades Blandas (Soft Skills)

### Liderazgo Técnico
- He mentoreado a 3 desarrolladores junior, ayudándoles a ascender a nivel mid/senior mediante revisiones de código constructivas y pair programming.
- Facilito discusiones técnicas buscando consenso, no imponiendo mi visión. "Strong opinions, weakly held".

### Resolución de Conflictos
- En situaciones de desacuerdo técnico, propongo pruebas de concepto (POCs) rápidas para validar hipótesis con datos, no con opiniones.
- Fomento una cultura "blameless post-mortem" donde los errores son oportunidades de aprendizaje sistémico, no culpa individual.

## Preguntas Frecuentes (FAQ)

### ¿Cuál es tu mayor debilidad técnica?
A veces puedo obsesionarme con la optimización prematura. He aprendido a usar el principio YAGNI (You Aren't Gonna Need It) para balancear la perfección técnica con la entrega de valor.

### ¿Cómo te mantienes actualizado?
Leo blogs de ingeniería (Uber, Netflix), sigo newsletters (ByteByteGo), y tengo proyectos personales (como este portfolio de microservicios) donde experimento con nuevas tecnologías en un entorno controlado.
