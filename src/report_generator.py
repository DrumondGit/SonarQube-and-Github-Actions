import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

def generate_simple_report(csv_file='sonar_analysis_results.csv'):
    """Gera relatório PNG com métricas principais."""
    if not os.path.exists(csv_file):
        print(f"Arquivo {csv_file} não encontrado!")
        return
    
    df = pd.read_csv(csv_file)
    print("Dados carregados para geração de relatório!")
    
    plt.style.use('default')
    sns.set_palette("husl")
    
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    fig.suptitle('Relatório SonarQube - Análise de Qualidade de Código', fontsize=16, fontweight='bold')
    
    # Gráfico 1: Problemas Encontrados
    _plot_issues(df, axes[0, 0])
    
    # Gráfico 2: Ratings de Qualidade
    _plot_ratings(df, axes[0, 1])
    
    # Gráfico 3: Complexidade vs Tamanho
    _plot_complexity(df, axes[1, 0])
    
    # Gráfico 4: Segurança e Duplicação
    _plot_security_duplication(df, axes[1, 1])
    
    plt.tight_layout()
    plt.subplots_adjust(top=0.93)
    plt.savefig('sonar_report.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("Relatório PNG gerado: sonar_report.png")

def generate_metrics_summary(csv_file='sonar_analysis_results.csv'):
    """Gera resumo simples das métricas principais."""
    if not os.path.exists(csv_file):
        return
    
    df = pd.read_csv(csv_file)
    main_metrics = ['bugs', 'vulnerabilities', 'code_smells', 'security_hotspots']
    
    metrics_data = []
    labels = []
    for metric in main_metrics:
        if metric in df.columns:
            metrics_data.append(df[metric].iloc[0])
            labels.append(metric.replace('_', ' ').title())
    
    fig, ax = plt.subplots(figsize=(10, 6))
    bars = ax.barh(labels, metrics_data, color=['#e74c3c', '#f39c12', '#3498db', '#9b59b6'])
    ax.set_xlabel('Quantidade')
    ax.set_title('Resumo das Métricas Principais', fontsize=14, fontweight='bold')
    ax.grid(axis='x', alpha=0.3)
    
    for bar, value in zip(bars, metrics_data):
        width = bar.get_width()
        ax.text(width + max(metrics_data)*0.01, bar.get_y() + bar.get_height()/2, 
                f'{int(value)}', ha='left', va='center', fontweight='bold')
    
    plt.tight_layout()
    plt.savefig('sonar_summary.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("Resumo PNG gerado: sonar_summary.png")

def _plot_issues(df, ax):
    """Plota gráfico de problemas identificados."""
    if all(col in df.columns for col in ['bugs', 'vulnerabilities', 'code_smells']):
        issues_data = df[['bugs', 'vulnerabilities', 'code_smells']].iloc[0]
        bars = ax.bar(['Bugs', 'Vulnerabilidades', 'Code Smells'], issues_data.values, 
                     color=['#ff6b6b', '#ffa726', '#42a5f5'])
        ax.set_title('Problemas Identificados', fontweight='bold')
        ax.set_ylabel('Quantidade')
        
        for bar, value in zip(bars, issues_data.values):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + 1, f'{int(value)}', 
                   ha='center', va='bottom')

def _plot_ratings(df, ax):
    """Plota gráfico de ratings de qualidade."""
    if all(col in df.columns for col in ['reliability_rating', 'security_rating', 'sqale_rating']):
        ratings_data = df[['reliability_rating', 'security_rating', 'sqale_rating']].iloc[0]
        bars = ax.bar(['Confiabilidade', 'Segurança', 'Manutenibilidade'], ratings_data.values, 
                     color=['#ab47bc', '#ec407a', '#ffca28'])
        ax.set_title('Ratings de Qualidade (1-5)', fontweight='bold')
        ax.set_ylim(0, 5)
        
        for bar, value in zip(bars, ratings_data.values):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + 0.1, f'{value}', 
                   ha='center', va='bottom')

def _plot_complexity(df, ax):
    """Plota complexidade vs tamanho do código."""
    if all(col in df.columns for col in ['complexity', 'ncloc']):
        ax.scatter(df['ncloc'], df['complexity'], s=100, alpha=0.7, color='purple')
        ax.set_xlabel('Linhas de Código (NCLOC)')
        ax.set_ylabel('Complexidade Ciclomática')
        ax.set_title('Complexidade vs Tamanho do Código', fontweight='bold')
        ax.grid(True, alpha=0.3)

def _plot_security_duplication(df, ax):
    """Plota segurança e duplicação."""
    if all(col in df.columns for col in ['security_hotspots', 'duplicated_lines_density']):
        security_data = df['security_hotspots'].iloc[0]
        duplication_data = df['duplicated_lines_density'].iloc[0]
        
        categories = ['Hotspots Segurança', 'Duplicação (%)']
        values = [security_data, duplication_data]
        
        bars = ax.bar(categories, values, color=['#ef5350', '#26a69a'])
        ax.set_title('Segurança e Duplicação', fontweight='bold')
        ax.set_ylabel('Valor')
        
        for bar, value in zip(bars, values):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + max(values)*0.05,
                   f'{value}', ha='center', va='bottom')