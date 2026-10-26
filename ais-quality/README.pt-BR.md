# AIS Quality

**Auditoria local de dados AIS com regras explicáveis e machine learning opcional.** Projeto open-source da Volarin Technologies · **0.4.0 beta**.

O software recebe um CSV de posições de embarcações, verifica sua qualidade e gera relatórios para revisão antes de análises marítimas. Não exige servidor, conta, API paga ou conexão durante a execução.

![Relatório demonstrativo com dados sintéticos](docs/report-preview.png)

## Executar

Com Python 3.10 ou superior, extraia o projeto, entre na pasta e rode:

```bash
python3 ais_quality.py examples/sample.csv --language pt --output reports
```

Abra `reports/report.html`. O modo básico não tem dependências externas.

Para instalar o comando e o ML opcional:

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install '.[ml]'
ais-quality examples/ml-demo.csv --ml --language pt --output reports
```

No Windows, ative o ambiente com `.venv\Scripts\activate`. A instalação baixa dependências uma vez; depois o processamento é local.

## Verificações

- Campos ausentes, problemas de formato, duplicações e MMSI malformado.
- Coordenadas e horários inválidos.
- Posições diferentes para a mesma embarcação no mesmo horário.
- Lacunas temporais por embarcação.
- Velocidade estimada e deslocamento acima de limites configuráveis.
- ML opcional para priorizar segmentos fora do padrão observado no arquivo.

Os relatórios mostram severidade, evidências e recomendações de revisão. As exportações incluem HTML, JSON, CSV de ocorrências, registros problemáticos, resumo por embarcação e segmentos avaliados pelo ML. Os alertas de ML ficam separados das regras.

## Configurar

```bash
ais-quality arquivo.csv --language pt --gap-minutes 30 --max-speed-knots 60 --max-jump-nm 20
ais-quality arquivo.csv --column timestamp=Horario --column lat=Latitude --column lon=Longitude
```

Colunas canônicas: `mmsi`, `timestamp`, `lat`, `lon`. Vários aliases são reconhecidos. Horários sem fuso são rejeitados por padrão. Use `--assume-utc` somente se a origem documentar UTC, como na amostra da NOAA:

```bash
ais-quality examples/real-noaa.csv --assume-utc --language pt --output reports-noaa
```

Limites padrão: 100 mil registros e 100 milhões de bytes. É uma ferramenta em memória; aumentar os limites pode exigir mais RAM. O HTML mostra até 500 registros por seção; JSON e CSV mantêm o resultado completo. Os seis arquivos de saída conhecidos são substituídos em novas execuções; guarde relatórios anteriores em outras pastas.

## O que foi validado

Incluímos 5 mil registros reais da NOAA com origem, licença do catálogo e hash documentados, cenários sintéticos, avaliação de falsos positivos de ML e medição de desempenho até 100 mil registros no modo básico. Veja [validação](docs/VALIDATION.md) e [origem dos dados](SOURCES.md).

O ML se ajusta ao próprio arquivo: **não é um modelo marítimo previamente treinado, nem uma garantia de precisão**. Uma ocorrência pede revisão; não comprova erro, irregularidade ou intenção. Não usar para navegação. A amostra real é um recorte inicial do arquivo e não representa toda a operação marítima.

[Documentação completa em inglês](README.md) · [Como contribuir](CONTRIBUTING.md) · [Histórico](CHANGELOG.md).
