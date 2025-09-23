import os
import pandas as pd
import subprocess
import requests
import time
import json


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
            return {}
    except Exception as e:
        print(f"Erro ao buscar métricas do SonarQube: {e}")
        return {}

def get_npm_test_metrics(repo_path):
    """Extrai métricas dos testes npm."""
    metrics = {
        'test_passed': 0,
        'test_failed': 0,
        'test_coverage': 0
    }
    
    try:
        # Tenta ler do arquivo de cobertura se existir
        lcov_file = os.path.join(repo_path, 'coverage', 'lcov.info')
        if os.path.exists(lcov_file):
            with open(lcov_file, 'r') as f:
                lcov_content = f.read()
                # Calcula cobertura baseada no LCOV
                lines_found = 0
                lines_hit = 0
                
                for line in lcov_content.split('\n'):
                    if line.startswith('LF:'):
                        lines_found = int(line.split(':')[1])
                    elif line.startswith('LH:'):
                        lines_hit = int(line.split(':')[1])
                
                if lines_found > 0:
                    metrics['test_coverage'] = round((lines_hit / lines_found) * 100, 2)
        
        # Tenta extrair estatísticas de testes do console
        package_file = os.path.join(repo_path, 'package.json')
        if os.path.exists(package_file):
            with open(package_file, 'r') as f:
                package_data = json.load(f)
                scripts = package_data.get('scripts', {})
                print(f"Scripts disponíveis: {list(scripts.keys())}")
        
        print(f"Métricas de teste extraídas: {metrics}")
        
    except Exception as e:
        print(f"Erro ao extrair métricas de teste: {e}")
    
    return metrics

def analyze_repo(repo_path, repo_name):
    print(f"Analisando repositório: {repo_name}")
    SONAR_TOKEN = os.environ.get('SONAR_TOKEN')
    SONAR_URL = os.environ.get('SONAR_URL', 'http://localhost:9000')
    project_key = f"{repo_name}".replace('/', '_')
    organization = os.environ.get('SONAR_ORGANIZATION', 'drumondgit')
    
    # Verifica se existe arquivo de cobertura
    lcov_path = os.path.join(repo_path, 'coverage', 'lcov.info')
    sonar_properties = [
        "sonar-scanner",
        f"-Dsonar.projectKey={project_key}",
        f"-Dsonar.organization={organization}",
        f"-Dsonar.sources=.",
        f"-Dsonar.host.url={SONAR_URL}",
        f"-Dsonar.login={SONAR_TOKEN}",
        "-Dsonar.sourceEncoding=UTF-8",
        "-Dsonar.verbose=true"
    ]
    
    if os.path.exists(lcov_path):
        sonar_properties.append(f"-Dsonar.javascript.lcov.reportPaths={lcov_path}")
        print(f"Usando arquivo de cobertura: {lcov_path}")
    else:
        print("Arquivo de cobertura não encontrado, análise sem dados de cobertura")
    
    try:
        result = subprocess.run(sonar_properties, cwd=repo_path, capture_output=True, text=True)
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
        # Primeiro verifica quais scripts estão disponíveis
        result_scripts = subprocess.run(["npm", "run"], cwd=repo_path, capture_output=True, text=True)
        print("Scripts disponíveis:")
        print(result_scripts.stdout)
        
        # Tenta executar o teste padrão
        result = subprocess.run(["npm", "test"], cwd=repo_path, capture_output=True, text=True)
        print("Output do npm test:")
        print(result.stdout[:1000] + "..." if len(result.stdout) > 1000 else result.stdout)
        
        if result.returncode != 0:
            print(f"Aviso: npm test retornou código {result.returncode}")
            print(f"Stderr: {result.stderr}")
        
        return result.stdout
        
    except Exception as e:
        print(f"Falha ao executar npm test: {e}")
        return None

def run_npm_test(repo_path):
    print(f"Executando npm test em: {repo_path}")
    try:
        # Primeiro, verifica se há script de cobertura
        result_check = subprocess.run(["npm", "run"], cwd=repo_path, capture_output=True, text=True)
        
        if 'test:coverage' in result_check.stdout:
            # Usa script específico de cobertura se existir
            result = subprocess.run(["npm", "run", "test:coverage"], cwd=repo_path, capture_output=True, text=True)
        else:
            # Tenta com --coverage
            result = subprocess.run(["npm", "test", "--", "--coverage"], cwd=repo_path, capture_output=True, text=True)
        
        print("Output do npm test:")
        print(result.stdout)
        
        if result.returncode != 0:
            print(f"Aviso: npm test retornou código {result.returncode}")
            print(f"Stderr: {result.stderr}")
        
        print("Cobertura de testes capturada com sucesso.")
        return result.stdout
        
    except Exception as e:
        print(f"Falha ao executar npm test: {e}")
        return None
    
def check_coverage_files(repo_path):
    """Verifica se arquivos de cobertura foram gerados."""
    coverage_dir = os.path.join(repo_path, 'coverage')
    if os.path.exists(coverage_dir):
        print("Arquivos de cobertura encontrados:")
        for root, dirs, files in os.walk(coverage_dir):
            for file in files:
                print(f"  {os.path.join(root, file)}")
        return True
    else:
        print("Diretório de cobertura não encontrado")
        return False    

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
        
        # Executa npm test primeiro
        test_output = run_npm_test(repo_path)
        
        result = {"repo": repo}
        
        # Extrai métricas do npm test
        npm_metrics = get_npm_test_metrics(repo_path)
        result.update(npm_metrics)
        
        # Executa análise SonarQube
        project_key = analyze_repo(repo_path, repo)
        
        if project_key:
            # Coleta métricas do SonarQube
            sonar_metrics = get_sonar_metrics(project_key)
            result.update(sonar_metrics)
        
        sonar_results.append(result)

    # Gera artefato CSV
    df = pd.DataFrame(sonar_results)
    
    # Reordena as colunas
    columns_order = ['repo', 'bugs', 'vulnerabilities', 'code_smells', 
                    'coverage', 'test_coverage', 'ncloc', 'complexity',
                    'duplicated_lines_density', 'security_hotspots',
                    'reliability_rating', 'security_rating', 'sqale_rating',
                    'test_success_density', 'test_passed', 'test_failed']
    
    existing_columns = [col for col in columns_order if col in df.columns]
    df = df[existing_columns]
    
    df.to_csv("sonar_analysis_results.csv", index=False)
    print("Artefato CSV gerado: sonar_analysis_results.csv")
    print(df)

if __name__ == "__main__":
    main()






