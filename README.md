# Diagnóstico e Otimização HDMI para RTX 3050 Laptop

Projeto para diagnosticar e corrigir gargalos causados por projeção HDMI em 4K durante jogos ou aplicações gráficas pesadas em notebooks com NVIDIA GeForce RTX 3050 Laptop GPU.

O fluxo atual combina monitoramento em tempo real com uma ação corretiva opcional: quando o sistema detecta 4K + VRAM/RAM em nível crítico, ele pode mudar a projeção para a TV e forçar `1920x1080 @ 60Hz`.

## Diagnóstico do Problema

### Sintoma

Ao espelhar a saída de vídeo do notebook para uma TV externa via HDMI durante jogos ou aplicações gráficas pesadas, a imagem na TV apresentava congelamentos severos, quedas bruscas de frames, stuttering e lentidão generalizada. Ao mesmo tempo, a taxa de quadros permanecia fluida na tela nativa do notebook.

### Causa raiz

O monitoramento em tempo real com `pynvml` e `psutil` indicou um efeito cascata de esgotamento de memória causado pela resolução automática aplicada pelo Windows:

1. Upscaling automático para 4K: ao conectar o HDMI, o Windows configurava a TV em `3840x2160`, aumentando o custo de renderização e cópia de buffers.
2. Estouro de VRAM: a RTX 3050 Laptop com 4 GB de VRAM ficava próxima do limite físico. O log registrou `3991MB / 4096MB (97.4%)`.
3. Gargalo de RAM e paging: com a VRAM esgotada, texturas e buffers passam a pressionar a RAM do sistema. O log registrou `99.8%` de RAM, cenário propício para paginação em disco e input lag.

## Arquitetura

Os arquivos `monitor.py` e `optimize_resolution.py` continuam existindo como entradas simples para manter o uso direto pela linha de comando. A lógica principal fica no pacote `hdmi_optimizer/`.

```text
n/
├─ README.md
├─ requirements.txt
├─ diagnostico_rtx3050.txt
├─ monitor.py
├─ optimize_resolution.py
└─ hdmi_optimizer/
   ├─ __init__.py
   ├─ config.py
   ├─ models.py
   ├─ policy.py
   ├─ cli.py
   ├─ monitoring/
   │  ├─ gpu.py
   │  ├─ system.py
   │  ├─ displays.py
   │  ├─ logger.py
   │  └─ service.py
   └─ optimization/
      ├─ projection.py
      ├─ resolution.py
      └─ service.py
```

### Responsabilidades

- `monitor.py`: entrada curta para executar o monitor.
- `optimize_resolution.py`: entrada curta para executar a otimização manual.
- `hdmi_optimizer/config.py`: constantes de resolução, limites e intervalo.
- `hdmi_optimizer/models.py`: modelos de dados do diagnóstico.
- `hdmi_optimizer/policy.py`: regra que decide se o gargalo exige otimização.
- `hdmi_optimizer/cli.py`: argumentos de linha de comando.
- `hdmi_optimizer/monitoring/gpu.py`: leitura da GPU via NVML.
- `hdmi_optimizer/monitoring/system.py`: leitura de CPU/RAM via `psutil`.
- `hdmi_optimizer/monitoring/displays.py`: leitura das telas via `screeninfo`.
- `hdmi_optimizer/monitoring/logger.py`: formatação e escrita do log.
- `hdmi_optimizer/monitoring/service.py`: loop principal de monitoramento.
- `hdmi_optimizer/optimization/projection.py`: troca para "Apenas segunda tela".
- `hdmi_optimizer/optimization/resolution.py`: aplicação de resolução via Win32.
- `hdmi_optimizer/optimization/service.py`: orquestra projeção + resolução.

## Fluxo Automático

Quando `monitor.py` roda com `--auto-otimizar`, o serviço de monitoramento coleta um snapshot com GPU, sistema e telas. Em seguida, `OptimizationPolicy` avalia se existe uma tela em `3840x2160` ou superior, VRAM acima do limite configurado e RAM acima do limite configurado.

Se a regra for satisfeita, `OptimizationService` executa a correção uma única vez:

```text
monitor.py
  -> hdmi_optimizer.cli.main_monitor()
  -> MonitoringService
  -> OptimizationPolicy
  -> OptimizationService
  -> displayswitch.exe /external
  -> ChangeDisplaySettings(1920x1080 @ 60Hz)
```

## Requisitos

- Windows
- Driver NVIDIA instalado
- Python 3.10 ou superior
- TV/monitor conectado via HDMI

Instale as dependências:

```powershell
pip install -r requirements.txt
```

## Uso

Para apenas monitorar e gerar o diagnóstico:

```powershell
python monitor.py
```

Para monitorar e aplicar a correção automaticamente quando o gargalo aparecer:

```powershell
python monitor.py --auto-otimizar
```

Para aplicar a otimização manualmente antes de abrir o jogo:

```powershell
python optimize_resolution.py
```

Para personalizar a resolução manual:

```powershell
python optimize_resolution.py --largura 1920 --altura 1080 --frequencia 60
```

Para ajustar os limites do modo automático:

```powershell
python monitor.py --auto-otimizar --limite-vram 92 --limite-ram 94
```

## Resultado Esperado

Depois da otimização, a saída HDMI passa a operar em `1080p @ 60Hz`, reduzindo a pressão sobre VRAM e RAM. A intenção é evitar que o Windows entre no ciclo de fallback para RAM e paginação em disco, diminuindo stuttering, congelamentos e input lag na TV.

## Observações de Segurança

O modo `--auto-otimizar` altera a configuração de vídeo do Windows durante a execução. Se a TV perder sinal, use o atalho `Win + P` para escolher outro modo de projeção ou aguarde o Windows restaurar a configuração anterior.

O script não altera configurações permanentes de driver NVIDIA nem modifica arquivos do sistema. Ele usa `displayswitch.exe` e a API Win32 para aplicar a resolução na sessão atual.
