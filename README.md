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

Mensagens em **JSON delimitado por newline (NDJSON)** — uma linha por mensagem.
Dois formatos, ambos suportados:

```json
{"conteudo": "# Título\n- item", "log": "Atualizando...", "acao": "update"}
{"tipo": "previsao_tempo", "dados": {"local": "SP", "dias": [...]}, "log": "..."}
```

| Campo      | Descrição                                                          |
|------------|--------------------------------------------------------------------|
| `tipo`     | Renderizador a usar. Default `markdown`. Skills: ver tabela abaixo. |
| `conteudo` | Markdown a renderizar (usado quando `tipo` é `markdown`).           |
| `dados`    | Objeto estruturado, específico de cada skill (quando `tipo` != md). |
| `log`      | Linha adicionada ao log lateral (opcional).                        |
| `acao`     | `update` (default) ou `clear` (limpa o painel).                    |

> **Compatibilidade:** sem o campo `tipo`, o comportamento é idêntico ao original
> (renderiza `conteudo` como Markdown).

### Skills disponíveis

Cada skill é uma ferramenta MCP dedicada que o agente Hermes pode invocar. Os dados
são fornecidos pelo agente (o MCP não acessa rede); a TUI apenas os desenha em estilo
ncurses.

| Ferramenta MCP            | `tipo`           | O que renderiza                                      |
|---------------------------|------------------|------------------------------------------------------|
| `exibir_previsao_tempo`   | `previsao_tempo` | Cards de previsão do tempo com arte ASCII (wttr.in)  |
| `exibir_tabela`           | `tabela`         | Tabela rica com bordas e cores                        |
| `exibir_grafico`          | `grafico`        | Gráfico de barras (plotext, com fallback unicode)     |
| `exibir_metricas`         | `metricas`       | Gauges/barras coloridas por limiar (CPU, RAM, KPIs)   |
| `exibir_alerta`           | `alerta`         | Banner com texto gigante (pyfiglet)                   |
| `exibir_qrcode`           | `qrcode`         | QR Code em ASCII                                      |
| `exibir_tarefas`          | `tarefas`        | Checklist com ✓/☐ e prioridades                       |
| `atualizar_monitor`       | `markdown`       | Markdown livre (texto genérico)                       |

Exemplos de payload para teste via `nc` (uma linha cada):

```bash
# Previsão do tempo
printf '{"tipo":"previsao_tempo","dados":{"local":"São Paulo","dias":[{"dia":"Hoje","condicao":"chuva","temp_max":24,"temp_min":17,"descricao":"Pancadas","umidade":80,"vento":"15 km/h"},{"dia":"Ter","condicao":"sol","temp_max":28,"temp_min":18,"descricao":"Ensolarado"}]}}\n' | nc 127.0.0.1 9999

# Tabela
printf '{"tipo":"tabela","dados":{"titulo":"Vendas","colunas":["Produto","Qtd"],"linhas":[["Café","12"],["Pão","30"]]}}\n' | nc 127.0.0.1 9999

# Gráfico de barras
printf '{"tipo":"grafico","dados":{"titulo":"Temp","unidade":"°C","series":[{"label":"Seg","valor":23},{"label":"Ter","valor":27},{"label":"Qua","valor":19}]}}\n' | nc 127.0.0.1 9999

# Métricas / gauges
printf '{"tipo":"metricas","dados":{"titulo":"Sistema","metricas":[{"label":"CPU","valor":42,"unidade":"%%"},{"label":"RAM","valor":6,"max":8,"unidade":"GB"},{"label":"Disco","valor":91,"unidade":"%%"}]}}\n' | nc 127.0.0.1 9999

# Alerta / banner
printf '{"tipo":"alerta","dados":{"texto":"BACKUP OK","nivel":"info","subtitulo":"concluído às 03:00"}}\n' | nc 127.0.0.1 9999

# QR Code
printf '{"tipo":"qrcode","dados":{"conteudo":"https://exemplo.com","legenda":"Aponte a câmera"}}\n' | nc 127.0.0.1 9999

# Tarefas
printf '{"tipo":"tarefas","dados":{"titulo":"Hoje","itens":[{"texto":"Comprar pão","feito":false,"prioridade":"alta"},{"texto":"Pagar conta","feito":true}]}}\n' | nc 127.0.0.1 9999
```

### Instalação

```bash
git clone <seu-repo> matrixui
cd matrixui

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Rodando a TUI no monitor físico (TTY1)

#### Opção A — getty@tty1 + .bash_profile *(recomendada, testada em produção)*

A forma mais simples e confiável: getty faz login automático, e o `.bash_profile`
inicia a TUI. Use o script automatizado:

```bash
# Copie o repositório para a Orange Pi e execute:
sudo bash install.sh <SEU_USUARIO>
```

Se preferir fazer manualmente:

1. Configure o override do getty:

```bash
sudo systemctl edit getty@tty1
```

Adicione na seção `[Service]`:

```ini
[Service]
ExecStart=
ExecStart=-/sbin/agetty --autologin <SEU_USUARIO> --noclear %I $TERM
Restart=always
RestartSec=3
```

2. Adicione o bloco TTY1 ao `~/.bash_profile`:

```bash
if [ "$(tty)" = "/dev/tty1" ]; then
    cd ~/matrixui && source .venv/bin/activate && exec python tui_display.py
fi
```

3. Habilite e inicie:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now getty@tty1
```

Ao rebootar, a TUI aparece automaticamente no monitor.

#### Opção B — systemd (hermes-tui.service) *(alternativa: sem login shell)*

