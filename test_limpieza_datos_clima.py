# test_limpieza_datos_clima.py
"""
Pruebas unitarias para el módulo de limpieza de datos meteorológicos.

Este script contiene pruebas automatizadas para verificar el correcto funcionamiento
de todas las funciones del módulo limpieza_datos_clima.py. Las pruebas cubren
traducciones, conversiones, unificaciones y detección de problemas en los datos.

Autor: Leonardo
Fecha: Abril 2025
"""

import unittest
import pandas as pd
import numpy as np
import io
from unittest.mock import patch, MagicMock

from limpieza_datos_clima import (
    traducir_direccion_viento,
    traducir_condicion_cielo,
    eliminar_columnas_innecesarias,
    convertir_tipos_datos,
    unificar_fecha_hora,
    normalizar_nombres_columnas,
    marcar_estado_viento,
    detectar_outliers,
    verificar_duplicados,
    proceso_completo_limpieza
)


class TestLimpiezaDatosClima(unittest.TestCase):
    """
    Pruebas unitarias para el script de limpieza de datos meteorológicos.

    Esta clase contiene métodos para probar cada una de las funciones
    del módulo de limpieza de datos, verificando que transforman los datos
    correctamente según lo esperado.
    """

    def setUp(self):
        """
        Configura los datos de prueba necesarios antes de cada test.

        Crea DataFrames de ejemplo con datos similares a los reales para usar
        en las pruebas, incluyendo un conjunto con duplicados para probar
        esa funcionalidad específica.
        """
        # Crear un DataFrame de prueba con datos similares al original
        self.datos_prueba = pd.DataFrame({
            'date': ['2025-02-18', '2025-02-18', '2025-02-19', '2025-02-19'],
            'hour': [8, 9, 8, 9],
            'temperature': ['22.5', '23.0', '21.5', '22.0'],
            'humidity': ['65', '68', '70', '67'],
            'wind_speed': ['10', '12', '8', '9'],
            'wind_direction': ['N', 'NE', 'S', 'SO'],
            'sky_condition': ['Despejado', 'Poco nuboso', 'Nuboso', 'Cubierto'],
            'timestamp': ['2025-02-18 08:15:00', '2025-02-18 09:15:00',
                          '2025-02-19 08:15:00', '2025-02-19 09:15:00']
        })

        # Crear una copia para usar en pruebas que necesiten datos duplicados
        # Añadir los índices 0 y 2 del DataFrame original para simular duplicados
        self.datos_con_duplicados = pd.concat([self.datos_prueba,
                                               self.datos_prueba.iloc[[0, 2]]])

    def test_traducir_direccion_viento(self):
        """
        Prueba la traducción de la dirección del viento.

        Verifica que:
        1. Se añaden las columnas correctas
        2. Las traducciones sean precisas
        3. Los valores en grados sean correctos
        """
        resultado = traducir_direccion_viento(self.datos_prueba)

        # Verificar que se agregaron las columnas correctas
        self.assertIn('wind_direction_completo', resultado.columns)
        self.assertIn('wind_direction_grados', resultado.columns)

        # Verificar traducciones específicas
        self.assertEqual(resultado.loc[0, 'wind_direction_completo'], 'north')
        self.assertEqual(resultado.loc[1, 'wind_direction_completo'], 'northeast')

        # Verificar grados
        self.assertEqual(resultado.loc[0, 'wind_direction_grados'], 0)
        self.assertEqual(resultado.loc[1, 'wind_direction_grados'], 45)

    def test_traducir_condicion_cielo(self):
        """
        Prueba la traducción de la condición del cielo.

        Verifica que:
        1. Se añade la columna correcta
        2. Las traducciones sean precisas para distintas condiciones
        """
        resultado = traducir_condicion_cielo(self.datos_prueba)

        # Verificar que se agregó la columna correcta
        self.assertIn('sky_condition_ingles', resultado.columns)

        # Verificar traducciones específicas
        self.assertEqual(resultado.loc[0, 'sky_condition_ingles'], 'clear')
        self.assertEqual(resultado.loc[1, 'sky_condition_ingles'], 'few clouds')
        self.assertEqual(resultado.loc[2, 'sky_condition_ingles'], 'cloudy')

    def test_eliminar_columnas_innecesarias(self):
        """
        Prueba la eliminación de columnas.

        Verifica que:
        1. Se eliminan las columnas especificadas
        2. Las demás columnas permanezcan intactas
        """
        columnas_a_eliminar = ['timestamp']
        resultado = eliminar_columnas_innecesarias(self.datos_prueba, columnas_a_eliminar)

        # Verificar que se eliminó la columna
        self.assertNotIn('timestamp', resultado.columns)

        # Verificar que las demás columnas permanecen
        self.assertIn('date', resultado.columns)
        self.assertIn('hour', resultado.columns)

    def test_convertir_tipos_datos(self):
        """
        Prueba la conversión de tipos de datos.

        Verifica que:
        1. Las fechas se convierten a datetime
        2. Las horas tengan el formato correcto
        3. Los valores numéricos se convierten a float
        """
        # Primero agregamos wind_direction_grados para probar su conversión
        df_temp = self.datos_prueba.copy()
        df_temp['wind_direction_grados'] = ['0', '45', '180', '225']

        resultado = convertir_tipos_datos(df_temp)

        # Verificar tipos de datos
        self.assertTrue(pd.api.types.is_datetime64_any_dtype(resultado['date']))
        self.assertEqual(resultado['hour'][0], '08:00')  # formato correcto de hora
        self.assertTrue(pd.api.types.is_float_dtype(resultado['temperature']))
        self.assertTrue(pd.api.types.is_float_dtype(resultado['humidity']))
        self.assertTrue(pd.api.types.is_float_dtype(resultado['wind_speed']))
        self.assertTrue(pd.api.types.is_float_dtype(resultado['wind_direction_grados']))

    def test_unificar_fecha_hora(self):
        """
        Prueba la unificación de fecha y hora.

        Verifica que:
        1. Se cree la columna datetime
        2. El formato de fecha/hora sea correcto
        """
        # Primero convertir los tipos para que la unificación funcione correctamente
        df_temp = convertir_tipos_datos(self.datos_prueba)
        resultado = unificar_fecha_hora(df_temp)

        # Verificar que se creó la columna datetime
        self.assertIn('datetime', resultado.columns)

        # Verificar que el formato es correcto
        primera_fecha = resultado.loc[0, 'datetime']
        self.assertEqual(pd.Timestamp('2025-02-18 08:00:00'), primera_fecha)

    def test_normalizar_nombres_columnas(self):
        """
        Prueba la normalización de nombres de columnas.

        Verifica que:
        1. Los nombres se convierten a minúsculas
        2. Los renombres específicos se aplican correctamente
        """
        # Crear un DataFrame con nombres mixtos
        df_temp = pd.DataFrame({
            'TEMPERATURA': [22.5, 23.0],
            'Humedad_Relativa': [65, 68]
        })

        renombres = {'temperatura': 'temp', 'humedad_relativa': 'humidity'}
        resultado = normalizar_nombres_columnas(df_temp, renombres)

        # Verificar que los nombres están en minúsculas y renombrados
        self.assertIn('temp', resultado.columns)
        self.assertIn('humidity', resultado.columns)
        self.assertNotIn('TEMPERATURA', resultado.columns)
        self.assertNotIn('Humedad_Relativa', resultado.columns)

    def test_marcar_estado_viento(self):
        """
        Prueba la marcación del estado del viento.

        Verifica que:
        1. Se cree la columna wind_status
        2. Los valores se marcan correctamente (calm/with wind)
        """
        # Preparar datos con valores nulos
        df_temp = pd.DataFrame({
            'wind_direction_degrees': [0.0, 45.0, np.nan, 180.0]
        })

        resultado = marcar_estado_viento(df_temp)

        # Verificar que se creó la columna wind_status
        self.assertIn('wind_status', resultado.columns)

        # Verificar los valores
        self.assertEqual(resultado.loc[0, 'wind_status'], 'with wind')
        self.assertEqual(resultado.loc[2, 'wind_status'], 'calm')

    def test_detectar_outliers(self):
        """
        Prueba la detección de outliers.

        Verifica que:
        1. Se detectan correctamente valores fuera de rangos normales
        2. Las filas con outliers se identifican adecuadamente
        """
        # Crear datos con outliers
        df_outliers = pd.DataFrame({
            'temperature': [22.5, -15.0, 55.0, 20.0],
            'humidity': [65, 68, 101, 50],
            'wind_speed': [10, -5, 15, 8]
        })

        resultado = detectar_outliers(df_outliers)

        # Debe haber 2 filas con outliers (índices 1, 2)
        self.assertEqual(len(resultado), 2)

        # Verificar que las filas correctas fueron detectadas
        self.assertTrue(1 in resultado.index)
        self.assertTrue(2 in resultado.index)

    def test_verificar_duplicados(self):
        """
        Prueba la verificación y eliminación de duplicados.

        Verifica que:
        1. Se detecta el número correcto de duplicados
        2. Las filas duplicadas se eliminan correctamente
        """
        resultado, num_duplicados = verificar_duplicados(self.datos_con_duplicados)

        # Debe haber encontrado 2 duplicados
        self.assertEqual(num_duplicados, 2)

        # El DataFrame resultante debe tener 4 filas (6 originales - 2 duplicados)
        self.assertEqual(len(resultado), 4)

    def test_proceso_completo_limpieza(self):
        """
        Prueba el proceso completo de limpieza.

        Verifica que:
        1. La estructura del DataFrame resultante sea la esperada
        2. Se eliminan las columnas innecesarias
        3. No hay duplicados
        4. Las columnas están en el orden correcto
        """
        resultado = proceso_completo_limpieza(self.datos_prueba)

        # Verificar que el DataFrame resultante tiene la estructura esperada
        self.assertIn('datetime', resultado.columns)
        self.assertIn('temperature', resultado.columns)
        self.assertIn('wind_direction', resultado.columns)
        self.assertIn('sky_condition', resultado.columns)
        self.assertIn('wind_direction_degrees', resultado.columns)
        self.assertIn('wind_status', resultado.columns)

        # Verificar que se eliminaron las columnas innecesarias
        self.assertNotIn('date', resultado.columns)
        self.assertNotIn('hour', resultado.columns)
        self.assertNotIn('timestamp', resultado.columns)

        # Verificar el número de filas (no debe haber duplicados)
        self.assertEqual(len(resultado), 4)

        # Verificar que datetime es la primera columna
        self.assertEqual(resultado.columns[0], 'datetime')


if __name__ == '__main__':
    unittest.main()