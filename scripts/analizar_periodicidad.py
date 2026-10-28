import csv
import statistics
from collections import defaultdict
from pathlib import Path

carpeta = Path("results")
entrada = carpeta / "activaciones.csv"

columnas = [
    "reactor", "reaction", "periodo_nominal_ns",
    "tiempo_logico_ns", "microstep",
    "inicio_fisico_ns", "fin_fisico_ns", "duracion_ns"
]

filas = []
omitidas = 0

with entrada.open(newline="", encoding="utf-8", errors="replace") as archivo:
    for campos in csv.reader(archivo):
        if len(campos) != 8:
            omitidas += 1
            continue

        try:
            numeros = [int(valor) for valor in campos[2:]]
        except ValueError:
            omitidas += 1
            continue

        filas.append(dict(zip(columnas, campos[:2] + numeros)))

if not filas:
    raise SystemExit("No se encontraron filas de datos validas.")

with (carpeta / "activaciones_limpias.csv").open(
    "w", newline="", encoding="utf-8"
) as archivo:
    escritor = csv.DictWriter(archivo, fieldnames=columnas)
    escritor.writeheader()
    escritor.writerows(filas)

grupos = defaultdict(list)

for fila in filas:
    if fila["periodo_nominal_ns"] > 0:
        grupos[(fila["reactor"], fila["reaction"])].append(fila)

resumen = []
intervalos = []
muestras = []

for (reactor, reaccion), registros in sorted(grupos.items()):
    registros.sort(
        key=lambda f: (f["tiempo_logico_ns"], f["microstep"])
    )

    periodos = {f["periodo_nominal_ns"] for f in registros}
    if len(periodos) != 1:
        raise SystemExit(f"Periodos inconsistentes en {reactor}/{reaccion}")

    periodo = periodos.pop()

    if len(registros) < 2:
        raise SystemExit(f"Faltan activaciones en {reactor}/{reaccion}")

    fisicos = []
    logicos = []
    jitters = []

    for indice, actual in enumerate(registros):
        detalle = dict(actual)
        detalle["activacion"] = indice + 1

        if indice == 0:
            detalle.update({
                "intervalo_logico_ns": "",
                "intervalo_fisico_ns": "",
                "jitter_ns": ""
            })
        else:
            anterior = registros[indice - 1]

            dl = (
                actual["tiempo_logico_ns"]
                - anterior["tiempo_logico_ns"]
            )
            dp = (
                actual["inicio_fisico_ns"]
                - anterior["inicio_fisico_ns"]
            )
            jitter = dp - periodo

            logicos.append(dl)
            fisicos.append(dp)
            jitters.append(jitter)

            detalle.update({
                "intervalo_logico_ns": dl,
                "intervalo_fisico_ns": dp,
                "jitter_ns": jitter
            })

            intervalos.append(detalle)

        if indice < 21:
            muestras.append(detalle)

    duraciones = [f["duracion_ns"] for f in registros]

    resumen.append({
        "reactor": reactor,
        "reaction": reaccion,
        "activaciones": len(registros),
        "intervalos": len(fisicos),
        "periodo_nominal_ms": periodo / 1e6,
        "intervalos_logicos_incorrectos":
            sum(valor != periodo for valor in logicos),
        "intervalos_fisicos_negativos":
            sum(valor < 0 for valor in fisicos),
        "periodo_fisico_medio_ms":
            statistics.mean(fisicos) / 1e6,
        "periodo_fisico_min_ms": min(fisicos) / 1e6,
        "periodo_fisico_max_ms": max(fisicos) / 1e6,
        "desviacion_poblacional_ms":
            statistics.pstdev(fisicos) / 1e6,
        "jitter_medio_ms": statistics.mean(jitters) / 1e6,
        "jitter_min_ms": min(jitters) / 1e6,
        "jitter_max_ms": max(jitters) / 1e6,
        "jitter_max_absoluto_ms":
            max(abs(valor) for valor in jitters) / 1e6,
        "jitter_pico_pico_ms":
            (max(jitters) - min(jitters)) / 1e6,
        "duracion_media_us":
            statistics.mean(duraciones) / 1e3,
        "duracion_max_us": max(duraciones) / 1e3
    })

def guardar(nombre, datos):
    with (carpeta / nombre).open(
        "w", newline="", encoding="utf-8"
    ) as archivo:
        escritor = csv.DictWriter(
            archivo, fieldnames=list(datos[0].keys())
        )
        escritor.writeheader()
        escritor.writerows(datos)

guardar("resumen_periodicidad.csv", resumen)
guardar("intervalos_periodicos.csv", intervalos)
guardar("primeras_21_activaciones.csv", muestras)

print(f"Filas de datos validas: {len(filas)}")
print(f"Filas omitidas, incluido el encabezado: {omitidas}")
print()

for fila in resumen:
    print(
        f"{fila['reactor']}: "
        f"N={fila['activaciones']}, "
        f"T={fila['periodo_nominal_ms']:.3f} ms, "
        f"media={fila['periodo_fisico_medio_ms']:.6f} ms, "
        f"min={fila['periodo_fisico_min_ms']:.6f} ms, "
        f"max={fila['periodo_fisico_max_ms']:.6f} ms, "
        f"desv={fila['desviacion_poblacional_ms']:.6f} ms, "
        f"errores_logicos={fila['intervalos_logicos_incorrectos']}"
    )
