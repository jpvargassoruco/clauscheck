# Normativa de cláusulas abusivas y contratos de adhesión (consumidor / consumidor financiero)

Fuente: `seed/normativa.json`, cuerpos `LEY453`, `DS2130`, `DS4732`, `LEY393`, `CCOM`, `LEY708` (importados vía `python -m app.seed`; 107 artículos nuevos, 6 cuerpos nuevos). Todos los textos son verbatim de la fuente citada; ninguno fue parafraseado como oficial.

## Ley N° 453 (2013) — Ley General de los Derechos de las Usuarias y los Usuarios y de las Consumidoras y los Consumidores

Fuente: https://www.lexivox.org/norms/BO-L-N453.html (2013-12-04)

**Corrección de numeración**: el encargo suponía arts. ~24-26 para cláusulas abusivas; el texto real está en **arts. 19-22 y 25** (interpretación pro-consumidor está en art. 6.6, no en 24-26).

| Art. | Inciso | Título | Verificado |
|---|---|---|---|
| 5 | 1 | Definición usuarias/usuarios, consumidoras/consumidores | sí |
| 6 | 6 | Principio de favorabilidad (interpretación pro-consumidor) | sí |
| 19 | I, II | Definición de contrato de adhesión / aprobación previa de modelos | sí |
| 20 | — | Eficacia de los contratos de adhesión | sí |
| 21 | a, b, párrafo final | Contenido mínimo del contrato de adhesión (claridad, no remisión a docs no entregados) | sí |
| 22 | encabezado, a-f, párrafo final | **Enumeración de cláusulas abusivas + nulidad "se tienen por no puestas"** (8 entradas, cada inciso por separado) | sí |
| 25 | — | Prohibición de publicidad e información engañosa/abusiva | sí |

**Detección habilitada**: definición legal de "contrato de adhesión" y de "cláusula abusiva"; lista taxativa de 6 tipos de cláusula abusiva (exclusión/limitación de derechos, modificación unilateral, exoneración de responsabilidad, silencio como aceptación, cesión de datos a terceros, cláusula residual); regla de nulidad automática; regla de interpretación pro-consumidor en caso de duda; requisitos formales mínimos del contrato de adhesión (claridad, no remisión a documentos no entregados); publicidad engañosa como vicio contractual.

## D.S. 2130 (2014) — Reglamento a la Ley 453

Fuente: https://www.lexivox.org/norms/BO-RE-DSN2130.html (2014-09-25)

| Art. | Inciso | Título | Verificado |
|---|---|---|---|
| 11 | I-IV | Prevención de cláusulas abusivas (deber del proveedor, control por autoridad, responsabilidad civil/penal, sanción) | sí |
| 12 | 1-7, II | Enumeración de prácticas comerciales abusivas (venta condicionada, negativa injustificada, envío no solicitado, aprovechamiento de vulnerabilidad, incumplimiento normas técnicas, reajuste no informado, plazo no especificado) + exclusión por autoridad | sí |

**Detección habilitada**: cruce cláusula-abusiva ↔ responsabilidad civil/penal del proveedor; catálogo de prácticas comerciales abusivas conexas a cláusulas contractuales (condicionamiento de venta, envío no solicitado, aprovechamiento de edad/discapacidad, fórmulas de reajuste ocultas, plazos indeterminados).

## D.S. 4732 (2022) — Prevención de cláusulas y prácticas abusivas en preventa de inmuebles

Fuente: https://www.lexivox.org/norms/BO-DS-N4732.html (2022-06-01)

| Art. | Inciso | Título | Verificado |
|---|---|---|---|
| 2 | — | Ámbito de aplicación (venta futura, reserva de propiedad, preventa de inmuebles) | sí |
| 3 | — | Certificación previa obligatoria de "no cláusulas abusivas" (Viceministerio de Defensa del Consumidor) | sí |
| 4 | 1-18 | Parámetros exigidos en el contrato para la certificación (identificación de propietario/promotor, título, precio no modificable unilateralmente, prohibición de cláusulas desproporcionales, fechas de obra/entrega, pagos, áreas comunes, permisos municipales) | sí |
| 5 | 1-8 | Enumeración de prácticas comerciales abusivas específicas de preventa inmobiliaria (contrato no certificado, oferta sin facultad de disposición, incumplimiento de plazo/características, cobros no pactados, venta sin autorización municipal) | sí |

**Detección habilitada**: para contratos de preventa/venta futura de inmuebles — ausencia de certificación previa; cláusula de modificación unilateral de precio; cláusulas desproporcionadas; falta de fecha de entrega/obra; cobros no previstos en contrato; venta sin permisos municipales.

## Ley N° 393 (2013) — Ley de Servicios Financieros

Fuente: https://www.lexivox.org/norms/BO-L-N393.html (2013-08-21); texto verbatim tomado del PDF ordenado oficial de ASFI: https://www.asfi.gob.bo/sites/default/files/2025-07/Texto%20ordenado.pdf

**Corrección de numeración**: el encargo suponía arts. ~85-87 para contratos de adhesión/cláusulas abusivas; el texto real está en **arts. 84-89**.

