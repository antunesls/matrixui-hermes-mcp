#!/bin/bash
#
# Hermes Terminal Dashboard — Script de instalação automatizada
#
# Uso:
#   sudo bash install.sh                    # detecta usuário via $SUDO_USER
#   sudo bash install.sh orangepi           # especifica usuário explicitamente
#   HERMES_USER=root bash install.sh        # via variável de ambiente
#
# O script:
#   1. Valida que está rodando como root.
#   2. Detecta o usuário alvo (default: orangepi ou $SUDO_USER).
#   3. Cria/atualiza override do getty@tty1 com autologin + Restart.
#   4. Instala e habilita hermes-tui.service.
#   5. Configura ~/.bash_profile para iniciar a TUI no TTY1.
#   6. Imprime resumo e comandos de verificação.

set -euo pipefail

# =========================================================================
# Configuração
# =========================================================================
HERMES_USER="${1:-${HERMES_USER:-${SUDO_USER:-orangepi}}}"
HERMES_DIR="${HERMES_DIR:-/home/$HERMES_USER/matrixui}"
PYTHON_BIN="${PYTHON_BIN:-$HERMES_DIR/.venv/bin/python}"
TUI_HOST="${TUI_HOST:-127.0.0.1}"
TUI_PORT="${TUI_PORT:-9999}"

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# =========================================================================
# Funções
# =========================================================================
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[OK]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERRO]${NC} $1"
    exit 1
}

# =========================================================================
# Validações
# =========================================================================
if [[ $EUID -ne 0 ]]; then
    log_error "Este script deve ser executado como root (use 'sudo bash install.sh')"
fi

if [[ ! -d "$HERMES_DIR" ]]; then
    log_error "Diretório $HERMES_DIR não existe. Clone o repositório primeiro."
fi

if [[ ! -f "$HERMES_DIR/tui_display.py" ]]; then
    log_error "tui_display.py não encontrado em $HERMES_DIR"
fi

if [[ ! -f "$HERMES_DIR/hermes-tui.service" ]]; then
    log_error "hermes-tui.service não encontrado em $HERMES_DIR"
fi

# =========================================================================
# Verificar que o usuário alvo existe
# =========================================================================
if ! id "$HERMES_USER" &>/dev/null; then
    log_error "Usuário '$HERMES_USER' não existe no sistema"
fi

HERMES_HOME=$(eval echo "~$HERMES_USER")
log_info "Usuário alvo: $HERMES_USER (home: $HERMES_HOME)"
log_info "Diretório do projeto: $HERMES_DIR"
log_info "Python: $PYTHON_BIN"
log_info "TCP: $TUI_HOST:$TUI_PORT"
echo

# =========================================================================
# 1. Criar/atualizar override do getty@tty1
# =========================================================================
log_info "Configurando getty@tty1 com autologin e Restart..."

GETTY_OVERRIDE_DIR="/etc/systemd/system/getty@tty1.service.d"
GETTY_OVERRIDE_FILE="$GETTY_OVERRIDE_DIR/override.conf"

mkdir -p "$GETTY_OVERRIDE_DIR"

cat > "$GETTY_OVERRIDE_FILE" << EOF
[Service]
ExecStart=
ExecStart=-/sbin/agetty --autologin ${HERMES_USER} --noclear %I \$TERM
Restart=always
RestartSec=3
EOF

log_success "Override do getty@tty1 criado/atualizado"

# =========================================================================
# 2. Habilitar getty@tty1
# =========================================================================
log_info "Habilitando getty@tty1 com systemctl..."
systemctl daemon-reload
systemctl enable --now getty@tty1

log_success "getty@tty1 habilitado e iniciado"

# =========================================================================
# 3. Configurar ~/.bash_profile
# =========================================================================
log_info "Configurando ~/.bash_profile do usuário $HERMES_USER..."

BASH_PROFILE="$HERMES_HOME/.bash_profile"
GUARD_START="# === HERMES TUI LAUNCHER (installer-managed) ==="
GUARD_END="# === END HERMES TUI LAUNCHER ==="

# Se o arquivo não existe, cria
if [[ ! -f "$BASH_PROFILE" ]]; then
    touch "$BASH_PROFILE"
    chown "$HERMES_USER:$HERMES_USER" "$BASH_PROFILE"
fi

# Se o bloco já existe, remove-o (para evitar duplicatas)
if grep -q "$GUARD_START" "$BASH_PROFILE"; then
    log_warn ".bash_profile já contém bloco hermes-tui; removendo versão antiga..."
    sed -i "/$GUARD_START/,/$GUARD_END/d" "$BASH_PROFILE"
fi

# Adicionar novo bloco
cat >> "$BASH_PROFILE" << EOF

$GUARD_START
if [ "\$(tty)" = "/dev/tty1" ]; then
    exec $PYTHON_BIN $HERMES_DIR/tui_display.py
fi
$GUARD_END
EOF

chown "$HERMES_USER:$HERMES_USER" "$BASH_PROFILE"
log_success "Bloco TTY1 launcher adicionado a $BASH_PROFILE"

# =========================================================================
# 5. Resumo e próximos passos
# =========================================================================
echo
echo -e "${GREEN}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  Hermes Terminal Dashboard — Instalação concluída com sucesso!  ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════════════╝${NC}"
echo

echo "Resumo do que foi feito:"
echo "  ✓ getty@tty1 configurado com autologin (usuário: $HERMES_USER)"
echo "  ✓ getty@tty1 com Restart=always e RestartSec=3"
echo "  ✓ getty@tty1 habilitado e iniciado"
echo "  ✓ ~/.bash_profile configurado para iniciar TUI no TTY1"
echo

echo "Comandos de verificação:"
echo -e "  ${BLUE}systemctl is-active getty@tty1${NC}"
echo -e "  ${BLUE}systemctl status getty@tty1${NC}"
echo -e "  ${BLUE}cat ~/.bash_profile | grep -A 3 'HERMES TUI LAUNCHER'${NC}"
echo

echo "Próximos passos:"
echo -e "  1. ${YELLOW}Reinicie a Orange Pi${NC} para confirmar que tudo sobe sozinho:"
echo -e "     ${BLUE}sudo reboot${NC}"
echo
echo -e "  2. Após reboot, a TUI deve aparecer automaticamente no monitor TTY1."
echo
echo -e "  3. Para diagnosticar problemas:"
echo -e "     ${BLUE}journalctl -u getty@tty1 -n 30 --no-pager${NC}"
echo -e "     ${BLUE}cat ~/.bash_profile | grep -A 3 'HERMES TUI LAUNCHER'${NC}"
echo
echo -e "  4. Para parar/reiniciar o getty@tty1:"
echo -e "     ${BLUE}sudo systemctl stop getty@tty1${NC}"
echo -e "     ${BLUE}sudo systemctl restart getty@tty1${NC}"
echo

log_success "Instalação concluída!"
