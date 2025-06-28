from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.preprocessing import LabelEncoder
from .base_model import BasePsycometricModel


class ValuesAnalysisModel(BasePsycometricModel):
    def __init__(self):
        super().__init__('values_model')
        self.value_categories = {
            'moralidad': ['64', '65', '69', '70', '72'],
            'legalidad': ['66', '67', '71'],
            'indiferencia': ['68'],
            'corrupcion': ['73']
        }
        self.category_descriptions = {
            'moralidad': 'Fuerte sentido de ética personal y preocupación por lo correcto',
            'legalidad': 'Respeto por normas y procedimientos establecidos',
            'indiferencia': 'Tendencia a evitar involucrarse en situaciones conflictivas',
            'corrupcion': 'Posible predisposición a comportamientos cuestionables éticamente'
        }

    def preprocess_data(self, raw_responses):
        """Prepara los datos para el modelo de valores"""
        response_dict = self._convert_to_response_dict(raw_responses)
        text_parts = []

        for category, qids in self.value_categories.items():
            for qid in qids:
                response = response_dict.get(qid, '')
                text_parts.append(f"{category}_q{qid}_{response[:30].replace(' ', '_')}")

        return [' '.join(text_parts)]

    def build_model(self):
        """Construye pipeline de procesamiento de texto"""
        self.model = Pipeline([
            ('tfidf', TfidfVectorizer(
                ngram_range=(1, 2),
                max_features=1000,
                stop_words=None
            )),
            ('clf', MultinomialNB(alpha=0.1))
        ])
        self.encoder = LabelEncoder()

    def train(self, X, y):
        """Entrenamiento con codificación de etiquetas"""
        self.encoder.fit(y)
        y_encoded = self.encoder.transform(y)
        super().train(X, y_encoded)

    def predict_proba(self, X):
        """Obtiene probabilidades para cada categoría de valores"""
        if not self.model:
            self.load_model()

        probas = self.model.predict_proba(X)
        results = {}
        for i, class_name in enumerate(self.encoder.classes_):
            results[class_name] = {
                'score': float(probas[0][i]),
                'description': self.category_descriptions.get(class_name, '')
            }
        return results

    def get_config(self):
        return {
            'value_categories': self.value_categories,
            'category_descriptions': self.category_descriptions
        }

    def set_config(self, config):
        self.value_categories = config.get('value_categories', self.value_categories)
        self.category_descriptions = config.get('category_descriptions', self.category_descriptions)