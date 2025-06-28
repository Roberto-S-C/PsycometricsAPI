import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from .base_model import BasePsycometricModel


class PressureAnalysisModel(BasePsycometricModel):
    def __init__(self):
        super().__init__('pressure_model')
        self.question_ids = [str(i) for i in range(31, 41)] + [str(i) for i in range(52, 64)]
        self.response_mapping = {
            'Siempre': 4, 'Usualmente': 3,
            'Raramente': 2, 'Nunca': 1,
            'Mucho más de lo usual': 4,
            'Más de lo usual': 3,
            'No más de lo usual': 2,
            'Menos de lo usual': 1
        }
        self.class_names = ['Baja', 'Moderada', 'Alta']

    def preprocess_data(self, raw_responses):
        """Procesa el formato específico de respuestas"""
        response_dict = self._convert_to_response_dict(raw_responses)
        sample = []

        for qid in self.question_ids:
            response = response_dict.get(qid, 'Nunca')
            normalized_response = response.capitalize() if len(response) > 1 else response
            sample.append(self.response_mapping.get(normalized_response, 1))

        sample = np.array(sample).reshape(1, -1)

        if self.scaler:
            return self.scaler.transform(sample)
        return sample

    def build_model(self):
        """Construye un clasificador Random Forest optimizado"""
        self.model = RandomForestClassifier(
            n_estimators=200,
            max_depth=15,
            min_samples_split=5,
            class_weight='balanced',
            random_state=42,
            n_jobs=-1
        )
        self.scaler = StandardScaler()

    def train(self, X, y):
        """Entrenamiento con escalado de características"""
        X = np.vstack(X)
        self.scaler.fit(X)
        X_scaled = self.scaler.transform(X)
        super().train(X_scaled, y)

    def interpret_results(self, predictions):
        """Genera interpretaciones comprensibles"""
        return [{
            'level': self.class_names[pred],
            'description': self._get_description(pred),
            'score': int(pred)
        } for pred in predictions]

    def _get_description(self, level):
        descriptions = [
            "Dificultad significativa para manejar presión. Recomendado para roles con baja exigencia de estrés.",
            "Capacidad aceptable para manejar presión, con áreas de mejora. Adecuado para roles con estrés intermitente.",
            "Excelente desempeño bajo presión. Ideal para roles de alta exigencia y toma de decisiones críticas."
        ]
        return descriptions[level]

    def get_config(self):
        return {
            'question_ids': self.question_ids,
            'response_mapping': self.response_mapping,
            'class_names': self.class_names
        }

    def set_config(self, config):
        self.question_ids = config.get('question_ids', self.question_ids)
        self.response_mapping = config.get('response_mapping', self.response_mapping)
        self.class_names = config.get('class_names', self.class_names)