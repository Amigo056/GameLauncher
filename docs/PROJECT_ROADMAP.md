# GameLauncher - Plano de Evolucao e Arquitetura Alvo

Este documento e o mapa vivo do projeto. A ideia e simples: transformar o
GameLauncher numa app pessoal, robusta e extensivel, para gerir emuladores,
ROMs, controlos, perfis graficos, saves e multiplayer local/remoto sem a app
ficar presa a hacks especificos de um emulador.

## Visao Do Produto

O GameLauncher deve ser uma app desktop para:

- Ter todos os emuladores relevantes organizados num unico sitio.
- Listar as ROMs que o utilizador quer jogar, com capas, favoritos, recentes e estatisticas.
- Lançar jogos com configuracoes corretas por emulador.
- Facilitar controlos, incluindo varios jogadores no mesmo PC.
- Ter perfis graficos por emulador: `Performance`, `Equilibrado` e `Qualidade`.
- Analisar o PC e recomendar emuladores por peso: `Muito leve`, `Leve`, `Medio`, `Pesado`, `Muito pesado`.
- No futuro, facilitar multiplayer remoto com amigos atraves de integracoes externas ou netplay nativo.

## Principios

- Primeiro estabilidade, depois expansao.
- NDS e GBA devem ficar impecaveis antes de adicionar muitas plataformas.
- Cada emulador deve ser um adaptador isolado, nao regras espalhadas pela UI.
- A UI nunca deve construir comandos, mexer em ficheiros de config nem conhecer detalhes internos de emuladores.
- Configuracoes devem ser validadas antes de serem usadas.
- Features grandes devem entrar por fases pequenas, testaveis e reversiveis.
- O projeto deve continuar pessoal e pratico, mesmo com arquitetura mais madura.

## Arquitetura Alvo

Arquitetura em camadas, estilo Clean Architecture, mas aplicada de forma pragmatica.

```text
src/
  domain/
    entities/
    value_objects/
    exceptions.py

  application/
    ports/
    use_cases/
    services/
    events.py

  infrastructure/
    adapters/
      emulators/
      controllers/
      graphics/
      hardware/
      covers/
    persistence/
    config/
    system/
    cache/
    container.py

  presentation/
    pages/
    widgets/
    viewmodels/
    theme.py
```

### Domain

Contem o modelo puro do projeto, sem Tkinter, subprocess, SQLite ou ficheiros JSON.

Entidades e value objects principais:

- `Game`
- `Rom`
- `Cover`
- `Emulator`
- `Platform`
- `PlaySession`
- `SaveSlot`
- `Controller`
- `ControllerProfile`
- `PlayerProfile`
- `GraphicsProfile`
- `HardwareProfile`
- `EmulatorRecommendation`
- `MultiplayerSession`

### Application

Contem os casos de uso. Orquestra o dominio atraves de portas/interfaces.

Use cases alvo:

- `ScanLibraryUseCase`
- `LaunchGameUseCase`
- `TrackPlaySessionUseCase`
- `ManageSaveSlotsUseCase`
- `ConfigureControllerUseCase`
- `ApplyGraphicsProfileUseCase`
- `AnalyzeHardwareUseCase`
- `RecommendEmulatorsUseCase`
- `StartLocalMultiplayerUseCase`
- `StartRemoteSessionUseCase`

Portas importantes:

- `GameRepository`
- `SessionRepository`
- `EmulatorRepository`
- `ProcessManager`
- `FileSystem`
- `ControllerBackend`
- `HardwareProbe`
- `CoverProvider`
- `GraphicsConfigWriter`
- `EmulatorAdapter`

### Infrastructure

Implementa detalhes concretos:

- SQLite para sessoes e historico.
- JSON para configuracoes e catalogo de emuladores.
- Filesystem para ROMs, saves, capas e perfis.
- `subprocess`/`psutil` para lancamento e monitorizacao.
- Backends de comandos via pygame/SDL.
- Adaptadores por emulador.
- Probes de hardware para CPU, GPU, RAM e sistema operativo.

Adaptadores de emulador devem encapsular:

- Deteccao do executavel.
- Extensoes suportadas.
- Construção do comando.
- Configuracoes graficas.
- Configuracoes de controlos.
- Regras de saves.
- Suporte local multiplayer.
- Suporte remoto/netplay, se existir.

### Presentation

Tkinter deve ficar so com apresentacao e interacao:

- Paginas.
- Widgets.
- ViewModels.
- Toasts.
- Estado visual.

A UI chama use cases. Nao deve abrir subprocessos diretamente nem alterar configs de emuladores.

## Modelo De Emulador Alvo

Cada emulador deve ser descrito por configuracao mais um adaptador.

