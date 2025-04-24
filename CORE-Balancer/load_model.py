import logging
import os

from function_app import CONNECTION_STRING_ENV_VAR, CONTAINER_NAME, MODEL_BLOB_NAME
from azure.storage.blob import BlobServiceClient


def load_model():
    global model
    if model is not None:
        logging.info("Modelo ya cargado.")
        return
    
    try:
        connection_string = os.environ.get(CONNECTION_STRING_ENV_VAR)
        if not connection_string:
            logging.error(f"Variable de entorno '{CONNECTION_STRING_ENV_VAR}' no encontrada.")
            # Considera lanzar una excepción o manejar el error apropiadamente
            return

        blob_service_client = BlobServiceClient.from_connection_string(connection_string)
        blob_client = blob_service_client.get_blob_client(container=CONTAINER_NAME, blob=MODEL_BLOB_NAME)

        downloader = blob_client.download_blob()
        model_bytes = downloader.readall()
        logging.info(f"Modelo descargado ({len(model_bytes)} bytes). Cargando en memoria...")

        import tensorflow as tf
        import tempfile

        with tempfile.NamedTemporaryFile(suffix=".h5", delete=False) as temp_model_file: # Usa el sufijo correcto
            temp_model_file.write(model_bytes)
            temp_model_path = temp_model_file.name

        try:
             model = tf.keras.models.load_model(temp_model_path)
             logging.info("Modelo Keras cargado exitosamente desde archivo temporal.")
        finally:
             os.remove(temp_model_path)
             logging.info(f"Archivo temporal {temp_model_path} eliminado.")

        if model is None:
             logging.error("¡Fallo al cargar el modelo con las opciones probadas!")

    except Exception as e:
        logging.error(f"Error al descargar o cargar el modelo: {e}", exc_info=True)
        # Decide cómo manejar el error: ¿debería fallar la función o intentar de nuevo?
        model = None # Asegurarse de que no se use un modelo parcialmente cargado

