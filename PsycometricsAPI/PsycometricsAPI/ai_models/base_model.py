import joblib
import os
import numpy as np
from pathlib import Path
from abc import ABC, abstractmethod


class BasePsycometricModel(ABC):
    def __init__(self, model_name):
        self.model_name = model_name
        self.model = None
        self.scaler = None
        self.encoder = None
        self.base_path = Path(__file__).parent / 'pretrained_models'
        self.model_path = self.base_path / f'{model_name}.pkl'
        os.makedirs(self.base_path, exist_ok=True)

    @abstractmethod
    def preprocess_data(self, raw_data):
        """Preprocesa los datos crudos para el modelo"""
        pass

    @abstractmethod
    def build_model(self):
        """Construye la arquitectura del modelo"""
        pass

    def train(self, X, y, **kwargs):
        """Entrena el modelo con datos preprocesados"""
        if not self.model:
            self.build_model()
        self.model.fit(X, y, **kwargs)

    def predict(self, X):
        """Realiza predicciones con el modelo entrenado"""
        if not self.model:
            raise ValueError("Modelo no entrenado. Llame a train() primero.")
        return self.model.predict(X)

    def save_model(self):
        """Guarda el modelo entrenado con todos sus componentes"""
        if not self.model:
            raise ValueError("Modelo no entrenado. Nada que guardar.")

        to_save = {
            'model': self.model,
            'scaler': self.scaler,
            'encoder': self.encoder,
            'config': self.get_config()
        }
        joblib.dump(to_save, self.model_path)

    def load_model(self):
        """Carga un modelo previamente entrenado"""
        if not os.path.exists(self.model_path):
            raise FileNotFoundError(f"Modelo {self.model_name} no encontrado.")

        data = joblib.load(self.model_path)
        self.model = data['model']
        self.scaler = data.get('scaler')
        self.encoder = data.get('encoder')
        self.set_config(data.get('config', {}))

    def get_config(self):
        """Obtiene la configuración específica del modelo"""
        return {}

    def set_config(self, config):
        """Establece la configuración del modelo"""
        pass

    def _convert_to_response_dict(self, raw_responses):
        """Convierte el formato de respuestas a diccionario"""
        if isinstance(raw_responses, dict) and 'responses' in raw_responses:
            return {r['question_id']: r['response'] for r in raw_responses['responses']}
        return raw_responses