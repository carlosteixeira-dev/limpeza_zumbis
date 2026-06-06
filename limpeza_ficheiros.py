"""
limpeza_ficheiros.py
--------------------
Limpa ficheiros temporários e capturas de ecrã antigas.

Bibliotecas usadas:
- os       : para percorrer pastas e apagar ficheiros
- pathlib  : para manipular caminhos de ficheiros
- logging  : para guardar log do que foi apagado
- datetime : para verificar a idade dos ficheiros
"""

import os  # para operações no sistema de ficheiros
import logging  # para guardar log
from pathlib import Path  # para manipular caminhos
from datetime import datetime, timedelta  # para calcular idade dos ficheiros

# --- CONFIGURAÇÃO ---
DIAS_CAPTURAS = 30       # apaga capturas com mais de 30 dias
PASTA_CAPTURAS = Path(r"C:\Users\carlo\Pictures\Screenshots")  # pasta de capturas
PASTA_TEMP = Path(os.environ.get("TEMP", r"C:\Users\carlo\AppData\Local\Temp"))  # pasta temp

# extensões de ficheiros temporários a apagar
EXTENSOES_TEMP = {".tmp", ".temp", ".log", ".bak", ".old", ".$$$"}


def obter_idade_dias(ficheiro: Path) -> float:
    """Devolve a idade de um ficheiro em dias."""
    try:
        modificado = datetime.fromtimestamp(ficheiro.stat().st_mtime)  # data de modificação
        return (datetime.now() - modificado).days  # diferença em dias
    except:
        return 0


def limpar_capturas(logger: logging.Logger) -> list[dict]:
    """
    Apaga capturas de ecrã com mais de DIAS_CAPTURAS dias.
    Devolve lista de ficheiros apagados.
    """
    apagados = []  # lista de ficheiros apagados

    if not PASTA_CAPTURAS.exists():  # verifica se a pasta existe
        logger.warning(f"⚠️  Pasta de capturas não encontrada: {PASTA_CAPTURAS}")
        return []

    for ficheiro in PASTA_CAPTURAS.iterdir():  # percorre a pasta
        if not ficheiro.is_file():  # ignora pastas
            continue

        idade = obter_idade_dias(ficheiro)  # calcula a idade

        if idade >= DIAS_CAPTURAS:  # só apaga se for antigo
            try:
                tamanho_mb = ficheiro.stat().st_size / 1024 / 1024  # tamanho em MB
                ficheiro.unlink()  # apaga o ficheiro
                logger.info(f"🖼️  Captura apagada: {ficheiro.name} ({idade} dias, {tamanho_mb:.1f} MB)")
                apagados.append({
                    "tipo": "captura",
                    "nome": ficheiro.name,
                    "idade_dias": idade,
                    "tamanho_mb": round(tamanho_mb, 1)
                })
            except Exception as erro:
                logger.warning(f"⚠️  Não foi possível apagar {ficheiro.name}: {erro}")

    return apagados


def limpar_temporarios(logger: logging.Logger) -> list[dict]:
    """
    Apaga ficheiros temporários da pasta TEMP.
    Devolve lista de ficheiros apagados.
    """
    apagados = []  # lista de ficheiros apagados

    if not PASTA_TEMP.exists():  # verifica se a pasta existe
        logger.warning(f"⚠️  Pasta TEMP não encontrada: {PASTA_TEMP}")
        return []

    for ficheiro in PASTA_TEMP.iterdir():  # percorre a pasta
        if not ficheiro.is_file():  # ignora pastas
            continue

        # só apaga extensões conhecidas como temporárias
        if ficheiro.suffix.lower() not in EXTENSOES_TEMP:
            continue

        try:
            tamanho_mb = ficheiro.stat().st_size / 1024 / 1024  # tamanho em MB
            ficheiro.unlink()  # apaga o ficheiro
            logger.info(f"🗑️  Temp apagado: {ficheiro.name} ({tamanho_mb:.1f} MB)")
            apagados.append({
                "tipo": "temp",
                "nome": ficheiro.name,
                "idade_dias": obter_idade_dias(ficheiro),
                "tamanho_mb": round(tamanho_mb, 1)
            })
        except Exception as erro:
            logger.warning(f"⚠️  Não foi possível apagar {ficheiro.name}: {erro}")

    return apagados


def correr_limpeza(logger: logging.Logger) -> list[dict]:
    """
    Corre a limpeza completa — capturas e temporários.
    Devolve lista de todos os ficheiros apagados.
    """
    logger.info("🧹 A limpar ficheiros...")

    apagados = []
    apagados.extend(limpar_capturas(logger))    # limpa capturas
    apagados.extend(limpar_temporarios(logger))  # limpa temporários

    total_mb = sum(f["tamanho_mb"] for f in apagados)  # espaço total libertado

    if apagados:
        logger.info(f"   ✅ {len(apagados)} ficheiro(s) apagado(s) | {total_mb:.1f} MB libertados")
    else:
        logger.info("   ✅ Nada para limpar")

    return apagados


if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(message)s")
    logger = logging.getLogger(__name__)
    correr_limpeza(logger)