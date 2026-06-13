#!/usr/bin/env python3
"""Hermes Terminal Dashboard — Logo ASCII do projeto.

Pode ser executado diretamente para visualizar o logo no terminal:
    python logo.py
"""

from __future__ import annotations

from rich.align import Align
from rich.console import Console, Group, RenderableType
from rich.panel import Panel
from rich.text import Text

# --------------------------------------------------------------------------- #
# Arte ASCII do logo (gerado via pyfiglet doom + ajustes manuais)
# Guardado como constante para embutir no README e usar sem deps extras.
# --------------------------------------------------------------------------- #
HERMES_LOGO_ASCII = r"""
 _   _ _____ ____  __  __ _____ ____
| | | | ____|  _ \|  \/  | ____/ ___|
| |_| |  _| | |_) | |\/| |  _| \___ \
|  _  | |___|  _ <| |  | | |___ ___) |
|_| |_|_____|_| \_\_|  |_|_____|____/
"""

SUBTITLE_ASCII = "A G E N T   O S   ·   T E R M I N A L   D A S H B O A R D"

DECO_TOP    = "  ☽  ·  ·  ·  ◆  ·  ·  ·  ☾  "
DECO_LINE   = "─" * 50
DECO_BOTTOM = "  ·  ·  ·  ☽  ◆  ☾  ·  ·  ·  "

# Versão do projeto (mantida aqui como fonte de verdade).
VERSION = "1.4.0"


def render_logo(cor: str = "#00ff9c", largura: int = 60) -> RenderableType:
    """Retorna o logo do projeto como um renderable Rich.

    Args:
        cor: Cor hex neon do logo (default: verde neon).
        largura: Largura do painel envolvente.

    Returns:
        Rich renderable pronto para exibição.
    """
    # Tenta usar pyfiglet para melhorar a arte se disponível.
    hermes_art = _gerar_arte_hermes(cor)

    subtitulo = Text(SUBTITLE_ASCII, style=f"bold {cor}", justify="center")
    subtitulo_dim = Text(f"v{VERSION}", style="dim", justify="center")

    deco_top = Text(DECO_TOP, style=f"bold {cor}", justify="center")
    sep = Text(DECO_LINE, style=f"dim {cor}", justify="center")
    deco_bot = Text(DECO_BOTTOM, style=f"dim {cor}", justify="center")

    corpo = Group(
        deco_top,
        sep,
        hermes_art,
        sep,
        subtitulo,
        subtitulo_dim,
        sep,
        deco_bot,
    )

    return Panel(
        Align.center(corpo),
        border_style=cor,
        padding=(1, 4),
    )


def _gerar_arte_hermes(cor: str) -> RenderableType:
    """Gera a arte ASCII de HERMES via pyfiglet (doom) ou fallback."""
    try:
        from pyfiglet import figlet_format

        arte = figlet_format("HERMES", font="doom")
    except Exception:
        arte = HERMES_LOGO_ASCII

    return Text(arte, style=f"bold {cor}", justify="center")


# --------------------------------------------------------------------------- #
# Execução standalone
# --------------------------------------------------------------------------- #
if __name__ == "__main__":
    console = Console()
    console.print()
    console.print(render_logo())
    console.print(f"  [dim]Hermes Terminal Dashboard v{VERSION}[/dim]")
    console.print()
