# madrid_weather_collector.py
"""
Recolector de Datos Meteorológicos de Madrid

Este script recopila datos meteorológicos horarios para Madrid desde la API de AEMET
(Agencia Estatal de Meteorología española) y los almacena en formato CSV para su
posterior análisis.

Características:
- Recolección automática de datos en intervalos configurables
- Actualización inteligente del CSV evitando duplicados
- Manejo de errores y reintentos automáticos
- Almacenamiento en ubicación configurable

Autor: [Tu Nombre]
Fecha: Abril 2025
"""

import json
import pandas as pd
import requests
from datetime import datetime, timedelta
import time
import os
from pathlib import Path
import logging
from config import API_KEY

class WeatherDataCollector:
    """
    Clase para recolectar, procesar y almacenar datos meteorológicos de AEMET
    para un municipio específico (por defecto Madrid).
    """

    def __init__(self, api_key, municipality_code="28079", data_dir=None):
        """
        Inicializa el recolector de datos meteorológicos.

        Args:
            api_key (str): Clave de API para acceder a los servicios de AEMET
            municipality_code (str): Código INE del municipio (por defecto: 28079 - Madrid)
            data_dir (str, opcional): Directorio donde se guardarán los datos. Si es None,
                                     se usará una carpeta 'weather_data' en el directorio del proyecto
        """
        self.api_key = api_key
        self.municipality_code = municipality_code

        # Configurar el sistema de logging
        self._setup_logging()

        # Configurar el directorio de datos
        self._setup_data_directory(data_dir)

        # Configurar la URL base y los headers para las solicitudes API
        self.base_url = "https://opendata.aemet.es/opendata/api/prediccion/especifica/municipio/horaria/"
        self.headers = {
            'api_key': self.api_key
        }

        self.logger.info(f"Recolector inicializado para el municipio {municipality_code}")
        self.logger.info(f"Los datos se guardarán en: {self.csv_path}")

    def _setup_logging(self):
        """Configura el sistema de logging para la clase"""
        # Crear logger
        self.logger = logging.getLogger('WeatherCollector')
        self.logger.setLevel(logging.INFO)

        # Crear handler para la consola
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)

        # Crear formato para los logs
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        console_handler.setFormatter(formatter)

        # Añadir handler al logger
        self.logger.addHandler(console_handler)

    def _setup_data_directory(self, data_dir=None):
        """
        Configura el directorio para almacenar los datos.

        Args:
            data_dir (str, opcional): Directorio específico donde guardar los datos
        """
        # Si no se especifica un directorio, usar el directorio del proyecto actual
        if data_dir is None:
            project_dir = os.path.dirname(os.path.abspath(__file__))
            self.data_dir = os.path.join(project_dir, 'data')
        else:
            self.data_dir = data_dir

        self.csv_path = os.path.join(self.data_dir, 'madrid_weather_forecast.csv')

        # Crear directorio si no existe
        try:
            os.makedirs(self.data_dir, exist_ok=True)
            self.logger.info(f"Directorio de datos: {self.data_dir}")
        except Exception as e:
            self.logger.error(f"Error al crear directorio: {e}")
            # Usar directorio actual como respaldo
            self.data_dir = os.getcwd()
            self.csv_path = os.path.join(self.data_dir, 'madrid_weather_forecast.csv')
            self.logger.info(f"Usando directorio alternativo: {self.data_dir}")

    def get_weather_data(self):
        """
        Obtiene datos meteorológicos desde la API de AEMET.

        La API de AEMET requiere dos llamadas:
        1. Primera llamada para obtener la URL con los datos reales
        2. Segunda llamada a esa URL para obtener los datos en formato JSON

        Returns:
            list/None: Datos meteorológicos en formato JSON o None sí ocurre un error
        """
        try:
            # Primera llamada a la API para obtener la URL de los datos
            initial_url = f"{self.base_url}{self.municipality_code}"
            self.logger.debug(f"Realizando solicitud a: {initial_url}")

            response = requests.get(initial_url, headers=self.headers)
            response.raise_for_status()  # Lanza excepción si hay error HTTP

            data_url = response.json().get('datos')

            if not data_url:
                self.logger.error("No se encontró la URL de datos en la respuesta")
                return None

            # Segunda llamada a la API para obtener los datos meteorológicos
            self.logger.debug(f"Obteniendo datos desde: {data_url}")
            data_response = requests.get(data_url)
            data_response.raise_for_status()

            return data_response.json()

        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error en la solicitud HTTP: {e}")
            return None
        except json.JSONDecodeError as e:
            self.logger.error(f"Error al procesar JSON: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Error inesperado: {e}")
            return None

    def parse_weather_data(self, json_data):
        """
        Procesa los datos JSON obtenidos de la API y los convierte en un DataFrame.

        Args:
            json_data (list): Datos meteorológicos en formato JSON

        Returns:
            pandas.DataFrame: DataFrame con los datos meteorológicos procesados
        """
        rows = []
        collection_timestamp = datetime.now().strftime('%d/%m/%Y %H:%M:%S')

        try:
            # Iterar por cada día en la predicción
            for day in json_data[0]['prediccion']['dia']:
                # Convertir la fecha al formato dd/mm/yyyy
                base_date = datetime.strptime(day['fecha'], '%Y-%m-%dT%H:%M:%S').strftime('%d/%m/%Y')

                # Procesar cada hora del día (0-23)
                for period in range(24):
                    period_str = f"{period:02d}"  # Formato de dos dígitos: 00, 01, 02...

                    # Extraer los valores de cada parámetro meteorológico para la hora actual
                    # Si no hay datos para alguna hora, se guarda None
                    temp = next((item['value'] for item in day['temperatura'] if item['periodo'] == period_str), None)
                    humidity = next((item['value'] for item in day['humedadRelativa'] if item['periodo'] == period_str),
                                    None)
                    sky_condition = next(
                        (item['descripcion'] for item in day['estadoCielo'] if item['periodo'] == period_str), None)

                    # Los datos de viento tienen una estructura más compleja
                    wind_data = next((item for item in day['vientoAndRachaMax'] if
                                      item.get('periodo') == period_str and 'direccion' in item), None)

                    # Solo crear una fila si hay datos de temperatura (indicador principal)
                    if temp is not None:
                        row = {
                            'date': base_date,
                            'hour': period,
                            'temperature': temp,
                            'humidity': humidity,
                            'sky_condition': sky_condition,
                            'wind_direction': wind_data['direccion'][0] if wind_data else None,
                            'wind_speed': wind_data['velocidad'][0] if wind_data else None,
                            'timestamp': collection_timestamp  # Cuándo se recolectaron estos datos
                        }
                        rows.append(row)

            # Crear DataFrame con todos los datos recopilados
            return pd.DataFrame(rows)

        except (KeyError, IndexError, TypeError) as e:
            self.logger.error(f"Error al procesar los datos: {e}")
            # Devolver DataFrame vacío en caso de error
            return pd.DataFrame()

    def update_csv(self):
        """
        Actualiza el archivo CSV con nuevos datos, evitando duplicados.

        El proceso:
        1. Obtiene nuevos datos de la API
        2. Procesa los datos en un DataFrame
        3. Combina con datos existentes (si los hay) evitando duplicados
        4. Guarda el resultado en CSV

        Returns:
            bool: True si la actualización fue exitosa, False en caso contrario
        """
        try:
            # Obtener nuevos datos
            self.logger.info("Obteniendo nuevos datos meteorológicos...")
            json_data = self.get_weather_data()

            if json_data is None:
                self.logger.error("No se pudieron obtener datos. Abortando actualización.")
                return False

            # Procesar los datos en un DataFrame
            self.logger.info("Procesando datos...")
            new_df = self.parse_weather_data(json_data)

            if new_df.empty:
                self.logger.error("No se pudieron procesar los datos. DataFrame vacío.")
                return False

            # Crear identificador único para cada predicción (fecha + hora)
            new_df['unique_id'] = new_df['date'] + '_' + new_df['hour'].astype(str)

            # Cargar CSV existente si existe
            if os.path.exists(self.csv_path):
                self.logger.info(f"Actualizando archivo existente: {self.csv_path}")
                try:
                    existing_df = pd.read_csv(self.csv_path)

                    # Crear el mismo identificador único en los datos existentes
                    existing_df['unique_id'] = existing_df['date'] + '_' + existing_df['hour'].astype(str)

                    # Eliminar pronósticos antiguos para las mismas combinaciones de fecha/hora
                    existing_df = existing_df[~existing_df['unique_id'].isin(new_df['unique_id'])]

                    # Combinar datos antiguos y nuevos
                    combined_df = pd.concat([existing_df, new_df], ignore_index=True)

                except PermissionError:
                    self.logger.error(f"Permiso denegado para leer {self.csv_path}")
                    # Crear nuevo archivo con marca de tiempo
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    self.csv_path = os.path.join(self.data_dir, f'madrid_weather_forecast_{timestamp}.csv')
                    self.logger.info(f"Creando nuevo archivo: {self.csv_path}")
                    combined_df = new_df
                except Exception as e:
                    self.logger.error(f"Error al leer CSV existente: {e}")
                    combined_df = new_df
            else:
                self.logger.info("Creando nuevo archivo CSV")
                combined_df = new_df

            # Eliminar la columna temporal unique_id
            combined_df = combined_df.drop('unique_id', axis=1)

            # Ordenar por fecha y hora
            self.logger.info("Ordenando datos por fecha y hora...")
            combined_df['date'] = pd.to_datetime(combined_df['date'], format='%d/%m/%Y')
            combined_df = combined_df.sort_values(['date', 'hour'])
            combined_df['date'] = combined_df['date'].dt.strftime('%d/%m/%Y')

            # Guardar en CSV con manejo de errores
            try:
                combined_df.to_csv(self.csv_path, index=False)
                self.logger.info(f"CSV actualizado con éxito: {self.csv_path}")
                self.logger.info(f"Registros totales: {len(combined_df)}")
                return True
            except PermissionError:
                # Sí hay error de permisos, intentar guardar con nombre alternativo
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_path = os.path.join(self.data_dir, f'madrid_weather_forecast_{timestamp}.csv')
                combined_df.to_csv(backup_path, index=False)
                self.logger.warning(f"Permiso denegado para ruta original. Guardado en: {backup_path}")
                return True
            except Exception as e:
                self.logger.error(f"Error al guardar CSV: {e}")
                return False

        except Exception as e:
            self.logger.error(f"Error al actualizar CSV: {e}")
            return False


