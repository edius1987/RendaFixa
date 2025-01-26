import flet as ft
from decimal import Decimal
from dataclasses import dataclass
from typing import Optional
import locale
import math
from fpdf import FPDF
import os
from datetime import datetime

# Tentativa de configurar locale para formato brasileiro
try:
    locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')
except locale.Error:
    try:
        locale.setlocale(locale.LC_ALL, 'Portuguese_Brazil.1252')
    except locale.Error:
        locale.setlocale(locale.LC_ALL, '')

@dataclass
class InvestmentResult:
    interest_amount: float
    tax_amount: Optional[float] = None
    tax_percentage: Optional[float] = None
    iof_amount: Optional[float] = None

class FinanceCalculator:
    @staticmethod
    def compound_interest(amount: float, index: float, days: int) -> float:
        interest = amount * (math.pow(index, days) - 1)
        return round(interest, 2)

    @staticmethod
    def get_index_ir(days: int) -> float:
        if days <= 180:
            return 22.5
        elif days <= 360:
            return 20.0
        elif days <= 720:
            return 17.5
        else:
            return 15.0

    @staticmethod
    def get_iof_percentage(days_to_redeem: int) -> float:
        iof_table = [
            96, 93, 90, 86, 83, 80, 76, 73, 70, 66, 63, 60, 56, 53, 50, 46,
            43, 40, 36, 33, 30, 26, 23, 20, 16, 13, 10, 6, 3, 0
        ]
        
        if days_to_redeem <= 30:
            index = days_to_redeem - 1
            return iof_table[index]
        return 0

    @staticmethod
    def get_iof_amount(days_to_redeem: int, interest_amount: float) -> float:
        iof_percentage = FinanceCalculator.get_iof_percentage(days_to_redeem)
        return interest_amount * (iof_percentage / 100)

    @staticmethod
    def get_index_lcx(yearly_interest: float, di: float) -> float:
        index = yearly_interest / 100
        return math.pow((index * di) / 100 + 1, 1 / 365)

    @staticmethod
    def get_index_poupanca(index: float) -> float:
        # Correção do cálculo da poupança: 70% da taxa SELIC quando SELIC > 8.5% ao ano
        # ou 0.5% ao mês + TR quando SELIC <= 8.5%
        selic_mensal = (index / 100) / 12
        if index > 8.5:
            return math.pow((selic_mensal * 0.7) + 1, 1/30)
        else:
            return math.pow((0.5/100) + 1, 1/30)  # Simplificado, sem considerar TR

    @staticmethod
    def calculate_full_months_days(days: int) -> int:
        days_in_month = 30
        return 0 if days < days_in_month else math.floor(days / days_in_month) * days_in_month

class InvestmentCalculator:
    def __init__(self):
        self.finance = FinanceCalculator()

    def calculate_poupanca(self, amount: float, index: float, days: int) -> dict:
        full_months_days = self.finance.calculate_full_months_days(days)
        interest_amount = self.finance.compound_interest(
            amount,
            self.finance.get_index_poupanca(index),
            full_months_days
        )
        return {"interest_amount": interest_amount}

    def calculate_lcx(self, amount: float, di: float, yearly_index: float, days: int) -> dict:
        interest_amount = self.finance.compound_interest(
            amount,
            self.finance.get_index_lcx(yearly_index, di),
            days
        )
        return {"interest_amount": interest_amount}

    def calculate_cdb(self, amount: float, di: float, yearly_index: float, days: int) -> dict:
        interest_amount = self.finance.compound_interest(
            amount,
            self.finance.get_index_lcx(yearly_index, di),
            days
        )
        tax_percentage = self.finance.get_index_ir(days)
        iof_amount = self.finance.get_iof_amount(days, interest_amount)
        tax_amount = (interest_amount - iof_amount) * (tax_percentage / 100)
        
        return {
            "interest_amount": interest_amount,
            "tax_amount": tax_amount,
            "tax_percentage": tax_percentage,
            "iof_amount": iof_amount
        }

