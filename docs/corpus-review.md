# Revisión del catálogo normativo (`seed/normativa.json`)

**IMPORTANTE — este catálogo completo requiere revisión de un abogado habilitado antes de cualquier uso comercial.** El texto fue obtenido de fuentes públicas mediante herramientas automatizadas (WebSearch/WebFetch); aunque cada artículo fue cruzado contra al menos una fuente cuando fue posible, no reemplaza el cotejo contra la Gaceta Oficial impresa.

## Código Civil (D.L. 12760, 6-ago-1975)

36/36 artículos requeridos por el Manual §06 encontrados y con texto verbatim, `verificado: true`.

- Fuentes: `bolivia.infoleyes.com` (mayoría), `paradaabogados.com` (arts. 485, 549, 554, 568, 581, 732, 1435), `lexivox.org` (arts. 584, 614, 624, 628, 685*, 700, 705, 719, 720, 726).
- Arts. 491 y 628 incluyen además una entrada separada para el inciso citado explícitamente por el Manual (491 inciso "3"; 628 inciso "II").
- **Problema detectado — Art. 685:** las fuentes lexivox.org, OAS PDF y paradaabogados.com coinciden en un texto con la palabra "obra" ("...concede a la obra el uso o goce..."), que no tiene sentido gramatical y parece un error de OCR propagado entre espejos del mismo documento escaneado. `bolivia.infoleyes.com` trae "...concede a la otra..." (correcto). Se adoptó esta última versión; **requiere confirmación contra un ejemplar impreso u oficial antes de uso comercial**.

## Constitución Política del Estado (2009)

9/9 incisos requeridos encontrados, `verificado: true`. Fuente principal: `lexivox.org/norms/BO-CPE-20090207.html`, cruzado contra `bolivia.infoleyes.com` para Art. 48 (coincidencia exacta) y para 21.2/115.II/116.II/119.II.

- Nota metodológica: el HTML de lexivox no imprime rótulos "I./II." en los artículos narrativos (21, 56, 115, 116, 119, 130); el parágrafo pedido se identificó por posición de párrafo y se contrastó contra infoleyes.com, con coincidencia textual exacta en los casos verificables. Riesgo residual bajo pero no nulo de desalineación de parágrafo en 56 y 130 (artículos citados completos, por lo que el riesgo no aplica a ellos).

## Normativa laboral y especial

| Cuerpo | Artículos incluidos | Estado | Fuente(s) |
|---|---|---|---|
| Ley General del Trabajo (1942-12-08) | 16, 46 (los dos exigidos) | ✅ verificado | infoleyes.com |
| D.S. 110/2009 (1-may-2009) | Art. 1 ✅ · Art. 2 ❌ no encontrado | parcial | lexivox.org; PDF oficial (cfb.org.bo) no se pudo extraer |
| Ley 065/2010 de Pensiones | Art. 91 (obligaciones del empleador, confianza baja) · Art. 96 ✅ | parcial | infoleyes.com |
| Código de Seguridad Social (cuerpo `CSS`, vía D.L. 13214, 24-dic-1975) | Art. 2 ✅ (registro patronal) · Art. 6 ✅ (afiliación de trabajadores, párrafo operativo) | ✅ | infoleyes.com/norma/1136 |
| D.S. 21637 | — | ❌ no encontrado | no se localizó artículo citable; ver nota en el cuerpo |
| D.S. 3150/1952 | Art. 1 (confianza baja, texto truncado) | parcial | infoleyes.com |
| D.S. 17288/1980 | Art. 1 ✅ (escala completa) | ✅ | infoleyes.com |
| D.S. 5383/2025 | Art. 6 ✅ (incremento salarial 5%) · Art. 7 ✅ (Salario Mínimo Nacional Bs 2.750) | ✅ | infoleyes.com |
| Ley 045/2010 | Art. 5 inciso I.1 (definición de discriminación) ✅ | ✅ | lexivox.org |
| Ley 16998/1979 (cuerpo `DL16998`, Ley General de Higiene, Seguridad Ocupacional y Bienestar) | Art. 3 ✅ · Art. 6 (confianza baja, posible fragmento) | parcial | lexivox.org |

**Corrección al encargo original:** D.S. 3150/1952 y D.S. 17288/1980 NO regulan "retiro voluntario/desahucio" — ambos regulan la **escala de vacaciones anuales** por años de servicio (D.S. 3150 modifica el Art. 44 LGT; D.S. 17288 restablece/actualiza esa escala). Se documentaron con su tema real; no se encontraron reglas de desahucio en estos dos decretos.

## Resumen de conteos

- Cuerpos: 12 (`CC`, `CPE`, `LGT`, `DS110`, `LEY065`, `CSS`, `DS21637`, `DS3150`, `DS17288`, `DS5383`, `LEY045`, `DL16998`).
- Artículos totales: 63 (incluye entradas de inciso separadas para CC 491.3, CC 628.II y CPE 48.II/III/IV).
- `verificado: true`: 58. `verificado: false` (texto no encontrado o de confianza baja, con `nota` explicando el motivo): 5 — D.S. 110 art. 2, Ley 065 art. 91, D.S. 21637 (sin artículo), D.S. 3150 art. 1, Ley 16998 art. 6.

## Método

Fetches vía WebSearch/WebFetch contra lexivox.org, bolivia.infoleyes.com, paradaabogados.com, y PDFs oficiales (OEP, OAS) cuando disponibles. Ningún texto fue redactado de memoria: los artículos no confirmables verbatim quedaron con `verificado:false` y una `nota` describiendo el problema, en vez de texto parafraseado.

**Antes de cualquier uso comercial:** un abogado debe (1) confirmar Art. 685 CC contra fuente impresa, (2) completar D.S. 110 art. 2, (3) confirmar la puntuación exacta de Ley 065 art. 91, (4) verificar D.S. 3150 art. 1 y localizar el texto completo de la escala, (5) decidir si D.S. 21637 aporta algún artículo citable, y (6) confirmar si Ley 16998 art. 6 está completo o es un fragmento de lista.
