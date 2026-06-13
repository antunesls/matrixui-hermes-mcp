# Changelog

Todas as mudanças notáveis neste projeto serão documentadas neste arquivo.

O formato segue [Keep a Changelog](https://keepachangelog.com/pt-BR/), e este projeto
adere ao [Semantic Versioning](https://semver.org/lang/pt-BR/).

## [1.1.0] — 2026-06-13

### Added

- **install.sh** — Script Bash automatizado para instalação completa em um ambiente Linux
  (Orange Pi/Ubuntu Server). Detecta o usuário alvo, configura getty@tty1 com autologin,
  instala o serviço systemd, habilita restart automático e configura o ~/.bash_profile.
  Uso: `sudo bash install.sh [usuario]`.

- **Seção "Solução de Problemas" (Troubleshooting)** no README.md (PT + EN) com
  diagnóstico e fixes para:
  - getty@tty1 não sobe no boot
  - TUI não aparece no monitor
  - Porta 9999 já em uso

- **Comentários detalhados** no `config.example.json` para cada campo e variável de
  ambiente, facilitando a configuração na Orange Pi.

### Changed

- **hermes-tui.service** — Aumentado `RestartSec` de 2s para 3s para dar mais tempo
  ao serviço recuperar-se de falhas transitórias (ex.: TTY não pronto imediatamente
  após boot).

## [1.0.0] — 2026-06-13

### Added

- **Projeto inicial: Hermes Terminal Dashboard** — Plugin MCP completo e pronto para
  produção que permite a um agente de IA exibir informações visuais em um monitor
  físico ligado a um dispositivo Linux sem interface gráfica (Orange Pi, Ubuntu
  Server, etc.).

- **tui_display.py** — Interface visual (Textual + Rich) com:
  - Header em tempo real: título, relógio, indicador de status de conexão
  - Painel principal (70%): renderizador Markdown com suporte a títulos, listas,
    tabelas, blocos de código
  - Sidebar (30%): RichLog com histórico de atividades
  - Servidor asyncio TCP (NDJSON) em segundo plano
  - Atalhos: `Q` (sair), `C` (limpar)
  - Tema cyberpunk: cores neon verde (#00ff9c) e ciano (#00e5ff)

- **mcp_server.py** — Servidor MCP (SDK oficial `mcp[cli]`, transporte stdio) com:
  - Ferramenta `atualizar_monitor(conteudo_markdown, mensagem_log)` — exibe Markdown
    no painel principal
  - Ferramenta `limpar_monitor()` — reseta o painel
  - Docstrings ricas guiando o modelo sobre quando usar as ferramentas
  - Conexão TCP rápida com timeout e tratamento de erros gracioso
  - Mensagens amigáveis para a IA quando o monitor está offline

- **requirements.txt** — Dependências: `textual>=0.80`, `rich>=13.7`, `mcp[cli]>=1.2`

- **hermes-tui.service** — Unit systemd para rodar a TUI no TTY1 com:
  - Autoinício no boot via `WantedBy=multi-user.target`
  - Restart automático (`Restart=always`, `RestartSec=2`)
  - Captura de stdout/stderr para journald

- **config.example.json** — Exemplo de configuração MCP para o agente Hermes,
  mostrando como registrar o `mcp_server.py` via stdio.

- **README.md** (Português + English) — Documentação completa:
  - Descrição da arquitetura (diagram ASCII)
  - Protocolo NDJSON explicado
  - Guia de instalação (venv + pip)
  - 3 opções de rodar a TUI no TTY1 (systemd recomendado, openvt, tmux)
  - Configuração do Hermes
  - Testes manuais e via MCP Inspector
  - Referência de env vars e atalhos

- **.gitignore** — Padrões para Python, venv, IDEs, logs e arquivos locais.

[1.1.0]: https://github.com/antunesls/matrixui-hermes-mcp/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/antunesls/matrixui-hermes-mcp/releases/tag/v1.0.0
