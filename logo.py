#!/usr/bin/env python3
"""Hermes Terminal Dashboard — Logo ASCII do projeto.

Pode ser executado diretamente para visualizar o logo no terminal:
    python logo.py
"""

from __future__ import annotations

from rich.align import Align
from rich.console import Console, RenderableType
from rich.text import Text

# --------------------------------------------------------------------------- #
# Logo customizado MATRIXUI
# --------------------------------------------------------------------------- #
MATRIXUI_LOGO_ASCII = (
    "╔════════════════════════════════════════════════════════════════╗\n"
    "║  1 0 1     0 1 0     1 1 0      0 0 1      1 0 1               ║\n"
    "║                                                                ║\n"
    "║   ███╗   ███╗  █████╗  ████████╗ ██████╗  ██╗ ██╗  ██╗         ║\n"
    "║   ████╗ ████║ ██╔══██╗ ╚══██╔══╝ ██╔══██╗ ██║ ╚██╗██╔╝         ║\n"
    "║   ██╔████╔██║ ███████║    ██║    ██████╔╝ ██║  ╚███╔╝          ║\n"
    "║   ██║╚██╔╝██║ ██╔══██║    ██║    ██╔══██╗ ██║  ██╔██╗          ║\n"
    "║   ██║ ╚═╝ ██║ ██║  ██║    ██║    ██║  ██║ ██║ ██╔╝ ██╗         ║\n"
    "║                                                                ║\n"
    "║              ██╗   ██╗ ██╗                                     ║\n"
    "║              ██║   ██║ ██║      ACCESS_GRANTED                 ║\n"
    "║              ██║   ██║ ██║      STATUS::ACTIVE                 ║\n"
    "║              ╚██████╔╝ ██║      MATRIX_UI::READY               ║\n"
    "║               ╚═════╝  ╚═╝                                     ║\n"
    "║                                                                ║\n"
    "║  [ booting interface ] [ neural display ] [ secure shell ]     ║\n"
    "╚════════════════════════════════════════════════════════════════╝"
)

# Versão do projeto (mantida aqui como fonte de verdade).
VERSION = "1.6.0"

# Palavras-chave de status (para detecção de linha)
_STATUS_KEYWORDS = ("ACCESS_GRANTED", "STATUS::", "MATRIX_UI::")
_FOOTER_KEYWORDS = ("booting interface", "neural display", "secure shell")
_BINARY_KEYWORDS = ("1 0 1", "0 1 0", "1 1 0", "0 0 1")


def render_logo(cor: str = "#00ff00", largura: int = 60) -> RenderableType:
    """Retorna o logo do projeto como um renderable Rich centralizado.

    Args:
        cor: Cor hex neon do logo (default: #00ff00 — verde Matrix clássico).
        largura: Ignorado — logo tem largura fixa. Mantido por compatibilidade.

    Returns:
        Rich renderable centralizado com coloração uniforme na cor escolhida.
    """
    texto = Text(no_wrap=True)
    for linha in MATRIXUI_LOGO_ASCII.splitlines():
        estilo = _estilo_linha(linha, cor)
        texto.append(linha + "\n", style=estilo)
    return Align.center(texto)


def _estilo_linha(linha: str, cor: str) -> str:
    """Determina o estilo Rich para uma linha do logo (tudo na mesma cor)."""
    if "██" in linha:
        return f"bold {cor}"
    if any(kw in linha for kw in _STATUS_KEYWORDS):
        return f"bold {cor}"
    if any(kw in linha for kw in _FOOTER_KEYWORDS) or any(kw in linha for kw in _BINARY_KEYWORDS):
        return f"dim {cor}"
    return cor


# --------------------------------------------------------------------------- #
# Execução standalone
# --------------------------------------------------------------------------- #
if __name__ == "__main__":
    console = Console()
    console.print()
    console.print(render_logo())
    console.print(f"\n  [dim]Hermes Terminal Dashboard · MatrixUI  v{VERSION}[/dim]\n")
