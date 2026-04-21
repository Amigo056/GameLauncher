# GameLauncher

## Estado Atual

### Arquitetura
Projeto segue **Clean Architecture** com separação clara:

- **Domain**: Entidades (`Game`, `Emulator`), Repositórios (interfaces), Serviços
- **Application**: Casos de uso (Download, Launch, Scrape), Eventos
- **Infrastructure**: Implementações concretas (JSON, Filesystem, Web Scraping, Process Manager)
- **Presentation**: Pages (Tkinter), ViewModels (MVVM com Observable)

### Fluxo de Navegação Implementado

```bash
Home 🏠
├── Emuladores 📁
│   └── Seleção (NDS/PSP)
│       └── Hub do Emulador (2 botões)
│           ├── 🎮 Meus Jogos (Grid local)
│           │   └── Launch → Minimiza → Aguarda → Restaura
│           └── 🌐 Procurar Online (Scraper)
│               └── Abre browser para download
└── ⚙️ Definições (placeholder)
```


### Funcionalidades Concluídas
1. **Gestão de Emuladores**: Deteção automática de executáveis, validação de paths
2. **Biblioteca Local**: Scan de ROMs, deteção de região por filename, grid com covers
3. **Cache de Imagens**: Sistema duplo - procura por nome (`melonds_*.jpg` ou `*.png`) + guarda path no JSON
4. **Lançamento**: Integração com `LaunchEmulatorUseCase`, minimização da app, monitorização de processo
5. **Scraping**: Integração com romsgames.net, paginação, badge "INSTALADO" para jogos existentes
6. **Persistência**: Catálogo JSON com cache de covers, evita re-download de imagens

---

## 🚀 Próximas Implementações (Roadmap)

### Fase 1 - Core Experience (Prioridade Alta)

#### Sistema de Download Automático ⬇️
- Download direto de ROMs (não só abrir browser)
- Fila de downloads com progresso visual
- Extração automática de ZIPs
- Pause/Resume downloads

#### Página de Definições ⚙️
- Configurar paths dos emuladores via UI
- Seleção de pasta de ROMs personalizada
- Tema (Dark/Light) - já tens dark por default
- Configurações de scraping (delay, páginas máximas)

#### Melhorias na Biblioteca
- **Filtros avançados**: Por região, por letra (A-Z), apenas favoritos
- **Ordenação**: Alfabética, data adicionado, mais jogados
- **Search em tempo real** (atualmente é preciso Enter)
- **Grid responsivo** (ajustar número de colunas ao tamanho da janela)

### Fase 2 - User Experience (Prioridade Média)

#### Sistema de Favoritos ⭐
- Star nos jogos
- Secção "Favoritos" no Hub

#### Histórico e Estatísticas 📊
- "Recentemente Jogados" (últimos 10)
- Tempo total jogado por jogo
- Estatísticas globais (total de horas, jogos completados)

#### Metadados e Personalização
- Editar título/capa de jogos manualmente
- Adicionar notas/descrições
- Tags personalizadas (ex: "Completo", "A jogar", "Zerado")

### Fase 3 - Polish & Advanced Features (Prioridade Baixa)

#### Performance
- Thumbnails em baixa resolução (loading lazy)
- Cache de imagens em memória (LRU cache)
- Background loading das próximas páginas

#### Integrações
- Suporte a mais plataformas (GBA, SNES, PS1, etc)
- Integração com RetroAchievements
- Scraper múltiplo (fallback se um site falhar)

#### Quality of Life
- **Modo Big Picture** (interface para controlo/TV)
- **Arrastar e largar** ROMs para adicionar
- **Verificação de integridade** (checksum MD5)
- **Backup de saves** automático

#### Cloud & Sync ☁️ (Futuro distante)
- Sincronização de saves na cloud
- Sync de biblioteca entre dispositivos

---

## 🛠️ Bugs Conhecidos / TODO Imediato

1. **Navegação**: Voltar do Hub às vezes mostra ecrã preto (já corrigido com `lift()`)
2. **Covers**: Alguns jogos não detetam capa se o nome tiver caracteres especiais (usar `safe_id`)
3. **Scraper**: Tratamento de erros quando site está offline
4. **Process Manager**: Verificar se emulador crashou (não só se fechou normalmente)

---

## 💡 Sugestões de Arquitetura Futura

**Migração para SQLite**: Quando o catálogo crescer (>1000 jogos), o JSON vai ficar lento. Preparar migração para SQLite mantendo a mesma interface `CatalogRepository`.

**Plugin System**: Permitir adicionar novos scrapers/emuladores via plugins sem modificar código core.

**Themes**: Sistema de temas definido por JSON/CSS-like para Tkinter.