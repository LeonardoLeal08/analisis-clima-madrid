# request_api.py
"""
Script para probar la conexión con la API de AEMET (Agencia Estatal de Meteorología española)
y obtener datos meteorológicos diarios para Madrid.

Este script sirve como prueba inicial para verificar que la clave API funciona correctamente
y que podemos acceder a los datos meteorológicos básicos.
"""

import requests
from config import API_KEY

# Clave de acceso a la API de AEMET
API_KEY

# URL base para todas las peticiones a la API de AEMET
URL_BASE = "https://opendata.aemet.es/opendata/api"


def obtener_datos_meteorologicos():
    """
    Realiza una solicitud a la API de AEMET para obtener la predicción meteorológica diaria
    para Madrid (código INE: 28079).

    La API de AEMET funciona en dos pasos:
    1. Primero se obtiene una URL con los datos reales
    2. Luego se hace una segunda petición a esa URL para obtener los datos en formato JSON

    Returns:
        dict/None: Datos meteorológicos en formato JSON o None si ocurre un error
    """
    # Endpoint específico para la predicción diaria en Madrid (código INE: 28079)
    endpoint = f"{URL_BASE}/prediccion/especifica/municipio/diaria/28079"
    params = {"api_key": API_KEY}

    # Primer paso: hacer la petición inicial a la API para obtener la URL de los datos
    respuesta = requests.get(endpoint, params=params)

    # Verificar si la primera petición fue exitosa (código 200)
    if respuesta.status_code == 200:
        datos = respuesta.json()
        if "datos" in datos:
            # Extraer la URL donde están los datos reales
            url_datos = datos["datos"]

            # Segundo paso: obtener los datos meteorológicos de la URL proporcionada
            respuesta_datos = requests.get(url_datos)
            if respuesta_datos.status_code == 200:
                return respuesta_datos.json()
            else:
                print(f"Error al obtener los datos: {respuesta_datos.status_code}")
        else:
            print("No se encontró la clave 'datos' en la respuesta.")
    else:
        print(f"Error en la solicitud inicial: {respuesta.status_code} - {respuesta.text}")

    # En caso de error en cualquier paso, devolver None
    return None


# Ejecución principal del script
if __name__ == "__main__":
    print("Obteniendo datos meteorológicos de Madrid...")
    datos_madrid = obtener_datos_meteorologicos()

    if datos_madrid:
        print("Datos obtenidos correctamente:")
        print(datos_madrid)
    else:
        print("No se pudieron obtener los datos meteorológicos.")