Se você prefere que o systemd reclame o TTY1 diretamente (sem shell de login):

```bash
# Ajuste os caminhos/usuário dentro do arquivo e instale:
sudo cp hermes-tui.service /etc/systemd/system/hermes-tui.service
sudo systemctl daemon-reload
sudo systemctl disable getty@tty1   # evita conflito
sudo systemctl enable --now hermes-tui.service
```

O unit declara `Conflicts=getty@tty1.service` e assume o `/dev/tty1`, reiniciando
automaticamente se cair (`Restart=always`).

#### Opção C — `openvt` (sob demanda)

Inicia a TUI em um terminal virtual livre e troca para ele:

```bash
sudo openvt -c 1 -s -- python ~/matrixui/tui_display.py
```

#### Opção D — `tmux` (inspecionável)

```bash
tmux new-session -d -s hermes 'python ~/matrixui/tui_display.py'
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
      "args": ["/home/<SEU_USUARIO>/matrixui/mcp_server.py"],
      "env": {
        "HERMES_TUI_HOST": "127.0.0.1",
        "HERMES_TUI_PORT": "9999"
      }
    }
  }
}
```

> Use o `python` do virtualenv (ex.: `/home/<SEU_USUARIO>/matrixui/.venv/bin/python`) para
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

### Solução de Problemas

#### getty@tty1 não sobe no boot

Se o serviço `getty@tty1` não inicializa automaticamente ao ligar a Orange Pi:

```bash
systemctl is-active getty@tty1   # verifica o status
```

Se estiver inativo, crie um override com autologin e restart automático:

```bash
sudo systemctl edit getty@tty1
```

Adicione ou descomente as linhas (editor abre a seção `[Service]`):

```ini
[Service]
ExecStart=
ExecStart=-/sbin/agetty --autologin orangepi --noclear %I $TERM
Restart=always
RestartSec=3
```

Depois salve e execute:

```bash
sudo systemctl daemon-reload
sudo systemctl start getty@tty1
systemctl status getty@tty1   # confirma que está ativo
```

#### TUI não aparece no monitor

Se a TUI não renderiza após reboot:

**Se você está usando Opção A (getty + .bash_profile):**

```bash
systemctl is-active getty@tty1   # confirma que getty está ativo
systemctl status getty@tty1      # mostra se há erros
journalctl -u getty@tty1 -n 30 --no-pager   # logs do getty
cat ~/.bash_profile | grep -A 3 'HERMES TUI LAUNCHER'   # verifica o bloco TTY1
python ~/matrixui/tui_display.py   # testa a TUI manualmente
```

**Se você está usando Opção B (hermes-tui.service):**

```bash
systemctl status hermes-tui.service   # status do serviço
journalctl -u hermes-tui.service -n 50 --no-pager   # últimos 50 logs
```

Causas comuns em ambos os casos:
- Virtualenv não criada ou dependências não instaladas → `pip install -r requirements.txt`.
- Python ou path incorreto no `.bash_profile` ou `.service` → edite e verifique os caminhos.
- Permissões de TTY → confirme que o usuário tem acesso a `/dev/tty1`.

#### Porta 9999 já em uso

Se receber erro `Address already in use` ao iniciar a TUI:

```bash
ss -tlnp | grep 9999   # identifica qual processo ocupa a porta
sudo lsof -i :9999     # alternativa (se lsof estiver instalado)
```

Para usar uma porta diferente, ajuste as variáveis de ambiente no
`/etc/systemd/system/hermes-tui.service` (campo `Environment`) e no `config.json` do Hermes:

```bash
sudo systemctl edit hermes-tui.service
# [Service]
# Environment=HERMES_TUI_PORT=9998
sudo systemctl daemon-reload && sudo systemctl restart hermes-tui.service
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
- `mcp_server.py` — an MCP server (official `mcp` SDK, stdio transport) exposing
  `atualizar_monitor`/`limpar_monitor` plus specialized **skills**: `exibir_previsao_tempo`
  (weather cards), `exibir_tabela` (rich table), `exibir_grafico` (bar chart),
  `exibir_metricas` (gauges), `exibir_alerta` (big-text banner), `exibir_qrcode`, and
  `exibir_tarefas` (checklist). It sends a newline-delimited JSON payload to the TUI.
- `renderers.py` — registry mapping each skill `tipo` to a Rich renderable (ncurses-style).

**Install**

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

**Run the TUI on TTY1** — recommended: use the `install.sh` script to set up getty@tty1
autologin + .bash_profile launcher (tested in production). Alternative: use the bundled
`hermes-tui.service` if you prefer systemd to claim `/dev/tty1` directly. Other options:
`openvt` or `tmux`.

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

**Troubleshooting**

- *getty@tty1 won't start on boot* — Create an override: `sudo systemctl edit getty@tty1`, add
  `[Service]`, `ExecStart=` (clear line), then `ExecStart=-/sbin/agetty --autologin <YOUR_USER> --noclear %I $TERM`,
  `Restart=always`, `RestartSec=3`. Reload: `sudo systemctl daemon-reload && systemctl is-active getty@tty1`.

- *TUI not appearing* — For option A (getty + .bash_profile): check `systemctl status getty@tty1` and
  `journalctl -u getty@tty1 -n 30 --no-pager`. Verify `.bash_profile` contains the launcher block. For option B
  (hermes-tui.service): check `systemctl status hermes-tui.service`. In both cases, verify venv and Python path.

- *Port 9999 in use* — Find owner: `ss -tlnp | grep 9999`. Change port via `HERMES_TUI_PORT=9998` env var in
  service file (option B) or `.service` override and agent config.
