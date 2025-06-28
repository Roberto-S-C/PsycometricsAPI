import numpy as np
from sklearn.svm import SVC
from sklearn.preprocessing import StandardScaler, LabelEncoder
from .base_model import BasePsycometricModel


class FrustrationToleranceModel(BasePsycometricModel):
    def __init__(self):
        super().__init__('frustration_model')
        self.frustration_questions = [str(i) for i in range(31, 41)]
        self.positive_responses = ['Siempre', 'Usualmente']
        self.scaler = StandardScaler()
        self.encoder = LabelEncoder()
        self.classes_ = ['Baja', 'Moderada', 'Alta']

    def preprocess_data(self, raw_responses):
        """Preprocesamiento para modelo de frustración"""
        response_dict = self._convert_to_response_dict(raw_responses)
        features = []

        for qid in self.frustration_questions:
            response = response_dict.get(qid, 'Nunca')
            normalized = response.capitalize()
            features.append(1 if normalized in self.positive_responses else 0)

        features = np.array([features])
        return self.scaler.transform(features) if hasattr(self.scaler, 'mean_') else features

    def build_model(self):
        """SVM con kernel RBF para tolerancia a frustración"""
        self.model = SVC(
            kernel='rbf',
            C=1.0,
            gamma='scale',
            probability=True,
            class_weight='balanced'
        )
        self.encoder.fit(self.classes_)

    def train(self, X, y):
        """Entrenamiento con escalado de características"""
        X = np.vstack(X)
        self.scaler.fit(X)
        X_scaled = self.scaler.transform(X)
        y_encoded = self.encoder.transform(y)
        super().train(X_scaled, y_encoded)

    def predict_tolerance(self, X):
        """Predice nivel de tolerancia con interpretación"""
        if not self.model:
            self.load_model()

        X_processed = self.preprocess_data(X)
        pred = self.model.predict(X_processed)
        proba = np.max(self.model.predict_proba(X_processed))

        return {
            'level': self.encoder.inverse_transform(pred)[0],
            'confidence': float(proba),
            'interpretation': self._get_interpretation(pred[0])
        }

    def _get_interpretation(self, level):
        interpretations = [
            "Dificultad para manejar situaciones frustrantes. Beneficiaría de estrategias de afrontamiento.",
            "Capacidad moderada para manejar frustraciones. Algunas áreas para mejorar.",
            "Alta resiliencia frente a frustraciones. Buen manejo de adversidades."
        ]
        return interpretations[level]