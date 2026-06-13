#!/usr/bin/env python3
"""Hermes Terminal Dashboard — Servidor MCP (Plugin/Ferramenta da IA).

Servidor MCP (Model Context Protocol) construído com o SDK oficial `mcp`
(`mcp.server.fastmcp.FastMCP`), exposto via transporte **stdio** — formato
carregado pelo `config.json` do agente Hermes.

Expõe a ferramenta `atualizar_monitor`, que se conecta ao servidor TCP da TUI
(`tui_display.py`) em `localhost:9999`, envia um payload JSON delimitado por
newline (NDJSON) e encerra a conexão, retornando uma string de status para a IA.

Execução direta (stdio):
    python mcp_server.py

Inspeção/teste:
    mcp dev mcp_server.py

Variáveis de ambiente:
    HERMES_TUI_HOST  (default: 127.0.0.1)
    HERMES_TUI_PORT  (default: 9999)
"""

from __future__ import annotations

import asyncio
import json
import os
from typing import Any

from mcp.server.fastmcp import FastMCP

# --------------------------------------------------------------------------- #
# Configuração
# --------------------------------------------------------------------------- #
HOST: str = os.getenv("HERMES_TUI_HOST", "127.0.0.1")
PORT: int = int(os.getenv("HERMES_TUI_PORT", "9999"))
CONNECT_TIMEOUT: float = 5.0  # segundos

mcp = FastMCP("Hermes Terminal Dashboard")


# --------------------------------------------------------------------------- #
# Comunicação com a TUI
# --------------------------------------------------------------------------- #
async def _enviar_payload(payload: dict[str, Any]) -> str:
    """Abre uma conexão TCP rápida com a TUI, envia o payload NDJSON e fecha.

    Args:
        payload: Dicionário a ser serializado em JSON e enviado.

    Returns:
        Mensagem de status legível para a IA (sucesso ou erro).
    """
    linha = (json.dumps(payload, ensure_ascii=False) + "\n").encode("utf-8")

    try:
        reader, writer = await asyncio.wait_for(
            asyncio.open_connection(HOST, PORT), timeout=CONNECT_TIMEOUT
        )
    except (ConnectionRefusedError, ConnectionError, OSError, asyncio.TimeoutError):
        return (
            f"⚠️ Monitor offline: não foi possível conectar ao display TUI em "
            f"{HOST}:{PORT}. Verifique se o `tui_display.py` está rodando na "
            f"Orange Pi."
        )

    try:
        writer.write(linha)
        await asyncio.wait_for(writer.drain(), timeout=CONNECT_TIMEOUT)
        # Tenta ler a confirmação da TUI (não obrigatório).
        try:
            await asyncio.wait_for(reader.readline(), timeout=CONNECT_TIMEOUT)
        except asyncio.TimeoutError:
            pass
    except (ConnectionError, OSError, asyncio.TimeoutError) as exc:
        return f"⚠️ Erro ao enviar dados ao monitor: {exc}"
    finally:
        try:
            writer.close()
            await writer.wait_closed()
        except (ConnectionError, OSError):
            pass

    return "✅ Monitor atualizado com sucesso."


# --------------------------------------------------------------------------- #
# Ferramenta MCP
# --------------------------------------------------------------------------- #
@mcp.tool()
async def atualizar_monitor(
    conteudo_markdown: str, mensagem_log: str | None = None
) -> str:
    """Exibe conteúdo visual no monitor físico conectado à Orange Pi.

    USE ESTA FERRAMENTA SEMPRE QUE o usuário pedir para você **exibir, desenhar,
    listar, mostrar ou apresentar** dados estruturados visualmente na tela física
    (o monitor ligado ao dispositivo Linux). Exemplos de gatilhos: "mostre a
    previsão do tempo na tela", "liste minhas tarefas no monitor", "desenhe uma
    tabela com os resultados", "exiba o status do sistema".

    O conteúdo é renderizado em um painel que suporta **Markdown completo**:
    - Títulos (`#`, `##`, ...)
    - Listas ordenadas e não ordenadas
    - Tabelas Markdown (`| coluna | coluna |`)
    - Blocos de código com destaque de sintaxe (```linguagem)
    - Negrito, itálico, citações e links

    Sempre formate o `conteudo_markdown` de forma rica e legível para
    aproveitar a tela. A cada chamada o painel principal é substituído pelo
    novo conteúdo.

    Args:
        conteudo_markdown: O texto em formato Markdown a ser renderizado no
            painel principal do monitor. Aceite Markdown completo.
        mensagem_log: (Opcional) Uma nota curta de atividade exibida no log
            lateral do monitor, descrevendo a ação. Ex.: "Atualizando previsão
            do tempo...". Mantenha curta (uma linha).

    Returns:
        Uma string indicando se o monitor foi atualizado com sucesso ou se
        ocorreu um erro (ex.: monitor offline).
    """
    payload: dict[str, Any] = {"conteudo": conteudo_markdown, "acao": "update"}
    if mensagem_log:
        payload["log"] = mensagem_log
    return await _enviar_payload(payload)


@mcp.tool()
async def limpar_monitor() -> str:
    """Limpa o painel principal do monitor físico, voltando à tela inicial.

    Use quando o usuário pedir para **limpar, apagar ou resetar** o que está
    sendo exibido na tela física.

    Returns:
        Uma string de status (sucesso ou erro).
    """
    return await _enviar_payload({"acao": "clear", "log": "Tela limpa pelo agente."})


if __name__ == "__main__":
    # Transporte stdio (default) — formato consumido pelo config.json do Hermes.
    mcp.run()
