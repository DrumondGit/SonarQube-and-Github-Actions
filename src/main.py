import os
from sonar_analyzer import analyze_repo, get_sonar_metrics, check_project_exists
from report_generator import generate_simple_report, generate_metrics_summary
from file_manager import save_results_to_csv, get_repositories_list

def main():
    """Função principal com melhor debug."""
    repos = get_repositories_list('repos')
    if not repos:
        return
    
    sonar_results = []
    
    for repo in repos:
        repo_path = os.path.join('repos', repo)
        print(f"\n{'='*50}")
        print(f"PROCESSANDO: {repo}")
        print(f"{'='*50}")
        
        # Verifica se o projeto já existe
        project_key = f"{repo}".replace('/', '_')
        print(f"Project key: {project_key}")
        
        if check_project_exists(project_key):
            print(f"✅ Projeto {project_key} já existe no SonarCloud")
        else:
            print(f"⚠️ Projeto {project_key} não encontrado no SonarCloud")
        
        # Análise SonarQube
        project_key = analyze_repo(repo_path, repo)
        result = {"repo": repo}
        
        if project_key:
            print(f"Buscando métricas para {project_key}...")
            metrics = get_sonar_metrics(project_key)
            if metrics:
                result.update(metrics)
                print(f"✅ Métricas obtidas: {len(metrics)} itens")
            else:
                print("❌ Não foi possível obter métricas")
        else:
            print("❌ Análise SonarQube falhou")
        

    # Salva resultados e gera relatórios
    if sonar_results:
        save_results_to_csv(sonar_results)
        
        print("Gerando relatórios em PNG...")
        generate_simple_report()
        generate_metrics_summary()
        
        print("\n✅ Processo concluído!")
        print("Arquivos gerados:")
        print("- sonar_analysis_results.csv")
        print("- sonar_report.png")
        print("- sonar_summary.png")
    else:
        print("❌ Nenhum resultado para salvar")

if __name__ == "__main__":
    main()