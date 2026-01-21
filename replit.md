# Discord Bot - Sistema Completo

## Visao Geral
Bot de Discord completo em Python com multiplos sistemas integrados:
- Sistema de Perfil com XP e Nivel
- Economia com trabalho, daily e banco
- Sistema de Pets com Blind Box (3 tipos de caixas, 6 raridades)
- Sistema de Casamento
- 5 Profissoes com comandos especificos
- Sistema de Missoes com !atualizar e !coletar
- Mini-Games (Forca multiplayer, Quiz, Duelos)
- Sistema Social
- Mercado P2P
- Administracao

## Estrutura do Projeto
```
├── main.py              # Arquivo principal do bot
├── database/
│   └── db_manager.py    # Gerenciador de banco de dados SQLite
├── cogs/
│   ├── perfil.py        # Comandos de perfil, nivel, bio, cor
│   ├── economia.py      # Saldo, trabalhar, daily, depositar, etc
│   ├── pets.py          # Sistema de blind box e pets
│   ├── casamento.py     # Sistema de casamento
│   ├── profissoes.py    # 5 profissoes com comandos
│   ├── missoes.py       # Missoes, atualizar, coletar
│   ├── conquistas.py    # Sistema de conquistas
│   ├── ranking.py       # Rankings diversos
│   ├── minigames.py     # Forca, quiz, duelos, dados
│   ├── social.py        # Interacoes sociais e reputacao
│   ├── mercado.py       # Mercado P2P
│   ├── inventario.py    # Gerenciamento de inventario
│   ├── entretenimento.py# 8ball, piadas, sorteios
│   ├── utilidade.py     # Help paginado, ping, serverinfo
│   └── administracao.py # Comandos de moderacao
└── bot_database.db      # Banco de dados SQLite (gerado)
```

## Configuracao
1. Adicione o token do Discord como secret: `DISCORD_TOKEN`
2. Execute `python main.py`

## Funcionalidades Principais

### Sistema de Blind Box
- Caixa Comum (500 moedas): Todas as raridades
- Caixa Rara (2000 moedas): Sem comum, chances maiores
- Caixa Mistica (10000 moedas): Sem comum/incomum, melhor chances

### Raridades de Pets
1. Comum (branco)
2. Incomum (verde)
3. Raro (azul)
4. Epico (roxo)
5. Lendario (dourado)
6. Mistico (vermelho)

### Profissoes
- Cacador: cacar, rastrear, armar
- Engenheiro: construir, reparar, projetar
- Alquimista: sintetizar, transmutar, destilar
- Chef: cozinhar, preparar, assar
- Comerciante: negociar, investir, especular

### Jogo da Forca
- Multiplayer com escolha de palavra via DM
- Letras escondidas: x (minusculo)
- Letras reveladas: MAIUSCULA

## Preferencias do Usuario
- Comandos sem hifen
- Aliases com e sem acento
- Case-insensitive
- Cooldown so aplica em uso correto
- Sem frases motivacionais

## Alteracoes Recentes
- Nov 2025: Criacao inicial do bot completo
