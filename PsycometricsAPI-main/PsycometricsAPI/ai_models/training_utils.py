import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint


class ModelTrainer:
    def __init__(self, models_dir='pretrained_models'):
        self.models_dir = Path(models_dir)
        self.models_dir.mkdir(exist_ok=True)

    def load_dataset(self, data_path):
        """Carga y valida el dataset"""
        df = pd.read_csv(data_path)
        required_columns = [f'q{i}' for i in range(1, 84)] + ['pressure_label', 'values_label', 'health_label']

        if not all(col in df.columns for col in required_columns):
            raise ValueError("Dataset no contiene todas las columnas requeridas")

        return df

    def format_responses(self, row):
        """Convierte fila del DataFrame al formato de respuestas esperado"""
        responses = []
        for qid in range(1, 84):
            responses.append({
                'question_id': str(qid),
                'response': row[f'q{qid}']
            })

        return {
            '_id': str(row.get('id', '')),
            'test_id': 'sample_test',
            'candidate_id': str(row.get('candidate_id', '')),
            'hr_id': str(row.get('hr_id', '')),
            'completed_at': pd.Timestamp.now().isoformat(),
            'responses': responses,
            'pressure_label': row['pressure_label'],
            'values_label': row['values_label'],
            'health_label': row['health_label']
        }

    def prepare_data(self, df, test_size=0.2):
        """Prepara los datos para entrenamiento"""
        formatted_data = [self.format_responses(row) for _, row in df.iterrows()]
        return train_test_split(formatted_data, test_size=test_size, random_state=42)

    def train_pressure_model(self, train_data, val_data=None):
        """Entrenamiento completo del modelo de presión"""
        from .pressure_model import PressureAnalysisModel

        model = PressureAnalysisModel()
        X_train = [model.preprocess_data(d) for d in train_data]
        y_train = [d['pressure_label'] for d in train_data]

        # Validación
        if val_data:
            X_val = [model.preprocess_data(d) for d in val_data]
            y_val = [d['pressure_label'] for d in val_data]
        else:
            X_train, X_val, y_train, y_val = train_test_split(X_train, y_train, test_size=0.2)

        # Entrenamiento
        model.build_model()
        model.train(np.vstack(X_train), np.array(y_train))

        # Evaluación
        val_pred = model.predict(np.vstack(X_val))
        print("\nPressure Model Validation Report:")
        print(classification_report(y_val, val_pred))

        model.save_model()
        return model

    def train_health_model(self, train_data, epochs=50, batch_size=32):
        """Entrenamiento completo del modelo de salud"""
        from .health_model import PsychologicalHealthModel

        model = PsychologicalHealthModel()
        X_train = np.vstack([model.preprocess_data(d) for d in train_data])
        y_train = np.array([d['health_label'] for d in train_data])

        # Callbacks
        callbacks = [
            EarlyStopping(patience=5, restore_best_weights=True),
            ModelCheckpoint(
                str(self.models_dir / 'health_model_best.h5'),
                save_best_only=True,
                monitor='val_accuracy'
            )
        ]

        # Entrenamiento
        model.build_model()
        history = model.model.fit(
            X_train, y_train,
            validation_split=0.2,
            epochs=epochs,
            batch_size=batch_size,
            callbacks=callbacks,
            verbose=1
        )

        model.save_model()
        return model, history

    def train_all_models(self, data_path, test_size=0.2):
        """Pipeline completo de entrenamiento"""
        print("Cargando dataset...")
        df = self.load_dataset(data_path)
        train_data, test_data = self.prepare_data(df, test_size)

        print("\nEntrenando modelo de presión...")
        pressure_model = self.train_pressure_model(train_data, test_data)

        print("\nEntrenando modelo de salud psicológica...")
        health_model, health_history = self.train_health_model(train_data)

        # Aquí se agregarían los otros modelos

        print("\nEntrenamiento completado!")
        return {
            'pressure_model': pressure_model,
            'health_model': health_model,
            'test_data': test_data
        }

    def evaluate_models(self, models, test_data):
        """Evaluación completa de todos los modelos"""
        results = {}

        if 'pressure_model' in models:
            X_test = [models['pressure_model'].preprocess_data(d) for d in test_data]
            y_test = [d['pressure_label'] for d in test_data]
            preds = models['pressure_model'].predict(np.vstack(X_test))
            results['pressure'] = classification_report(y_test, preds, output_dict=True)

        # Evaluación para otros modelos...

        return results


# Uso ejemplo:
if __name__ == '__main__':
    trainer = ModelTrainer()

    # Entrenamiento completo
    results = trainer.train_all_models('psychometric_data.csv')

    # Evaluación
    metrics = trainer.evaluate_models(results, results['test_data'])
    print("Métricas de evaluación:", metrics)