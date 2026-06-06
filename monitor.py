"""
monitor.py
----------
Monitoriza processos órfãos no Windows e liberta memória.
Um processo órfão é um processo filho cujo pai já não existe.

Bibliotecas usadas:
- psutil   : para aceder à lista de processos do sistema
- logging  : para guardar log do que foi feito
- time     : para aguardar entre verificações
"""

import psutil  # para monitorizar processos
import logging  # para guardar log
import time  # para pausas entre verificações
import os  # para criar a pasta de logs
from datetime import datetime  # para registar a hora das ações

# --- CONFIGURAÇÃO ---
INTERVALO_SEGUNDOS = 30       # verifica de 30 em 30 segundos
RAM_MINIMA_MB = 100           # só mata órfãos que consumam mais de 100MB
PASTA_LOGS = os.path.join(os.path.dirname(__file__), "logs")  # pasta de logs

# processos do sistema a ignorar — nunca matar estes
PROCESSOS_IGNORAR = {
    "system", "smss.exe", "csrss.exe", "wininit.exe",
    "winlogon.exe", "services.exe", "lsass.exe", "svchost.exe",
    "explorer.exe", "taskmgr.exe", "python.exe", "pythonw.exe",
}


def configurar_log() -> logging.Logger:
    """Configura o sistema de log — guarda num ficheiro diário."""
    os.makedirs(PASTA_LOGS, exist_ok=True)  # cria a pasta se não existir

    hoje = datetime.now().strftime("%Y-%m-%d")  # data de hoje
    ficheiro_log = os.path.join(PASTA_LOGS, f"log_{hoje}.txt")  # ficheiro do dia

    logging.basicConfig(
        level=logging.INFO,  # nível de detalhe
        format="%(asctime)s | %(levelname)s | %(message)s",  # formato
        handlers=[
            logging.FileHandler(ficheiro_log, encoding="utf-8"),  # guarda em ficheiro
            logging.StreamHandler()  # também mostra no terminal
        ]
    )
    return logging.getLogger(__name__)


def obter_pids_ativos() -> set:
    """Devolve o conjunto de todos os PIDs ativos no sistema."""
    return {p.pid for p in psutil.process_iter()}  # conjunto de PIDs


def e_orfao(processo: psutil.Process, pids_ativos: set) -> bool:
    """
    Verifica se um processo é órfão.
    Um processo é órfão se o seu pai já não existe.
    """
    try:
        ppid = processo.ppid()  # PID do processo pai
        if ppid == 0:  # PID 0 é o sistema — não é órfão
            return False
        return ppid not in pids_ativos  # pai não existe = órfão
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return False  # processo já desapareceu ou sem acesso


def obter_ram_mb(processo: psutil.Process) -> float:
    """Devolve a RAM usada pelo processo em MB."""
    try:
        return processo.memory_info().rss / 1024 / 1024  # converte bytes para MB
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return 0.0  # não conseguiu aceder


def matar_processo(processo: psutil.Process, logger: logging.Logger) -> dict | None:
    """
    Tenta matar um processo órfão.
    Devolve um dicionário com info sobre o que foi morto, ou None se falhou.
    """
    try:
        nome = processo.name()  # nome do processo
        pid = processo.pid  # PID do processo
        ram_mb = obter_ram_mb(processo)  # RAM usada

        # ignora processos do sistema
        if nome.lower() in PROCESSOS_IGNORAR:
            return None

        # ignora processos que usam pouca RAM
        if ram_mb < RAM_MINIMA_MB:
            return None

        processo.kill()  # mata o processo

        logger.info(f"✅ Morto: {nome} (PID {pid}) | RAM libertada: {ram_mb:.1f} MB")

        return {
            "hora": datetime.now().strftime("%H:%M:%S"),  # hora da ação
            "nome": nome,   # nome do processo
            "pid": pid,     # PID
            "ram_mb": round(ram_mb, 1)  # RAM libertada
        }

    except psutil.NoSuchProcess:
        return None  # processo já desapareceu entretanto
    except psutil.AccessDenied:
        logger.warning(f"⚠️  Sem permissão para matar PID {processo.pid}")
        return None


def verificar_orfaos(logger: logging.Logger) -> list[dict]:
    """
    Percorre todos os processos e mata os órfãos que consomem RAM suficiente.
    Devolve lista de processos mortos.
    """
    mortos = []  # lista de processos mortos nesta verificação
    pids_ativos = obter_pids_ativos()  # PIDs ativos agora

    for proc in psutil.process_iter(["pid", "name", "ppid"]):  # percorre processos
        try:
            if e_orfao(proc, pids_ativos):  # verifica se é órfão
                resultado = matar_processo(proc, logger)  # tenta matar
                if resultado:
                    mortos.append(resultado)  # guarda na lista
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue  # processo desapareceu — ignora

    return mortos


def correr_monitor(logger: logging.Logger) -> list[dict]:
    """
    Corre uma verificação única.
    Devolve lista de processos mortos — usada pelo relatorio.py.
    """
    logger.info("🔍 A verificar processos órfãos...")
    mortos = verificar_orfaos(logger)

    if mortos:
        logger.info(f"   ✅ {len(mortos)} processo(s) morto(s)")
    else:
        logger.info("   ✅ Nenhum órfão encontrado")

    return mortos


def loop_monitor():
    """Loop principal — corre indefinidamente."""
    logger = configurar_log()  # configura o log
    logger.info("🚀 Monitor de processos órfãos iniciado")
    logger.info(f"   Intervalo: {INTERVALO_SEGUNDOS}s | RAM mínima: {RAM_MINIMA_MB}MB")

    todos_mortos = []  # acumula todos os processos mortos no dia

    while True:  # corre para sempre
        mortos = correr_monitor(logger)  # verifica órfãos
        todos_mortos.extend(mortos)  # acumula
        time.sleep(INTERVALO_SEGUNDOS)  # aguarda antes da próxima verificação


if __name__ == "__main__":
    loop_monitor()  # corre o monitor