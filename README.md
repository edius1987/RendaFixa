# Calculadora de Renda Fixa

Uma aplicação multiplataforma para cálculo e comparação de investimentos em renda fixa, desenvolvida com Python e Flet.
Inspirado no projeto [rendafixa](https://github.com/rendafixa/rendafixa.github.io), com várias alterações e adições como a geração de relatórios e gráficos.

## Funcionalidades

- Cálculo de rendimentos para:
  - Poupança
  - CDB/RDB
  - LCI/LCA
- Comparação visual através de gráficos
- Análise de Gross up (comparação de taxas equivalentes)
- Exportação de resultados em CSV e PDF
- Tabela de rentabilidade mensal detalhada
- Interface responsiva e amigável

## Tecnologias Utilizadas

- Python 3.x
- Flet (Framework UI)
- FPDF (Geração de PDF)
- Poetry (Gerenciamento de dependências)

## Instalação

1. Clone o repositório:
```bash
git clone https://github.com/edius1987/calculadora-renda-fixa.git
cd calculadora-renda-fixa
```

2. Instale as dependências usando Poetry:

```bash
poetry install flet fpdf
```

3. Execute a aplicação:

```bash
# Como aplicativo desktop
poetry run python main.py

# Como aplicativo web
poetry run flet run -w main.py
```

## Como Usar

1. **Dados de Entrada**:

   - Valor inicial do investimento
   - Prazo (dias, meses ou anos)
   - Taxa DI (% ao ano)
   - Taxa SELIC (% ao ano)
   - Taxa CDB/RDB (% do DI)
   - Taxa LCI/LCA (% do DI)
2. **Funcionalidades Principais**:

   - **Calcular**: Processa os dados e mostra os resultados
   - **Gross up**: Compara taxas equivalentes entre CDB e LCI/LCA
   - **Gráfico Comparativo**: Visualização dos rendimentos
   - **Exportar CSV**: Dados em formato tabular
   - **Exportar PDF**: Relatório completo com gráficos
3. **Resultados Exibidos**:

   - Valor investido
   - Rendimento bruto
   - IOF (quando aplicável)
   - Imposto de Renda (quando aplicável)
   - Rendimento líquido
   - Valor total líquido

## Detalhes Técnicos

### Cálculos Implementados

- **Poupança**:

  - 70% da Taxa SELIC quando SELIC > 8.5% ao ano
  - 0.5% ao mês + TR quando SELIC ≤ 8.5%
- **CDB/RDB**:

  - Rendimento baseado na taxa DI
  - Aplicação de IR conforme prazo:
    - Até 180 dias: 22.5%
    - 181 a 360 dias: 20%
    - 361 a 720 dias: 17.5%
    - Acima de 720 dias: 15%
  - IOF regressivo nos primeiros 30 dias
- **LCI/LCA**:

  - Rendimento baseado na taxa DI
  - Isento de IR
  - Isento de IOF

### Estrutura do Projeto

```
calculadora-renda-fixa/
├── main.py                 # Arquivo principal
├── images/                 # Recursos visuais
│   └── icon.png           # Ícone do aplicativo
├── pyproject.toml         # Configuração Poetry
└── README.md              # Documentação
```

## Solução de Problemas

### Erro de Biblioteca no Ubuntu

Se encontrar erro de biblioteca libmpv.so.1:

1. Instale as dependências:

```bash
sudo apt install libmpv-dev libmujs-dev libjpeg62
```

2. Crie o link simbólico:

```bash
cd /usr/lib/x86_64-linux-gnu
sudo ln -s libmpv.so libmpv.so.1
```

## Contribuindo

1. Faça um fork do projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

## Licença

Este projeto está sob a licença MIT. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.

## Contato

Seu Nome - [@edius_ferreira](https://twitter.com/edius_ferreira)

Link do Projeto: [https://github.com/edius1987/calculadora-renda-fixa](https://github.com/1987/calculadora-renda-fixa)

`
## Referências

[Python Flet - Introdução ao Python Flet_Curso de Python Flet][https://www.usandopy.com/pt/curso-de-python-flet/python-flet-introducao-ao-python-flet/]
[Flutter With Python - DEV Community][https://dev.to/ankushsinghgandhi/building-cross-platform-apps-with-flutter-and-python-a-short-guide-using-flet-epa]
[Build multi-platform apps in Python powered by Flutter | Flet][https://flet.dev/]
[Python: Venv e Poetry para criar ambientes virtuais][https://www.alura.com.br/artigos/ven-poetry-no-python]
[Criação de um projeto Python com Poetry][https://aprendendoprogramar.com.br/tutoriais/python/create-app-with-poetry/#criacao-e-configuracao-de-um-projeto-project-setup]
[Usando o Poetry em seus projetos python][https://medium.com/@volneycasas/usando-o-poetry-em-seus-projetos-python-70be5f018281]
[Poetry — Gerenciamento de dependências em Python][https://dev.to/devs-jequie/poetry-gerenciamento-de-dependencias-em-python-4djf]
[Python com flet](https://phylos.net/2023-07-10/python-com-flet)