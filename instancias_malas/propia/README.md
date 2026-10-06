# Caso negativo de `propia`

Seis nodos, cuatro lotes y presupuesto 5000, con los costos, radios y pesos **oficiales**
del enunciado (CAI 1000 / 1000 m / peso 1; tránsito 2000 / 2000 m / peso 3; bomberos
5000 / 3000 m / peso 5). Red dirigida con 13 calles.

Estaciones que aportan algo:

| Estación | Costo | Cubre | Valor | Valor por millón |
|---|---|---|---|---|
| L1 hurto | 1200 | hurto 2 | 1 | 0,00083 |
| L1 accidente | 2400 | accidente 5 | 3 | 0,00125 |
| L3 hurto | 800 | hurto 2 | 1 | 0,00125 |
| L3 accidente | 1600 | accidente 5 | 3 | 0,001875 |
| L3 incendio | 4000 | incendio 3 | 5 | 0,00125 |
| L4 hurto | 500 | hurtos 1, 2, 4 | 3 | 0,006 |
| L4 accidente | 1000 | accidente 5 | 3 | 0,003 |
| L4 incendio | 2500 | incendio 3 | 5 | 0,002 |

L2 no cubre nada. El único incendio (peso 5) solo se cubre desde L3 o desde L4.

Traza de `propia` (`py main.py parte2 instancias_malas/propia propia`):

1. Restante 5000. La mejor razón es `L4 hurto` (3 / 500 = 0,006). La elige.
2. Restante 4500. L4 ya está ocupado. Quedan `L3 accidente` (0,001875), `L3 incendio`
   (5 / 4000 = 0,00125) y `L1 accidente` (0,00125). Gana `L3 accidente`.
3. Restante 2900. Ya no queda ningún lote que cubra el incendio. Resultado: valor **6**,
   costo 2100.

El óptimo (fuerza bruta y `py main.py parte3 instancias_malas/propia`) es `L3 accidente`
+ `L4 incendio`: valor **8**, costo 4100.

La decisión que la desvía es el paso 2: entre la estación de tránsito de L3 y la de
bomberos de L3, la razón prefiere la más barata y eficiente (0,001875 > 0,00125), y con
eso ocupa el último lote desde el que se llegaba al incendio. Habría bastado con elegir
`L3 incendio` en el paso 2 (valor 3 + 5 = 8, costo 4500). La razón valor/costo no ve que
un lote es un recurso escaso: una estación barata en el lote equivocado bloquea la
estación que más vale.
