import seaborn as sns
import matplotlib.pyplot as plt
from io import BytesIO
import base64


def generate_heatmap(correlation_matrix):
    """Generar heatmap para correlaciones (RF 3.2.10)"""
    plt.figure(figsize=(10, 8))
    sns.heatmap(correlation_matrix, annot=True, cmap='coolwarm')

    # Convertir a base64 para HTML
    buf = BytesIO()
    plt.savefig(buf, format='png')
    return base64.b64encode(buf.getvalue()).decode('utf-8')


def generate_scatter_plot(x, y):
    """Gráfico de dispersión estrés vs productividad (p.12)"""
    plt.figure(figsize=(10, 6))
    sns.scatterplot(x=x, y=y, hue=y, palette='viridis')
    plt.xlabel('Nivel de Estrés')
    plt.ylabel('Productividad')

    buf = BytesIO()
    plt.savefig(buf, format='png')
    return base64.b64encode(buf.getvalue()).decode('utf-8')