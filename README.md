# Práctica 4 — Control longitudinal de una aeronave con Lingua Franca

Universidad de Antioquia · Departamento de Ingeniería Electrónica  
Sistemas de Tiempo Real · Semestre 2026-2
Mauricio Aguas - Manuel Salazar

Simulación didáctica de un lazo de control de velocidad longitudinal implementado en Lingua Franca (LF), con target C. El proyecto combina módulos con diferentes períodos, comunicación mediante puertos, un controlador proporcional saturado e instrumentación temporal.

> Este modelo no es un controlador aeronáutico real. No implementa control de altitud, velocidad vertical, sustentación ni dinámica detallada del motor.

## 1. Objetivos

- Implementar cinco reactors conectados mediante puertos tipados.
- Separar la recepción de eventos del cálculo periódico.
- Aplicar un controlador proporcional con empuje limitado a [0, 1].
- Evaluar un cambio de referencia y un sesgo temporal del sensor.
- Comparar las ganancias proporcionales 0.05, 0.2 y 0.5 s/m.
- Distinguir tiempo lógico, microstep, intervalo físico y duración observada de las reacciones.

## 2. Arquitectura

```text
SpeedReference ──referencia──► SpeedController ──empuje──► AircraftDynamics
                                    ▲                          │
                                    │                          │ velocidad
                                    └──medicion── AirDataSensor ◄┘

FlightMonitor recibe referencia, velocidad, medición, error, empuje y sesgo.
```

| Reactor | Función | Período | Offset periódico |
|---|---|---:|---:|
| `SpeedReference` | Publicar la referencia | 100 ms | 0 ms |
| `AirDataSensor` | Publicar la velocidad medida | 5 ms | 0 ms |
| `SpeedController` | Calcular error y empuje | 10 ms | 0 ms |
| `AircraftDynamics` | Integrar la dinámica longitudinal | 10 ms | 10 ms |
| `FlightMonitor` | Registrar las variables del lazo | 100 ms | 0 ms |

La planta publica su estado inicial mediante una reacción de inicio, sin integrarlo en tiempo cero. El sensor incluye dos timers adicionales de una sola activación para iniciar y retirar el sesgo.

El diagrama de composición exportado desde las herramientas de LF debe conservarse entre las evidencias del proyecto.

## 3. Modelo matemático

### Medición y error

```text
v_med[k] = v[k] + d_v[k]
e_v[k]   = v_ref[k] - v_med[k]
```

### Control proporcional

```text
u_T[k] = min(1, max(0, Kp * e_v[k]))
```

### Planta discreta

```text
v[k+1] = v[k] + Ts * (a_T * u_T[k] - a_D * v[k])
```

| Parámetro | Valor base | Unidad |
|---|---:|---|
| Velocidad inicial | 80 | m/s |
| `Ts` | 0.01 | s |
| `a_T` | 20 | m/s² |
| `a_D` | 0.1 | s⁻¹ |
| `Kp` | 0.2 | s/m |
| Empuje | [0, 1] | Adimensional |
| Duración lógica | 20 | s |

Los coeficientes son didácticos, no parámetros identificados de una aeronave real.

## 4. Escenario experimental

### Referencia

- Desde 0 hasta antes de 10 s: 100 m/s.
- Desde 10 s: 110 m/s.

### Perturbación de medición

- Durante `5 <= t < 6 s`: `d_v = -5 m/s`.
- Fuera de ese intervalo: `d_v = 0 m/s`.

La perturbación dura 1 segundo, equivalente a 200 publicaciones del sensor. No corresponde al ejemplo breve de diez muestras. Se escogió este intervalo para observar el transitorio con el monitor de 100 ms.

El sesgo modifica la medición, no directamente el estado de la planta. La velocidad real puede cambiar posteriormente por la respuesta del controlador.

## 5. Tratamiento multirate y causalidad

