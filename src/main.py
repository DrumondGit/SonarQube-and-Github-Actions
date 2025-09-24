import os
from report_generator import generate_simple_report, generate_metrics_summary
from file_manager import save_results_to_csv, get_repositories_list
from sonar_analyzer import analyze_repo, get_sonar_metrics


def main():
    """Função principal simplificada."""
    repos = get_repositories_list('repos')
    if not repos:
        return
    
    sonar_results = []
    
    for repo in repos:
        repo_path = os.path.join('repos', repo)
        print(f"\n=== Processando {repo} ===")
        
        # Análise SonarQube
        project_key = analyze_repo(repo_path, repo)
        result = {"repo": repo}
        
        if project_key:
            result.update(get_sonar_metrics(project_key))
        
        sonar_results.append(result)
        print(f"=== Concluído {repo} ===\n")
    
    # Salva resultados e gera relatórios
    save_results_to_csv(sonar_results)
    
    print("Gerando relatórios em PNG...")
    generate_simple_report()
    generate_metrics_summary()
    
    print("\n✅ Processo concluído!")
    print("Arquivos gerados:")
    print("- sonar_analysis_results.csv")
    print("- sonar_report.png")
    print("- sonar_summary.png")

if __name__ == "__main__":
    main()