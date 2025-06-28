import numpy as np
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.preprocessing import OneHotEncoder
from .base_model import BasePsycometricModel


class InterestsAnalysisModel(BasePsycometricModel):
    def __init__(self):
        super().__init__('interests_model')
        self.interest_questions = [str(i) for i in range(74, 84)]
        self.categories = ['economico', 'politico', 'social', 'religioso']
        self.feature_mapping = self._create_feature_mapping()

    def _create_feature_mapping(self):
        """Crea el mapeo de características para intereses"""
        mapping = {}
        # Preguntas económicas
        mapping.update({f"74_{opt}": [1, 0, 0, 0] for opt in ['A', 'B']})
        mapping.update({f"75_{opt}": [1, 0, 0, 0] for opt in ['C']})
        # Preguntas políticas
        mapping.update({f"76_{opt}": [0, 1, 0, 0] for opt in ['B']})
        # Preguntas sociales
        mapping.update({f"77_{opt}": [0, 0, 1, 0] for opt in ['A']})
        # Preguntas religiosas
        mapping.update({f"78_{opt}": [0, 0, 0, 1] for opt in ['C']})
        return mapping

    def preprocess_data(self, raw_responses):
        """Convierte respuestas a características numéricas"""
        response_dict = self._convert_to_response_dict(raw_responses)
        features = np.zeros((1, len(self.categories)))

        for qid in self.interest_questions:
            response = response_dict.get(qid, 'A').upper()
            key = f"{qid}_{response}"
            if key in self.feature_mapping:
                features += self.feature_mapping[key]

        return features

    def build_model(self):
        """Modelo Gradient Boosting para intereses"""
        self.model = GradientBoostingClassifier(
            n_estimators=150,
            learning_rate=0.1,
            max_depth=4,
            random_state=42
        )
        self.encoder = OneHotEncoder(sparse=False)

    def predict_interests(self, X):
        """Predice intereses dominantes con interpretación"""
        if not self.model:
            self.load_model()

        probas = self.model.predict_proba(X)[0]
        results = {}
        for i, category in enumerate(self.categories):
            results[category] = {
                'score': float(probas[i]),
                'interpretation': self._get_interpretation(category, probas[i])
            }
        return results

    def _get_interpretation(self, category, score):
        interpretations = {
            'economico': f"Interés en aspectos financieros y materiales ({score:.0%})",
            'politico': f"Interés en poder e influencia ({score:.0%})",
            'social': f"Interés en relaciones y bienestar colectivo ({score:.0%})",
            'religioso': f"Interés en espiritualidad y valores trascendentes ({score:.0%})"
        }
        return interpretations[category]

    def get_config(self):
        return {
            'interest_questions': self.interest_questions,
            'categories': self.categories
        }