def run_weather_collector(api_key, interval_hours=6, data_dir=None):
    """
    Ejecuta el recolector de datos meteorológicos a intervalos específicos.

    Args:
        api_key (str): Clave de API para AEMET
        interval_hours (int): Horas entre actualizaciones de datos
        data_dir (str, opcional): Directorio donde guardar los datos
    """
    # Configurar logging para la función principal
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger('WeatherCollectorRunner')

    # Crear instancia del recolector
    collector = WeatherDataCollector(api_key, data_dir=data_dir)

    logger.info(f"Iniciando recolector de datos meteorológicos de Madrid")
    logger.info(f"Intervalo de actualización: {interval_hours} horas")

    # Bucle principal para ejecutar indefinidamente
    while True:
        try:
            start_time = datetime.now()
            logger.info(f"Iniciando recolección de datos: {start_time.strftime('%d/%m/%Y %H:%M:%S')}")

            # Actualizar datos
            success = collector.update_csv()

            if success:
                logger.info("Recolección de datos completada con éxito")
            else:
                logger.warning("La recolección de datos no fue exitosa")

            # Calcular tiempo hasta la próxima ejecución
            next_run = start_time + timedelta(hours=interval_hours)
            logger.info(f"Próxima ejecución programada: {next_run.strftime('%d/%m/%Y %H:%M:%S')}")

            # Esperar hasta el próximo intervalo
            wait_seconds = interval_hours * 3600
            logger.info(f"Esperando {interval_hours} horas hasta la próxima actualización...")
            time.sleep(wait_seconds)

        except KeyboardInterrupt:
            logger.info("Programa detenido por el usuario")
            break
        except Exception as e:
            logger.error(f"Error inesperado: {e}")
            logger.info("Reintentando en 10 minutos...")
            time.sleep(600)  # Esperar 10 minutos antes de reintentar


if __name__ == "__main__":
    # Clave de API para AEMET
    API_KEY

    # Directorio del proyecto actual
    project_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(project_dir, 'data')

    # Iniciar el recolector
    run_weather_collector(API_KEY, interval_hours=6, data_dir=data_dir)