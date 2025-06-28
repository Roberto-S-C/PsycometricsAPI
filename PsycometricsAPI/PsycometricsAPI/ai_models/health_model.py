import numpy as np
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Dropout, BatchNormalization
from tensorflow.keras.callbacks import EarlyStopping
from sklearn.preprocessing import StandardScaler
from .base_model import BasePsycometricModel


class PsychologicalHealthModel(BasePsycometricModel):
    def __init__(self):
        super().__init__('health_model')
        self.health_questions = [str(i) for i in range(52, 64)]
        self.response_weights = {
            'Mucho más de lo usual': 1.0,
            'Más de lo usual': 0.75,
            'No más de lo usual': 0.5,
            'Menos de lo usual': 0.25
        }
        self.scaler = StandardScaler()
        self.classes = ['Saludable', 'Riesgo', 'Problemas']

    def preprocess_data(self, raw_responses):
        """Preprocesamiento para red neuronal"""
        response_dict = self._convert_to_response_dict(raw_responses)
        features = []

        for qid in self.health_questions:
            response = response_dict.get(qid, 'No más de lo usual')
            features.append(self.response_weights.get(response, 0.5))

        features = np.array([features])
        return self.scaler.transform(features) if hasattr(self.scaler, 'mean_') else features

    def build_model(self):
        """Red neuronal para evaluación de salud psicológica"""
        self.model = Sequential([
            Dense(64, activation='relu', input_shape=(len(self.health_questions),)),
            BatchNormalization(),
            Dropout(0.3),
            Dense(32, activation='relu'),
            Dense(16, activation='relu'),
            Dense(3, activation='softmax')
        ])

        self.model.compile(
            optimizer=tf.keras.optimizers.Adam(learning_rate=0.001),
            loss='sparse_categorical_crossentropy',
            metrics=['accuracy',
                     tf.keras.metrics.Precision(name='precision'),
                     tf.keras.metrics.Recall(name='recall')]
        )

    def train(self, X, y, epochs=50, batch_size=32, validation_split=0.2):
        """Entrenamiento con early stopping"""
        X = np.vstack(X)
        self.scaler.fit(X)
        X_scaled = self.scaler.transform(X)

        callbacks = [
            EarlyStopping(patience=5, restore_best_weights=True, monitor='val_loss')
        ]

        history = self.model.fit(
            X_scaled, y,
            epochs=epochs,
            batch_size=batch_size,
            validation_split=validation_split,
            callbacks=callbacks,
            verbose=1
        )
        return history

    def predict_health(self, X):
        """Predice el estado de salud psicológica"""
        if not self.model:
            self.load_model()

        X_processed = self.preprocess_data(X)
        pred = self.model.predict(X_processed)
        idx = np.argmax(pred)

        return {
            'status': self.classes[idx],
            'confidence': float(pred[0][idx]),
            'details': {cls: float(pred[0][i]) for i, cls in enumerate(self.classes)},
            'recommendation': self._get_recommendation(idx)
        }

    def _get_recommendation(self, level):
        recommendations = [
            "Continúa con tus actuales estrategias de bienestar.",
            "Considera buscar apoyo preventivo o evaluaciones periódicas.",
            "Recomendado buscar evaluación profesional para apoyo adicional."
        ]
        return recommendations[level]