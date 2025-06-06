import joblib
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier


class StressPredictor:
    def __init__(self, model_path='ai/models/stress_model.joblib'):
        self.model = joblib.load(model_path)

    def predict(self, responses: pd.DataFrame):
        """Predecir aptitud bajo presión (RF 3.2.10)"""
        return self.model.predict_proba(responses)[:, 1]


class EmotionalIntelligenceClassifier:
    def __init__(self, model_path='ai/models/ei_model.joblib'):
        self.model = joblib.load(model_path)

    def classify(self, responses: pd.DataFrame):
        """Clasificar nivel de inteligencia emocional (p.11)"""
        return self.model.predict(responses)