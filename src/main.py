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
        # Procura por padrões comuns de relatório de cobertura
        lines = test_output.split('\n')
        
        for line in lines:
            # Procura por padrões de cobertura (exemplos comuns)
            if 'Coverage:' in line and '%' in line:
                # Exemplo: "Coverage: 85.5%"
                parts = line.split()
                for part in parts:
                    if '%' in part:
                        coverage_str = part.replace('%', '')
                        try:
                            metrics['test_coverage'] = float(coverage_str)
                            break
                        except ValueError:
                            continue
            
            # Procura por estatísticas de testes
            elif 'passing' in line.lower() and 'failing' in line.lower():
                # Exemplo: "10 passing, 2 failing"
                import re
                passing_match = re.search(r'(\d+)\s+passing', line)
                failing_match = re.search(r'(\d+)\s+failing', line)
                
                if passing_match:
                    metrics['test_passed'] = int(passing_match.group(1))
                if failing_match:
                    metrics['test_failed'] = int(failing_match.group(1))
            
            # Padrão do Jest/Mocha com cobertura
            elif 'All files' in line and '|' in line:
                # Exemplo: "All files | 85.71 | 100 | 80 | 85.71 |"
                parts = line.split('|')
                if len(parts) > 2:
                    try:
                        metrics['test_coverage'] = float(parts[1].strip())
                        break
                    except ValueError:
                        continue
        
        # Se não encontrou cobertura no output, tenta ler do arquivo lcov
        if metrics['test_coverage'] == 0:
            coverage_file = os.path.join('repos/axios', 'coverage', 'coverage-summary.json')
            if os.path.exists(coverage_file):
                import json
                with open(coverage_file, 'r') as f:
                    coverage_data = json.load(f)
                    if 'total' in coverage_data and 'lines' in coverage_data['total']:
                        metrics['test_coverage'] = coverage_data['total']['lines']['pct']
            
            # Tenta ler do arquivo lcov.info
            lcov_file = os.path.join('repos/axios', 'coverage', 'lcov.info')
            if os.path.exists(lcov_file) and metrics['test_coverage'] == 0:
                with open(lcov_file, 'r') as f:
                    lcov_content = f.read()
                    if 'LF:' in lcov_content and 'LH:' in lcov_content:
                        import re
                        lf_match = re.search(r'LF:(\d+)', lcov_content)
                        lh_match = re.search(r'LH:(\d+)', lcov_content)
                        if lf_match and lh_match:
                            lf = int(lf_match.group(1))
                            lh = int(lh_match.group(1))
                            if lf > 0:
                                metrics['test_coverage'] = round((lh / lf) * 100, 2)
        
        print(f"Métricas extraídas: {metrics}")
        
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
        
        # Verifica arquivos de cobertura antes de executar testes
        print(f"Verificando cobertura em: {repo_path}")
        check_coverage_files(repo_path)
        
        # Executa npm test e coleta métricas PRIMEIRO
        test_output = run_npm_test(repo_path)
        
        # Verifica novamente após executar testes
        check_coverage_files(repo_path)
        
        result = {"repo": repo}
        
        # Extrai métricas do npm test
        if test_output:
            npm_metrics = get_npm_test_metrics(test_output)
            result.update(npm_metrics)
        
        # Executa análise SonarQube e obtém o project_key
        project_key = analyze_repo(repo_path, repo)
        
        if project_key:
            # Coleta métricas do SonarQube
            sonar_metrics = get_sonar_metrics(project_key)
            result.update(sonar_metrics)
        
        sonar_results.append(result)

    # Resto do código permanece igual...

if __name__ == "__main__":
    main()






