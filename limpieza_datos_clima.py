# limpieza_datos_clima.py
"""
Módulo para la limpieza y procesamiento de datos meteorológicos de Madrid.

Este script contiene funciones para transformar, limpiar y normalizar datos
meteorológicos obtenidos de la API de AEMET. Realiza tareas como traducción
de términos, detección de valores atípicos, unificación de formatos y
eliminación de duplicados.

Autor: Leonardo Leal Vivas
Fecha: Abril 2025
"""

import pandas as pd
import numpy as np


def traducir_direccion_viento(df):
    """
    Traduce la dirección del viento de abreviaturas en español a inglés y añade valores en grados.

    Args:
        df (pandas.DataFrame): DataFrame con la columna 'wind_direction' que contiene
                               abreviaturas de direcciones (N, NE, S, etc.)

    Returns:
        pandas.DataFrame: DataFrame con dos columnas adicionales:
                         - 'wind_direction_completo': Nombre completo en inglés
                         - 'wind_direction_grados': Valor en grados (0-360)
    """
    # Diccionario para traducir abreviaturas a nombres completos en inglés
    wind_direction_completo = {
        "N": "north", "NE": "northeast", "E": "east", "SE": "southeast",
        "S": "south", "SO": "southwest", "O": "west", "NO": "northwest", "C": "calm"
    }

    # Diccionario para convertir abreviaturas a grados (donde 0° = Norte, 90° = Este, etc.)
    wind_direction_grados = {
        "N": 0, "NE": 45, "E": 90, "SE": 135, "S": 180,
        "SO": 225, "O": 270, "NO": 315, "C": np.nan  # Calma no tiene dirección
    }

    # Crear copia para no modificar el DataFrame original
    df_result = df.copy()

    # Aplicar las traducciones usando el método map
    df_result["wind_direction_completo"] = df["wind_direction"].map(wind_direction_completo)
    df_result["wind_direction_grados"] = df["wind_direction"].map(wind_direction_grados)

    return df_result


def traducir_condicion_cielo(df):
    """
    Traduce la condición del cielo de español a inglés.

    Args:
        df (pandas.DataFrame): DataFrame con la columna 'sky_condition' que contiene
                              descripciones en español

    Returns:
        pandas.DataFrame: DataFrame con una columna adicional 'sky_condition_ingles'
                         que contiene las traducciones
    """
    # Diccionario de traducción de condiciones del cielo
    sky_condition_ingles = {
        'Nubes altas': 'high clouds',
        'Cubierto': 'overcast',
        'Poco nuboso': 'few clouds',
        'Nuboso': 'cloudy',
        'Muy nuboso': 'very cloudy',
        'Despejado': 'clear',
        'Cubierto con lluvia escasa': 'overcast with light rain',
        'Cubierto con lluvia': 'overcast with rain',
        'Cubierto con tormenta y lluvia escasa': 'overcast with thunderstorm and light rain'
    }

    # Crear copia para no modificar el DataFrame original
    df_result = df.copy()

    # Aplicar traducción
    df_result["sky_condition_ingles"] = df["sky_condition"].map(sky_condition_ingles)

    return df_result


def eliminar_columnas_innecesarias(df, columnas_a_eliminar):
    """
    Elimina columnas que no son necesarias para el análisis.

    Args:
        df (pandas.DataFrame): DataFrame de entrada
        columnas_a_eliminar (list): Lista con los nombres de las columnas a eliminar

    Returns:
        pandas.DataFrame: DataFrame sin las columnas especificadas
    """
    # Crear copia para no modificar el DataFrame original
    df_result = df.copy()

    # Eliminar columnas innecesarias
    df_result.drop(columnas_a_eliminar, axis=1, inplace=True)

    return df_result


def convertir_tipos_datos(df):
    """
    Convierte los tipos de datos para asegurar consistencia en el análisis.

    Conversiones realizadas:
    - 'date': a formato datetime
    - 'hour': a formato de hora 'HH:00'
    - Valores numéricos ('temperature', 'humidity', 'wind_speed', 'wind_direction_grados'): a float

    Args:
        df (pandas.DataFrame): DataFrame con columnas a convertir

    Returns:
        pandas.DataFrame: DataFrame con los tipos de datos convertidos
    """
    # Crear copia para no modificar el DataFrame original
    df_result = df.copy()

    # Convertir fecha a formato datetime
    df_result["date"] = pd.to_datetime(df_result["date"], dayfirst=False)

    # Convertir hora a formato 'HH:00'
    df_result["hour"] = df_result["hour"].apply(lambda x: f"{x:02d}:00")

    # Convertir valores numéricos a float
    df_result["temperature"] = df_result["temperature"].astype(float)
    df_result["humidity"] = df_result["humidity"].astype(float)
    df_result["wind_speed"] = df_result["wind_speed"].astype(float)

    # Convertir grados de dirección del viento si existe la columna
    if "wind_direction_grados" in df_result.columns:
        df_result["wind_direction_grados"] = df_result["wind_direction_grados"].astype(float)

    return df_result


def unificar_fecha_hora(df):
    """
    Unifica las columnas de fecha y hora en una sola columna datetime.

    Args:
        df (pandas.DataFrame): DataFrame con columnas 'date' y 'hour'

    Returns:
        pandas.DataFrame: DataFrame con una nueva columna 'datetime'
    """
    # Crear copia para no modificar el DataFrame original
    df_result = df.copy()

    # Combinar fecha y hora en un solo campo datetime
    df_result["datetime"] = pd.to_datetime(
        df_result["date"].astype(str) + " " + df_result["hour"].astype(str)
    )

    return df_result


