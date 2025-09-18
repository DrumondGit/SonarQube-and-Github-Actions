# sonar_analyser.py
import os
import subprocess
import sys

SONAR_TOKEN = os.environ.get('SONAR_TOKEN')
SONAR_URL = os.environ.get('SONAR_URL', 'http://localhost:9000')
REPOS_DIR = 'repos'


def analyze_repo(repo_path, repo_name):
    print(f"Analisando repositório: {repo_name}")
    project_key = f"{repo_name}".replace('/', '_')
    cmd = [
        "sonar-scanner",
        f"-Dsonar.projectKey={project_key}",
        f"-Dsonar.sources=.",
        f"-Dsonar.host.url={SONAR_URL}",
        f"-Dsonar.login={SONAR_TOKEN}"
    ]
    try:
        result = subprocess.run(cmd, cwd=repo_path, capture_output=True, text=True)
        print(result.stdout)
        if result.returncode != 0:
            print(f"Erro ao analisar {repo_name}: {result.stderr}")
        else:
            print(f"Análise concluída para {repo_name}")
    except Exception as e:
        print(f"Falha ao analisar {repo_name}: {e}")


# Este arquivo agora serve apenas como módulo utilitário para analyze_repo
