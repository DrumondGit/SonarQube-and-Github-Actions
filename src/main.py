import os
import pandas as pd
import subprocess
import requests
import time
import matplotlib.pyplot as plt
import seaborn as sns

def get_sonar_metrics(project_key):
    """Coleta métricas do SonarQube via API."""
    SONAR_URL = os.environ.get('SONAR_URL', 'http://localhost:9000')
    SONAR_TOKEN = os.environ.get('SONAR_TOKEN')
    
    # Espera um pouco para garantir que a análise foi processada
    time.sleep(15)
    
    metrics = [
        'bugs', 'code_smells', 'vulnerabilities', 'coverage',
        'duplicated_lines_density', 'ncloc', 'complexity',
        'security_hotspots', 'reliability_rating', 'security_rating',
        'sqale_rating', 'test_success_density'
    ]
    
    try:
        url = f"{SONAR_URL}/api/measures/component"
        params = {
            'component': project_key,
            'metricKeys': ','.join(metrics)
        }
        headers = {'Authorization': f'Bearer {SONAR_TOKEN}'}
        
        response = requests.get(url, params=params, headers=headers)
        if response.status_code == 200:
            data = response.json()
            if 'component' in data and 'measures' in data['component']:
                return {measure['metric']: measure['value'] 
                       for measure in data['component']['measures']}
            else:
                print(f"Estrutura de resposta inesperada: {data}")
                return {}
        else:
            print(f"Erro ao buscar métricas: {response.status_code}")
            print(f"Resposta: {response.text}")
            return {}
    except Exception as e:
        print(f"Erro ao buscar métricas do SonarQube: {e}")
        return {}

def get_npm_test_metrics(test_output):
    """Extrai métricas dos testes npm."""
    metrics = {
        'test_passed': 0,
        'test_failed': 0,
        'test_coverage': 0
    }
    
    try:
        if 'test_coverage' in test_output:
            metrics['test_coverage'] = float(test_output.split('coverage: ')[1].split('%')[0])
    except Exception as e:
        print(f"Erro ao extrair métricas de teste: {e}")
    
    return metrics

def analyze_repo(repo_path, repo_name):
    print(f"Analisando repositório: {repo_name}")
    SONAR_TOKEN = os.environ.get('SONAR_TOKEN')
    SONAR_URL = os.environ.get('SONAR_URL', 'http://localhost:9000')
    project_key = f"{repo_name}".replace('/', '_')
    organization = os.environ.get('SONAR_ORGANIZATION', 'drumondgit')
    
    cmd = [
        "sonar-scanner",
        f"-Dsonar.projectKey={project_key}",
        f"-Dsonar.organization={organization}",
        f"-Dsonar.sources=.",
        f"-Dsonar.host.url={SONAR_URL}",
        f"-Dsonar.login={SONAR_TOKEN}",
        "-Dsonar.java.binaries=.",
        "-Dsonar.sourceEncoding=UTF-8",
        "-Dsonar.javascript.lcov.reportPaths=coverage/lcov.info",
        "-Dsonar.verbose=true"
    ]
    try:
        result = subprocess.run(cmd, cwd=repo_path, capture_output=True, text=True)
        print(result.stdout)
        if result.returncode != 0:
            print(f"Erro ao analisar {repo_name}: {result.stderr}")
            return None
        else:
            print(f"Análise concluída para {repo_name}")
            return project_key
    except Exception as e:
        print(f"Falha ao analisar {repo_name}: {e}")
        return None

REPOS_DIR = 'repos'

def run_npm_test(repo_path):
    print(f"Executando npm test em: {repo_path}")
    try:
        result = subprocess.run(["npm", "test", "--", "--coverage"], cwd=repo_path, capture_output=True, text=True)
        print(result.stdout)
        if result.returncode != 0:
            print(f"Erro ao executar npm test: {result.stderr}")
            return None
        else:
            print("Cobertura de testes capturada com sucesso.")
            return result.stdout
    except Exception as e:
        print(f"Falha ao executar npm test: {e}")
        return None

