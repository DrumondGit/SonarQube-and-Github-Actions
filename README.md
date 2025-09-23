# KT - SonarQube com GitHub Actions

## 📋 Visão Geral
Este documento descreve o processo completo para configurar e utilizar o SonarQube Cloud integrado com GitHub Actions para análise estática de código.

## 🚀 Pré-requisitos

- Conta no [SonarCloud](https://sonarcloud.io)
- Repositório GitHub com código para análise
- Acesso de administrador ao repositório

## 🔑 Passo 1: Configuração do SonarCloud

### 1.1 Acessar SonarCloud
1. Acesse [https://sonarcloud.io](https://sonarcloud.io)
2. Faça login usando sua conta GitHub

### 1.2 Criar Organização
1. Clique em **"Create new organization"**
2. Escolha o plano **Free** (gratuito)
3. Selecione os repositórios que deseja analisar ou **"Choose later"**
4. Complete a criação da organização

### 1.3 Obter Sonar Organization
1. Após criar a organização, anote o nome da organização
2. Ele estará na URL: `https://sonarcloud.io/projects?organization=**nome-da-organizacao**`
3. **Exemplo:** Se a URL é `https://sonarcloud.io/projects?organization=drumondgit`, então:
   - `SONAR_ORGANIZATION = drumondgit`

## 🔐 Passo 2: Gerar Token do SonarCloud

### 2.1 Criar Token de Acesso
1. No SonarCloud, clique no seu ícone de perfil (canto superior direito)
2. Selecione **"My Account"**
3. Vá para a aba **"Security"**
4. Em **"Generate Tokens"**, digite um nome para o token (ex: `github-actions`)
5. Clique em **"Generate"**
6. **⚠️ COPIE O TOKEN IMEDIATAMENTE** - você não poderá vê-lo novamente!

## ⚙️ Passo 3: Configurar Secrets no GitHub

### 3.1 Acessar Configurações do Repositório
1. No seu repositório GitHub, vá em **"Settings"**
2. No menu lateral, clique em **"Secrets and variables"** → **"Actions"**

### 3.2 Adicionar Secrets
Clique em **"New repository secret"** e adicione:

#### Secret 1: SONAR_TOKEN
- **Name:** `SONAR_TOKEN`
- **Value:** Cole o token gerado no Passo 2.6

#### Secret 2: SONAR_ORGANIZATION
- **Name:** `SONAR_ORGANIZATION` 
- **Value:** O nome da sua organização (obtido no Passo 1.3)

## 📁 Passo 4: Estrutura do Projeto

Seu repositório deve ter a seguinte estrutura:

```
seu-repositorio/
├── .github/
│   └── workflows/
│       └── sonar-analysis.yml    # Pipeline do GitHub Actions
├── src/
│   ├── main.py                   # Script principal de análise
│   ├── sonar_analyser.py         # Módulo de análise SonarQube
│   └── file_adapter.py           # Manipulação de arquivos
├── repos/                        # Diretório para clones dos repositórios
├── sonar_analysis_results.csv    # Resultados gerados (ignorar no git)
└── README.md                     # Este arquivo
```

## 🔧 Passo 5: Configurar a Pipeline

### 5.1 Arquivo da Pipeline (.github/workflows/sonar-analysis.yml)

```yaml
name: SonarQube Repository Analysis Pipeline

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]
  workflow_dispatch:

env:
  SONAR_TOKEN: ${{ secrets.SONAR_TOKEN }}
  SONAR_URL: "https://sonarcloud.io"
  SONAR_ORGANIZATION: ${{ secrets.SONAR_ORGANIZATION }}

jobs:
  analyze-repositories:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: "3.10"
      
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install pandas requests

      - name: Install Java 17
        run: |
          sudo apt update
          sudo apt install -y openjdk-17-jdk
          echo "JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64" >> $GITHUB_ENV
          echo "/usr/lib/jvm/java-17-openjdk-amd64/bin" >> $GITHUB_PATH

      - name: Install Node.js
        run: |
          curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
          sudo apt-get install -y nodejs

      - name: Clone Target Repository
        run: |
          git clone https://github.com/axios/axios.git repos/axios
          cd repos/axios
          npm install

      - name: Install SonarScanner
        run: |
          curl -sSLo sonar-scanner.zip https://binaries.sonarsource.com/Distribution/sonar-scanner-cli/sonar-scanner-cli-5.0.1.3006-linux.zip
          unzip -o sonar-scanner.zip
          echo "${PWD}/sonar-scanner-5.0.1.3006-linux/bin" >> $GITHUB_PATH

      - name: Run Analysis
        run: |
          python src/main.py

      - name: Upload Results
        uses: actions/upload-artifact@v4
        with:
          name: sonar-analysis-results
          path: sonar_analysis_results.csv
```

## 🏃‍♂️ Passo 6: Executar a Análise

### 6.1 Execução Automática
- A pipeline executa automaticamente em **push** para main
- Executa em **pull requests** para main
- Pode ser executada manualmente via **workflow_dispatch**

### 6.2 Execução Manual
1. Vá para a aba **"Actions"** no seu repositório GitHub
2. Selecione **"SonarQube Repository Analysis Pipeline"**
3. Clique em **"Run workflow"**
4. Selecione o branch e clique em **"Run workflow"**

## 📊 Passo 7: Verificar Resultados

### 7.1 No SonarCloud
1. Acesse [https://sonarcloud.io](https://sonarcloud.io)
2. Selecione sua organização
3. Veja os projetos analisados
4. Acesse os detalhes de cada análise

### 7.2 No GitHub
1. Após execução da pipeline, baixe o artefato **"sonar-analysis-results"**
2. Abra o arquivo **sonar_analysis_results.csv**
3. Analise as métricas geradas

## 📈 Métricas Coletadas

O sistema coleta automaticamente:

- **✅ Bugs** - Problemas no código
- **⚠️ Vulnerabilities** - Vulnerabilidades de segurança  
- **👃 Code Smells** - Más práticas de código
- **📊 Coverage** - Cobertura de testes
- **📏 Complexity** - Complexidade ciclomática
- **🔒 Security Hotspots** - Pontos quentes de segurança
- **📝 Lines of Code** - Total de linhas de código

## 🛠️ Solução de Problemas Comuns

### Erro: "Invalid token"
- Verifique se o token foi copiado corretamente
- Gere um novo token se necessário

### Erro: "Organization not found"
- Confirme o nome exato da organização
- Verifique permissões na organização

### Erro: Java version mismatch
- A pipeline já configura Java 17 automaticamente

### Pipeline não executa
- Verifique se o arquivo YAML está no caminho correto
- Confirme que as secrets estão configuradas

## 🔗 Links Úteis

- [SonarCloud Documentation](https://docs.sonarcloud.io)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [SonarScanner Documentation](https://docs.sonarqube.org/latest/analysis/scan/sonarscanner/)

## 📞 Suporte

Em caso de problemas:
1. Verifique os logs da pipeline no GitHub Actions
2. Confirme que todas as secrets estão configuradas
3. Verifique a documentação oficial
4. Consulte o arquivo de resultados para detalhes

---

**✅ Configuração concluída!** Sua pipeline está pronta para analisar código automaticamente.