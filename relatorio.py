"""
relatorio.py
------------
Lê os logs do dia e envia um resumo para o Telegram às 20h.

Bibliotecas usadas:
- requests  : para enviar mensagem ao Telegram
- schedule  : para agendar o envio às 20h
- time      : para o loop de espera
"""

import os  # para aceder aos ficheiros
import re  # para extrair informação do log
import time  # para o loop de espera
import requests  # para enviar para o Telegram
import schedule  # para agendar tarefas
from datetime import datetime  # para a data de hoje

# --- CONFIGURAÇÃO ---
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "8819065536:AAEAqGIVndm9xwS308EQWkfLYjsu4JJbhRU")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "5898541746")
PASTA_LOGS = os.path.join(os.path.dirname(__file__), "logs")  # pasta de logs
HORA_RELATORIO = "20:00"  # hora de envio do relatório


def ler_log_hoje() -> list[dict]:
    """
    Lê o ficheiro de log do dia atual.
    Extrai os processos mortos e a RAM libertada.
    """
    hoje = datetime.now().strftime("%Y-%m-%d")  # data de hoje
    ficheiro = os.path.join(PASTA_LOGS, f"log_{hoje}.txt")  # ficheiro do dia

    if not os.path.exists(ficheiro):  # se não existe ainda
        return []

    processos = []  # lista de processos encontrados no log

    with open(ficheiro, "r", encoding="utf-8") as f:
        for linha in f:  # percorre cada linha do log
            # procura linhas com processos mortos
            if "✅ Morto:" in linha:
                # extrai nome, PID e RAM com regex
                match = re.search(
                    r"Morto: (\S+) \(PID (\d+)\) \| RAM libertada: ([\d.]+) MB",
                    linha
                )
                if match:
                    # extrai a hora da linha de log
                    hora_match = re.match(r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})", linha)
                    hora = hora_match.group(1)[-8:] if hora_match else "?"  # só HH:MM:SS

                    processos.append({
                        "hora": hora,                        # hora da ação
                        "nome": match.group(1),              # nome do processo
                        "pid": match.group(2),               # PID
                        "ram_mb": float(match.group(3))      # RAM libertada
                    })

    return processos


def formatar_relatorio(processos: list[dict]) -> str:
    """Formata o relatório para enviar no Telegram."""
    hoje = datetime.now().strftime("%d/%m/%Y")  # data formatada
    total_ram = sum(p["ram_mb"] for p in processos)  # RAM total libertada

    linhas = [
        f"🖥️ <b>RELATÓRIO DIÁRIO — {hoje}</b>",
        "━━━━━━━━━━━━━━━━━━━━━━",
        ""
    ]

    if not processos:
        linhas.append("✅ Nenhum processo órfão detetado hoje.")
    else:
        linhas.append(f"🧹 <b>{len(processos)} processo(s) eliminado(s)</b>")
        linhas.append(f"💾 RAM total libertada: <b>{total_ram:.1f} MB</b>")
        linhas.append("")
        linhas.append("─────────────────────")
        linhas.append("")

        for p in processos:  # lista cada processo morto
            linhas.append(f"⏰ {p['hora']}")
            linhas.append(f"   🔴 {p['nome']} (PID {p['pid']})")
            linhas.append(f"   💾 RAM libertada: {p['ram_mb']} MB")
            linhas.append("")

    linhas.append("─────────────────────")
    linhas.append("🤖 Monitor de Processos Órfãos")

    return "\n".join(linhas)


def enviar_relatorio():
    """Lê o log do dia e envia o relatório para o Telegram."""
    print(f"📤 A enviar relatório diário... ({datetime.now().strftime('%H:%M:%S')})")

    processos = ler_log_hoje()  # lê o log do dia
    mensagem = formatar_relatorio(processos)  # formata a mensagem

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": mensagem,
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    }

    try:
        r = requests.post(url, data=payload, timeout=10)
        if r.status_code == 200:
            print("✅ Relatório enviado para o Telegram!")
        else:
            print(f"❌ Erro Telegram: {r.status_code}")
    except Exception as erro:
        print(f"❌ Erro: {erro}")


def correr_agendador():
    """Agenda o envio do relatório e corre o loop."""
    print(f"📅 Relatório agendado para as {HORA_RELATORIO}")

    schedule.every().day.at(HORA_RELATORIO).do(enviar_relatorio)  # agenda às 20h

    while True:  # loop de espera
        schedule.run_pending()  # verifica se há tarefas a correr
        time.sleep(60)  # verifica de minuto em minuto


if __name__ == "__main__":
    # teste imediato — envia logo o relatório
    enviar_relatorio()