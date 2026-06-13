#!/usr/bin/env python3
"""Exemplos de uso das skills do Hermes Terminal Dashboard.

Cada exemplo mostra o payload NDJSON que seria enviado ao servidor TCP da TUI.
Para testar: salve o payload em um arquivo ou use printf/echo com `nc`.

Exemplo:
    printf '<payload>\n' | nc 127.0.0.1 9999
"""

import json

# =========================================================================
# 1. PREVISÃO DO TEMPO
# =========================================================================
PREVISAO_TEMPO = {
    "tipo": "previsao_tempo",
    "dados": {
        "local": "São Paulo, SP",
        "dias": [
            {
                "dia": "Hoje",
                "condicao": "chuva",
                "temp_max": 24,
                "temp_min": 17,
                "descricao": "Pancadas de chuva",
                "umidade": 80,
                "vento": "15 km/h",
            },
            {
                "dia": "Amanhã",
                "condicao": "nublado",
                "temp_max": 26,
                "temp_min": 18,
                "descricao": "Nublado",
                "umidade": 70,
            },
            {
                "dia": "Quinta",
                "condicao": "sol",
                "temp_max": 28,
                "temp_min": 20,
                "descricao": "Ensolarado",
                "umidade": 60,
            },
        ],
    },
    "log": "Previsão atualizada para os próximos 3 dias",
}

# =========================================================================
# 2. TABELA (dados estruturados)
# =========================================================================
TABELA_VENDAS = {
    "tipo": "tabela",
    "dados": {
        "titulo": "Vendas do mês (Jun)",
        "colunas": ["Produto", "Quantidade", "Preço Unit.", "Total"],
        "linhas": [
            ["Café Premium", "120", "R$ 15,00", "R$ 1.800,00"],
            ["Pão Francês", "450", "R$ 0,75", "R$ 337,50"],
            ["Bolo Chocolate", "35", "R$ 25,00", "R$ 875,00"],
            ["Suco Natural", "200", "R$ 8,50", "R$ 1.700,00"],
        ],
    },
    "log": "Vendas do período resumidas",
}

# =========================================================================
# 3. GRÁFICO (série temporal)
# =========================================================================
GRAFICO_TEMPERATURA_SEMANA = {
    "tipo": "grafico",
    "dados": {
        "titulo": "Temperatura por dia",
        "unidade": "°C",
        "series": [
            {"label": "Seg", "valor": 23},
            {"label": "Ter", "valor": 27},
            {"label": "Qua", "valor": 25},
            {"label": "Qui", "valor": 24},
            {"label": "Sex", "valor": 28},
            {"label": "Sab", "valor": 29},
            {"label": "Dom", "valor": 26},
        ],
    },
    "log": "Gráfico de temperatura da semana",
}

GRAFICO_INVESTIMENTO = {
    "tipo": "grafico",
    "dados": {
        "titulo": "Retorno por mês (6 meses)",
        "unidade": "%",
        "series": [
            {"label": "Jan", "valor": 2.5},
            {"label": "Fev", "valor": 1.8},
            {"label": "Mar", "valor": 3.2},
            {"label": "Abr", "valor": 2.1},
            {"label": "Mai", "valor": 4.5},
            {"label": "Jun", "valor": 3.8},
        ],
    },
}

# =========================================================================
# 4. MÉTRICAS / GAUGES (monitores em tempo real)
# =========================================================================
METRICAS_SERVIDOR = {
    "tipo": "metricas",
    "dados": {
        "titulo": "Status do Servidor",
        "metricas": [
            {"label": "CPU", "valor": 42, "unidade": "%"},
            {"label": "Memória RAM", "valor": 6.8, "max": 8, "unidade": "GB"},
            {"label": "Disco /", "valor": 540, "max": 600, "unidade": "GB"},
            {"label": "Uptime", "valor": 99.8, "unidade": "%"},
            {"label": "Conexões", "valor": 145, "max": 500},
        ],
    },
    "log": "Métricas de saúde do servidor atualizadas",
}