Exemplo conceitual:

```json
{
  "id": "mgba",
  "name": "mGBA",
  "platform": "game-boy-advance",
  "performance_tier": "muito_leve",
  "rom_extensions": [".gba", ".gbc", ".gb"],
  "supports_local_multiplayer": true,
  "supports_remote_multiplayer": false,
  "supports_controller_profiles": true,
  "supports_graphics_profiles": true,
  "graphics_profiles": {
    "performance": "mgba.performance.json",
    "balanced": "mgba.balanced.json",
    "quality": "mgba.quality.json"
  }
}
```

## Perfis Graficos

Cada emulador deve ter tres perfis:

- `Performance`: maximiza FPS e estabilidade.
- `Equilibrado`: boa imagem sem sacrificar demasiado desempenho.
- `Qualidade`: maximiza resolucao, filtros e qualidade visual.

Campos possiveis por perfil:

- Resolucao interna.
- Fullscreen/windowed.
- Backend grafico.
- VSync.
- Frameskip.
- Shaders/filtros.
- Escala.
- Audio latency.
- Threading.
- Limite de FPS.
- Presets especificos por emulador.

Exemplo conceitual:

```json
{
  "emulator_id": "ppsspp",
  "profile": "performance",
  "settings": {
    "backend": "vulkan",
    "internal_resolution": "1x",
    "frameskip": "auto",
    "texture_scaling": false,
    "vsync": false,
    "fullscreen": true
  }
}
```

Regras:

- Os perfis graficos sao dados de aplicacao, nao logica dentro da UI.
- Aplicar um perfil deve passar por `ApplyGraphicsProfileUseCase`.
- Cada emulador pode ter um `GraphicsConfigWriter` proprio.
- A app deve guardar o perfil escolhido por emulador e, no futuro, por jogo.

## Fases Do Projeto

### Fase 0 - Estabilizacao Do Nucleo

Objetivo: fazer a base deixar de mentir.

Tarefas:

- Corrigir `EventBus`, `SessionTracker`, `PlaySession` e `SQLiteSessionRepository`.
- Garantir que o tracking inicia no startup.
- Remover restos de codigo gerado e strings perdidas dentro de modulos reais.
- Trocar prints de debug por logging.
- Corrigir testes quebrados ou alinhar expectativas antigas.
- Confirmar que NDS e GBA abrem sem regressao.

Definition of done:

- Testes unitarios principais verdes.
- App abre e fecha sem erros.
- Sessao de jogo e guardada no SQLite.
- UI mostra estatisticas reais depois de jogar.

### Fase 1 - NDS E GBA Como Plataformas Base

Objetivo: tornar as plataformas atuais confortaveis e estaveis.

Tarefas:

- Melhorar scan de ROMs.
- Melhorar capas NDS.
- Criar estrategia leve para capas GBA: templates ou capas locais.
- Criar pagina de detalhe real do jogo.
- Criar favoritos e recentes.
- Melhorar saves e backups automaticos.

Definition of done:

- NDS e GBA estao bons para uso diario.
- Cada jogo tem detalhe, playtime, saves e estado visual aceitavel.
- Capas ausentes nao deixam a UI parecer partida.

Estado atual:

- Em progresso.
- Scan local ja ordena resultados e mostra titulos mais limpos na UI.
- Favoritos ja ficam guardados em `config/settings.json`.
- Biblioteca ja tem filtros `Todos`, `Favoritos` e `Recentes`.
- Pagina de detalhe ja mostra capa, informacao da ROM, estatisticas e saves.
- Backups manuais de saves ja podem ser criados pela pagina de detalhe.

Proximos passos desta fase:

- Melhorar estrategia de capas GBA sem depender apenas de screenshot via emulador.
- Melhorar capas NDS quando a ROM nao tem icon/banner utilizavel.
- Mostrar historico de sessoes por jogo na pagina de detalhe.
- Evoluir saves para restaurar/eliminar backups pela UI.

### Fase 2 - Controlos E Perfis Por Jogador

Objetivo: ligar comandos e mapear botoes sem editar ficheiros manualmente.

Tarefas:

- Normalizar modelo `ControllerProfile`.
- Criar wizard de mapeamento: A, B, Start, Select, direcional, analogicos.
- Guardar perfis por comando.
- Suportar Player 1, Player 2, Player 3 e Player 4.
- Criar adaptadores de configuracao por emulador.

Definition of done:

- O utilizador consegue configurar um comando pela UI.
- Perfil fica guardado e reaplicavel.
- N64 deixa de ser caso especial espalhado pela UI.

### Fase 3 - Perfis Graficos Por Emulador

Objetivo: controlar qualidade/performance por emulador de forma simples.

Tarefas:

