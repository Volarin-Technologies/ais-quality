"""Bilingual report rendering and actionable rule descriptions."""
from html import escape

RULES = {
'missing_field': ('error', 'Missing required value', 'Campo obrigatório ausente', 'Review the source record; do not infer missing values silently.', 'Revise a origem; não preencha valores por suposição.'),
'malformed_row': ('error', 'Incorrect CSV column count', 'Quantidade incorreta de colunas', 'Check delimiter and quoting in the source CSV.', 'Confira o separador e as aspas no CSV.'),
'duplicate': ('warning', 'Exact duplicate record', 'Registro exatamente duplicado', 'Review the ingestion process before removing duplicates.', 'Revise a ingestão antes de remover duplicações.'),
'invalid_mmsi': ('error', 'Invalid MMSI structure', 'Estrutura de MMSI inválida', 'Check the original identifier. Registry validity is not verified.', 'Confira o identificador original. Não há consulta a cadastro.'),
'invalid_coordinate': ('error', 'Invalid or unavailable coordinate', 'Coordenada inválida ou indisponível', 'Check coordinate order, units and AIS unavailable-value sentinels.', 'Confira a ordem, as unidades e os valores AIS de posição indisponível.'),
'invalid_timestamp': ('error', 'Invalid timestamp or missing timezone', 'Horário inválido ou sem fuso', 'Check ISO 8601 and timezone; use assume-utc only when the source documents UTC.', 'Confira ISO 8601 e fuso; use assume-utc apenas se a origem documentar UTC.'),
'position_conflict': ('warning', 'Conflicting simultaneous positions', 'Posições conflitantes no mesmo horário', 'Compare the original messages and receiver records. Conflicts are excluded from movement and ML.', 'Compare mensagens e receptores. Conflitos são excluídos de movimento e ML.'),
'speed_exceeded': ('warning', 'Estimated speed exceeds configured limit', 'Velocidade estimada acima do limite', 'Review both positions and timestamps; adjust the limit for the vessel and operation.', 'Revise as duas posições e horários; ajuste o limite à embarcação e operação.'),
'position_jump': ('warning', 'Displacement exceeds configured limit', 'Deslocamento acima do limite', 'Review the segment endpoints. A long displacement alone is not proof of bad data.', 'Revise as extremidades do segmento. Distância elevada não comprova erro.'),
}


def enrich(issues, language):
    result = []
    for entry in issues:
        severity, en, pt, recommendation_en, recommendation_pt = RULES[entry['code']]
        result.append(dict(entry, severity=severity, title=pt if language == 'pt' else en,
                           recommendation=recommendation_pt if language == 'pt' else recommendation_en))
    return result