def generate_simple_report(csv_file='sonar_analysis_results.csv'):
    """
    Gera um relatório PNG simples sem gráfico de cobertura
    """
    if not os.path.exists(csv_file):
        print(f"Arquivo {csv_file} não encontrado!")
        return
    
    try:
        df = pd.read_csv(csv_file)
        print("Dados carregados com sucesso para geração de relatório!")
    except Exception as e:
        print(f"Erro ao ler o arquivo: {e}")
        return
    
    # Configuração do estilo
    plt.style.use('default')
    sns.set_palette("husl")
    
    # Cria figura com 2x2 grid (removemos o gráfico de cobertura)
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    fig.suptitle('Relatório SonarQube - Análise de Qualidade de Código', fontsize=16, fontweight='bold')
    
    # Gráfico 1: Problemas Encontrados (Bugs, Vulnerabilidades, Code Smells)
    if all(col in df.columns for col in ['bugs', 'vulnerabilities', 'code_smells']):
        issues_data = df[['bugs', 'vulnerabilities', 'code_smells']].iloc[0]
        bars = axes[0, 0].bar(['Bugs', 'Vulnerabilidades', 'Code Smells'], issues_data.values, 
                            color=['#ff6b6b', '#ffa726', '#42a5f5'])
        axes[0, 0].set_title('Problemas Identificados', fontweight='bold')
        axes[0, 0].set_ylabel('Quantidade')
        
        # Adiciona valores nas barras
        for bar, value in zip(bars, issues_data.values):
            height = bar.get_height()
            axes[0, 0].text(bar.get_x() + bar.get_width()/2., height + 1,
                           f'{int(value)}', ha='center', va='bottom')
    
    # Gráfico 2: Ratings de Qualidade
    if all(col in df.columns for col in ['reliability_rating', 'security_rating', 'sqale_rating']):
        ratings_data = df[['reliability_rating', 'security_rating', 'sqale_rating']].iloc[0]
        bars = axes[0, 1].bar(['Confiabilidade', 'Segurança', 'Manutenibilidade'], 
                            ratings_data.values, color=['#ab47bc', '#ec407a', '#ffca28'])
        axes[0, 1].set_title('Ratings de Qualidade (1-5)', fontweight='bold')
        axes[0, 1].set_ylim(0, 5)
        
        for bar, value in zip(bars, ratings_data.values):
            height = bar.get_height()
            axes[0, 1].text(bar.get_x() + bar.get_width()/2., height + 0.1,
                           f'{value}', ha='center', va='bottom')
    
    # Gráfico 3: Complexidade vs Tamanho
    if all(col in df.columns for col in ['complexity', 'ncloc']):
        axes[1, 0].scatter(df['ncloc'], df['complexity'], s=100, alpha=0.7, color='purple')
        axes[1, 0].set_xlabel('Linhas de Código (NCLOC)')
        axes[1, 0].set_ylabel('Complexidade Ciclomática')
        axes[1, 0].set_title('Complexidade vs Tamanho do Código', fontweight='bold')
        axes[1, 0].grid(True, alpha=0.3)
        
        # Adiciona label do repositório
        for i, row in df.iterrows():
            axes[1, 0].annotate(row['repo'], (row['ncloc'], row['complexity']), 
                              xytext=(10, 10), textcoords='offset points',
                              bbox=dict(boxstyle='round,pad=0.3', facecolor='yellow', alpha=0.7))
    
    # Gráfico 4: Hotspots de Segurança e Duplicação
    if all(col in df.columns for col in ['security_hotspots', 'duplicated_lines_density']):
        security_data = df['security_hotspots'].iloc[0]
        duplication_data = df['duplicated_lines_density'].iloc[0]
        
        categories = ['Hotspots Segurança', 'Duplicação (%)']
        values = [security_data, duplication_data]
        colors = ['#ef5350', '#26a69a']
        
        bars = axes[1, 1].bar(categories, values, color=colors)
        axes[1, 1].set_title('Segurança e Duplicação', fontweight='bold')
        axes[1, 1].set_ylabel('Valor')
        
        for bar, value in zip(bars, values):
            height = bar.get_height()
            axes[1, 1].text(bar.get_x() + bar.get_width()/2., height + max(values)*0.05,
                           f'{value}', ha='center', va='bottom')
    
    # Ajusta layout
    plt.tight_layout()
    plt.subplots_adjust(top=0.93)
    
    # Salva o relatório
    plt.savefig('sonar_report.png', dpi=300, bbox_inches='tight')
    print("Relatório PNG gerado: sonar_report.png")
    plt.close()  # Fecha a figura para liberar memória

