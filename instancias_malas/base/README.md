# Caso negativo de `base`

Tres nodos, tres lotes y presupuesto 7000. Los costos, radios y pesos son los
**oficiales** del enunciado (CAI 1000 / 1000 m / peso 1; tránsito 2000 / 2000 m /
peso 3; bomberos 5000 / 3000 m / peso 5). Calles de una sola vía: 0→1 (1000 m) y
0→2 (600 m).

Estaciones que aportan algo (costo = costo_base × factor_zona):

| Estación | Costo | Cubre | Valor |
|---|---|---|---|
| L1 hurto | 1200 | hurtos 4, 5, 7, 9 | 4 |
| L1 incendio | 6000 | incendio 6 | 5 |
| L2 hurto | 1500 | hurtos 1, 3, 4, 5, 7, 8, 9, 11 | 8 |
| L2 accidente | 3000 | accidentes 2 y 10 | 6 |
| L3 hurto | 1500 | hurtos 1, 3, 8 | 3 |
| L3 accidente | 3000 | accidente 2 | 3 |

Traza de la base (`py main.py parte2 instancias_malas/base base`):

1. Restante 7000. El mayor valor nuevo es `L2 hurto` (8 > 6 > 5 > 4 > 3). La elige.
2. Restante 5500. L2 ya está ocupado, así que `L2 accidente` ya no se puede. `L1 hurto`
   y `L3 hurto` no agregan nada (sus hurtos ya están cubiertos) y `L1 incendio` (6000)
   no cabe. Solo queda `L3 accidente` (valor nuevo 3). La elige.
3. Restante 2500. Nada aporta. Resultado: valor **11**, costo 4500.

El óptimo (fuerza bruta y `py main.py parte3 instancias_malas/base`) es `L1 hurto` +
`L2 accidente` + `L3 hurto`: valor **13**, costo 5700.

La decisión que la desvía es el paso 1: `L2 hurto` es la estación que más vale por sí
sola, pero ocupa el lote L2, el único cuya estación de tránsito cubre los DOS accidentes
(peso 3 cada uno). Los hurtos de L2 se pueden cubrir casi todos desde L1 y L3. La base
solo mira el valor de la estación siguiente, no lo que ese lote impide construir después.