def render_html(report):
    pt = report.get('language') == 'pt'
    def t(en, br): return br if pt else en
    def esc(v): return escape(str(v))
    limit = 500
    def table(headers, rows):
        count = 0
        shown = []
        for row in rows:
            count += 1
            if len(shown) < limit:
                shown.append(row)
        body = ''.join('<tr>'+''.join('<td>'+esc(v)+'</td>' for v in row)+'</tr>' for row in shown)
        if not body:
            body = '<tr><td colspan="'+str(len(headers))+'">'+t('No entries.', 'Nenhum registro.')+'</td></tr>'
        suffix = '<p>'+t('Showing first 500 entries; full data is in JSON and CSV.', 'Exibindo os primeiros 500 registros; dados completos em JSON e CSV.')+'</p>' if count>limit else ''
        return '<div class="table"><table><thead><tr>'+''.join('<th>'+esc(h)+'</th>' for h in headers)+'</tr></thead><tbody>'+body+'</tbody></table></div>'+suffix
    cards = ''.join('<article><b>'+str(value)+'</b><span>'+label+'</span></article>' for label,value in [
        (t('Records','Registros'),report['total_rows']),
        (t('Flagged rows','Linhas com alertas'),report['flagged_rows']),
        (t('Temporal gaps','Lacunas temporais'),len(report['gaps'])),
        (t('ML alerts','Alertas de ML'),len(report['ml']['alerts']))])
    issues = table([t('CSV line','Linha CSV'), t('Severity','Severidade'), t('Finding','Ocorrência'), t('Evidence','Evidências'),t('Next step','Próximo passo')],
                   ([i['line'], ({'warning':'aviso','error':'erro'}[i['severity']] if pt else i['severity']), i['title'], i['detail'], i['recommendation']] for i in report['issues']))
    vessels = table(['MMSI',t('Records','Registros'),t('Flagged rows','Com alertas'),t('Unique timestamps','Horários únicos'),t('Gaps','Lacunas')],
                    ([v['mmsi'],v['total_rows'],v['flagged_rows'],v['unique_timestamps'],v['gap_count']] for v in report['vessels']))
    gaps = table(['MMSI',t('Start UTC','Início UTC'),t('End UTC','Fim UTC'),t('Minutes','Minutos')],
                 ([g['mmsi'],g['start'],g['end'],round(g['minutes'],3)] for g in report['gaps']))
    ml = report['ml']
    ml_status = {'disabled':t('Disabled','Desativado'),'insufficient_data':t('Insufficient eligible data','Dados elegíveis insuficientes'),'completed':t('Completed','Concluído')}[ml['status']]
    ml_table = table([t('Ending line','Linha final'),'MMSI',t('Estimated knots','Nós estimados'),t('Minutes','Minutos'),t('Turn degrees','Mudança de rumo °'),t('Score','Pontuação')],
                     ([a['line'],a['mmsi'],round(a['speed_knots'],2),round(a['interval_minutes'],2),round(a['turn_degrees'],2),round(a['anomaly_score'],5)] for a in ml['alerts']))
    settings = report['settings']
    notes = t('Rule findings are separate from statistical ML alerts. A warning is a review request, not proof of an error. Gap events do not establish transmitter failure. ML fits and scores this file; scores are not probabilities. Not for navigation.',
              'As regras são separadas dos alertas estatísticos de ML. Um aviso pede revisão e não comprova erro. Lacunas não confirmam falha de transmissão. O ML se ajusta e avalia este arquivo; pontuações não são probabilidades. Não usar para navegação.')
    configuration = t('Thresholds','Limites')+f": {settings['max_speed_knots']:g} kn · {settings['max_jump_nm']:g} nm · "+t('gap','lacuna')+f" {report['gap_threshold_minutes']:g} min · "+t('assume UTC','presumir UTC')+': '+t(str(settings['assume_utc']), 'sim' if settings['assume_utc'] else 'não')
    return f'''<!doctype html><html lang="{'pt-BR' if pt else 'en'}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>AIS Quality · {esc(report['source'])}</title>
<style>:root{{color-scheme:light}}*{{box-sizing:border-box}}body{{margin:0;background:#f3f5f8;color:#142437;font:15px Arial,sans-serif}}main{{max-width:1240px;margin:auto;padding:40px 24px}}header{{border-top:5px solid #2855e8;padding-top:24px}}small{{letter-spacing:2px;color:#2855e8}}h1{{font-size:52px;letter-spacing:-2px;margin:16px 0}}p{{line-height:1.65;color:#526176}}.cards{{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin:28px 0}}article{{background:white;padding:24px;border:1px solid #dae0e8}}b{{display:block;font-size:38px}}span{{display:block;margin-top:10px;color:#526176}}.table{{overflow:auto;background:white;border:1px solid #dae0e8}}table{{border-collapse:collapse;width:100%;text-align:left;font-size:13px}}td,th{{padding:14px;border-bottom:1px solid #e2e7ef;vertical-align:top;overflow-wrap:anywhere;min-width:90px}}th{{background:#e8edf6;white-space:nowrap;overflow-wrap:normal}}h2{{margin-top:36px;font-size:22px}}.note{{padding:18px;border-left:3px solid #2855e8;background:#e8edf6}}a{{color:#2855e8}}nav a{{margin-right:18px}}footer{{padding:24px 0;color:#526176}}@media(max-width:650px){{.cards{{grid-template-columns:1fr 1fr}}h1{{font-size:40px}}}}@media print{{main{{padding:0}}.table{{overflow:visible}}nav{{display:none}}}}</style></head><body><main><header><small>VOLARIN TECHNOLOGIES / OPEN SOURCE</small><h1>AIS Quality</h1><p>{t('Local AIS data audit','Auditoria local de dados AIS')} · v{esc(report['version'])} · {esc(report['source'])}</p></header><nav><a href="#findings">{t('Findings','Ocorrências')}</a><a href="#vessels">{t('Vessels','Embarcações')}</a><a href="#ml">Machine learning</a></nav><div class="cards">{cards}</div><p class="note">{notes}</p><p>{esc(configuration)}</p>
<h2 id="findings">{t('Rule findings and review guidance','Ocorrências das regras e orientações de revisão')}</h2>{issues}
<h2 id="vessels">{t('Vessel summary','Resumo por embarcação')}</h2>{vessels}
<h2>{t('Temporal gaps','Lacunas temporais')}</h2>{gaps}
<h2 id="ml">Machine learning · {ml_status}</h2><p>{t('Positive scores mark unusual segments relative to this fitted model. Displayed metrics describe segments and do not explain causality.','Pontuações positivas indicam segmentos incomuns para este modelo. As métricas descrevem os segmentos e não explicam causalidade.')}</p>{ml_table}
<footer>{t('Complete exports','Exportações completas')}: report.json · issues.csv · flagged_records.csv · vessels.csv · ml_segments.csv</footer></main></body></html>'''