Las entradas se almacenan en el estado privado de cada reactor. El cálculo periódico utiliza el último dato recibido; no se implementa una cola ni un promedio de muestras.

El sensor publica cada 5 ms, pero el controlador calcula cada 10 ms. Recibir una medición no dispara un cálculo adicional de empuje.

En `AircraftDynamics`, las reacciones que publican la velocidad se declaran antes de la reacción que recibe el empuje. La secuencia de una actualización es:

1. La planta integra usando el empuje previamente almacenado y publica la velocidad.
2. El sensor recibe la velocidad y publica la medición en su activación periódica.
3. El controlador recibe la medición y calcula el comando en su activación periódica.
4. La planta almacena el nuevo comando para la siguiente integración.

No se debe reordenar arbitrariamente esas reacciones: su orden forma parte del diseño causal.

## 6. Organización del proyecto

La siguiente es la organización propuesta para la entrega; algunas carpetas pueden estar pendientes de consolidación:

```text
Practica4_LF/
├── README.md
├── .gitignore
├── Makefile                     # Pendiente de incorporar/verificar
├── src/
│   └── AircraftController.lf
├── examples/                    # Pruebas incrementales de aprendizaje
├── scripts/                     # Procesamiento de registros
├── results/
│   ├── kp_0p05/
│   ├── kp_0p2/
│   └── kp_0p5/
├── figures/                     # Diagramas y gráficas
└── report/                      # Fuentes LaTeX e informe
```

Los comandos siguientes se ejecutan desde la raíz del proyecto. Si los scripts siguen en la raíz, se ejecutan allí; si se trasladan a `scripts/`, se ajusta la ruta del comando.

## 7. Entorno y dependencias

El desarrollo se realizó en Ubuntu mediante WSL en Windows, utilizando el compilador de Lingua Franca con target C.

Herramientas utilizadas o necesarias para reproducir el flujo:

- Compilador LF: `lfc`.
- Compilador C: GCC.
- CMake.
- Java compatible con la versión instalada de LF; se utilizó Java 17 en las instrucciones de preparación.
- Python 3 para el procesamiento de registros.
- Git para control de versiones.

La instalación del compilador LF debe seguir su documentación oficial. Este repositorio no incluye las herramientas instaladas ni el entorno WSL.

Para registrar las versiones locales:

```bash
mkdir -p results
{
    cat /etc/os-release
    uname -r
    lfc --version
    gcc --version
    cmake --version
    java -version
    python3 --version
    git --version
} > results/entorno.txt 2>&1
```

No se fijan aquí versiones que todavía no se hayan registrado experimentalmente.

## 8. Compilación y ejecución

```bash
lfc src/AircraftController.lf
./bin/AircraftController
```

Para guardar por separado las variables del control y el diagnóstico:

```bash
mkdir -p results/kp_0p2

lfc src/AircraftController.lf && \
cp src/AircraftController.lf results/kp_0p2/codigo_usado.lf && \
./bin/AircraftController \
    > results/kp_0p2/control.txt \
    2> results/kp_0p2/diagnostico_bruto.txt
```

El operador `&&` evita ejecutar un binario anterior si falla la compilación. Estos comandos sobrescriben los archivos de destino: para conservar repeticiones deben usarse carpetas diferentes.

No utilizar ejecución rápida para estudiar intervalos físicos frente a períodos nominales.

## 9. Comparación de ganancias

Editar únicamente la instancia del controlador en el `main reactor`:

```lf
controlador = new SpeedController(kp = 0.2)
```

Repetir con `kp = 0.05`, `kp = 0.2` y `kp = 0.5`, compilando después de cada cambio. Guardar cada corrida y una copia de su fuente en la carpeta correspondiente.

Después de los experimentos, devolver la instancia a `kp = 0.2` y recompilar para mantener la configuración base.

### Resultados registrados a los 20 segundos

Referencia final: 110 m/s.

