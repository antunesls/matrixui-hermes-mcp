#!/usr/bin/env python3
"""Hermes Terminal Dashboard — Interface Visual (TUI).

Aplicação de terminal rica (Textual + Rich) destinada a rodar em primeiro plano
no monitor físico de um dispositivo Linux em modo CLI (ex.: Orange Pi com Ubuntu
Server, sem X11/Wayland).

A aplicação sobe um servidor TCP interno (asyncio) em segundo plano para receber
comandos vindos do servidor MCP (`mcp_server.py`). As mensagens trafegam como
JSON delimitado por newline (NDJSON) — uma linha = uma mensagem — com o schema:

    {"tipo": "<skill>", "dados": {...}, "log": "<linha de log>"}
    {"conteudo": "<markdown>", "log": "<linha de log>", "acao": "update|clear"}

O campo `tipo` (default "markdown") seleciona um renderizador especializado do
módulo `renderers.py` (previsao_tempo, tabela, grafico, metricas, alerta, qrcode,
tarefas). Quando ausente ou "markdown", o campo `conteudo` é renderizado como
Markdown — mantendo compatibilidade com o protocolo original.

Execução:
    python tui_display.py

Variáveis de ambiente:
    HERMES_TUI_HOST  (default: 127.0.0.1)
    HERMES_TUI_PORT  (default: 9999)
"""

from __future__ import annotations

import asyncio
import json
import os
from datetime import datetime
from typing import Any

from rich.console import RenderableType
from rich.markdown import Markdown
from textual.app import App, ComposeResult
from textual.containers import Horizontal, ScrollableContainer
from textual.reactive import reactive
from textual.widgets import Footer, RichLog, Static

from renderers import RENDERERS, TITULOS_SKILL

# --------------------------------------------------------------------------- #
# Configuração
# --------------------------------------------------------------------------- #
HOST: str = os.getenv("HERMES_TUI_HOST", "127.0.0.1")
PORT: int = int(os.getenv("HERMES_TUI_PORT", "9999"))

# Tamanho máximo de uma única linha NDJSON aceita (proteção contra payloads enormes).
MAX_LINE_BYTES: int = 4 * 1024 * 1024  # 4 MiB

WELCOME_MARKDOWN: str = """\
# HERMES AGENT OS

> Monitor visual pronto. Aguardando comandos do agente...

O painel principal renderiza **Markdown** completo: títulos, listas, tabelas e
blocos de código. O agente atualiza esta tela através da ferramenta MCP
`atualizar_monitor`.

```text
status: online
canal : TCP NDJSON
```
"""


class HermesHeader(Static):
    """Header customizado com título, relógio em tempo real e status de conexão."""

    clock: reactive[str] = reactive("")
    status: reactive[str] = reactive("AGUARDANDO")
    last_update: reactive[str] = reactive("--:--:--")

    def on_mount(self) -> None:
        """Inicia o relógio assim que o widget é montado."""
        self.set_interval(1.0, self._tick)
        self._tick()

    def _tick(self) -> None:
        self.clock = datetime.now().strftime("%Y-%m-%d  %H:%M:%S")

    def watch_clock(self, _value: str) -> None:
        self._render()

    def watch_status(self, _value: str) -> None:
        self._render()

    def watch_last_update(self, _value: str) -> None:
        self._render()

    def _render(self) -> None:
        """Renderiza a barra do header com colunas alinhadas."""
        title = "[b]HERMES AGENT OS[/b]"
        status = f"[b]◉ {self.status}[/b]"
        info = f"upd {self.last_update}  │  {self.clock}"
        self.update(f"{title}    [dim]│[/dim]    {status}    [dim]│[/dim]    {info}")


