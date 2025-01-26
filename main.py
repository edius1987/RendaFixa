import flet as ft
from decimal import Decimal
from dataclasses import dataclass
from typing import Optional
import locale
import math

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
    page.padding = 20
    
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
                        ft.Icon(icon),
                        ft.Text(title, size=20, weight=ft.FontWeight.BOLD),
                    ]),
                    ft.Text("Valor Investido: R$ 0,00"),
                    ft.Text("Rendimento Bruto: R$ 0,00"),
                    ft.Text("Rendimento Líquido: R$ 0,00"),
                    ft.Text("Valor Total Líquido: R$ 0,00"),
                    ft.ProgressBar(value=0, height=25),
                ]),
                padding=20
            )
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

    def create_chart():
        return ft.Container(
            content=ft.Column([
                ft.Text("Comparativo de Rendimentos", size=20, weight=ft.FontWeight.BOLD),
                ft.Row([
                    ft.Container(
                        content=ft.Column([
                            ft.Text("Poupança", color=ft.Colors.AMBER),
                            ft.ProgressBar(
                                value=0,
                                color=ft.Colors.AMBER,
                                bgcolor=ft.Colors.AMBER_100,
                                height=30,
                            ),
                            ft.Text("0%", text_align=ft.TextAlign.RIGHT),
                        ]),
                        expand=True,
                    ),
                    ft.Container(
                        content=ft.Column([
                            ft.Text("CDB/RDB", color=ft.Colors.BLUE),
                            ft.ProgressBar(
                                value=0,
                                color=ft.Colors.BLUE,
                                bgcolor=ft.Colors.BLUE_100,
                                height=30,
                            ),
                            ft.Text("0%", text_align=ft.TextAlign.RIGHT),
                        ]),
                        expand=True,
                    ),
                    ft.Container(
                        content=ft.Column([
                            ft.Text("LCI/LCA", color=ft.Colors.GREEN),
                            ft.ProgressBar(
                                value=0,
                                color=ft.Colors.GREEN,
                                bgcolor=ft.Colors.GREEN_100,
                                height=30,
                            ),
                            ft.Text("0%", text_align=ft.TextAlign.RIGHT),
                        ]),
                        expand=True,
                    ),
                ]),
            ]),
            padding=20,
            border=ft.border.all(1, ft.Colors.GREY_400),
        )

    chart = create_chart()
    chart_dialog = ft.AlertDialog(
        title=ft.Text("Comparativo de Rendimentos"),
        content=chart,
        actions=[
            ft.TextButton("Fechar", on_click=lambda e: close_chart_dialog(e))
        ],
    )

    def close_chart_dialog(e):
        chart_dialog.open = False
        page.update()

    def update_chart(poupanca: float, cdb: float, lci: float):
        # Atualiza as barras de progresso e percentuais
        chart.content.controls[1].controls[0].content.controls[1].value = poupanca/100
        chart.content.controls[1].controls[0].content.controls[2].value = f"{poupanca:.2f}%"
        
        chart.content.controls[1].controls[1].content.controls[1].value = cdb/100
        chart.content.controls[1].controls[1].content.controls[2].value = f"{cdb:.2f}%"
        
        chart.content.controls[1].controls[2].content.controls[1].value = lci/100
        chart.content.controls[1].controls[2].content.controls[2].value = f"{lci:.2f}%"
        
        chart.update()

    def export_csv():
        try:
            with open('simulacao_investimentos.csv', 'w', encoding='utf-8') as f:
                f.write("Tipo,Valor Investido,Rendimento Bruto,IOF,IR,Rendimento Líquido,Valor Total\n")
                for card, tipo in [(poupanca_card, "Poupança"), (cdb_card, "CDB/RDB"), (lci_card, "LCI/LCA")]:
                    valores = [v.value.split(": ")[1] for v in card.content.content.controls[1:5]]
                    f.write(f"{tipo},{','.join(valores)}\n")
            page.show_snack_bar(ft.SnackBar(content=ft.Text("Arquivo CSV gerado com sucesso!")))
        except Exception as e:
            page.show_snack_bar(ft.SnackBar(content=ft.Text(f"Erro ao gerar CSV: {str(e)}")))

    def show_chart_dialog(e):
        page.dialog = chart_dialog
        chart_dialog.open = True
        page.update()

    def calcular(e):
        try:
            valor = float(valor_inicial.value.replace('.', '').replace(',', '.'))
            dias = int(prazo.value)
            
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
            
        except Exception as e:
            print(f"Erro nos cálculos: {e}")
    
    # Botões de ação
    botoes = ft.Row([
        ft.ElevatedButton(
            "Gráfico Comparativo",
            icon=ft.Icons.BAR_CHART,
            on_click=show_chart_dialog
        ),
        ft.ElevatedButton(
            "Exportar CSV",
            icon=ft.Icons.DOWNLOAD,
            on_click=lambda _: export_csv()
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

    page.add(
        ft.Container(
            content=ft.Column([
                input_container,
                ft.Divider(),
                ft.Container(
                    content=ft.Column([
                        ft.Text("Simulação", size=24, weight=ft.FontWeight.BOLD),
                        ft.Text(
                            "Simulação da rentabilidade do seu investimento conforme o tipo de aplicação:",
                            size=16,
                            color=ft.colors.GREY_700,
                        ),
                        results_container,
                    ]),
                    padding=20,
                ),
            ]),
            padding=20,
        )
    )

if __name__ == "__main__":
    ft.app(target=main) 