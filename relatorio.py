import os  # para aceder aos ficheiros
import re  # para extrair informação do log
import time  # para o loop de espera
import requests  # para enviar para o Telegram
import schedule  # para agendar tarefas
from datetime import datetime  # para a data de hoje
from dotenv import load_dotenv
load_dotenv()

# --- CONFIGURAÇÃO ---
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "")   # token do bot
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")  # ID do chat
PASTA_LOGS = os.path.join(os.path.dirname(__file__), "logs")  # pasta de logs
HORA_RELATORIO = "20:00"  # hora de envio do relatório


def ler_log_hoje() -> tuple[list[dict], list[dict]]:
    """
    Lê o ficheiro de log do dia atual.
    Devolve (processos_mortos, ficheiros_apagados).
    """
    hoje = datetime.now().strftime("%Y-%m-%d")  # data de hoje
    ficheiro = os.path.join(PASTA_LOGS, f"log_{hoje}.txt")  # ficheiro do dia

    if not os.path.exists(ficheiro):
        return [], []

    processos = []   # processos órfãos eliminados
    ficheiros = []   # ficheiros apagados

    with open(ficheiro, "r", encoding="utf-8") as f:
        for linha in f:
            # processos órfãos
            if "✅ Morto:" in linha:
                match = re.search(
                    r"Morto: (\S+) \(PID (\d+)\) \| RAM libertada: ([\d.]+) MB", linha
                )
                if match:
                    hora_match = re.match(r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})", linha)
                    hora = hora_match.group(1)[-8:] if hora_match else "?"
                    processos.append({
                        "hora": hora,
                        "nome": match.group(1),
                        "pid": match.group(2),
                        "ram_mb": float(match.group(3))
                    })

            # capturas apagadas
            if "🖼️  Captura apagada:" in linha:
                match = re.search(r"Captura apagada: (.+?) \((\d+) dias, ([\d.]+) MB\)", linha)
                if match:
                    ficheiros.append({
                        "tipo": "captura",
                        "nome": match.group(1),
                        "idade_dias": int(match.group(2)),
                        "tamanho_mb": float(match.group(3))
                    })

            # temporários apagados
            if "🗑️  Temp apagado:" in linha:
                match = re.search(r"Temp apagado: (.+?) \(([\d.]+) MB\)", linha)
                if match:
                    ficheiros.append({
                        "tipo": "temp",
                        "nome": match.group(1),
                        "idade_dias": 0,
                        "tamanho_mb": float(match.group(2))
                    })

    return processos, ficheiros


def formatar_relatorio(processos: list[dict], ficheiros: list[dict]) -> str:
    """Formata o relatório completo para enviar no Telegram."""
    hoje = datetime.now().strftime("%d/%m/%Y")
    total_ram = sum(p["ram_mb"] for p in processos)
    total_mb_ficheiros = sum(f["tamanho_mb"] for f in ficheiros)

    linhas = [
        f"🖥️ <b>RELATÓRIO DIÁRIO — {hoje}</b>",
        "━━━━━━━━━━━━━━━━━━━━━━",
        ""
    ]

    # secção de processos órfãos
    linhas.append("🔴 <b>Processos Órfãos</b>")
    if not processos:
        linhas.append("✅ Nenhum processo órfão detetado")
    else:
        linhas.append(f"   {len(processos)} eliminado(s) | RAM libertada: <b>{total_ram:.1f} MB</b>")
        for p in processos:
            linhas.append(f"   ⏰ {p['hora']} — {p['nome']} (PID {p['pid']}) — {p['ram_mb']} MB")

    linhas.append("")

    # secção de ficheiros apagados
    linhas.append("🧹 <b>Limpeza de Ficheiros</b>")
    if not ficheiros:
        linhas.append("✅ Nenhum ficheiro apagado")
    else:
        capturas = [f for f in ficheiros if f["tipo"] == "captura"]
        temporarios = [f for f in ficheiros if f["tipo"] == "temp"]
        linhas.append(f"   {len(ficheiros)} ficheiro(s) | Espaço libertado: <b>{total_mb_ficheiros:.1f} MB</b>")
        if capturas:
            linhas.append(f"   🖼️  {len(capturas)} captura(s) de ecrã apagada(s)")
        if temporarios:
            linhas.append(f"   🗑️  {len(temporarios)} ficheiro(s) temporário(s) apagado(s)")

    linhas.append("")
    linhas.append("─────────────────────")
    linhas.append("🤖 Sistema de Manutenção Automática")

    return "\n".join(linhas)


def enviar_relatorio():
    """Lê o log do dia e envia o relatório para o Telegram."""
    print(f"📤 A enviar relatório diário... ({datetime.now().strftime('%H:%M:%S')})")

    processos, ficheiros = ler_log_hoje()  # lê o log do dia
    mensagem = formatar_relatorio(processos, ficheiros)  # formata

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
    schedule.every().day.at(HORA_RELATORIO).do(enviar_relatorio)  # agenda

    while True:
        schedule.run_pending()  # verifica tarefas pendentes
        time.sleep(60)  # verifica de minuto em minuto


if __name__ == "__main__":
    enviar_relatorio()  # teste imediato