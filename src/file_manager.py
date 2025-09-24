import os
import pandas as pd

def save_results_to_csv(results, filename="sonar_analysis_results.csv"):
    """Salva resultados em CSV."""
    if not results:
        print("Nenhum resultado para salvar.")
        return
    
    df = pd.DataFrame(results)
    
    columns_order = [
        'repo', 'bugs', 'vulnerabilities', 'code_smells', 'coverage', 
        'test_coverage', 'ncloc', 'complexity', 'duplicated_lines_density', 
        'security_hotspots', 'reliability_rating', 'security_rating', 
        'sqale_rating', 'test_passed', 'test_failed'
    ]
    
    existing_columns = [col for col in columns_order if col in df.columns]
    df = df[existing_columns]
    
    df.to_csv(filename, index=False)
    print(f"Artefato CSV gerado: {filename}")
    return df

def get_repositories_list(repos_dir='repos'):
    """Obtém lista de repositórios para análise."""
    if not os.path.exists(repos_dir):
        print(f"Diretório '{repos_dir}' não encontrado.")
        return []
    
    repos = [d for d in os.listdir(repos_dir) 
             if os.path.isdir(os.path.join(repos_dir, d))]
    
    if not repos:
        print(f"Nenhum repositório encontrado em '{repos_dir}'.")
    
    return repos