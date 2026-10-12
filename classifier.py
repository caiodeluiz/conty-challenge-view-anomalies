"""Explainable rules for consecutive hourly view counts; no external services."""

from statistics import median


MAX_HOURS = 8760
MAX_COUNT = 2**53 - 1
MIN_HOURS = 12
MIN_VOLUME = 500


def validate_series(views):
    if not isinstance(views, list) or not 1 <= len(views) <= MAX_HOURS:
        raise ValueError(f"views deve ter entre 1 e {MAX_HOURS} contagens por hora")
    if any(type(value) is not int or not 0 <= value <= MAX_COUNT for value in views):
        raise ValueError("cada contagem deve ser um inteiro não negativo até 2^53-1")
    return views


def classify(views):
    views = validate_series(views)
    peak = max(views)
    peak_index = views.index(peak)
    baseline = median(views)
    total = sum(views)
    positive_hours = sum(value > 0 for value in views)
    longest_run = run = 0
    previous = None
    for value in views:
        run = run + 1 if value == previous and value >= MIN_VOLUME else int(value >= MIN_VOLUME)
        longest_run = max(longest_run, run)
        previous = value

    interior = 0 < peak_index < len(views) - 1
    neighbors = max(views[peak_index - 1], views[peak_index + 1]) if interior else None
    isolated_peak = bool(
        interior and peak >= MIN_VOLUME and peak >= 10 * max(baseline, 1)
        and peak >= 6 * max(neighbors, 1) and views[peak_index + 1] <= peak / 10
        and peak >= 0.45 * total
    )
    boundary_peak = bool(
        not interior and peak >= MIN_VOLUME and peak >= 10 * max(baseline, 1)
        and peak >= 0.45 * total
    )

    plateau_drop = False
    for start in range(len(views) - 6):
        plateau = views[start:start + 6]
        center = median(plateau)
        if min(plateau) >= MIN_VOLUME and max(plateau) - min(plateau) <= center * 0.02:
            if views[start + 6] <= center * 0.1:
                plateau_drop = True
                break

    signals = {
        "hours": len(views), "positive_hours": positive_hours,
        "total_views": total, "peak_views": peak, "peak_hour_index": peak_index,
        "median_hourly_views": baseline,
        "peak_share": round(peak / total, 6) if total else 0,
        "longest_identical_high_run": longest_run,
        "isolated_peak_followed_by_drop": isolated_peak,
        "boundary_peak_without_both_neighbors": boundary_peak,
        "near_constant_plateau_followed_by_drop": plateau_drop,
    }
    if len(views) < MIN_HOURS or positive_hours < 3:
        return {
            "classification": "inconclusive",
            "reason": "Há poucas horas observadas ou atividade em menos de três horas; prefiro não acusar.",
            "reasons": ["observações insuficientes"], "signals": signals,
        }
    if boundary_peak:
        return {
            "classification": "inconclusive",
            "reason": "O pico está na extremidade da série; falta um dos vizinhos para avaliar seu contexto. Prefiro não acusar.",
            "reasons": ["pico sem contexto completo"], "signals": signals,
        }

    reasons = []
    if longest_run >= 6:
        reasons.append(f"A mesma contagem de pelo menos {MIN_VOLUME} views repete por {longest_run} horas consecutivas.")
    if isolated_peak:
        reasons.append("Um pico concentra pelo menos 45% das views, supera vizinhos em 6 vezes e cai pelo menos 90% na hora seguinte.")
    if plateau_drop:
        reasons.append(f"Seis horas com pelo menos {MIN_VOLUME} views em cada hora, quase constantes, são seguidas por uma queda de pelo menos 90%.")
    return {
        "classification": "suspicious" if reasons else "legitimate",
        "reason": " ".join(reasons) if reasons else "Nenhum dos padrões suspeitos definidos foi confirmado nesta série.",
        "reasons": reasons, "signals": signals,
    }
