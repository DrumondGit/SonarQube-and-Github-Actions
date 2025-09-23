import os
import pandas as pd
import subprocess
import requests
import time

def get_sonar_metrics(project_key):
    """Coleta métricas do SonarQube via API."""
    SONAR_URL = os.environ.get('SONAR_URL', 'http://localhost:9000')
    SONAR_TOKEN = os.environ.get('SONAR_TOKEN')
    
    # Espera um pouco para garantir que a análise foi processada
    time.sleep(15)  # Aumente o tempo se necessário
    
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
        # Aqui você pode implementar a lógica para extrair as métricas
        # do output do npm test, dependendo do formato do seu relatório
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

if __name__ == "__main__":
    main()