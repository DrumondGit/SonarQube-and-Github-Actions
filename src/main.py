import os
import pandas as pd
import subprocess
import file_adapter
def analyze_repo(repo_path, repo_name):
    print(f"Analisando repositório: {repo_name}")
    SONAR_TOKEN = os.environ.get('SONAR_TOKEN')
    SONAR_URL = os.environ.get('SONAR_URL', 'http://localhost:9000')
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

REPOS_DIR = 'repos'

def run_npm_test(repo_path):
    print(f"Executando npm test em: {repo_path}")
    try:
        result = subprocess.run(["npm", "test", "--", "--coverage"], cwd=repo_path, capture_output=True, text=True)
        print(result.stdout)
        if result.returncode != 0:
            print(f"Erro ao executar npm test: {result.stderr}")
        else:
            print("Cobertura de testes capturada com sucesso.")
    except Exception as e:
        print(f"Falha ao executar npm test: {e}")

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
        # Executa análise SonarQube
        analyze_repo(repo_path, repo)
        # Executa npm test para cobertura
        run_npm_test(repo_path)
        # Coleta dados do Sonar (exemplo: pega resultado do arquivo ou API)
        # Aqui você pode adaptar para coletar dados relevantes do SonarQube
        sonar_results.append({"repo": repo, "analise": "concluida"})
    # Gera artefato CSV
    df = pd.DataFrame(sonar_results)
    df.to_csv("sonar_analysis_results.csv", index=False)
    print("Artefato CSV gerado: sonar_analysis_results.csv")

if __name__ == "__main__":
    main()






