# 🎮 GameLauncher

> Launcher enterprise para emuladores de jogos retro — Nintendo DS, PSP, N64, GBA

---

## 📋 Índice

- [Visão Geral](#visão-eral)
- [Arquitetura](#arquitetura)
- [Estado Atual](#estado-atual)
  - [Funcionalidades Implementadas](#funcionalidades-implementadas)
  - [Fluxo de Navegação](#fluxo-de-navegação)
- [Estrutura do Projeto](#estrutura-do-projeto)
- [Como Executar](#como-executar)
- [Roadmap de Melhorias](#roadmap-de-melhorias)
  - [🔴 Crítico — Bugs & Fixes Imediatos](#-crítico--bugs--fixes-imediatos)
  - [🟡 Arquitetura Enterprise](#-arquitetura-enterprise)
  - [🟠 Performance & Escalabilidade](#-performance--escalabilidade)
  - [🔵 UI/UX & Polimento](#-uiux--polimento)
  - [🟢 Funcionalidades Novas](#-funcionalidades-novas)
  - [🟣 Qualidade de Código](#-qualidade-de-código)
- [Sistema de Covers Template](#sistema-de-covers-template)
  - [Porquê Templates?](#porquê-templates)
  - [Implementação Proposta](#implementação-proposta)
- [Testes](#testes)
- [Tooling & Dev Environment](#tooling--dev-environment)
- [Contribuição](#contribuição)
- [Licença](#licença)

---

## Visão Geral

O **GameLauncher** é uma aplicação desktop em Python (Tkinter) para gerir e lançar jogos retro através de emuladores. Suporta Nintendo DS, PSP, Nintendo 64 e Game Boy Advance, com deteção automática de emuladores, extração de covers das ROMs, tracking de tempo de jogo e configuração de controlos.

### Características Principais

- 🎯 **Deteção automática** de emuladores instalados
- 🖼️ **Extração nativa de covers** de ROMs (NDS, PSP)
- ⏱️ **Tracking de sessões** de jogo com persistência SQLite
- 🎮 **Configuração de controlos** por emulador (mupen64plus)
- 🔍 **Scan paralelo** da biblioteca com progresso em tempo real
- 🎨 **Tema dark mode** consistente
- 🔔 **Notificações toast** não-modais

---

## Arquitetura

O projeto segue **Clean Architecture** com separação em 4 camadas:

```
┌─────────────────────────────────────────┐
│         Presentation (UI)               │
│    Pages • Widgets • ViewModels         │
├─────────────────────────────────────────┤
│         Application (Use Cases)         │
│  ScanLibrary • LaunchGame • SaveManager │
├─────────────────────────────────────────┤
│         Domain (Entidades)              │
│   Game • Emulator • Cover • Rom         │
├─────────────────────────────────────────┤
│       Infrastructure (I/O)              │
│  Filesystem • SQLite • Process • Web    │
└─────────────────────────────────────────┘
```

### Padrões Utilizados

| Padrão | Implementação |
|--------|---------------|
| **Repository** | `GameRepository` (interface) → `LocalGameRepository` (implementação) |
| **Chain of Responsibility** | `CoverService` → múltiplos `CoverExtractor`s |
| **Observer** | `Observable` para data binding MVVM |
| **Event Bus** | `EventBus` pub/sub para desacoplar UI |
| **Dependency Injection** | `Container` manual com lazy initialization |
| **Protocol** | `ProcessManager` para abstração de sistema |

---

## Estado Atual

### Funcionalidades Implementadas

| Funcionalidade | Estado | Detalhes |
|----------------|--------|----------|
| Gestão de Emuladores | ✅ Completo | Deteção automática via `emulators.json`, validação de paths |
| Biblioteca Local | ✅ Completo | Scan de ROMs, deteção de região por filename, cache |
| **Covers NDS** | ✅ **Extração nativa** | Ícone 32x32 + título do banner ROM (formato oficial Nintendo) |
| **Covers PSP** | ✅ **Extração nativa** | PIC1.PNG/ICON0.PNG + título do PARAM.SFO (formato oficial Sony) |
| **Covers N64** | ⚠️ **Parcial** | Apenas fallback — ROMs N64 não têm covers embutidas |
| **Covers GBA** | ❌ **Não possível** | ROMs GBA não contêm banners/icons — requer solução alternativa |
| Cache de Imagens | ✅ Completo | Sistema duplo: procura por nome + cache em JSON |
| Lançamento de Jogos | ✅ Completo | Minimiza app, monitoriza processo, restaura ao fechar |
| Tracking de Tempo | ✅ Completo | SQLite com estatísticas agregadas |
| Configuração Controlos | ✅ Completo | Perfis PS4/Xbox/Switch/Genérico para mupen64plus |
| Scan Paralelo | ✅ Completo | ThreadPoolExecutor com chunks de 8 jogos |
| Tema Dark | ✅ Completo | Cores centralizadas em `theme.py` |
| Toast Notifications | ✅ Completo | Não-modais, auto-close, fade-in |
| Search em Tempo Real | ✅ Completo | Filtragem instantânea no grid |
| Save Slots | ✅ Completo | Criar, listar, restaurar e eliminar slots de save |

### Como Funciona a Extração de Covers

| Plataforma | Método | Fiabilidade |
|------------|--------|-------------|
| **Nintendo DS** | Extrai ícone 32x32 e título do **banner interno** da ROM (offset 0x068) | ✅ 100% — formato oficial Nintendo |
| **PSP** | Extrai PIC1.PNG/ICON0.PNG do **sistema de ficheiros UMD** via ISO9660 | ✅ 100% — formato oficial Sony |
| **Nintendo 64** | Não há dados de cover na ROM → usa **fallback** (procura ficheiros locais) | ⚠️ Depende do user ter covers manualmente |
| **Game Boy Advance** | **ROMs GBA não contêm banners/icons embutidos** — requer solução alternativa | ❌ Impossível extrair nativamente |

> **Nota técnica:** ROMs GBA seguem um formato de cartucho simples sem região dedicada a metadados visuais. Ao contrário do NDS (que tem um banner completo no header [^2^]) e do PSP (que usa um sistema de ficheiros ISO com recursos embutidos), o GBA apenas contém código e dados de jogo. A única informação textual é o título de 12 caracteres no header do cartucho (offset 0xA0) [^8^], insuficiente para uma cover visual.

### Fluxo de Navegação

```
Home 🏠
├── 📁 Emuladores
│   └── Seleção de Plataforma (Cards NDS/PSP/N64/GBA)
│       └── Página de Jogos Instalados
│           ├── 🔄 Atualizar (force refresh)
│           ├── 🔍 Search em tempo real
│           ├── 🎮 Controlos (apenas N64)
│           └── Grid de Cards com Cover + Título + Stats
│               └── ▶️ Jogar → Minimiza → Aguarda → Restaura
└── ⚙️ Definições (placeholder)
```

---

## Estrutura do Projeto

```
GameLauncher/
├── assets/
│   ├── covers/              # Covers extraídas (melonds/, ppsspp/, mupen64plus/, mgba/)
│   └── icons/               # Ícones das plataformas (n64.png, nds.png, psp.png)
├── config/
│   ├── controller_profiles/ # Perfis de controlos JSON
│   ├── emulators.json       # Configuração dos emuladores
│   └── settings.json        # Preferências do utilizador
├── src/
│   ├── application/         # Casos de uso e serviços
│   │   ├── protocols/       # Interfaces (ProcessManager)
│   │   ├── services/        # CoverService, SaveManager, SettingsService
│   │   ├── tracking/        # SessionTracker (EventBus → SQLite)
│   │   ├── use_cases/       # LaunchGame, ScanLibrary
│   │   └── events.py        # EventBus + DomainEvents
│   ├── domain/              # Entidades e regras de negócio
│   │   ├── entities/        # Game, Emulator, Rom, Cover, PlaySession
│   │   ├── repositories/    # Interfaces (GameRepository)
│   │   ├── services/        # CoverExtractor (interface)
│   │   └── exceptions.py    # Hierarquia de exceções
│   ├── infrastructure/      # Implementações concretas
│   │   ├── cache/           # CoverCache (JSON com TTL)
│   │   ├── config/          # ConfigLoader, Mapper, Validator
│   │   ├── covers/          # Extractores NDS/PSP/GBA/Fallback
│   │   ├── input/           # ControllerDetector, ProfileManager, SDLMapper
│   │   ├── persistence/     # LocalGameRepo, SQLiteSessionRepo
│   │   ├── system/          # SubprocessProcessManager
│   │   └── container.py     # DI Container manual
│   └── presentation/        # UI Tkinter
│       ├── pages/           # Home, EmulatorSelection, InstalledGames, ControllerConfig
│       ├── widgets/         # GameCard, Toast, DropZone, LoadingSpinner, VirtualGrid
│       ├── theme.py         # Tema visual centralizado
│       └── app_navigator.py # Navegação entre páginas
├── tests/
│   ├── unit/                # Testes unitários (pytest)
│   └── integration/         # Testes de integração
├── main.py                  # Entry point
├── pyproject.toml           # Configuração de tooling
├── Makefile                 # Comandos comuns
└── requirements.txt         # Dependências
```

---

## Como Executar

### Requisitos

- Python 3.10+
- Windows (para GBA screenshot e alguns emuladores)
- Emuladores instalados nas pastas configuradas em `config/emulators.json`

### Setup

```bash
# 1. Clonar repositório
git clone https://github.com/user/gamelauncher.git
cd gamelauncher

# 2. Criar virtual environment
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/Mac

# 3. Instalar dependências
pip install -r requirements.txt

# 4. Executar
python main.py
```

### Desenvolvimento

```bash
# Instalar dependências de desenvolvimento
make install-dev

# Executar testes
make test

# Verificar código (lint + type-check + testes)
make check

# Formatar código
make format
```

---

## Roadmap de Melhorias

### 🔴 Crítico — Bugs & Fixes Imediatos

| # | Problema | Solução | Prioridade |
|---|----------|---------|------------|
| 1 | **DI Container não é usado** em `AppNavigator` | Usar `container.game_repo` e `container.cover_service` em vez de construir manualmente | P0 |
| 2 | **GBA Extractor quebrado** — `mgba_path=None` | Resolver path do mGBA via `load_emulator_from_json("mgba")` no Container | P0 |
| 3 | **Pasta `roms/GBA` não criada** em `main.py` | Adicionar `"roms/GBA"` à lista `dirs` | P0 |
| 4 | **Ficheiros vazios** que quebram imports | Preencher stubs ou remover imports | P0 |

### 🟡 Arquitetura Enterprise

| # | Melhoria | Descrição | Impacto |
|---|----------|-----------|---------|
| 5 | **Anti-Corruption Layer para Configs** | `ConfigLoader` → `ConfigMapper` → `ConfigValidator` | Isola parsing de JSON do domínio |
| 6 | **Abstração do Filesystem** | Protocol `FileSystem` com implementações `OsFileSystem` e `InMemoryFileSystem` | Testes unitários sem I/O real |
| 7 | **Cache Persistente de Covers** | `CoverCache` com TTL + invalidação por checksum | Evita re-extrair covers sempre |
| 8 | **Tratamento de Erros Estruturado** | Hierarquia `GameLauncherError` → exceções específicas | Debugging e UX melhorados |

### 🟠 Performance & Escalabilidade

| # | Melhoria | Estado Atual | Alvo |
|---|----------|--------------|------|
| 9 | **Scan Paralelo** | ✅ Implementado | ThreadPoolExecutor, chunks de 8 |
| 10 | **Lazy Loading de Covers** | ❌ Não implementado | Só carregar covers visíveis no viewport |
| 11 | **Virtualização do Grid** | ⚠️ Stub | `VirtualGrid` com viewport clipping para 500+ jogos |
| 12 | **Cache de PhotoImage** | ❌ Não implementado | LRU cache por tamanho para evitar recriar objetos tk |

### 🔵 UI/UX & Polimento

| # | Funcionalidade | Descrição |
|---|----------------|-----------|
| 13 | **Tema Consistente** | ✅ `theme.py` centralizado — usar em todo o lado |
| 14 | **Animações/Transições** | Fade in/out entre páginas, hover suave nos cards |
| 15 | **Toast Notifications** | ✅ Implementado — info/success/warning/error |
| 16 | **Drag & Drop de ROMs** | ⚠️ Stub — integrar TkDND para arrastar ficheiros |
| 17 | **Context Menu nos Cards** | Right-click: Jogar, Detalhes, Abrir pasta, Eliminar |
| 18 | **Game Detail Page** | ⚠️ Stub — mostrar cover grande, metadados, histórico |
| 19 | **Modo Big Picture** | Interface otimizada para controlo/TV |

### 🟢 Funcionalidades Novas

| # | Funcionalidade | Descrição | Prioridade |
|---|----------------|-----------|------------|
| 20 | **Download Automático** | Fila de downloads com progresso, extração ZIP | P1 |
| 21 | **Favoritos** | Star nos cards, secção "Favoritos" no Hub | P2 |
| 22 | **Recentemente Jogados** | Lista dos últimos 10 jogos lançados | P2 |
| 23 | **Estatísticas Globais** | Tempo total, jogos mais jogados, sessões | P2 |
| 24 | **Tags Personalizadas** | "Completo", "A jogar", "Zerado" | P3 |
| 25 | **Verificação de Integridade** | Checksum MD5 das ROMs | P3 |
| 26 | **Backup Cloud de Saves** | Integração Google Drive/Dropbox | P4 |
| 27 | **Plugin System** | Adicionar scrapers/emuladores via plugins | P4 |

### 🟣 Qualidade de Código

| # | Ferramenta | Estado | Configuração |
|---|------------|--------|--------------|
| 28 | **Ruff** (lint + format) | ✅ Configurado | `pyproject.toml` — regras strict |
| 29 | **Mypy** (type-check) | ✅ Configurado | `disallow_untyped_defs=true` |
| 30 | **Pytest** | ✅ Configurado | Cobertura, markers slow/integration |
| 31 | **Pre-commit Hooks** | ✅ Configurado | ruff, mypy, pytest, trailing-whitespace |
| 32 | **Docstrings** | ⚠️ Parcial | Google-style em métodos públicos |
| 33 | **CI/CD GitHub Actions** | ❌ Não configurado | Testes em Python 3.10/3.11/3.12 |

---

## Sistema de Covers Template

### Porquê Templates?

As ROMs de **algumas plataformas não contêm dados visuais embutidos** que possam ser extraídos:

| Plataforma | Extração Nativa | Situação |
|------------|-----------------|----------|
| **Nintendo DS** | ✅ **Sim** — Banner interno com ícone 32x32 e título | Não precisa de template |
| **PSP** | ✅ **Sim** — Sistema de ficheiros ISO com PIC1.PNG/ICON0.PNG | Não precisa de template |
| **Nintendo 64** | ❌ **Não** — ROMs não têm covers embutidas | **Beneficia de template** |
| **Game Boy Advance** | ❌ **Não** — ROMs GBA não têm banners/icons [^2^] [^8^] | **Beneficia de template** |

> **Nota:** A ideia de templates aplica-se **exclusivamente a plataformas onde a extração nativa é impossível**. Para NDS e PSP, a extração nativa é 100% fiável e não deve ser substituída.

### Implementação Proposta

#### 1. Assets Base

```
assets/covers/templates/
├── gba_template.png      # Fundo branco + "GAME BOY ADVANCE" + logo
├── n64_template.png      # Fundo branco + "NINTENDO 64" + logo
└── generic_template.png  # Fundo branco + "RETRO GAME" + ícone genérico
```

#### 2. Especificações do Template

| Propriedade | Valor |
|-------------|-------|
| **Resolução** | 512×512 px (master), redimensionado conforme necessário |
| **Fundo** | Branco (#FFFFFF) ou gradiente sutil da cor da plataforma |
| **Elementos** | Logo da consola (topo), ícone da plataforma (centro), área de texto (base) |
| **Fonte** | Bold sans-serif (ex: Arial Black, Impact, ou fonte do tema) |
| **Área de Texto** | 512×120 px na base, fundo semi-transparente para legibilidade |

#### 3. Geração Dinâmica

```python
# src/infrastructure/covers/template_generator.py

from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
from src.domain.entities.game import Cover

class TemplateCoverGenerator:
    """Gera covers a partir de templates quando não há cover real."""

    TEMPLATES_DIR = Path("assets/covers/templates")

    def __init__(self):
        self._fonts: dict[str, ImageFont.FreeTypeFont] = {}

    def generate(
        self,
        game_title: str,
        emulator_id: str,
        output_path: Path,
        size: tuple[int, int] = (512, 512)
    ) -> Cover:
        """Gera cover template para um jogo."""

        # 1. Carregar template base da plataforma
        template_path = self.TEMPLATES_DIR / f"{emulator_id}_template.png"
        if not template_path.exists():
            template_path = self.TEMPLATES_DIR / "generic_template.png"

        img = Image.open(template_path).convert("RGBA")
        img = img.resize(size, Image.Resampling.LANCZOS)

        # 2. Preparar camada de texto
        draw = ImageDraw.Draw(img)

        # 3. Configurar fonte (fallback para default se não encontrar)
        try:
            font = ImageFont.truetype("arialbd.ttf", 28)
        except OSError:
            font = ImageFont.load_default()

        # 4. Calcular posição do texto (centro inferior)
        bbox = draw.textbbox((0, 0), game_title, font=font)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]

        x = (size[0] - text_w) // 2
        y = size[1] - text_h - 40  # 40px do fundo

        # 5. Desenhar sombra para legibilidade
        draw.text((x+2, y+2), game_title, font=font, fill=(0, 0, 0, 128))
        # 6. Desenhar texto principal
        draw.text((x, y), game_title, font=font, fill=(33, 33, 33, 255))

        # 7. Guardar
        output_path.parent.mkdir(parents=True, exist_ok=True)
        img.save(output_path, "PNG")

        return Cover(local_path=output_path)
```

#### 4. Integração no CoverService (com lógica condicional)

```python
# src/application/services/cover_service.py

class CoverService:
    def __init__(self, extractors: list[CoverExtractor], output_dir: Path):
        self.extractors = extractors
        self.output_dir = Path(output_dir)
        self.template_generator = TemplateCoverGenerator()

    def resolve_cover(self, rom_path: Path, game_id: str, emulator_id: str):
        """
        Tenta extrair cover. Estratégia:
        1. Extratores nativos (para plataformas que suportam: NDS, PSP)
        2. Template generator (para plataformas sem extração nativa: GBA, N64)
        """
        emu_output = self.output_dir / emulator_id.lower()

        # PASSO 1: Tentar extratores nativos (chain of responsibility)
        # Estes funcionam para NDS, PSP, etc.
        for extractor in self.extractors:
            if extractor.can_extract(rom_path):
                cover, title = extractor.extract(rom_path, game_id, emu_output)
                if cover and cover.is_local:
                    return cover, title

        # PASSO 2: Fallback para template (plataformas sem extração nativa)
        # Aplica-se a: GBA, N64, e futuros emuladores sem banners embutidos
        template_path = emu_output / f"{game_id}_template.png"
        if not template_path.exists():
            cover = self.template_generator.generate(
                game_title=game_id.replace("-", " ").title(),
                emulator_id=emulator_id,
                output_path=template_path
            )
            return cover, None

        return Cover(local_path=template_path), None
```

#### 5. Configuração por Plataforma

```json
// config/emulators.json (adição)
{
  "emulators": [
    {
      "id": "mgba",
      "name": "Game Boy Advance",
      "icon": "assets/icons/gba.png",
      "template_cover": "assets/covers/templates/gba_template.png",
      "supports_native_extraction": false,
      // ... resto da config
    },
    {
      "id": "mupen64plus",
      "name": "Nintendo 64",
      "icon": "assets/icons/n64.png",
      "template_cover": "assets/covers/templates/n64_template.png",
      "supports_native_extraction": false,
      // ... resto da config
    },
    {
      "id": "melonds",
      "name": "Nintendo DS",
      "icon": "assets/icons/nds.png",
      "supports_native_extraction": true,
      // ... resto da config
    }
  ]
}
```

### Exemplo Visual

```
┌─────────────────────────────┐
│                             │
│      GAME BOY ADVANCE       │  <- Logo da plataforma (topo)
│                             │
│         [ÍCONE GBA]         │  <- Ícone/ilustração da consola
│                             │
│                             │
│    ┌─────────────────┐      │
│    │  POKÉMON EMERALD │     │  <- Nome do jogo (base, fundo semi-transparente)
│    └─────────────────┘      │
└─────────────────────────────┘
         512×512 px
```

### Vantagens

- ✅ **Consistência visual** — todos os cards têm o mesmo formato
- ✅ **Identificação rápida** — plataforma visível à primeira vista
- ✅ **Profissionalismo** — não parece "quebrado" ou incompleto
- ✅ **Extensibilidade** — adicionar novo emulador = criar 1 template PNG
- ✅ **Performance** — geração uma vez, cache permanente
- ✅ **Sem dependências externas** — não requer APIs de imagem
- ✅ **Não interfere em plataformas com extração nativa** — NDS/PSP continuam a extrair covers reais

---

## Testes

### Estrutura de Testes

```
tests/
├── unit/
│   ├── test_launch_command.py      # Comandos de lançamento por plataforma
│   ├── test_local_game_repo.py     # Scan, cache, fuzzy matching
│   ├── test_nds_extractor.py       # Paleta BGR555, índice 0 transparente
│   ├── test_psp_extractor.py       # Parsing SFO, leitura ISO
│   ├── test_scan_library.py        # Scan paralelo, chunks, progresso
│   └── test_session_tracking.py    # EventBus → SQLite, estatísticas
└── integration/
    └── test_cover_pipeline.py      # Chain of responsibility
```

### Executar Testes

```bash
# Todos os testes
pytest tests/ -v

# Com cobertura
pytest tests/ --cov=src --cov-report=html

# Apenas unitários
pytest tests/unit -v

# Apenas integração
pytest tests/integration -v

# Excluir testes lentos
pytest tests/ -m "not slow"
```

### Prioridade de Testes

| Prioridade | Teste | O que valida |
|------------|-------|--------------|
| P0 | `test_nds_extractor.py` | Paleta BGR555, índice 0 transparente |
| P0 | `test_psp_extractor.py` | Parsing SFO, leitura ISO |
| P0 | `test_gba_extractor.py` | Captura de janela, fallback |
| P1 | `test_local_game_repo.py` | Scan, cache, fuzzy matching |
| P1 | `test_cover_pipeline.py` | Chain of responsibility |
| P2 | `test_launch_command.py` | build_launch_command por plataforma |
| P2 | `test_settings_service.py` | Save/load JSON |

---

## Tooling & Dev Environment

### Makefile

| Comando | Descrição |
|---------|-----------|
| `make install` | Instala dependências de produção |
| `make install-dev` | Instala dev deps + pre-commit hooks |
| `make test` | Testes unitários |
| `make test-cov` | Testes com cobertura |
| `make lint` | Verifica código com ruff |
| `make lint-fix` | Auto-corrige problemas do ruff |
| `make format` | Formata código com ruff |
| `make type-check` | Verifica tipos com mypy |
| `make check` | Lint + type-check + testes |
| `make ci` | Comando completo para CI/CD |
| `make clean` | Limpa caches e ficheiros temporários |
| `make run` | Corre a aplicação |

### Ruff (Linter & Formatter)

- Substitui black, flake8, isort, pydocstyle
- 10-100x mais rápido (Rust)
- Regras: Pyflakes, pycodestyle, bugbear, simplify, isort, naming, annotations, security, docstrings, comprehensions, return, unused-args, eradicate, pylint

### Mypy (Type Checking)

- `disallow_untyped_defs=true`
- `strict_equality=true`
- Stubs para pycdlib e pygame ignorados

### Pre-commit Hooks

- ruff (lint + auto-fix)
- ruff-format
- mypy
- trailing-whitespace
- end-of-file-fixer
- check-yaml/json/toml
- check-added-large-files (>1MB)

---

## Contribuição

1. Fork do repositório
2. Criar branch (`git checkout -b feature/nova-funcionalidade`)
3. Commit com mensagens claras (`git commit -m "feat: adicionar scan paralelo"`)
4. Push para a branch (`git push origin feature/nova-funcionalidade`)
5. Abrir Pull Request

### Convenções de Código

- **Estilo**: Ruff format (compatível Black)
- **Docstrings**: Google-style
- **Tipos**: mypy strict
- **Testes**: pytest com cobertura mínima 80%

---

## Licença

MIT License — ver [LICENSE](LICENSE) para detalhes.

---

> **Nota:** Este projeto está em desenvolvimento ativo. A arquitetura está estabilizada mas funcionalidades UI/UX estão em constante evolução. Contribuições são bem-vindas! 🎮
