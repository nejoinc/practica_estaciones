# Caso negativo de `propia_ls`

Seis nodos, tres lotes y presupuesto 6000, con los costos, radios y pesos **oficiales**
del enunciado (CAI 1000 / 1000 m / peso 1; tránsito 2000 / 2000 m / peso 3; bomberos
5000 / 3000 m / peso 5). Red dirigida con 15 calles.

Estaciones que aportan algo:

| Estación | Costo | Cubre | Valor |
|---|---|---|---|
| L1 hurto | 1000 | hurtos 1, 2, 3, 4, 9, 12 | 6 |
| L1 accidente | 2000 | accidentes 10 y 11 | 6 |
| L1 incendio | 5000 | incendios 7 y 8 | 10 |
| L2 hurto | 500 | hurtos 3 y 9 | 2 |
| L2 incendio | 2500 | incendio 7 | 5 |
| L3 hurto | 1200 | hurtos 3 y 9 | 2 |
| L3 incendio | 6000 | incendio 7 | 5 |

Recordatorio: `propia_ls` es **híbrida**. Primero prueba varios arranques golosos (los
dos golosos normales y uno por cada primera estación posible, completando con la razón
valor/costo) y después hace **mejora local**: cambia una estación, quita una o dos, o
quita dos y pone una elegida, y siempre rellena el hueco con el goloso por razón.

Traza (`py main.py parte2 instancias_malas/propia_ls propia_ls`):

1. Arranques. El mejor es el goloso base: `L1 incendio` + `L2 hurto`, valor 12, costo
   5500. Los demás dan 11, 8, 6 o 5 (por ejemplo, forzar `L1 accidente` primero completa
   con `L2 hurto`: valor 8).
2. Mejora local desde (`L1 incendio`, `L2 hurto`). Ningún vecino supera 12:
   - cambiar `L1 incendio` por `L1 accidente` deja (`L2 hurto`, `L1 accidente`) = 8, y el
     relleno no agrega `L3 hurto` porque sus hurtos 3 y 9 ya los cubre `L2 hurto`;
   - cambiar `L2 hurto` por `L2 accidente` da 10; quitar estaciones y rellenar da 6, 11 o 12;
   - quitar las dos y poner `L2 incendio` hace que el relleno elija `L1 hurto`
     (razón 6 / 1000) en vez de `L1 accidente` (6 / 2000): valor 11;
   - quitar las dos y poner `L1 accidente` hace que el relleno elija `L2 hurto`
     (2 / 500) en vez de `L2 incendio` (5 / 2500): valor 8.
3. Resultado: valor **12**, costo 5500.

El óptimo (fuerza bruta y `py main.py parte3 instancias_malas/propia_ls`) es
`L1 accidente` + `L2 incendio` + `L3 hurto`: valor **13**, costo 5700.

La decisión que la desvía es el relleno goloso por razón: para llegar al óptimo hay que
cambiar a la vez las DOS estaciones (L1 a tránsito y L2 a bomberos). El vecindario más
grande solo elige a mano UNA estación nueva y deja la otra al relleno, que siempre
prefiere el CAI barato del lote libre (mejor razón) y nunca la pareja tránsito + bomberos.
