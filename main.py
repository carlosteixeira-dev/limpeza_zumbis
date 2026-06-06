"""
main.py
-------
Ponto de entrada — arranca o monitor e o agendador do relatório em paralelo.

Bibliotecas usadas:
- threading : para correr monitor e agendador ao mesmo tempo
"""

import threading  # para correr as duas tarefas em paralelo
from monitor import loop_monitor, configurar_log  # monitor de órfãos
from relatorio import correr_agendador  # agendador do relatório


def main():
    """Arranca o monitor e o agendador em threads separadas."""
    logger = configurar_log()  # configura o log
    logger.info("🚀 A iniciar Monitor de Processos Órfãos...")

    # thread do monitor — corre em segundo plano
    thread_monitor = threading.Thread(target=loop_monitor, daemon=True)
    thread_monitor.start()  # arranca o monitor

    # thread do agendador — corre em segundo plano
    thread_relatorio = threading.Thread(target=correr_agendador, daemon=True)
    thread_relatorio.start()  # arranca o agendador

    logger.info("✅ Tudo a correr! Relatório enviado às 20:00.")

    # mantém o programa vivo
    thread_monitor.join()


if __name__ == "__main__":
    main()