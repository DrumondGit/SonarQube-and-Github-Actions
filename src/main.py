import os
import pandas as pd
import subprocess
import requests
import time

def get_sonar_metrics(project_key):
    """Coleta métricas do SonarQube via API."""
    SONAR_URL = os.environ.get('SONAR_URL', 'http://localhost:9000')
    SONAR_TOKEN = os.environ.get('SONAR_TOKEN')
    
    # Espera para garantir que a análise foi processada
    time.sleep(20)
    
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
        # Tenta ler do arquivo de cobertura LCOV
        lcov_file = os.path.join(repo_path, 'coverage', 'lcov.info')
        if os.path.exists(lcov_file):
            with open(lcov_file, 'r') as f:
                lcov_content = f.read()
                lines_found = 0
                lines_hit = 0
                
                for line in lcov_content.split('\n'):
                    if line.startswith('LF:'):
                        lines_found = int(line.split(':')[1])
                    elif line.startswith('LH:'):
                        lines_hit = int(line.split(':')[1])
                
                if lines_found > 0:
                    metrics['test_coverage'] = round((lines_hit / lines_found) * 100, 2)
                    print(f"Cobertura calculada: {metrics['test_coverage']}% ({lines_hit}/{lines_found} linhas)")
        
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
    
    # Configuração do SonarScanner
    sonar_properties = [
        "sonar-scanner",
        f"-Dsonar.projectKey={project_key}",
        f"-Dsonar.organization={organization}",
        f"-Dsonar.sources=lib,src",
        f"-Dsonar.host.url={SONAR_URL}",
        f"-Dsonar.login={SONAR_TOKEN}",
        "-Dsonar.sourceEncoding=UTF-8",
        "-Dsonar.verbose=true"
    ]
    
    # Adiciona cobertura se existir
    lcov_path = os.path.join(repo_path, 'coverage', 'lcov.info')
    if os.path.exists(lcov_path):
        sonar_properties.append(f"-Dsonar.javascript.lcov.reportPaths={lcov_path}")
        print(f"Usando arquivo de cobertura: {lcov_path}")
    else:
        print("Arquivo de cobertura não encontrado")
    
    try:
        result = subprocess.run(sonar_properties, cwd=repo_path, capture_output=True, text=True)
        print("Saída do SonarScanner:")
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

def run_npm_test(repo_path):
    print(f"Executando npm test em: {repo_path}")
    try:
        # Executa apenas os testes unitários (test:node) que são mais estáveis
        result = subprocess.run(["npm", "run", "test:node"], cwd=repo_path, capture_output=True, text=True)
        
        print("Output do npm test:node:")
        print(result.stdout[:1000] + "..." if len(result.stdout) > 1000 else result.stdout)
        
        if result.returncode != 0:
            print(f"Aviso: npm test:node retornou código {result.returncode}")
        
        return result.stdout
        
    except Exception as e:
        print(f"Falha ao executar npm test: {e}")
        return None

def main():
    REPOS_DIR = 'repos'
    
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
        
        print(f"\n=== Processando {repo} ===")
        
        # Executa npm test
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
        else:
            print(f"Falha na análise SonarQube para {repo}")
        
        sonar_results.append(result)
        print(f"=== Concluído {repo} ===\n")

    # Gera artefato CSV
    if sonar_results:
        df = pd.DataFrame(sonar_results)
        
        # Reordena as colunas
        columns_order = ['repo', 'bugs', 'vulnerabilities', 'code_smells', 
                        'coverage', 'test_coverage', 'ncloc', 'complexity',
                        'duplicated_lines_density', 'security_hotspots',
                        'reliability_rating', 'security_rating', 'sqale_rating',
                        'test_success_density', 'test_passed', 'test_failed']
        
        existing_columns = [col for col in columns_order if col in df.columns]
        if existing_columns:
            df = df[existing_columns]
        
        df.to_csv("sonar_analysis_results.csv", index=False)
        print("Artefato CSV gerado: sonar_analysis_results.csv")
        print("\nResumo dos resultados:")
        print(df.to_string(index=False))
    else:
        print("Nenhum resultado para gerar CSV")

if __name__ == "__main__":
    main()