| Art. | Inciso | Título | Verificado |
|---|---|---|---|
| 59 | I-IV | Régimen de control de tasas de interés (límites por D.S., tasa variable, tasas mínimas de depósito) | sí |
| 60 | — | Régimen de comisiones (topes fijados por ASFI) | sí |
| 61 | — | Mecanismos y procedimientos de control | sí |
| 73 | I-VI | Defensoría del Consumidor Financiero (creación, misión, segunda instancia de reclamos) | sí |
| 74 | I.a-I.h, II | Derechos del consumidor financiero (trato equitativo, calidad, información fidedigna, trato digno, canales de reclamo, confidencialidad) | sí |
| 75 | I, II | Suspensión de acuerdos/prácticas restrictivas o discriminatorias | sí |
| 84 | I-VII | **Registro de contratos ante ASFI**: obligación de registro previo, revisión de cláusulas abusivas por ASFI, prohibición de operar con contratos no registrados | sí |
| 85 | I, II | **Prohibición de cláusulas de exceso o abuso de posición dominante** | sí |
| 86 | — | Prohibición de modificaciones unilaterales del contrato (salvo beneficio al consumidor) | sí |
| 87 | — | Seguros colectivos: licitación pública, prohibición de cobros adicionales | sí |
| 88 | I-III | **Prohibición de cobros no pactados** (cargos sin contraprestación, servicios no solicitados, sanción + devolución) | sí |
| 89 | — | Prohibición de prácticas discriminatorias, abusivas o restrictivas | sí |

**Detección habilitada**: tasas de interés/comisiones fuera de los topes regulados por ASFI; contrato financiero no registrado ante ASFI; cláusulas de exceso/abuso de posición dominante; modificación unilateral de condiciones pactadas; cobro de comisiones sin contraprestación o por servicios no solicitados; seguros colectivos con cobro adicional indebido; incumplimiento de derechos básicos del consumidor financiero (información, trato digno, canal de reclamo).

## Código de Comercio (D.L. 14379, 1977)

Fuente: https://www.lexivox.org/norms/BO-COD-DL14379.html (1977-02-25); verificación cruzada en bolivia.infoleyes.com

**Nota importante**: se verificó secuencialmente arts. 786-805. Los arts. 787 (contratos de adhesión / cláusula predispuesta contra el redactor) y 802/804 (cláusula penal / limitación de responsabilidad) **no existen con ese contenido en el Código de Comercio** — esas reglas están en el Código Civil (cuerpo `CC`, ya presente en el seed), no en el Código de Comercio. No se fabricaron entradas para esos temas; se dejaron placeholders `verificado:false` con nota explicativa.

| Art. | Inciso | Título | Verificado |
|---|---|---|---|
| 786 | — | Aplicación supletoria del Código Civil a los negocios mercantiles | sí |
| 803 | — | Buena fe en los contratos mercantiles | sí |
| N/A-1 | — | (placeholder) art. 787 no trata contratos de adhesión — remitir a CC | no |
| N/A-2 | — | (placeholder) arts. 802/804 no tratan cláusula penal — remitir a CC | no |

**Detección habilitada**: aplicación supletoria de reglas civiles de interpretación a contratos mercantiles; presunción de buena fe como estándar de interpretación de cláusulas comerciales ambiguas.

## Ley N° 708 (2015) — Ley de Conciliación y Arbitraje

Fuente: https://www.lexivox.org/norms/BO-L-N708.html (2015-06-25)

**Corrección de numeración**: el encargo suponía arts. ~39-41 y 44; el texto real está en **arts. 4, 5, 42-44**.

| Art. | Inciso | Título | Verificado |
|---|---|---|---|
| 4 | — | Materias excluidas de conciliación y arbitraje (recursos naturales, tributos, orden público, estado civil, etc.) | sí |
| 5 | 1 | Exclusión expresa: materia laboral y de seguridad social | sí |
| 42 | — | Cláusula arbitral (definición) | sí |
| 43 | 1-3 | Convenio arbitral (definición, soporte, relación contractual/extracontractual) | sí |
| 44 | 1, 2 | Autonomía de la cláusula/convenio arbitral respecto del contrato; nulidad del contrato no afecta la cláusula | sí |

**Nota**: la ley excluye materia laboral/seguridad social del arbitraje (art. 5.1), pero **no excluye expresamente materia de consumo/consumidor** — dato relevante para evaluar si una cláusula arbitral en un contrato de adhesión de consumo es en sí misma abusiva bajo Ley 453 art. 22, aunque no sea nula por esta ley.

**Detección habilitada**: cláusula arbitral/convenio arbitral válido según forma (escrito, soporte físico o electrónico); autonomía de la cláusula arbitral (no cae aunque el contrato principal sea nulo) — relevante para distinguir "cláusula arbitral abusiva por imposición unilateral" (Ley 453) de "cláusula arbitral formalmente válida" (Ley 708); ausencia de exclusión de consumo del arbitraje bajo esta ley.

## Resumen de conteo

| Cuerpo | Artículos importados | Verificados | No verificados |
|---|---|---|---|
| LEY453 | 17 | 17 | 0 |
| DS2130 | 12 | 12 | 0 |
| DS4732 | 28 | 28 | 0 |
| LEY393 | 38 | 38 | 0 |
| CCOM | 4 | 2 | 2 |
| LEY708 | 8 | 8 | 0 |
| **Total nuevo** | **107** | **105** | **2** |

Post-importación en la base de datos (`select c.code, count(*) ... group by 1`): confirmado 6 cuerpos nuevos y conteos de arriba coinciden 1:1 con lo importado. Re-embed ejecutado (`POST /api/v1/admin/normativa/reembed`): `count(embedding) = count(*) = 171` sobre el total de artículos en la tabla (incluye normativa laboral preexistente + `TESTCUERPO`).