- Criar entidade `GraphicsProfile`.
- Criar use case `ApplyGraphicsProfileUseCase`.
- Criar config writers para mGBA e melonDS primeiro.
- Depois adicionar PPSSPP e Mupen64Plus.
- Guardar perfil escolhido nas settings.
- Criar UI simples com tres opcoes: Performance, Equilibrado, Qualidade.

Definition of done:

- Cada emulador suportado tem tres perfis.
- A app aplica o perfil antes de abrir o jogo.
- O perfil escolhido persiste entre sessoes.

### Fase 4 - Catalogo De Emuladores Extensivel

Objetivo: adicionar emuladores sem reescrever a app.

Tarefas:

- Criar schema versionado para `emulators.json`.
- Separar catalogo de emuladores da configuracao local do utilizador.
- Criar `EmulatorAdapter` por familia/emulador.
- Adicionar tiers de desempenho.
- Adicionar capacidades: controlos, multiplayer local, netplay, save states, shaders.

Definition of done:

- Adicionar um novo emulador exige config + adapter pequeno.
- A UI mostra capacidades sem hardcode por id.
- Config invalida gera erro claro.

### Fase 5 - Analisador Do PC

Objetivo: a app recomendar o que o PC aguenta.

Tarefas:

- Detetar CPU, RAM, GPU, VRAM e sistema operativo.
- Criar `HardwareProfile`.
- Criar catalogo de requisitos por tier.
- Classificar emuladores em:
  - Muito leve
  - Leve
  - Medio
  - Pesado
  - Muito pesado
- Mostrar recomendacoes por plataforma.

Definition of done:

- A app mostra um relatorio simples do PC.
- Cada emulador recebe estado: recomendado, possivel com ajustes, pesado.
- Perfis graficos sugerem Performance/Equilibrado/Qualidade conforme hardware.

### Fase 6 - Multiplayer Local

Objetivo: jogar com amigos no mesmo PC com o minimo de friccao.

Tarefas:

- Criar `LocalMultiplayerSession`.
- Configurar jogadores e comandos.
- Aplicar perfis por jogador.
- Criar presets por emulador.
- Validar que o emulador suporta o modo pedido.

Definition of done:

- A UI permite escolher numero de jogadores.
- Cada jogador fica associado a um comando.
- A app aplica config antes de iniciar o jogo.

### Fase 7 - PSP E N64 Em Modo Performance

Objetivo: suportar plataformas mais pesadas com configuracoes amigas de PCs modestos.

Tarefas:

- Limpar adaptador PPSSPP.
- Limpar adaptador Mupen64Plus.
- Criar perfis graficos reais para ambos.
- Criar avisos de performance.
- Sugerir configuracao por hardware.

Definition of done:

- PSP e N64 continuam opcionais, mas bem configurados.
- A app consegue explicar porque recomenda Performance ou Equilibrado.

### Fase 8 - Multiplayer Remoto

Objetivo: permitir jogar com amigos remotamente sem tentar reinventar tudo no inicio.

Tarefas:

- Integrar primeiro com ferramentas externas:
  - Parsec
  - Steam Remote Play
  - Sunshine/Moonlight
- Depois avaliar netplay nativo:
  - RetroArch
  - Dolphin
  - PPSSPP
- Criar conceito de convite/sessao.

Definition of done:

- A app consegue preparar uma sessao remota com instrucoes ou integracao externa.
- Netplay nativo entra apenas onde for confiavel.

### Fase 9 - Big Picture, Polimento E Distribuicao

Objetivo: transformar a app numa experiencia confortavel para usar no sofa.

Tarefas:

- Modo Big Picture.
- Navegacao por comando.
- Tema polido.
- Instalador ou versao portable.
- Backup/export/import de configuracoes.
- Logs e diagnostico acessiveis pela UI.

Definition of done:

- A app pode ser usada sem teclado/rato nos fluxos principais.
- Configuracoes sao portaveis.
- Erros sao compreensiveis para o utilizador.

## Sprint Inicial Recomendada

Antes de adicionar features novas, fazer esta sprint:

1. Corrigir tracking de sessoes e EventBus.
2. Corrigir o modelo `PlaySession`.
3. Corrigir `SQLiteSessionRepository`.
4. Limpar codigo-string em config/cache.
5. Criar uma configuracao alvo para perfis graficos.
6. Colocar testes principais a verde.

So depois avancar para UI de perfis graficos e controlos.

## Regra De Ouro

Fazer duas plataformas muito bem primeiro. Depois transformar esse padrao num
sistema extensivel. Quando NDS e GBA estiverem excelentes, adicionar novos
emuladores passa a ser multiplicar uma base solida, nao acumular remendos.
