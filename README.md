# Hermes Terminal Dashboard

> Um plugin **MCP (Model Context Protocol)** que dá a um agente de IA (Hermes) a
> capacidade de **exibir informações visuais** em um monitor físico ligado a um
> dispositivo Linux em modo CLI/terminal — sem X11/Wayland (ex.: Orange Pi com
> Ubuntu Server).
>
> *An MCP plugin that lets an AI agent draw rich, structured content on a
> physical monitor attached to a headless Linux box (e.g. an Orange Pi running
> Ubuntu Server in pure TTY mode).*

---

## 🇧🇷 Português

### O que é

O projeto tem dois processos desacoplados que conversam por um **socket TCP local**
(asyncio), evitando problemas de concorrência e de permissão de arquivos:

```
 ┌──────────┐  stdio   ┌───────────────┐  TCP NDJSON   ┌────────────────┐  HDMI
 │  Hermes  │ ───────▶ │ mcp_server.py │ ────────────▶ │ tui_display.py │ ─────▶ Monitor TTY1
 │   (IA)   │          │ (ferramenta)  │ localhost:9999│   (Textual)    │
 └──────────┘          └───────────────┘               └────────────────┘
```

- **`tui_display.py`** — Interface visual (Textual + Rich) rodando em primeiro plano
  no monitor. Abre um servidor TCP interno (asyncio) na porta `9999` para receber
  comandos. Layout estilo *cyberpunk/hacker*: header com relógio e status, painel
  principal que renderiza **Markdown** (títulos, listas, tabelas, código) e uma barra
  lateral de log de atividades.
- **`mcp_server.py`** — Servidor MCP (SDK oficial `mcp`, transporte stdio). Expõe as
  ferramentas `atualizar_monitor` e `limpar_monitor` para a IA. Conecta no socket da
  TUI, envia o payload JSON e retorna sucesso/erro para o agente.

### Protocolo

Mensagens em **JSON delimitado por newline (NDJSON)** — uma linha por mensagem:

```json
{"conteudo": "# Título\n- item", "log": "Atualizando...", "acao": "update"}
```

| Campo      | Descrição                                              |
|------------|--------------------------------------------------------|
| `conteudo` | Markdown renderizado no painel principal (opcional).   |
| `log`      | Linha adicionada ao log lateral (opcional).            |
| `acao`     | `update` (default) ou `clear` (limpa o painel).        |

### Instalação

```bash
git clone <seu-repo> matrixui
cd matrixui

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Rodando a TUI no monitor físico (TTY1)

#### Opção A — systemd + autologin *(recomendada, sobe no boot)*

A TUI precisa "tomar conta" do TTY1. A forma mais robusta é um serviço systemd:

```bash
# 1. Ajuste os caminhos/usuário dentro do arquivo e instale:
sudo cp hermes-tui.service /etc/systemd/system/hermes-tui.service
sudo systemctl daemon-reload
sudo systemctl enable --now hermes-tui.service
```

O unit já declara `Conflicts=getty@tty1.service` e assume o `/dev/tty1`, então a TUI
aparece sozinha no monitor a cada boot e reinicia caso caia (`Restart=always`).

> **Autologin do getty (opcional):** se você prefere manter um shell de login no TTY1
> e iniciar a TUI a partir dele (em vez do serviço acima dominar o TTY), configure o
> autologin e chame a TUI no `~/.bash_profile`:
>
> ```bash
> sudo systemctl edit getty@tty1
> ```
> Conteúdo:
> ```ini
> [Service]
> ExecStart=
> ExecStart=-/sbin/agetty --autologin orangepi --noclear %I $TERM
> ```
> E no `~/.bash_profile` do usuário:
> ```bash
> if [ "$(tty)" = "/dev/tty1" ]; then
>   cd ~/matrixui && source .venv/bin/activate && exec python tui_display.py
> fi
> ```

#### Opção B — `openvt` (sob demanda)

Inicia a TUI em um terminal virtual livre e troca para ele:

```bash
sudo openvt -c 1 -s -- python /home/orangepi/matrixui/tui_display.py
```

#### Opção C — `tmux` (inspecionável)

```bash
tmux new-session -d -s hermes 'python /home/orangepi/matrixui/tui_display.py'
tmux attach -t hermes   # para visualizar
```

### Configurando o Hermes para carregar o servidor MCP

Use o `config.example.json` como base. Copie o bloco `hermes-monitor` para dentro do
`mcpServers` do `config.json` do seu agente, ajustando o caminho absoluto:

```json
{
  "mcpServers": {
    "hermes-monitor": {
      "command": "python",
      "args": ["/home/orangepi/matrixui/mcp_server.py"],
      "env": {
        "HERMES_TUI_HOST": "127.0.0.1",
        "HERMES_TUI_PORT": "9999"
      }
    }
  }
}
```

> Use o `python` do virtualenv (ex.: `/home/orangepi/matrixui/.venv/bin/python`) para
> garantir que as dependências sejam encontradas.

### Testando

Com a TUI rodando, teste o socket manualmente (sem o MCP):

```bash
printf '{"conteudo":"# Olá\n- item 1\n- item 2","log":"teste manual"}\n' | nc 127.0.0.1 9999
printf '{"acao":"clear"}\n' | nc 127.0.0.1 9999
```

Teste a ferramenta MCP com o inspector oficial:

```bash
mcp dev mcp_server.py
# invoque atualizar_monitor(conteudo_markdown="# Teste", mensagem_log="oi")
```

### Variáveis de ambiente

| Variável           | Default       | Descrição                  |
|--------------------|---------------|----------------------------|
| `HERMES_TUI_HOST`  | `127.0.0.1`   | Host do socket da TUI.      |
| `HERMES_TUI_PORT`  | `9999`        | Porta do socket da TUI.     |

### Atalhos da TUI

| Tecla | Ação            |
|-------|-----------------|
| `Q`   | Sair            |
| `C`   | Limpar o painel |

---

## 🇬🇧 English (quick guide)

**Hermes Terminal Dashboard** is an MCP plugin that lets an AI agent render rich
Markdown on a physical monitor attached to a headless Linux device.

- `tui_display.py` — a Textual/Rich TUI that runs on the monitor and opens an internal
  asyncio TCP server (port `9999`) to receive commands. Cyberpunk-styled layout: header
  with live clock + connection status, a 70% Markdown panel, and a 30% activity log.
- `mcp_server.py` — an MCP server (official `mcp` SDK, stdio transport) exposing the
  `atualizar_monitor` and `limpar_monitor` tools. It connects to the TUI socket, sends a
  newline-delimited JSON payload, and returns a success/error string to the AI.

**Install**

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

**Run the TUI on TTY1** — recommended: install the bundled systemd unit
(`hermes-tui.service`), which claims `/dev/tty1`, auto-starts on boot and restarts on
failure. Alternatives: `openvt -c 1 -s -- python tui_display.py` or a `tmux` session.

**Wire it into the agent** — copy the `hermes-monitor` block from `config.example.json`
into your agent's `config.json` under `mcpServers`, pointing `args` at the absolute path
of `mcp_server.py`.

**Test**

```bash
printf '{"conteudo":"# Hello","log":"manual test"}\n' | nc 127.0.0.1 9999
mcp dev mcp_server.py
```

**Protocol** — newline-delimited JSON, one message per line:
`{"conteudo": "...", "log": "...", "acao": "update|clear"}`.

**Env vars** — `HERMES_TUI_HOST` (default `127.0.0.1`), `HERMES_TUI_PORT` (default
`9999`). **Keys** — `Q` quit, `C` clear panel.