class HermesDashboard(App):
    """Aplicação principal da TUI do Hermes Terminal Dashboard."""

    TITLE = "HERMES AGENT OS"

    CSS = """
    Screen {
        background: #0a0e14;
        color: #c9d1d9;
    }

    HermesHeader {
        dock: top;
        height: 3;
        padding: 1 2;
        background: #0d1117;
        color: #00ff9c;
        border: round #00ff9c;
        content-align: left middle;
    }

    #body {
        height: 1fr;
        padding: 0 1;
    }

    #main-panel {
        width: 70%;
        height: 100%;
        margin: 0 1 0 0;
        padding: 1 2;
        background: #0d1117;
        border: round #00e5ff;
        border-title-color: #00e5ff;
        border-title-align: left;
    }

    #content {
        width: 100%;
        height: auto;
    }

    #sidebar {
        width: 30%;
        height: 100%;
        padding: 1 1;
        background: #0d1117;
        border: round #00ff9c;
        border-title-color: #00ff9c;
        border-title-align: left;
    }

    Footer {
        background: #0d1117;
        color: #00e5ff;
    }
    """

    BINDINGS = [
        ("q", "quit", "Sair"),
        ("c", "clear_panel", "Limpar painel"),
    ]

    def compose(self) -> ComposeResult:
        """Constrói a árvore de widgets da interface."""
        yield HermesHeader()
        with Horizontal(id="body"):
            with ScrollableContainer(id="main-panel") as panel:
                panel.border_title = "PAINEL PRINCIPAL"
                yield Static(Markdown(WELCOME_MARKDOWN), id="content")
            log = RichLog(id="sidebar", highlight=True, markup=True, wrap=True)
            log.border_title = "ACTIVITY LOG"
            yield log
        yield Footer()

    def on_mount(self) -> None:
        """Inicia o servidor TCP em segundo plano dentro do loop do Textual."""
        self._log("INFO", f"TUI iniciada. Servidor TCP em {HOST}:{PORT}")
        self.run_worker(
            self._serve(), name="tcp-server", group="net", exclusive=True
        )

    # ------------------------------------------------------------------ #
    # Servidor TCP (asyncio)
    # ------------------------------------------------------------------ #
    async def _serve(self) -> None:
        """Sobe o servidor asyncio e o mantém ativo durante a vida da app."""
        try:
            server = await asyncio.start_server(self._handle_client, HOST, PORT)
        except OSError as exc:
            self._log("ERRO", f"Falha ao abrir servidor TCP: {exc}")
            self._set_status("ERRO SOCKET")
            return

        addrs = ", ".join(str(sock.getsockname()) for sock in server.sockets)
        self._log("INFO", f"Escutando em {addrs}")
        self._set_status("ONLINE")
        async with server:
            await server.serve_forever()

    async def _handle_client(
        self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ) -> None:
        """Trata uma conexão: lê linhas NDJSON e aplica cada mensagem."""
        peer = writer.get_extra_info("peername")
        try:
            while not reader.at_eof():
                try:
                    raw = await reader.readline()
                except (asyncio.LimitOverrunError, ValueError):
                    self._log("ERRO", "Linha excede o limite permitido; descartada.")
                    break
                if not raw:
                    break
                if len(raw) > MAX_LINE_BYTES:
                    self._log("ERRO", "Payload muito grande; ignorado.")
                    continue
                line = raw.decode("utf-8", errors="replace").strip()
                if not line:
                    continue
                self._processar_mensagem(line)
            # Confirmação simples para o cliente (mcp_server).
            try:
                writer.write(b'{"status":"ok"}\n')
                await writer.drain()
            except (ConnectionError, OSError):
                pass
        except (ConnectionError, OSError) as exc:
            self._log("ERRO", f"Conexão {peer} encerrada: {exc}")
        finally:
            try:
                writer.close()
                await writer.wait_closed()
            except (ConnectionError, OSError):
                pass

    def _processar_mensagem(self, line: str) -> None:
        """Faz o parse de uma linha NDJSON e atualiza a interface."""
        try:
            payload: dict[str, Any] = json.loads(line)
        except json.JSONDecodeError as exc:
            self._log("ERRO", f"JSON inválido recebido: {exc}")
            return

        if not isinstance(payload, dict):
            self._log("ERRO", "Payload não é um objeto JSON; ignorado.")
            return

        acao = str(payload.get("acao", "update")).lower()
        tipo = str(payload.get("tipo", "markdown")).lower()
        log_msg = payload.get("log")

        if acao == "clear":
            self._set_panel_title("PAINEL PRINCIPAL")
            self._set_markdown(WELCOME_MARKDOWN)
            self._log("INFO", "Painel limpo pelo agente.")
        elif tipo != "markdown" and tipo in RENDERERS:
            self._render_skill(tipo, payload.get("dados", {}))
        else:
            conteudo = payload.get("conteudo")
            if tipo != "markdown" and tipo not in RENDERERS:
                self._log("ERRO", f"Tipo de renderização desconhecido: '{tipo}'")
            elif conteudo is not None:
                self._set_panel_title("PAINEL PRINCIPAL")
                self._set_markdown(str(conteudo))

        if log_msg:
            self._log("AGENTE", str(log_msg))

        self._mark_updated()

    def _render_skill(self, tipo: str, dados: dict[str, Any]) -> None:
        """Invoca o renderizador da skill e exibe o resultado no painel."""
        renderer = RENDERERS[tipo]
        try:
            renderable = renderer(dados if isinstance(dados, dict) else {})
        except Exception as exc:  # noqa: BLE001 - dados vindos da rede
            self._log("ERRO", f"Skill '{tipo}' falhou: {exc}")
            self._set_panel_title("ERRO")
            self._set_markdown(
                f"# ⚠️ Erro ao renderizar `{tipo}`\n\n```\n{exc}\n```"
            )
            return
        self._set_panel_title(TITULOS_SKILL.get(tipo, tipo.upper()))
        self._set_content(renderable)
        self._log("AGENTE", f"Skill renderizada: {tipo}")

    # ------------------------------------------------------------------ #
    # Helpers de atualização da UI
    # ------------------------------------------------------------------ #
    def _set_content(self, renderable: RenderableType) -> None:
        """Exibe um renderable do Rich no painel principal."""
        try:
            content = self.query_one("#content", Static)
            content.update(renderable)
        except Exception as exc:  # noqa: BLE001 - UI pode estar desmontando
            self._log("ERRO", f"Falha ao atualizar painel: {exc}")

    def _set_markdown(self, markdown_text: str) -> None:
        """Renderiza texto Markdown no painel principal."""
        self._set_content(Markdown(markdown_text))

    def _set_panel_title(self, title: str) -> None:
        """Atualiza o título da borda do painel principal."""
        try:
            self.query_one("#main-panel", ScrollableContainer).border_title = title
        except Exception:  # noqa: BLE001
            pass

    def _log(self, level: str, message: str) -> None:
        """Adiciona uma linha colorida ao RichLog lateral."""
        colors = {
            "INFO": "#00e5ff",
            "AGENTE": "#00ff9c",
            "ERRO": "#ff5c7c",
        }
        color = colors.get(level, "#c9d1d9")
        ts = datetime.now().strftime("%H:%M:%S")
        try:
            log = self.query_one("#sidebar", RichLog)
            log.write(f"[dim]{ts}[/dim] [b {color}]\\[{level}][/b {color}] {message}")
        except Exception:  # noqa: BLE001 - durante boot o widget pode não existir
            pass

    def _set_status(self, status: str) -> None:
        try:
            self.query_one(HermesHeader).status = status
        except Exception:  # noqa: BLE001
            pass

    def _mark_updated(self) -> None:
        try:
            self.query_one(HermesHeader).last_update = datetime.now().strftime(
                "%H:%M:%S"
            )
        except Exception:  # noqa: BLE001
            pass

    # ------------------------------------------------------------------ #
    # Ações de teclado
    # ------------------------------------------------------------------ #
    def action_clear_panel(self) -> None:
        """Limpa o painel principal (atalho `C`)."""
        self._set_panel_title("PAINEL PRINCIPAL")
        self._set_markdown(WELCOME_MARKDOWN)
        self._log("INFO", "Painel limpo manualmente.")


def main() -> None:
    """Ponto de entrada da aplicação."""
    HermesDashboard().run()


if __name__ == "__main__":
    main()
