#!/usr/bin/env bash
set -euo pipefail

entrada="results/diagnostico_bruto.txt"
salida="results/activaciones.csv"

if ! grep -q '^TRACE,' "$entrada"; then
    printf 'ERROR: no hay filas TRACE en %s\n' "$entrada" >&2
    exit 1
fi

{
    printf '%s\n' \
        'reactor,reaction,periodo_nominal_ns,tiempo_logico_ns,microstep,inicio_fisico_ns,fin_fisico_ns,duracion_ns'

    grep '^TRACE,' "$entrada" | cut -d, -f2-
} > "$salida"

printf 'CSV generado. Cantidad de lineas:\n'
wc -l "$salida"