def generate_metrics_summary(csv_file='sonar_analysis_results.csv'):
    """
    Gera um resumo simples das métricas principais
    """
    if not os.path.exists(csv_file):
        return
    
    df = pd.read_csv(csv_file)
    
    # Cria um gráfico de resumo simples
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Métricas principais para o resumo
    main_metrics = ['bugs', 'vulnerabilities', 'code_smells', 'security_hotspots']
    metrics_data = []
    labels = []
    
    for metric in main_metrics:
        if metric in df.columns:
            value = df[metric].iloc[0]
            metrics_data.append(value)
            labels.append(metric.replace('_', ' ').title())
    
    # Gráfico de barras horizontal
    bars = ax.barh(labels, metrics_data, color=['#e74c3c', '#f39c12', '#3498db', '#9b59b6'])
    ax.set_xlabel('Quantidade')
    ax.set_title('Resumo das Métricas Principais', fontsize=14, fontweight='bold')
    ax.grid(axis='x', alpha=0.3)
    
    # Adiciona valores nas barras
    for bar, value in zip(bars, metrics_data):
        width = bar.get_width()
        ax.text(width + max(metrics_data)*0.01, bar.get_y() + bar.get_height()/2, 
                f'{int(value)}', ha='left', va='center', fontweight='bold')
    
    plt.tight_layout()
    plt.savefig('sonar_summary.png', dpi=300, bbox_inches='tight')
    print("Resumo PNG gerado: sonar_summary.png")
    plt.close()

def main():
    if not os.path.exists(REPOS_DIR):
        print(f"Diretório '{REPOS_DIR}' não encontrado.")
        return
    
    repos = [d for d in os.listdir(REPOS_DIR) if os.path.isdir(os.path.join(REPOS_DIR, d))]
    if not repos:
        print("Nenhum repositório encontrado na pasta 'repos'.")
        return
    
    sonar_results = []
    for repo in repos:
        repo_path = os.path.join(REPOS_DIR, repo)
        
        # Executa análise SonarQube e obtém o project_key
        project_key = analyze_repo(repo_path, repo)
        
        result = {"repo": repo}
        
        if project_key:
            # Coleta métricas do SonarQube
            sonar_metrics = get_sonar_metrics(project_key)
            result.update(sonar_metrics)
        
        # Executa npm test e coleta métricas
        test_output = run_npm_test(repo_path)
        if test_output:
            npm_metrics = get_npm_test_metrics(test_output)
            result.update(npm_metrics)
        
        sonar_results.append(result)

    # Gera artefato CSV com todas as métricas
    df = pd.DataFrame(sonar_results)
    
    # Reordena as colunas para melhor visualização
    columns_order = ['repo', 'bugs', 'vulnerabilities', 'code_smells', 
                    'coverage', 'test_coverage', 'ncloc', 'complexity',
                    'duplicated_lines_density', 'security_hotspots',
                    'reliability_rating', 'security_rating', 'sqale_rating',
                    'test_success_density', 'test_passed', 'test_failed']
    
    # Reordena apenas as colunas que existem no DataFrame
    existing_columns = [col for col in columns_order if col in df.columns]
    df = df[existing_columns]
    
    df.to_csv("sonar_analysis_results.csv", index=False)
    print("Artefato CSV gerado: sonar_analysis_results.csv")

    # Gera os relatórios em PNG
    print("Gerando relatórios em PNG...")
    generate_simple_report()
    generate_metrics_summary()
    
    print("Relatórios gerados com sucesso!")
    print("Arquivos criados:")
    print("- sonar_analysis_results.csv")
    print("- sonar_report.png (Relatório completo)")
    print("- sonar_summary.png (Resumo das métricas)")

if __name__ == "__main__":
    main()