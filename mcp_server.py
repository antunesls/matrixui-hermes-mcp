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


async def _enviar_skill(
    tipo: str, dados: dict[str, Any], mensagem_log: str | None
) -> str:
    """Monta o payload de uma skill estruturada (`tipo` + `dados`) e envia."""
    payload: dict[str, Any] = {"tipo": tipo, "dados": dados}
    if mensagem_log:
        payload["log"] = mensagem_log
    return await _enviar_payload(payload)


# --------------------------------------------------------------------------- #
# Ferramenta MCP — Markdown genérico
# --------------------------------------------------------------------------- #
@mcp.tool()
async def atualizar_monitor(
    conteudo_markdown: str, mensagem_log: str | None = None
) -> str:
    """Exibe conteúdo Markdown livre no monitor físico conectado à Orange Pi.

    USE ESTA FERRAMENTA para texto livre / conteúdo genérico formatado em
    Markdown. Para dados estruturados, **prefira as ferramentas especializadas**
    (renderização mais bonita, estilo ncurses):
      - `exibir_previsao_tempo` — previsão do tempo
      - `exibir_tabela` — tabelas
      - `exibir_grafico` — gráficos de barras
      - `exibir_metricas` — gauges/barras de progresso (CPU, RAM, KPIs)
      - `exibir_alerta` — banner de alerta com texto gigante
      - `exibir_qrcode` — QR code
      - `exibir_tarefas` — checklist / lista de tarefas

    O conteúdo é renderizado num painel que suporta **Markdown completo**:
    títulos, listas, tabelas, blocos de código, negrito, itálico, citações e links.
    A cada chamada o painel principal é substituído pelo novo conteúdo.

    Args:
        conteudo_markdown: Texto em Markdown a renderizar no painel principal.
        mensagem_log: (Opcional) Nota curta de atividade no log lateral.

    Returns:
        String de status (sucesso ou erro, ex.: monitor offline).
    """
    payload: dict[str, Any] = {"conteudo": conteudo_markdown, "acao": "update"}
    if mensagem_log:
        payload["log"] = mensagem_log
    return await _enviar_payload(payload)


# --------------------------------------------------------------------------- #
# Ferramentas MCP — Skills especializadas
# --------------------------------------------------------------------------- #
@mcp.tool()
async def exibir_previsao_tempo(
    local: str, dias: list[dict], mensagem_log: str | None = None
) -> str:
    """Exibe a previsão do tempo no monitor em estilo ncurses (cards com arte ASCII).

    USE quando o usuário pedir para **mostrar/exibir a previsão do tempo** na tela.
    Você fornece os dados (já obtidos por você); esta ferramenta apenas os desenha.

    Args:
        local: Nome do local exibido no topo. Ex.: "São Paulo, BR".
        dias: Lista de dias. Cada item é um dict com as chaves:
            - "dia" (str): rótulo do dia. Ex.: "Hoje", "Seg", "14/06".
            - "condicao" (str): uma de — "sol", "nuvem", "nublado", "chuva",
              "tempestade", "neve", "neblina" (define a arte ASCII e a cor).
            - "temp_max" (número): temperatura máxima.
            - "temp_min" (número): temperatura mínima.
            - "descricao" (str): texto curto. Ex.: "Pancadas de chuva".
            - "umidade" (número, opcional): % de umidade.
            - "vento" (str, opcional): ex.: "12 km/h".
            Exemplo de um dia:
            {"dia": "Hoje", "condicao": "chuva", "temp_max": 24, "temp_min": 17,
             "descricao": "Pancadas", "umidade": 80, "vento": "15 km/h"}
        mensagem_log: (Opcional) Nota curta para o log lateral.

    Returns:
        String de status (sucesso ou erro).
    """
    return await _enviar_skill(
        "previsao_tempo", {"local": local, "dias": dias}, mensagem_log
    )


@mcp.tool()
async def exibir_tabela(
    colunas: list[str],
    linhas: list[list],
    titulo: str | None = None,
    mensagem_log: str | None = None,
) -> str:
    """Exibe uma tabela rica no monitor (rich.Table com bordas e cores).

    USE quando o usuário pedir para **mostrar dados em forma de tabela** na tela.
    Renderização superior a uma tabela Markdown.

    Args:
        colunas: Cabeçalhos das colunas. Ex.: ["Produto", "Qtd", "Preço"].
        linhas: Lista de linhas; cada linha é uma lista de células (na ordem das
            colunas). Ex.: [["Café", "12", "R$ 8,50"], ["Pão", "30", "R$ 0,75"]].
        titulo: (Opcional) Título exibido acima da tabela.
        mensagem_log: (Opcional) Nota curta para o log lateral.

    Returns:
        String de status (sucesso ou erro).
    """
    dados: dict[str, Any] = {"colunas": colunas, "linhas": linhas}
    if titulo:
        dados["titulo"] = titulo
    return await _enviar_skill("tabela", dados, mensagem_log)


