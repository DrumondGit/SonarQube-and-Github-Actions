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
    
    print("Verificando estrutura do projeto...")
    project_structure = os.listdir(repo_path)
    print(f"Conteúdo do diretório: {project_structure}")
    
    source_dirs = []
    possible_sources = ['lib', 'src', 'dist', 'build', 'js', 'javascript']
    
    for possible_dir in possible_sources:
        if os.path.exists(os.path.join(repo_path, possible_dir)):
            source_dirs.append(possible_dir)
            print(f"✅ Diretório fonte encontrado: {possible_dir}")
    
    if not source_dirs:
        print("ℹ️  Usando diretório raiz como fonte")
        source_dirs = ['.']
    else:
        source_dirs = ['.']
    
    sources_param = ','.join(source_dirs)
    
    cmd = [
        "sonar-scanner",
        f"-Dsonar.projectKey={project_key}",
        f"-Dsonar.organization={organization}",
        f"-Dsonar.sources=.",  # Usa diretório raiz que contém 'lib'
        f"-Dsonar.host.url={SONAR_URL}",
        f"-Dsonar.login={SONAR_TOKEN}",
        "-Dsonar.sourceEncoding=UTF-8",
        "-Dsonar.verbose=true",
        "-Dsonar.scm.disabled=true",
        "-Dsonar.exclusions=node_modules/**,test/**,**/*.test.js,**/*.spec.js"
    ]
    
    package_json = os.path.join(repo_path, 'package.json')
    if os.path.exists(package_json):
        cmd.append("-Dsonar.lang.patterns.js=**/*.js")
    
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
            
            return analyze_repo_fallback(repo_path, repo_name)
        else:
            print(f"✅ Análise concluída para {repo_name}")
            return project_key
    except Exception as e:
        print(f"❌ Falha ao analisar {repo_name}: {e}")
        return analyze_repo_fallback(repo_path, repo_name)

def analyze_repo_fallback(repo_path, repo_name):
    """Análise alternativa com configuração mínima."""
    print(f"Tentando análise alternativa para {repo_name}...")
    
    SONAR_TOKEN = os.environ.get('SONAR_TOKEN')
    SONAR_URL = os.environ.get('SONAR_URL', 'https://sonarcloud.io')
    project_key = f"{repo_name}".replace('/', '_')
    organization = os.environ.get('SONAR_ORGANIZATION', 'drumondgit')
    
    cmd = [
        "sonar-scanner",
        f"-Dsonar.projectKey={project_key}",
        f"-Dsonar.organization={organization}",
        f"-Dsonar.sources=.",  # Apenas diretório raiz
        f"-Dsonar.host.url={SONAR_URL}",
        f"-Dsonar.login={SONAR_TOKEN}",
        "-Dsonar.sourceEncoding=UTF-8",
        "-Dsonar.scm.disabled=true",
        "-Dsonar.exclusions=node_modules/**,test/**,**/*.test.js,**/*.spec.js,coverage/**,dist/**,build/**"
    ]
    
    try:
        result = subprocess.run(cmd, cwd=repo_path, capture_output=True, text=True)
        print("=== SAÍDA DA ANÁLISE ALTERNATIVA ===")
        print(result.stdout)
        
        if result.returncode == 0:
            print(f"✅ Análise alternativa concluída para {repo_name}")
            return project_key
        else:
            print(f"❌ Análise alternativa também falhou para {repo_name}")
            return None
    except Exception as e:
        print(f"❌ Falha na análise alternativa: {e}")
        return None

def get_sonar_metrics(project_key):
    """Coleta métricas do SonarQube via API."""
    SONAR_URL = os.environ.get('SONAR_URL', 'https://sonarcloud.io')
    SONAR_TOKEN = os.environ.get('SONAR_TOKEN')
    
    if not SONAR_TOKEN:
        print("❌ SONAR_TOKEN não encontrado")
        return {}
    
    print(f"Buscando métricas para projeto: {project_key}")
    
    time.sleep(20)
    
    metrics = [
        'bugs', 'code_smells', 'vulnerabilities', 'coverage',
        'duplicated_lines_density', 'ncloc', 'complexity',
        'security_hotspots', 'reliability_rating', 'security_rating',
        'sqale_rating'
    ]
    
    try:
        url = f"{SONAR_URL}/api/measures/component"
        params = {'component': project_key, 'metricKeys': ','.join(metrics)}
        headers = {'Authorization': f'Bearer {SONAR_TOKEN}'}
        
        response = requests.get(url, params=params, headers=headers, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            
            if 'component' in data and 'measures' in data['component']:
                metrics_dict = {measure['metric']: measure['value'] 
                              for measure in data['component']['measures']}
                print(f"✅ Métricas coletadas: {len(metrics_dict)} itens")
                return metrics_dict
            else:
                print("ℹ️  Nenhuma métrica disponível (projeto pode não existir)")
                return {}
        else:
            print(f"ℹ️  Projeto {project_key} não encontrado ou sem métricas")
            return {}
            
    except Exception as e:
        print(f"❌ Erro ao buscar métricas: {e}")
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