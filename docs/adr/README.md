# Registro de decisiones de arquitectura (ADR)

Cada decisión de refactorización se documenta en un archivo independiente con el
formato de [`0000-plantilla.md`](0000-plantilla.md): problema (Semana 3), cambio
propuesto, código afectado y atributo de calidad que mejora (Semana 8).

| ADR | Decisión | Problema | Atributo | Estado |
|---|---|---|---|---|
| [0001](0001-entidades-de-dominio-y-mapeo-por-nombre.md) | Entidades de dominio y mapeo por nombre de columna | P1 | Mantenibilidad · Seguridad (integridad) | Implementada en el MVP |
| [0002](0002-unidad-de-trabajo-transaccional.md) | Unidad de trabajo transaccional | P2 | Confiabilidad | Implementada y probada |
| [0003](0003-inactivacion-logica.md) | Inactivación lógica en lugar de borrado físico | P3 | Seguridad (integridad, no repudio) · Confiabilidad | Implementada; migración lista para aplicar |
| [0004](0004-fuente-unica-de-reglas-de-negocio.md) | Fuente única de reglas de negocio en el dominio | P4 | Mantenibilidad · Consistencia | Implementada en el MVP |
| [0005](0005-repositorios-y-filtrado-en-sql.md) | Repositorios con filtrado en SQL y sin SQL en la interfaz | P5 | Mantenibilidad · Eficiencia | Implementada en el MVP |