METRICAS_BACKUP = {
    "tipo": "metricas",
    "dados": {
        "titulo": "Progresso do Backup",
        "metricas": [
            {"label": "Arquivos processados", "valor": 8500, "max": 10000},
            {"label": "Dados transferidos", "valor": 450, "max": 500, "unidade": "GB"},
            {"label": "Taxa de sucesso", "valor": 99.5, "unidade": "%"},
        ],
    },
}

# =========================================================================
# 5. ALERTA (banner de destaque)
# =========================================================================
ALERTA_SUCESSO = {
    "tipo": "alerta",
    "dados": {
        "texto": "BACKUP OK",
        "nivel": "info",
        "subtitulo": "Backup noturno completado com sucesso",
    },
    "log": "Alerta de sucesso exibido",
}

ALERTA_AVISO = {
    "tipo": "alerta",
    "dados": {
        "texto": "ATENÇÃO",
        "nivel": "aviso",
        "subtitulo": "Espaço em disco está acabando (85% uso)",
    },
    "log": "Alerta de espaço em disco",
}

ALERTA_CRITICO = {
    "tipo": "alerta",
    "dados": {
        "texto": "ERRO CRÍTICO",
        "nivel": "critico",
        "subtitulo": "Falha na conexão com banco de dados",
    },
    "log": "Alerta crítico enviado",
}

# =========================================================================
# 6. QR CODE (compartilhamento)
# =========================================================================
QRCODE_LINK = {
    "tipo": "qrcode",
    "dados": {
        "conteudo": "https://exemplo.com/dashboard",
        "legenda": "Aponte a câmera para acessar o painel",
    },
    "log": "QR Code gerado",
}

QRCODE_WIFI = {
    "tipo": "qrcode",
    "dados": {
        "conteudo": "WIFI:S:MinhaRede;T:WPA;P:senha123;;",
        "legenda": "Conecte-se ao Wi-Fi da rede",
    },
}

# =========================================================================
# 7. TAREFAS / CHECKLIST
# =========================================================================
TAREFAS_DIARIAS = {
    "tipo": "tarefas",
    "dados": {
        "titulo": "Tarefas de hoje",
        "itens": [
            {
                "texto": "Conferir e-mails importantes",
                "feito": True,
                "prioridade": "alta",
            },
            {
                "texto": "Atualizar documentação do projeto",
                "feito": False,
                "prioridade": "alta",
            },
            {
                "texto": "Revisar PR do código novo",
                "feito": False,
                "prioridade": "media",
            },
            {
                "texto": "Organizar próxima reunião de sprint",
                "feito": False,
                "prioridade": "media",
            },
            {
                "texto": "Limpar pasta de downloads",
                "feito": False,
                "prioridade": "baixa",
            },
        ],
    },
    "log": "Lista de tarefas exibida",
}

TAREFAS_DEPLOY = {
    "tipo": "tarefas",
    "dados": {
        "titulo": "Checklist de Deploy",
        "itens": [
            {"texto": "Testes unitários passando", "feito": True},
            {"texto": "Testes integração OK", "feito": True},
            {"texto": "Revisão de código aprovada", "feito": True},
            {"texto": "Database migration executada", "feito": True},
            {"texto": "Cache invalidado", "feito": False, "prioridade": "alta"},
            {"texto": "Notificar stakeholders", "feito": False},
        ],
    },
}

# =========================================================================
# 8. MARKDOWN (uso genérico - compatível com protocolo antigo)
# =========================================================================
MARKDOWN_GENERICO = {
    "tipo": "markdown",  # ou omitir tipo, pois é o default
    "conteudo": """\
# Bem-vindo ao Hermes Dashboard

## Status Geral do Sistema

O sistema está operacional desde as **03:00** desta madrugada.

- ✅ API: `online`
- ✅ Banco de dados: `conectado`
- ⚠️ Cache Redis: `aguardando reconexão` (esperado em 2 min)

## Últimos Eventos

```
2026-06-13T08:45:23Z - Backup noturno concluído
2026-06-13T08:30:12Z - Atualização de dependências aplicada
2026-06-13T08:15:00Z - Teste de failover executado com sucesso
```

Para mais detalhes, acesse o [painel administrativo](https://admin.exemplo.com).
""",
    "log": "Informações gerais do sistema",
}