def main(page: ft.Page):
    page.title = "Calculadora de Renda Fixa"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 0  # Removido padding da página para a AppBar ocupar toda largura
    
    # Definição das cores personalizadas
    COLORS = {
        'primary': '#fb7968',    # Vermelho pastel
        'secondary': '#f9c593',  # Laranja pastel
        'background': '#fafad4', # Amarelo bem claro
        'accent': '#b0d1b2',     # Verde claro
        'dark_accent': '#89b2a2' # Verde escuro
    }
    
    # Configuração do tema
    page.bgcolor = COLORS['background']
    
    # Criar o chart_dialog no início da função main
    chart_dialog = None
    chart = None

    def create_chart():
        return ft.Container(
            content=ft.Column([
                ft.Text("Comparativo de Rendimentos", size=20, weight=ft.FontWeight.BOLD),
                ft.Row([
                    ft.Container(
                        content=ft.Column([
                            ft.Text("Poupança", color=COLORS['primary']),
                            ft.ProgressBar(
                                value=0,
                                color=COLORS['primary'],
                                bgcolor=ft.colors.GREY_200,
                                height=30,
                            ),
                            ft.Text("0%", text_align=ft.TextAlign.RIGHT),
                        ]),
                        expand=True,
                    ),
                    ft.Container(
                        content=ft.Column([
                            ft.Text("CDB/RDB", color=COLORS['secondary']),
                            ft.ProgressBar(
                                value=0,
                                color=COLORS['secondary'],
                                bgcolor=ft.colors.GREY_200,
                                height=30,
                            ),
                            ft.Text("0%", text_align=ft.TextAlign.RIGHT),
                        ]),
                        expand=True,
                    ),
                    ft.Container(
                        content=ft.Column([
                            ft.Text("LCI/LCA", color=COLORS['accent']),
                            ft.ProgressBar(
                                value=0,
                                color=COLORS['accent'],
                                bgcolor=ft.colors.GREY_200,
                                height=30,
                            ),
                            ft.Text("0%", text_align=ft.TextAlign.RIGHT),
                        ]),
                        expand=True,
                    ),
                ]),
            ]),
            padding=20,
            bgcolor=ft.colors.WHITE,
        )

    # AppBar personalizada com ícone
    page.appbar = ft.AppBar(
        leading=ft.Image(
            src="images/icon.png",  # Caminho para o ícone
            width=40,
            height=40,
            fit=ft.ImageFit.CONTAIN,
        ),
        leading_width=40,
        title=ft.Row([
            ft.Text("Calculadora de Renda Fixa", 
                   size=20, 
                   weight=ft.FontWeight.BOLD,
                   color=ft.Colors.WHITE),
        ]),
        center_title=False,
        bgcolor=COLORS['primary'],
    )

    # Criar o chart no início
    chart = create_chart()

    calc = FinanceCalculator()
    
    # Campos de entrada
    valor_inicial = ft.TextField(
        label="Valor da Aplicação",
        prefix_text="R$ ",
        suffix_text=",00",
        keyboard_type=ft.KeyboardType.NUMBER,
        prefix_icon=ft.Icons.ATTACH_MONEY,
    )
    
    prazo = ft.TextField(
        label="Vencimento",
        keyboard_type=ft.KeyboardType.NUMBER,
        prefix_icon=ft.Icons.CALENDAR_TODAY,
    )
    
    tipo_prazo = ft.Dropdown(
        label="Tipo de período",
        options=[
            ft.dropdown.Option("dias"),
            ft.dropdown.Option("meses"),
            ft.dropdown.Option("anos"),
        ],
        value="dias",
        prefix_icon=ft.Icons.TIMER,
    )
    
    taxa_di = ft.TextField(
        label="Taxa DI",
        suffix_text="% ao ano",
        keyboard_type=ft.KeyboardType.NUMBER,
        prefix_icon=ft.Icons.TRENDING_UP,
    )
    
    taxa_selic = ft.TextField(
        label="Taxa SELIC",
        suffix_text="% ao ano",
        keyboard_type=ft.KeyboardType.NUMBER,
        prefix_icon=ft.Icons.SHOW_CHART,
    )
    
    taxa_cdb = ft.TextField(
        label="CDB/RDB/LC",
        suffix_text="% DI",
        keyboard_type=ft.KeyboardType.NUMBER,
        prefix_icon=ft.Icons.ACCOUNT_BALANCE,
    )
    
    taxa_lci = ft.TextField(
        label="LCI/LCA",
        suffix_text="% DI",
        keyboard_type=ft.KeyboardType.NUMBER,
        prefix_icon=ft.Icons.ACCOUNT_BALANCE_WALLET,
    )

    def create_result_card(title: str, icon: str = ft.Icons.SHOW_CHART) -> ft.Card:
        return ft.Card(
            content=ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Icon(icon, color=COLORS['primary']),
                        ft.Text(title, size=20, weight=ft.FontWeight.BOLD),
                    ]),
                    ft.Text("Valor Investido: R$ 0,00"),
                    ft.Text("Rendimento Bruto: R$ 0,00"),
                    ft.Text("Rendimento Líquido: R$ 0,00"),
                    ft.Text("Valor Total Líquido: R$ 0,00"),
                    ft.ProgressBar(
                        value=0,
                        height=25,
                        bgcolor=COLORS['secondary'],
                        color=COLORS['primary']
                    ),
                ]),
                padding=20,
                bgcolor=ft.Colors.WHITE,
            ),
        )

    def format_currency(value: float) -> str:
        return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    def update_result_card(card: ft.Card, title: str, invested: float, result: InvestmentResult):
        total = invested + result.interest_amount
        if result.tax_amount:
            total -= result.tax_amount
        if result.iof_amount:
            total -= result.iof_amount
            
        profit = total - invested
        profit_percentage = (profit / invested * 100) if invested > 0 else 0
        
        column = card.content.content
        column.controls[1].value = f"Valor Investido: {format_currency(invested)}"
        column.controls[2].value = f"Rendimento Bruto: {format_currency(result.interest_amount)}"
        
        if result.iof_amount:
            column.controls[2].value += f"\nIOF: {format_currency(result.iof_amount)}"
        if result.tax_amount:
            column.controls[2].value += f"\nImposto de Renda: {format_currency(result.tax_amount)}"
            if result.tax_percentage:
                column.controls[2].value += f" ({result.tax_percentage}%)"
                
        column.controls[3].value = f"Rendimento Líquido: {format_currency(profit)}"
        column.controls[4].value = f"Valor Total Líquido: {format_currency(total)}"
        column.controls[5].value = profit_percentage / 100

    # Cards de resultado
    poupanca_card = create_result_card("Poupança", ft.Icons.SAVINGS)
    cdb_card = create_result_card("CDB / RDB", ft.Icons.ACCOUNT_BALANCE)
    lci_card = create_result_card("LCI / LCA", ft.Icons.ACCOUNT_BALANCE_WALLET)

    def update_chart(poupanca_perc: float, cdb_perc: float, lci_perc: float):
        max_perc = max(poupanca_perc, cdb_perc, lci_perc)
        
        chart.content.controls[1].controls[0].content.controls[1].value = poupanca_perc / max_perc
        chart.content.controls[1].controls[0].content.controls[2].value = f"{poupanca_perc:.2f}%"
        
        chart.content.controls[1].controls[1].content.controls[1].value = cdb_perc / max_perc
        chart.content.controls[1].controls[1].content.controls[2].value = f"{cdb_perc:.2f}%"
        
        chart.content.controls[1].controls[2].content.controls[1].value = lci_perc / max_perc
        chart.content.controls[1].controls[2].content.controls[2].value = f"{lci_perc:.2f}%"
        
        chart.update()

    def show_chart_dialog(e):
        try:
            chart_dialog = ft.AlertDialog(
                content=chart,
                title=ft.Text("Comparativo de Rendimentos"),
                actions=[
                    ft.TextButton("Fechar", on_click=lambda e: close_dialog(e, chart_dialog))
                ],
            )
            page.dialog = chart_dialog
            chart_dialog.open = True
            page.update()
        except Exception as e:
            show_snack_bar(page, f"Erro ao mostrar gráfico: {str(e)}")

    def calculate_gross_up(e):
        try:
            if not prazo.value or not taxa_di.value or not taxa_cdb.value or not taxa_lci.value:
                raise ValueError("Preencha os campos de prazo e taxas")

            dias = int(prazo.value)
            if tipo_prazo.value == "meses":
                dias = dias * 30
            elif tipo_prazo.value == "anos":
                dias = dias * 365

            # Criar instância do calculador
            calc = FinanceCalculator()
            
            # Obter alíquota de IR
            ir_rate = calc.get_index_ir(dias) / 100
            cdb_rate = float(taxa_cdb.value.replace(',', '.'))
            lci_rate = float(taxa_lci.value.replace(',', '.'))

            # Calcular taxas equivalentes
            lci_equivalent = cdb_rate * (1 - ir_rate)
            cdb_equivalent = lci_rate / (1 - ir_rate)

            # Mostrar resultado em um diálogo
            gross_up_dialog = ft.AlertDialog(
                title=ft.Text("Análise de Taxas Equivalentes (Gross up)"),
                content=ft.Container(
                    content=ft.Column([
                        ft.Text(f"Alíquota IR: {ir_rate*100:.1f}%"),
                        ft.Divider(),
                        ft.Text("Taxa equivalente LCI/LCA:"),
                        ft.Text(
                            f"{lci_equivalent:.2f}% do CDI",
                            size=20,
                            weight=ft.FontWeight.BOLD,
                            color=COLORS['primary']
                        ),
                        ft.Text(
                            "(Taxa que a LCI/LCA precisaria ter para igualar o CDB)",
                            size=12,
                            color=ft.colors.GREY_600
                        ),
                        ft.Divider(),
                        ft.Text("Taxa equivalente CDB:"),
                        ft.Text(
                            f"{cdb_equivalent:.2f}% do CDI",
                            size=20,
                            weight=ft.FontWeight.BOLD,
                            color=COLORS['primary']
                        ),
                        ft.Text(
                            "(Taxa que o CDB precisaria ter para igualar a LCI/LCA)",
                            size=12,
                            color=ft.colors.GREY_600
                        ),
                    ]),
                    padding=20,
                ),
                actions=[
                    ft.TextButton("Fechar", on_click=lambda e: close_dialog(e, gross_up_dialog))
                ],
            )

            page.dialog = gross_up_dialog
            gross_up_dialog.open = True
            page.update()

        except ValueError as ve:
            show_snack_bar(page, str(ve))
        except Exception as e:
            show_snack_bar(page, f"Erro no cálculo: {str(e)}")

    def close_dialog(e, dialog):
        dialog.open = False
        page.update()

    def show_snack_bar(page: ft.Page, message: str):
        snack_bar = ft.SnackBar(content=ft.Text(message))
        page.overlay.append(snack_bar)
        snack_bar.open = True
        page.update()

    def save_csv_file(e):
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_path = os.path.join(os.path.expanduser("~"), f"simulacao_investimentos_{timestamp}.csv")
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write("Tipo,Valor Investido,Rendimento Bruto,IOF,IR,Rendimento Líquido,Valor Total\n")
                for card, tipo in [(poupanca_card, "Poupança"), (cdb_card, "CDB/RDB"), (lci_card, "LCI/LCA")]:
                    valores = [v.value.split(": ")[1] for v in card.content.content.controls[1:5]]
                    f.write(f"{tipo},{','.join(valores)}\n")
            
            # Mostrar diálogo de sucesso
            success_dialog = ft.AlertDialog(
                title=ft.Text("Arquivo Salvo com Sucesso"),
                content=ft.Container(
                    content=ft.Column([
                        ft.Text("O arquivo CSV foi salvo em:"),
                        ft.Text(file_path, selectable=True),  # Text com seleção habilitada
                        ft.Text("Clique no caminho acima para copiar.", size=12, color=ft.colors.GREY_600),
                    ]),
                    padding=20,
                ),
                actions=[
                    ft.TextButton("OK", on_click=lambda e: close_dialog(e, success_dialog))
                ],
            )
            
            page.dialog = success_dialog
            success_dialog.open = True
            page.update()
            
        except Exception as e:
            show_snack_bar(page, f"Erro ao salvar CSV: {str(e)}")

    def save_pdf_file(e):
        try:
            # Gerar nome do arquivo automaticamente
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_path = os.path.join(os.path.expanduser("~"), f"simulacao_investimentos_{timestamp}.pdf")
            
            # Criar instância do calculador
            calc = FinanceCalculator()
            
            pdf = FPDF(orientation='L')
            pdf.add_page()
            
            # Configuração de margens
            pdf.set_margins(5, 5, 5)
            pdf.set_auto_page_break(auto=True, margin=5)
            pdf.set_xy(5, 5)
            
            # Título e dados iniciais
            pdf.set_font('Arial', 'B', 14)
            pdf.cell(0, 8, 'Relatório de Simulação de Investimentos', 0, 1, 'C')
            
            # Dados da simulação em duas colunas
            pdf.set_font('Arial', '', 10)
            pdf.cell(140, 6, f'Data: {datetime.now().strftime("%d/%m/%Y %H:%M")}', 0, 0)
            pdf.cell(140, 6, f'Valor inicial: R$ {valor_inicial.value}', 0, 1)
            pdf.cell(140, 6, f'Prazo: {prazo.value} {tipo_prazo.value}', 0, 0)
            pdf.cell(140, 6, f'Taxa DI: {taxa_di.value}% ao ano', 0, 1)
            
            # Tabela de resultados
            pdf.ln(3)
            pdf.set_font('Arial', 'B', 12)
            pdf.cell(0, 6, 'Resultados da Simulação', 0, 1)
            
            # Definição das larguras das colunas
            col_widths = [35, 35, 35, 25, 30, 20, 35, 35]
            
            # Cabeçalho da tabela
            headers = ['Tipo', 'Valor Investido', 'Rendimento Bruto', 'IOF', 'IR', 'IR %', 'Rendimento Líquido', 'Valor Total']
            pdf.set_font('Arial', '', 10)
            for i, header in enumerate(headers):
                pdf.cell(col_widths[i], 10, header, 1, 0, 'C')
            pdf.ln()
            
            # Função para extrair valor numérico do texto
            def extract_value(text):
                if not text or text == '-':
                    return '-'
                return text.split(": ")[-1].strip()
            
            # Dados da tabela
            dados_grafico = []
            for card, tipo in [(poupanca_card, "Poupança"), (cdb_card, "CDB/RDB"), (lci_card, "LCI/LCA")]:
                controls = card.content.content.controls
                
                # Valor Investido
                valor_investido = extract_value(controls[1].value)
                
                # Rendimento Bruto e impostos
                rendimento_info = controls[2].value.split("\n")
                rendimento_bruto = extract_value(rendimento_info[0])
                
                iof = '-'
                ir = '-'
                ir_perc = '-'
                
                for info in rendimento_info[1:] if len(rendimento_info) > 1 else []:
                    if "IOF" in info:
                        iof = extract_value(info)
                    elif "Imposto de Renda" in info:
                        ir_parts = info.split(": ")[1].split(" ")
                        ir = ir_parts[0]
                        if len(ir_parts) > 1:
                            ir_perc = ir_parts[1].strip("()")
                
                # Rendimento Líquido e Total
                rendimento_liquido = extract_value(controls[3].value)
                valor_total = extract_value(controls[4].value)
                
                # Escrever linha na tabela
                dados = [tipo, valor_investido, rendimento_bruto, iof, ir, ir_perc, rendimento_liquido, valor_total]
                for i, dado in enumerate(dados):
                    pdf.cell(col_widths[i], 10, dado, 1, 0, 'C')
                pdf.ln()
                
                # Coletar dados para o gráfico
                try:
                    valor = float(valor_investido.replace('R$ ', '').replace('.', '').replace(',', '.'))
                    rendimento = float(rendimento_liquido.replace('R$ ', '').replace('.', '').replace(',', '.'))
                    dados_grafico.append((tipo, (rendimento / valor) * 100))
                except:
                    dados_grafico.append((tipo, 0))
            
            pdf.ln(8)
            
            # Calcular dados do Gross up primeiro
            dias = int(prazo.value)
            if tipo_prazo.value == "meses":
                dias = dias * 30
            elif tipo_prazo.value == "anos":
                dias = dias * 365
            
            ir_rate = calc.get_index_ir(dias) / 100
            cdb_rate = float(taxa_cdb.value.replace(',', '.'))
            lci_rate = float(taxa_lci.value.replace(',', '.'))
            lci_equivalent = cdb_rate * (1 - ir_rate)
            cdb_equivalent = lci_rate / (1 - ir_rate)
            
            # Título do Gross up
            pdf.set_font('Arial', 'B', 12)
            pdf.cell(0, 8, 'Análise de Taxas Equivalentes (Gross up)', 0, 1)
            
            # Informações do Gross up em duas colunas
            pdf.set_font('Arial', '', 10)
            pdf.cell(140, 6, f'Alíquota IR: {ir_rate*100:.1f}%', 0, 0)
            pdf.cell(140, 6, f'Taxa DI: {taxa_di.value}% ao ano', 0, 1)
            
            # Taxa equivalente LCI/LCA
            pdf.cell(140, 6, 'Taxa equivalente LCI/LCA:', 0, 0)
            pdf.cell(140, 6, 'Taxa equivalente CDB:', 0, 1)
            
            pdf.set_font('Arial', 'B', 12)
            pdf.cell(140, 8, f'{lci_equivalent:.2f}% do CDI', 0, 0)
            pdf.cell(140, 8, f'{cdb_equivalent:.2f}% do CDI', 0, 1)
            
            pdf.set_font('Arial', '', 8)
            pdf.cell(140, 4, '(Taxa que a LCI/LCA precisaria ter para igualar o CDB)', 0, 0)
            pdf.cell(140, 4, '(Taxa que o CDB precisaria ter para igualar a LCI/LCA)', 0, 1)
            
            # Linha divisória horizontal
            pdf.ln(8)
            pdf.line(5, pdf.get_y(), pdf.w - 5, pdf.get_y())
            pdf.ln(8)
            
            # Gráfico Comparativo
            pdf.set_font('Arial', 'B', 12)
            pdf.cell(0, 8, 'Gráfico Comparativo de Rendimentos', 0, 1)
            
            # Configurações do gráfico otimizadas
            bar_height = 12
            spacing = 6
            max_percent = max(percent for _, percent in dados_grafico) if dados_grafico else 100
            
            # Desenhar barras
            y_position = pdf.get_y()
            x_start = 10
            x_label = 45
            x_end = pdf.w - 40  # Aumentado para usar mais espaço horizontal
            
            for tipo, percent in dados_grafico:
                pdf.set_font('Arial', '', 10)
                pdf.text(x_start, y_position + bar_height/2, f"{tipo}:")
                
                bar_width = (percent / max_percent) * (x_end - x_label - 20) if max_percent > 0 else 0
                
                # Cor da barra
                if tipo == "Poupança":
                    cor = COLORS['primary']
                elif tipo == "CDB/RDB":
                    cor = COLORS['secondary']
                else:
                    cor = COLORS['accent']
                
                cor_hex = cor.lstrip('#')
                r, g, b = tuple(int(cor_hex[i:i+2], 16) for i in (0, 2, 4))
                pdf.set_fill_color(r, g, b)
                
                if bar_width > 0:
                    pdf.rect(x_label, y_position, bar_width, bar_height, 'F')
                
                # Posicionar percentual após a barra
                pdf.text(x_label + bar_width + 5, y_position + bar_height/2, f"{percent:.2f}%")
                
                y_position += bar_height + spacing
            
            # Adicionar espaço após o gráfico
            pdf.ln(15)
            
            # Adicionar nova página para a tabela
            pdf.add_page()
            
            # Título da tabela de rentabilidade mensal
            pdf.set_font('Arial', 'B', 14)
            pdf.cell(0, 10, 'Rentabilidade Mensal', 0, 1, 'C')
            pdf.ln(5)
            
            # Calcular retornos mensais
            valor = float(valor_inicial.value.replace('.', '').replace(',', '.'))
            dias = int(prazo.value)
            if tipo_prazo.value == "meses":
                dias = dias * 30
            elif tipo_prazo.value == "anos":
                dias = dias * 365
            
            di = float(taxa_di.value.replace(',', '.'))
            ir_rate = calc.get_index_ir(dias) / 100
            
            def calculate_monthly_returns(valor: float, index: float, dias: int, tipo: str, ir_rate: float = 0) -> list:
                """Calcula os retornos mensais para um determinado investimento"""
                monthly_returns = []
                valor_atual = valor
                
                # Converter para índice diário
                if tipo == "Poupança":
                    daily_index = calc.get_index_poupanca(index)
                else:
                    daily_index = calc.get_index_lcx(index, float(taxa_di.value.replace(',', '.')))
                
                # Calcular para cada mês até completar o período
                meses = math.ceil(dias / 30)
                for mes in range(1, meses + 1):
                    dias_no_mes = min(30, dias - ((mes-1) * 30))
                    if dias_no_mes <= 0:
                        break
                        
                    rendimento = calc.compound_interest(valor_atual, daily_index, dias_no_mes)
                    
                    # Aplicar IR se necessário
                    if tipo == "CDB/RDB":
                        rendimento_liquido = rendimento * (1 - ir_rate)
                    else:
                        rendimento_liquido = rendimento
                        
                    valor_atual += rendimento_liquido
                    monthly_returns.append({
                        'mes': mes,
                        'rendimento': rendimento,
                        'rendimento_liquido': rendimento_liquido,
                        'valor_acumulado': valor_atual
                    })
                    
                return monthly_returns
            
            poupanca_returns = calculate_monthly_returns(valor, di, dias, "Poupança")
            cdb_returns = calculate_monthly_returns(valor, float(taxa_cdb.value.replace(',', '.')), dias, "CDB/RDB", ir_rate)
            lci_returns = calculate_monthly_returns(valor, float(taxa_lci.value.replace(',', '.')), dias, "LCI/LCA")
            
            # Configurar cabeçalho da tabela
            pdf.set_font('Arial', 'B', 8)
            headers = ['Mês', 
                      'Poupança (R$)', 'Acumulado', 
                      'CDB/RDB (R$)', 'Acumulado',
                      'LCI/LCA (R$)', 'Acumulado']
            
            # Calcular larguras das colunas
            col_width = (pdf.w - 20) / len(headers)
            
            # Desenhar cabeçalho
            for header in headers:
                pdf.cell(col_width, 8, header, 1, 0, 'C')
            pdf.ln()
            
            # Calcular número máximo de linhas que cabem na página
            linha_altura = 6  # altura de cada linha em mm
            espaco_disponivel = pdf.h - pdf.get_y() - 20  # 20mm de margem inferior
            max_linhas_pagina = int(espaco_disponivel / linha_altura)
            
            # Determinar quais linhas mostrar
            max_rows = max(len(poupanca_returns), len(cdb_returns), len(lci_returns))
            if max_rows > max_linhas_pagina:
                # Se não couber tudo, mostrar início e fim
                linhas_cada_parte = max_linhas_pagina // 2
                rows_to_show = list(range(linhas_cada_parte)) + ['...'] + list(range(max_rows - linhas_cada_parte, max_rows))
            else:
                rows_to_show = range(max_rows)
            
            # Preencher dados
            pdf.set_font('Arial', '', 8)
            ultima_linha_normal = True
            
            for i in rows_to_show:
                if i == '...':
                    # Linha de reticências
                    for _ in range(len(headers)):
                        pdf.cell(col_width, 6, "...", 1, 0, 'C')
                    pdf.ln()
                    ultima_linha_normal = False
                    continue
                
                # Mês
                pdf.cell(col_width, 6, str(i + 1), 1, 0, 'C')
                
                # Poupança
                if i < len(poupanca_returns):
                    pdf.cell(col_width, 6, f"R$ {poupanca_returns[i]['rendimento_liquido']:,.2f}", 1, 0, 'R')
                    pdf.cell(col_width, 6, f"R$ {poupanca_returns[i]['valor_acumulado']:,.2f}", 1, 0, 'R')
                else:
                    pdf.cell(col_width, 6, "-", 1, 0, 'C')
                    pdf.cell(col_width, 6, "-", 1, 0, 'C')
                
                # CDB/RDB
                if i < len(cdb_returns):
                    pdf.cell(col_width, 6, f"R$ {cdb_returns[i]['rendimento_liquido']:,.2f}", 1, 0, 'R')
                    pdf.cell(col_width, 6, f"R$ {cdb_returns[i]['valor_acumulado']:,.2f}", 1, 0, 'R')
                else:
                    pdf.cell(col_width, 6, "-", 1, 0, 'C')
                    pdf.cell(col_width, 6, "-", 1, 0, 'C')
                
                # LCI/LCA
                if i < len(lci_returns):
                    pdf.cell(col_width, 6, f"R$ {lci_returns[i]['rendimento_liquido']:,.2f}", 1, 0, 'R')
                    pdf.cell(col_width, 6, f"R$ {lci_returns[i]['valor_acumulado']:,.2f}", 1, 0, 'R')
                else:
                    pdf.cell(col_width, 6, "-", 1, 0, 'C')
                    pdf.cell(col_width, 6, "-", 1, 0, 'C')
                
                pdf.ln()
                ultima_linha_normal = True
            
            # Adicionar nota se houver linhas omitidas
            if not ultima_linha_normal:
                pdf.ln(5)
                pdf.set_font('Arial', 'I', 8)
                pdf.cell(0, 5, 'Nota: Algumas linhas intermediárias foram omitidas para melhor visualização', 0, 1, 'L')
            
            # Salvar PDF no local selecionado
            pdf.output(file_path)
            
            # Mostrar diálogo de sucesso
            success_dialog = ft.AlertDialog(
                title=ft.Text("Arquivo Salvo com Sucesso"),
                content=ft.Container(
                    content=ft.Column([
                        ft.Text("O arquivo PDF foi salvo em:"),
                        ft.Text(file_path, selectable=True),  # Text com seleção habilitada
                        ft.Text("Clique no caminho acima para copiar.", size=12, color=ft.colors.GREY_600),
                    ]),
                    padding=20,
                ),
                actions=[
                    ft.TextButton("OK", on_click=lambda e: close_dialog(e, success_dialog))
                ],
            )
            
            page.dialog = success_dialog
            success_dialog.open = True
            page.update()
            
        except Exception as e:
            show_snack_bar(page, f"Erro ao salvar PDF: {str(e)}")

    def export_csv():
        try:
            save_csv_file(None)  # Chamar diretamente a função de salvamento
        except Exception as e:
            show_snack_bar(page, f"Erro ao gerar CSV: {str(e)}")

    def export_pdf():
        try:
            save_pdf_file(None)  # Chamar diretamente a função de salvamento
        except Exception as e:
            show_snack_bar(page, f"Erro ao gerar PDF: {str(e)}")

    def calcular(e):
        try:
            # Validação dos campos
            if not valor_inicial.value or not prazo.value or not taxa_di.value or \
               not taxa_cdb.value or not taxa_lci.value:
                raise ValueError("Preencha todos os campos obrigatórios")

            valor = float(valor_inicial.value.replace('.', '').replace(',', '.'))
            dias = int(prazo.value)
            
            if valor <= 0:
                raise ValueError("O valor inicial deve ser maior que zero")
            if dias <= 0:
                raise ValueError("O prazo deve ser maior que zero")
            
            # Converter período se necessário
            if tipo_prazo.value == "meses":
                dias = dias * 30
            elif tipo_prazo.value == "anos":
                dias = dias * 365
                
            di = float(taxa_di.value.replace(',', '.'))
            
            # Cálculo Poupança
            index_poupanca = calc.get_index_poupanca(di)
            poupanca_result = InvestmentResult(
                interest_amount=calc.compound_interest(valor, index_poupanca, dias)
            )
            
            # Cálculo CDB
            cdb_rate = float(taxa_cdb.value.replace(',', '.'))
            index_cdb = calc.get_index_lcx(cdb_rate, di)
            interest_cdb = calc.compound_interest(valor, index_cdb, dias)
            
            tax_percentage = calc.get_index_ir(dias)
            iof_amount = calc.get_iof_amount(dias, interest_cdb)
            tax_amount = (interest_cdb - iof_amount) * (tax_percentage / 100)
            
            cdb_result = InvestmentResult(
                interest_amount=interest_cdb,
                tax_amount=tax_amount,
                tax_percentage=tax_percentage,
                iof_amount=iof_amount
            )
            
            # Cálculo LCI/LCA
            lci_rate = float(taxa_lci.value.replace(',', '.'))
            index_lci = calc.get_index_lcx(lci_rate, di)
            lci_result = InvestmentResult(
                interest_amount=calc.compound_interest(valor, index_lci, dias)
            )
            
            # Atualizar cards
            update_result_card(poupanca_card, "Poupança", valor, poupanca_result)
            update_result_card(cdb_card, "CDB / RDB", valor, cdb_result)
            update_result_card(lci_card, "LCI / LCA", valor, lci_result)
            
            # Atualizar gráfico
            poupanca_perc = (poupanca_result.interest_amount / valor) * 100
            cdb_perc = ((interest_cdb - tax_amount - iof_amount) / valor) * 100
            lci_perc = (lci_result.interest_amount / valor) * 100
            update_chart(poupanca_perc, cdb_perc, lci_perc)
            
            page.update()
            
        except ValueError as ve:
            show_snack_bar(page, str(ve))
        except Exception as e:
            show_snack_bar(page, f"Erro nos cálculos: {str(e)}")
    
    # Botões de ação com cores corrigidas
    botoes = ft.Row([
        ft.ElevatedButton(
            "Calcular",
            icon=ft.Icons.CALCULATE,
            on_click=calcular,
            style=ft.ButtonStyle(
                bgcolor=COLORS['primary'],
                color=ft.Colors.WHITE,
            )
        ),
        ft.ElevatedButton(
            "Gross up",
            icon=ft.Icons.COMPARE_ARROWS,
            on_click=calculate_gross_up,
            style=ft.ButtonStyle(
                bgcolor=COLORS['primary'],
                color=ft.Colors.WHITE,
            ),
            tooltip="Comparar taxas equivalentes entre CDB e LCI/LCA"
        ),
        ft.ElevatedButton(
            "Gráfico Comparativo",
            icon=ft.Icons.BAR_CHART,
            on_click=show_chart_dialog,
            style=ft.ButtonStyle(
                bgcolor=COLORS['accent'],
                color=ft.Colors.BLACK,
            )
        ),
        ft.ElevatedButton(
            "Exportar CSV",
            icon=ft.Icons.DOWNLOAD,
            on_click=lambda _: export_csv(),
            style=ft.ButtonStyle(
                bgcolor=COLORS['secondary'],
                color=ft.Colors.BLACK,
            )
        ),
        ft.ElevatedButton(
            "Exportar PDF",
            icon=ft.Icons.PICTURE_AS_PDF,
            on_click=lambda _: export_pdf(),
            style=ft.ButtonStyle(
                bgcolor=COLORS['dark_accent'],
                color=ft.Colors.WHITE,
            )
        ),
    ])

    # Layout
    page.scroll = ft.ScrollMode.AUTO
    
    input_container = ft.Container(
        content=ft.Column([
            ft.Text("Investimento", size=24, weight=ft.FontWeight.BOLD),
            valor_inicial,
            ft.Row([prazo, tipo_prazo]),
            taxa_di,
            taxa_selic,
            taxa_cdb,
            taxa_lci,
            botoes,
        ]),
        padding=20,
    )
    
    results_container = ft.Column(
        controls=[poupanca_card, cdb_card, lci_card],
        spacing=10
    )

    # Atualização automática ao modificar campos
    for field in [valor_inicial, prazo, taxa_di, taxa_selic, taxa_cdb, taxa_lci, tipo_prazo]:
        field.on_change = calcular

    # Valores iniciais para os campos
    valor_inicial.value = "1000"
    prazo.value = "360"
    taxa_di.value = "12.65"
    taxa_selic.value = "12.75"
    taxa_cdb.value = "100"
    taxa_lci.value = "100"
    tipo_prazo.value = "dias"

    # Adicionar o FilePicker ao inicializar a página
    page.overlay.extend([
        ft.FilePicker(),
    ])
    page.update()

    page.add(
        ft.Container(
            content=ft.Column([
                input_container,
                ft.Divider(color=COLORS['dark_accent']),
                ft.Container(
                    content=ft.Column([
                        ft.Text("Simulação", size=24, weight=ft.FontWeight.BOLD),
                        ft.Text(
                            "Simulação da rentabilidade do seu investimento conforme o tipo de aplicação:",
                            size=16,
                            color=COLORS['dark_accent'],
                        ),
                        results_container,
                    ]),
                    padding=20,
                ),
            ]),
            padding=20,
            bgcolor=COLORS['background'],
        )
    )

if __name__ == "__main__":
    ft.app(target=main) 