from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from bson import ObjectId
import pandas as pd
import joblib
from ..serializers import ResultSerializer
from ..db.mongo import result_collection, test_collection, candidate_collection
from ..utils.objectIdConversion import convert_objectid

# Carga de modelos IA (ruta relativa desde el directorio del proyecto)
STRESS_MODEL = joblib.load('PsycometricsAPI/ai/models/stress_model.joblib')
EI_MODEL = joblib.load('PsycometricsAPI/ai/models/ei_model.joblib')


@api_view(["GET", "POST"])
def result_list(request):
    if request.method == "GET":
        results = list(result_collection.find())
        results = [convert_objectid(r) for r in results]

        # Añadir análisis agregado para dashboard (RF 3.2.12)
        if request.query_params.get('aggregate') == 'true':
            aggregated = aggregate_results(results)
            return Response({
                'individual_results': results,
                'aggregated_metrics': aggregated
            })

        return Response(results)

    elif request.method == "POST":
        serializer = ResultSerializer(data=request.data)
        if serializer.is_valid():
            validated = serializer.validated_data

            # Convert string IDs to ObjectId
            test_id = ObjectId(validated.pop("test_id"))
            hr_id = ObjectId(validated.pop("hr_id"))
            candidate_id = ObjectId(validated.pop("candidate_id"))

            # Procesamiento IA (RF 3.2.10)
            responses = validated.get('responses', {})
            ia_analysis = analyze_responses(responses, test_id)

            result_data = {
                **validated,
                "test_id": test_id,
                "hr_id": hr_id,
                "candidate_id": candidate_id,
                "ia_analysis": ia_analysis  # Nuevo campo con resultados IA
            }

            inserted = result_collection.insert_one(result_data)
            new_result = result_collection.find_one({"_id": inserted.inserted_id})

            # Convertir para respuesta
            new_result = convert_objectid(new_result)

            return Response(new_result, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET", "DELETE"])
def result_detail(request, id):
    try:
        _id = ObjectId(id)
        result = result_collection.find_one({"_id": _id})
        if not result:
            return Response({"error": "Result not found"}, status=404)
    except:
        return Response({"error": "Invalid ID"}, status=400)

    if request.method == "GET":
        result = convert_objectid(result)

        # Añadir visualizaciones si se solicita (RF 3.2.10)
        if request.query_params.get('visualizations') == 'true':
            test_id = result['test_id']
            candidate_id = result['candidate_id']
            visualizations = generate_visualizations(test_id, candidate_id)
            result['visualizations'] = visualizations

        return Response(result)

    elif request.method == "DELETE":
        result_collection.delete_one({"_id": _id})
        return Response(status=status.HTTP_204_NO_CONTENT)


# --- Funciones de IA ---
def analyze_responses(responses, test_id):
    """Analiza respuestas usando modelos IA (p.11 IEEE)"""
    try:
        # Obtener estructura del test desde MongoDB
        test = test_collection.find_one({"_id": test_id})
        question_types = {q['number']: q['category'] for q in test['questions']}

        # Convertir a DataFrame para modelos
        df = pd.DataFrame([{
            f"q_{num}": resp['score']
            for num, resp in responses.items()
        }])

        # Preprocesamiento (escalado, etc.)
        df = df.fillna(0)

        # Predicciones
        return {
            'work_under_pressure': STRESS_MODEL.predict_proba(df)[0][1],  # RF 3.2.10
            'emotional_intelligence': EI_MODEL.predict(df)[0],  # p.11
            'question_categories': question_types  # Para heatmaps
        }
    except Exception as e:
        return {'error': str(e)}


def generate_visualizations(test_id, candidate_id):
    """Genera gráficas para el frontend (RF 3.2.10)"""
    from matplotlib import pyplot as plt
    import seaborn as sns
    import base64
    from io import BytesIO

    # 1. Heatmap por categorías
    results = result_collection.find({"test_id": ObjectId(test_id)})
    data = pd.DataFrame([r['responses'] for r in results])

    plt.figure(figsize=(10, 6))
    sns.heatmap(data.corr(), annot=True)
    buf = BytesIO()
    plt.savefig(buf, format='png')
    heatmap = base64.b64encode(buf.getvalue()).decode('utf-8')
    plt.close()

    # 2. Gráfico radial por competencia (ejemplo)
    candidate = candidate_collection.find_one({"_id": ObjectId(candidate_id)})
    scores = candidate.get('category_scores', {})

    categories = list(scores.keys())
    values = list(scores.values())

    plt.figure(figsize=(6, 6))
    ax = plt.subplot(polar=True)
    ax.fill(categories, values, 'b', alpha=0.1)
    buf = BytesIO()
    plt.savefig(buf, format='png')
    radar = base64.b64encode(buf.getvalue()).decode('utf-8')
    plt.close()

    return {
        'heatmap': f"data:image/png;base64,{heatmap}",
        'radar_chart': f"data:image/png;base64,{radar}"
    }


def aggregate_results(results):
    """Agrega métricas para dashboard RRHH (RF 3.2.12)"""
    if not results:
        return {}

    df = pd.DataFrame([{
        'candidate_id': r['candidate_id'],
        'test_id': r['test_id'],
        **r.get('ia_analysis', {})
    } for r in results])

    return {
        'avg_stress': df['work_under_pressure'].mean(),
        'ei_distribution': df['emotional_intelligence'].value_counts().to_dict(),
        'test_metrics': df.groupby('test_id').mean().to_dict('index')
    }