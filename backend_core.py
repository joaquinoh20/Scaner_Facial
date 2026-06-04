# backend_core.py
import math
import json
import numpy as np

def calcular_distancia_haversine(lat1, lon1, lat2, lon2):
    """
    Calcula la distancia en metros entre las coordenadas del empleado y la empresa.
    """
    R = 6371000.0  # Radio de la Tierra en metros
    
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    
    a = math.sin(delta_phi / 2.0) ** 2 + \
        math.cos(phi1) * math.cos(phi2) * \
        math.sin(delta_lambda / 2.0) ** 2
        
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return R * c

def comparar_vectores_faciales(vector_actual, vector_guardado_str, umbral=0.6):
    """
    Compara los puntos faciales de la cámara contra la base de datos usando Distancia Euclidiana.
    Protege la privacidad guardando números, no imágenes.
    """
    try:
        vec_db = np.array(json.loads(vector_guardado_str))
        vec_curr = np.array(vector_actual)
        distancia = np.linalg.norm(vec_curr - vec_db)
        return distancia < umbral, distancia
    except Exception as e:
        print(f"Error en comparación matemática: {e}")
        return False, 1.0