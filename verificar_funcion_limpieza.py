# verificar_funcion_limpieza.py

"""
Módulo para verificar las funciones del script refactorizado de limpieza del archivo CSV
obtenido por el módulo de recolección de datos.

Este script verifica que el proceso de limpieza completo realiza su función correctamente
y muestra en consola algunas estadísticas de los datos procesados.

Prerrequisitos:
1. Haber ejecutado previamente madrid_weather_collector.py para generar el archivo CSV crudo
2. Tener el módulo limpieza_datos_clima.py en el mismo directorio o en Python path
3. Tener una carpeta 'data' donde se encuentran los datos recolectados

Uso:
    python verificar_funcion_limpieza.py

Salida:
    - Información sobre el proceso de limpieza
    - Estadísticas básicas de los datos limpios
    - Archivo CSV con los datos limpios en ./data/madrid_weather_clean.csv
"""

import pandas as pd
from limpieza_datos_clima import proceso_completo_limpieza

# Cargar datos recolectados
print("Cargando datos...")
ruta_datos_crudos = "./data/madrid_weather_forecast.csv"  # Ajusta según la ubicación real del archivo de prueba o a limpiar.
datos_crudos = pd.read_csv(ruta_datos_crudos)
print(f"Datos cargados: {len(datos_crudos)} registros")

# Aplicar proceso de limpieza
print("Limpiando datos...")
datos_limpios = proceso_completo_limpieza(datos_crudos)
print(f"Limpieza completada: {len(datos_limpios)} registros limpios")

# Guardar datos limpios
ruta_datos_limpios = "./data/madrid_weather_clean.csv"
datos_limpios.to_csv(ruta_datos_limpios, index=False)
print(f"Datos limpios guardados en {ruta_datos_limpios}")

# Mostrar algunas estadísticas para verificar
print("\nEstadísticas de los datos limpios:")
print(f"Rango de fechas: {datos_limpios['datetime'].min()} a {datos_limpios['datetime'].max()}")
print(f"Temperatura media: {datos_limpios['temperature'].mean():.1f}°C")
print(f"Humedad media: {datos_limpios['humidity'].mean():.1f}%")
print(f"Velocidad media del viento: {datos_limpios['wind_speed'].mean():.1f} km/h")

# Contar estados del viento
print("\nEstados del viento:")
print(datos_limpios['wind_status'].value_counts())

# Contar condiciones del cielo
print("\nCondiciones del cielo más comunes:")
print(datos_limpios['sky_condition'].value_counts().head(3))

# Mensaje del flujo completo del proyecto
print("\n--- FLUJO COMPLETO DEL PROYECTO ---")
print("1. Ejecutar madrid_weather_collector.py para obtener datos de la API de AEMET")
print("2. Ejecutar verificar_funcion_limpieza.py (este script) para procesar los datos")
print("3. Los datos limpios quedan disponibles para análisis en ./data/madrid_weather_clean.csv")