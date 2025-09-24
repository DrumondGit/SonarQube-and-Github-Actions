import os
import subprocess
import requests
import time

def analyze_repo(repo_path, repo_name):
    """Executa análise SonarQube no repositório."""
    print(f"Analisando repositório: {repo_name}")
    SONAR_TOKEN = os.environ.get('SONAR_TOKEN')
    SONAR_URL = os.environ.get('SONAR_URL', 'https://sonarcloud.io')
    project_key = f"{repo_name}".replace('/', '_')
    organization = os.environ.get('SONAR_ORGANIZATION', 'drumondgit')
    
    # Configuração mais completa do SonarScanner
    cmd = [
        "sonar-scanner",
        f"-Dsonar.projectKey={project_key}",
        f"-Dsonar.organization={organization}",
        f"-Dsonar.sources=lib,src",  # Diretórios específicos do código
        f"-Dsonar.host.url={SONAR_URL}",
        f"-Dsonar.login={SONAR_TOKEN}",
        "-Dsonar.sourceEncoding=UTF-8",
        "-Dsonar.verbose=true",
        "-Dsonar.scm.disabled=true"  # Desabilita SCM para repositórios clonados
    ]
    
    # Adiciona configuração de cobertura se existir
    lcov_path = os.path.join(repo_path, 'coverage', 'lcov.info')
    if os.path.exists(lcov_path):
        cmd.append(f"-Dsonar.javascript.lcov.reportPaths={lcov_path}")
        print(f"Usando arquivo de cobertura: {lcov_path}")
    
    print(f"Comando SonarScanner: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, cwd=repo_path, capture_output=True, text=True)
        print("=== SAÍDA DO SONARSCANNER ===")
        print(result.stdout)
        
        if result.stderr:
            print("=== ERROS DO SONARSCANNER ===")
            print(result.stderr)
        
        if result.returncode != 0:
            print(f"❌ Erro ao analisar {repo_name} (código: {result.returncode})")
            return None
        else:
            print(f"✅ Análise concluída para {repo_name}")
            return project_key
    except Exception as e:
        print(f"❌ Falha ao analisar {repo_name}: {e}")
        return None

def get_sonar_metrics(project_key):
    """Coleta métricas do SonarQube via API."""
    SONAR_URL = os.environ.get('SONAR_URL', 'https://sonarcloud.io')
    SONAR_TOKEN = os.environ.get('SONAR_TOKEN')
    
    if not SONAR_TOKEN:
        print("❌ SONAR_TOKEN não encontrado")
        return {}
    
    print(f"Buscando métricas para projeto: {project_key}")
    
    # Espera mais tempo para garantir que a análise foi processada
    time.sleep(30)
    
    metrics = [
        'bugs', 'code_smells', 'vulnerabilities', 'coverage',
        'duplicated_lines_density', 'ncloc', 'complexity',
        'security_hotspots', 'reliability_rating', 'security_rating',
        'sqale_rating'
    ]
    
    try:
        url = f"{SONAR_URL}/api/measures/component"
        params = {
            'component': project_key, 
            'metricKeys': ','.join(metrics)
        }
        headers = {'Authorization': f'Bearer {SONAR_TOKEN}'}
        
        print(f"Fazendo requisição para: {url}")
        print(f"Parâmetros: {params}")
        
        response = requests.get(url, params=params, headers=headers, timeout=30)
        
        print(f"Status code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("Resposta da API recebida com sucesso")
            
            if 'component' in data and 'measures' in data['component']:
                metrics_dict = {measure['metric']: measure['value'] 
                              for measure in data['component']['measures']}
                print(f"Métricas coletadas: {metrics_dict}")
                return metrics_dict
            else:
                print("❌ Estrutura de resposta inesperada")
                print(f"Resposta: {data}")
                return {}
        else:
            print(f"❌ Erro na API: {response.status_code}")
            print(f"Resposta: {response.text}")
            return {}
            
    except requests.exceptions.Timeout:
        print("❌ Timeout na requisição da API")
        return {}
    except Exception as e:
        print(f"❌ Erro ao buscar métricas do SonarQube: {e}")
        return {}

def check_project_exists(project_key):
    """Verifica se o projeto existe no SonarCloud."""
    SONAR_URL = os.environ.get('SONAR_URL', 'https://sonarcloud.io')
    SONAR_TOKEN = os.environ.get('SONAR_TOKEN')
    
    try:
        url = f"{SONAR_URL}/api/components/show"
        params = {'component': project_key}
        headers = {'Authorization': f'Bearer {SONAR_TOKEN}'}
        
        response = requests.get(url, params=params, headers=headers)
        return response.status_code == 200
    except:
        return False