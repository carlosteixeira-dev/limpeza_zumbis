"""
main.py
-------
Ponto de entrada — arranca o monitor de processos, limpeza de ficheiros
e o agendador do relatório em paralelo.

Bibliotecas usadas:
- threading : para correr as tarefas em paralelo
"""

import threading  # para correr as tarefas em paralelo
import time  # para o loop principal
from monitor import loop_monitor, configurar_log  # monitor de órfãos
from relatorio import correr_agendador  # agendador do relatório
from limpeza_ficheiros import correr_limpeza  # limpeza de ficheiros
from dotenv import load_dotenv
load_dotenv()


def loop_limpeza(logger):
    """Corre a limpeza de ficheiros de hora a hora."""
    while True:
        correr_limpeza(logger)  # limpa ficheiros
        time.sleep(3600)  # aguarda 1 hora antes da próxima limpeza


def main():
    """Arranca todas as tarefas em threads separadas."""
    logger = configurar_log()  # configura o log
    logger.info("🚀 A iniciar sistema de manutenção...")

    # thread do monitor de processos órfãos
    thread_monitor = threading.Thread(target=loop_monitor, daemon=True)
    thread_monitor.start()

    # thread da limpeza de ficheiros
    thread_limpeza = threading.Thread(target=lambda: loop_limpeza(logger), daemon=True)
    thread_limpeza.start()

    # thread do agendador do relatório
    thread_relatorio = threading.Thread(target=correr_agendador, daemon=True)
    thread_relatorio.start()

    logger.info("✅ Tudo a correr!")
    logger.info("   🔍 Monitor de processos — a cada 30s")
    logger.info("   🧹 Limpeza de ficheiros — a cada 1h")
    logger.info("   📊 Relatório Telegram — às 20:00")

    # mantém o programa vivo
    thread_monitor.join()


if __name__ == "__main__":
    main()

"""
relatorio.py
------------
Lê os logs do dia e envia um resumo para o Telegram às 20h.
Inclui processos órfãos eliminados e ficheiros apagados.

Bibliotecas usadas:
- requests  : para enviar mensagem ao Telegram
- schedule  : para agendar o envio às 20h
- time      : para o loop de espera
"""