def normalizar_nombres_columnas(df, renombres=None):
    """
    Normaliza y renombra las columnas según sea necesario.

    Args:
        df (pandas.DataFrame): DataFrame con columnas a normalizar
        renombres (dict, opcional): Diccionario con {nombre_actual: nuevo_nombre}

    Returns:
        pandas.DataFrame: DataFrame con nombres de columnas normalizados
    """
    # Crear copia para no modificar el DataFrame original
    df_result = df.copy()

    # Convertir todos los nombres de columnas a minúsculas
    df_result.columns = df_result.columns.str.lower()

    # Aplicar renombres específicos si se proporcionan
    if renombres:
        df_result.rename(columns=renombres, inplace=True)

    return df_result


def marcar_estado_viento(df):
    """
    Marca el estado del viento como 'calm' (calma) o 'with wind' (con viento).

    El estado se determina basándose en si hay un valor en la columna 'wind_direction_degrees'.
    Valores NaN indican calma.

    Args:
        df (pandas.DataFrame): DataFrame con columna 'wind_direction_degrees'

    Returns:
        pandas.DataFrame: DataFrame con una nueva columna 'wind_status'
    """
    # Crear copia para no modificar el DataFrame original
    df_result = df.copy()

    # Marcar estado del viento basado en sí hay dirección del viento o no
    df_result["wind_status"] = df_result["wind_direction_degrees"].apply(
        lambda x: "calm" if pd.isna(x) else "with wind"
    )

    return df_result


def detectar_outliers(df):
    """
    Detecta valores atípicos en los datos meteorológicos.

    Se consideran outliers:
    - Temperaturas < -10°C o > 50°C
    - Humedad < 0% o > 100%
    - Velocidad del viento < 0 km/h

    Args:
        df (pandas.DataFrame): DataFrame con datos meteorológicos

    Returns:
        pandas.DataFrame: Subconjunto del DataFrame que contiene solo las filas con outliers
    """
    # Filtrar filas con valores atípicos
    return df[
        (df["temperature"] < -10) | (df["temperature"] > 50) |
        (df["humidity"] < 0) | (df["humidity"] > 100) |
        (df["wind_speed"] < 0)
        ]


def verificar_duplicados(df):
    """
    Verifica y elimina filas duplicadas.

    Args:
        df (pandas.DataFrame): DataFrame a verificar

    Returns:
        tuple: (DataFrame sin duplicados, número de duplicados encontrados)
    """
    # Crear copia para no modificar el DataFrame original
    df_result = df.copy()

    # Identificar duplicados
    duplicados = df_result.duplicated()

    # Eliminar duplicados y devolver el resultado junto con el conteo
    return df_result.drop_duplicates(), duplicados.sum()


def proceso_completo_limpieza(df):
    """
    Realiza el proceso completo de limpieza de datos meteorológicos.

    Este proceso incluye:
    1. Traducción de dirección del viento y condición del cielo
    2. Eliminación de columnas innecesarias
    3. Conversión de tipos de datos
    4. Unificación de fecha y hora
    5. Normalización de nombres de columnas
    6. Marcación del estado del viento
    7. Eliminación de duplicados

    Args:
        df (pandas.DataFrame): DataFrame con datos meteorológicos crudos

    Returns:
        pandas.DataFrame: DataFrame limpio y procesado listo para análisis
    """
    # 1. Traducir dirección del viento
    df = traducir_direccion_viento(df)

    # 2. Traducir condición del cielo
    df = traducir_condicion_cielo(df)

    # 3. Eliminar columnas originales que ya no son necesarias
    df = eliminar_columnas_innecesarias(df, ["wind_direction", "sky_condition", "timestamp"])

    # 4. Convertir tipos de datos para asegurar consistencia
    df = convertir_tipos_datos(df)

    # 5. Unificar fecha y hora en un solo campo datetime
    df = unificar_fecha_hora(df)

    # 6. Eliminar columnas fecha y hora originales (ya unificadas).
    df = eliminar_columnas_innecesarias(df, ["date", "hour"])

    # 7. Reordenar columnas (poner datetime primero para mejor visualización)
    columna_datetime = df.pop("datetime")
    df.insert(0, "datetime", columna_datetime)

    # 8. Normalizar nombres de columnas para consistencia
    renombres = {
        'sky_condition_ingles': 'sky_condition',  # Usar versión en inglés como principal
        'wind_direction_grados': 'wind_direction_degrees',  # Nombre más descriptivo
        'wind_direction_completo': 'wind_direction'  # Usar versión completa como principal
    }
    df = normalizar_nombres_columnas(df, renombres)

    # 9. Añadir marcador de estado del viento
    df = marcar_estado_viento(df)

    # 10. Eliminar duplicados para evitar sesgo en análisis
    df, _ = verificar_duplicados(df)

    return df


# Si se ejecuta el script directamente
if __name__ == "__main__":
    print("Módulo de limpieza de datos meteorológicos")
    print("Este script está diseñado para ser importado y usar sus funciones")
    print("Ejemplo de uso:")
    print("  from limpieza_datos_clima import proceso_completo_limpieza")
    print("  datos_limpios = proceso_completo_limpieza(datos_crudos)")