@mcp.tool()
async def exibir_grafico(
    series: list[dict],
    titulo: str | None = None,
    unidade: str | None = None,
    mensagem_log: str | None = None,
) -> str:
    """Exibe um gráfico de barras no monitor a partir de uma série de valores.

    USE quando o usuário pedir para **plotar/desenhar um gráfico** de valores ao
    longo de categorias (ex.: temperatura por dia, vendas por mês).

    Args:
        series: Lista de pontos. Cada item é um dict com:
            - "label" (str): rótulo da barra. Ex.: "Seg".
            - "valor" (número): altura da barra.
            Ex.: [{"label": "Seg", "valor": 23}, {"label": "Ter", "valor": 27}].
        titulo: (Opcional) Título do gráfico.
        unidade: (Opcional) Unidade dos valores. Ex.: "°C", "R$", "%".
        mensagem_log: (Opcional) Nota curta para o log lateral.

    Returns:
        String de status (sucesso ou erro).
    """
    dados: dict[str, Any] = {"series": series}
    if titulo:
        dados["titulo"] = titulo
    if unidade:
        dados["unidade"] = unidade
    return await _enviar_skill("grafico", dados, mensagem_log)


@mcp.tool()
async def exibir_metricas(
    metricas: list[dict], titulo: str | None = None, mensagem_log: str | None = None
) -> str:
    """Exibe métricas/gauges no monitor com barras de progresso coloridas.

    USE quando o usuário pedir para **mostrar indicadores/medidores** (CPU, RAM,
    disco, bateria, progresso, KPIs). As barras mudam de cor por faixa:
    verde (<60%), amarelo (<85%), vermelho (>=85%).

    Args:
        metricas: Lista de métricas. Cada item é um dict com:
            - "label" (str): nome da métrica. Ex.: "CPU".
            - "valor" (número): valor atual.
            - "max" (número, opcional): valor máximo (default 100).
            - "unidade" (str, opcional): ex.: "%", "GB".
            Ex.: [{"label": "CPU", "valor": 42, "unidade": "%"},
                  {"label": "RAM", "valor": 6, "max": 8, "unidade": "GB"}].
        titulo: (Opcional) Título do painel.
        mensagem_log: (Opcional) Nota curta para o log lateral.

    Returns:
        String de status (sucesso ou erro).
    """
    dados: dict[str, Any] = {"metricas": metricas}
    if titulo:
        dados["titulo"] = titulo
    return await _enviar_skill("metricas", dados, mensagem_log)


@mcp.tool()
async def exibir_alerta(
    texto: str,
    nivel: str = "info",
    subtitulo: str | None = None,
    mensagem_log: str | None = None,
) -> str:
    """Exibe um banner de alerta no monitor com texto gigante (ASCII art).

    USE quando o usuário pedir para **alertar/avisar/destacar** algo de forma
    chamativa na tela (ex.: "avise na tela que o backup terminou").

    Args:
        texto: Texto curto renderizado em letras grandes. Ex.: "BACKUP OK".
            Prefira poucas palavras (cabe melhor na tela).
        nivel: Severidade — "info" (ciano), "aviso" (amarelo) ou "critico"
            (vermelho). Define a cor do banner.
        subtitulo: (Opcional) Linha de detalhe abaixo do texto grande.
        mensagem_log: (Opcional) Nota curta para o log lateral.

    Returns:
        String de status (sucesso ou erro).
    """
    dados: dict[str, Any] = {"texto": texto, "nivel": nivel}
    if subtitulo:
        dados["subtitulo"] = subtitulo
    return await _enviar_skill("alerta", dados, mensagem_log)


@mcp.tool()
async def exibir_qrcode(
    conteudo: str, legenda: str | None = None, mensagem_log: str | None = None
) -> str:
    """Exibe um QR Code no monitor (ASCII) para o usuário escanear.

    USE quando o usuário pedir um **QR code** na tela — para compartilhar um link,
    credencial de Wi-Fi, endereço, etc.

    Args:
        conteudo: O dado codificado no QR. Ex.: uma URL "https://exemplo.com" ou
            uma string de Wi-Fi "WIFI:S:MinhaRede;T:WPA;P:senha123;;".
        legenda: (Opcional) Texto abaixo do QR. Default: o próprio conteúdo.
        mensagem_log: (Opcional) Nota curta para o log lateral.

    Returns:
        String de status (sucesso ou erro).
    """
    dados: dict[str, Any] = {"conteudo": conteudo}
    if legenda:
        dados["legenda"] = legenda
    return await _enviar_skill("qrcode", dados, mensagem_log)


@mcp.tool()
async def exibir_tarefas(
    itens: list[dict], titulo: str | None = None, mensagem_log: str | None = None
) -> str:
    """Exibe uma lista de tarefas / checklist no monitor.

    USE quando o usuário pedir para **listar tarefas/afazeres/checklist** na tela.

    Args:
        itens: Lista de tarefas. Cada item é um dict com:
            - "texto" (str): descrição da tarefa.
            - "feito" (bool): True se concluída (mostra ✓ e texto riscado).
            - "prioridade" (str, opcional): "alta", "media" ou "baixa" (tag colorida).
            Ex.: [{"texto": "Comprar pão", "feito": false, "prioridade": "alta"},
                  {"texto": "Pagar conta", "feito": true}].
        titulo: (Opcional) Título da lista. Ex.: "Hoje".
        mensagem_log: (Opcional) Nota curta para o log lateral.

    Returns:
        String de status (sucesso ou erro).
    """
    dados: dict[str, Any] = {"itens": itens}
    if titulo:
        dados["titulo"] = titulo
    return await _enviar_skill("tarefas", dados, mensagem_log)


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