| Kp (s/m) | Velocidad (m/s) | Error (m/s) | Empuje |
|---:|---:|---:|---:|
| 0.05 | 99.999858 | 10.000142 | 0.500007 |
| 0.20 | 107.317073 | 2.682927 | 0.536585 |
| 0.50 | 108.910891 | 1.089109 | 0.544554 |

El aumento de ganancia redujo el error final registrado. También aumentó el número de muestras del monitor con comando saturado: se observaron 1, 25 y 32 muestras con empuje 1 para las ganancias 0.05, 0.2 y 0.5, respectivamente.

Estos conteos no son duraciones exactas de saturación: el monitor publica cada 100 ms y el controlador calcula cada 10 ms.

El controlador proporcional conserva error estacionario. Sin sesgo y en régimen no saturado:

```text
v_eq = [a_T * Kp / (a_D + a_T * Kp)] * v_ref
```

No se declara una ganancia óptima. La selección base de 0.2 s/m es un compromiso didáctico entre seguimiento y uso de saturación en los ensayos realizados.

## 10. Instrumentación temporal

Las macros `DIAG_BEGIN()` y `DIAG_END(...)` registran una fila por reacción instrumentada en la salida de error estándar:

```text
TRACE,reactor,reaction,periodo_nominal_ns,tiempo_logico_ns,microstep,inicio_fisico_ns,fin_fisico_ns,duracion_ns
```

`TRACE` es un prefijo de identificación; no es una columna adicional en el CSV limpio. Un período nominal de cero identifica una reacción por evento o de inicio y no una duración de ejecución nula.

La conversión y el análisis se realizan mediante `procesar_activaciones.sh` y `analizar_periodicidad.py`, desarrollados durante la práctica. Los scripts originales esperan archivos directamente en `results/`; para analizar otra corrida deben copiarse sus registros a las rutas esperadas o adaptar esas rutas sin mezclar experimentos.

### Definiciones

```text
Intervalo lógico = tiempo_logico[i] - tiempo_logico[i-1]
Intervalo físico = inicio_fisico[i] - inicio_fisico[i-1]
Jitter           = intervalo_fisico - periodo_nominal
Duración medida  = fin_fisico - inicio_fisico
```

Las diferencias de marcas temporales se calculan como enteros antes de convertir unidades, para conservar precisión.

### Resultado de la corrida temporal analizada con Kp = 0.2

| Reactor | Activaciones periódicas | Intervalos | Media física (ms) | Máximo absoluto del jitter (µs) |
|---|---:|---:|---:|---:|
| AirDataSensor | 4001 | 4000 | 4.999998 | 401.152 |
| AircraftDynamics | 2000 | 1999 | 9.999993 | 342.358 |
| SpeedController | 2001 | 2000 | 9.999996 | 337.829 |
| SpeedReference | 201 | 200 | 100.000001 | 67.407 |
| FlightMonitor | 201 | 200 | 99.999879 | 145.551 |

Todos los intervalos lógicos analizados coincidieron con sus períodos nominales. Estos números corresponden a una corrida concreta; los intervalos físicos pueden cambiar entre ejecuciones y equipos.

## 11. Limitaciones de los resultados

- Una media física cercana al período nominal no implica ausencia de jitter.
- El jitter de intervalo no es lo mismo que el retraso de una activación respecto a su tag.
- Las marcas de inicio se toman dentro del cuerpo de la reacción, no al comienzo del trabajo interno del scheduler.
- La duración medida no incluye la escritura de la propia fila `TRACE`; esa escritura sí puede afectar activaciones posteriores.
- El cuerpo del monitor incluye sus operaciones de impresión.
- Los máximos observados no constituyen una demostración de WCET.
- La corrida no demuestra cumplimiento de deadlines bajo todas las condiciones.
- Los registros de texto introducen sobrecarga y las medidas se obtuvieron en un entorno WSL, no en Linux nativo dedicado.
- El monitor de 100 ms no revela todos los cambios de los módulos de 5 y 10 ms.