# =========================================================================
# 9. NOTÍCIAS
# =========================================================================
NOTICIAS_BRASIL = {
    "tipo": "noticias",
    "dados": {
        "titulo": "Últimas Notícias",
        "fonte": "G1",
        "itens": [
            {
                "titulo": "Selic mantida em 13,75% pelo Copom",
                "resumo": "O Comitê de Política Monetária decidiu manter a taxa básica de juros, sinalizando cautela diante da inflação persistente.",
                "categoria": "Economia",
                "tempo": "há 30 min",
            },
            {
                "titulo": "Seleção brasileira convoca 26 jogadores para Copa",
                "resumo": "O técnico anunciou a lista definitiva com surpresas no ataque e a ausência de jogadores lesionados.",
                "categoria": "Esportes",
                "tempo": "há 2 horas",
            },
            {
                "titulo": "Tempestade causa apagão em três estados do Nordeste",
                "resumo": "Ventos de até 90 km/h derrubaram torres de transmissão. Equipes de emergência trabalham para restabelecer energia.",
                "categoria": "Brasil",
                "tempo": "há 4 horas",
            },
            {
                "titulo": "Nova IA da TOTVS automatiza rotinas fiscais no Protheus",
                "resumo": "A solução integra machine learning para classificação de documentos e reduz tempo de fechamento fiscal em 40%.",
                "categoria": "Tecnologia",
                "tempo": "13/06 09:00",
            },
        ],
    },
    "log": "Feed de notícias atualizado",
}

# =========================================================================
# 10. JOGOS DE FUTEBOL
# =========================================================================
JOGOS_BRASILEIRAO = {
    "tipo": "jogos_futebol",
    "dados": {
        "titulo": "Rodada 15 — Brasileirão Série A",
        "data": "13/06/2026",
        "jogos": [
            {
                "time_casa": "Flamengo",
                "time_fora": "Palmeiras",
                "placar_casa": 2,
                "placar_fora": 1,
                "status": "encerrado",
                "estadio": "Maracanã",
                "destaque": "Gol de Gabriel Barbosa aos 78'",
            },
            {
                "time_casa": "Corinthians",
                "time_fora": "São Paulo",
                "placar_casa": 0,
                "placar_fora": 0,
                "status": "ao_vivo",
                "estadio": "Neo Química Arena",
                "destaque": "45+2' — 2º Tempo",
            },
            {
                "time_casa": "Atlético-MG",
                "time_fora": "Cruzeiro",
                "status": "agendado",
                "horario": "16:00",
                "estadio": "Arena MRV",
            },
            {
                "time_casa": "Botafogo",
                "time_fora": "Vasco",
                "status": "agendado",
                "horario": "18:30",
            },
        ],
    },
    "log": "Jogos do Brasileirão — 13/06/2026",
}

# =========================================================================
# Utilitário: exibir todos como NDJSON
# =========================================================================
if __name__ == "__main__":
    exemplos = {
        "previsao_tempo": PREVISAO_TEMPO,
        "tabela_vendas": TABELA_VENDAS,
        "grafico_temperatura": GRAFICO_TEMPERATURA_SEMANA,
        "grafico_investimento": GRAFICO_INVESTIMENTO,
        "metricas_servidor": METRICAS_SERVIDOR,
        "metricas_backup": METRICAS_BACKUP,
        "alerta_sucesso": ALERTA_SUCESSO,
        "alerta_aviso": ALERTA_AVISO,
        "alerta_critico": ALERTA_CRITICO,
        "qrcode_link": QRCODE_LINK,
        "qrcode_wifi": QRCODE_WIFI,
        "tarefas_diarias": TAREFAS_DIARIAS,
        "tarefas_deploy": TAREFAS_DEPLOY,
        "markdown_generico": MARKDOWN_GENERICO,
        "noticias_brasil": NOTICIAS_BRASIL,
        "jogos_brasileirao": JOGOS_BRASILEIRAO,
    }

    print("# Exemplos de payloads NDJSON para testar com `nc`\n")
    for nome, payload in exemplos.items():
        print(f"## {nome}")
        print(f"printf '{json.dumps(payload, ensure_ascii=False)}\\n' | nc 127.0.0.1 9999")
        print()
