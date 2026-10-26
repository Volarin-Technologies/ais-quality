Estou fazendo parte do projeto da Fovea AI, da Volarin Technologies, e estamos compartilhando nosso primeiro projeto open-source: o AIS Quality.

É uma ferramenta local em Python para revisar arquivos de posições de embarcações antes de usá-los em análises.

A versão inicial identifica campos ausentes, duplicações, coordenadas e horários inválidos, posições conflitantes e lacunas temporais. Também permite configurar limites de velocidade e deslocamento para revisão.

Incluímos um modo opcional de machine learning para sinalizar segmentos fora do padrão, mantendo esses alertas separados das verificações por regras. Os relatórios são exportados em HTML, JSON e CSV, em português ou inglês.

O projeto tem testes automatizados, exemplos reproduzíveis e uma verificação de compatibilidade com uma amostra pública da NOAA. Ainda é uma versão beta: os alertas pedem revisão e não comprovam erro nos dados.

Quem trabalha com dados AIS, geoprocessamento ou operações marítimas: quais problemas de qualidade vocês mais encontram?

Código: [INSERIR LINK DO REPOSITÓRIO]

#Python #OpenSource #AIS #GeoAI #DataQuality #MachineLearning #Volarin

---
Antes de publicar: substitua o link; confirme que os testes do repositório passaram. Use docs/report-preview.png, identificada como demonstração sintética. Não anuncie o código como público antes de publicar o repositório.
