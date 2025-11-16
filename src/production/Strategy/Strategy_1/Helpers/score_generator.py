import re
from typing import Dict, Any


def _to_float(val: Any) -> float:
    """
    Convert strings like 'Rs. 315 Cr', '300.5%', '17.5x' into float.
    If it's already a number, just return float(val).
    """
    if isinstance(val, (int, float)):
        return float(val)
    if not isinstance(val, str):
        return 0.0

    cleaned = val.replace("Rs.", "").replace("Rs", "")
    cleaned = cleaned.replace("Cr", "").replace(",", "")
    cleaned = cleaned.replace("x", "").strip()

    match = re.findall(r"[-+]?\d*\.?\d+", cleaned)
    if not match:
        return 0.0
    return float(match[0])


def _to_percent(val: Any) -> float:
    """
    Convert percentage string like '300.5%' to float 300.5.
    """
    if isinstance(val, (int, float)):
        return float(val)
    if not isinstance(val, str):
        return 0.0
    cleaned = val.replace("%", "").strip()
    try:
        return float(cleaned)
    except ValueError:
        return 0.0


def growth_pct(current: float, previous: float) -> float:
    """
    % growth with simple turnaround handling when previous == 0.
    """
    if previous == 0:
        if current > 0:
            return 100.0   # treat as strong positive turnaround
        if current < 0:
            return -100.0  # strong negative
        return 0.0
    return (current - previous) / previous * 100.0


def norm_linear(val: float, bad: float, good: float) -> float:
    """
    Map [bad .. good] linearly to [0 .. 100] with clipping.
    """
    if val <= bad:
        return 0.0
    if val >= good:
        return 100.0
    return (val - bad) / (good - bad) * 100.0


def pe_to_score(pe: float) -> float:
    """
    Simple valuation logic:
    - Negative/zero PE = 0
    - 8–20x: best zone
    - Very high PE gets punished.
    """
    if pe <= 0:
        return 0.0

    if pe < 8:
        # 0–8x → 50–90 (cheap but may be low quality)
        return 50.0 + (pe / 8.0) * 40.0
    if pe <= 20:
        # 8–20x → 90–100
        return 90.0 + (pe - 8.0) / (20.0 - 8.0) * 10.0
    if pe <= 35:
        # 20–35x → 100–40
        return 100.0 - (pe - 20.0) / (35.0 - 20.0) * 60.0
    if pe <= 60:
        # 35–60x → 40–10
        return 40.0 - (pe - 35.0) / (60.0 - 35.0) * 30.0

    return 5.0  # extremely expensive


def classify_result(score: float) -> str:
    if score >= 75:
        return "strong"
    if score >= 60:
        return "good"
    if score >= 45:
        return "ok"
    return "weak"


def calculate_result_score(data: Dict[str, Any]) -> Dict[str, Any]:
    results = data.get("results", {})

    # ---------- 1) Revenue Growth ----------
    rev = results.get("revenue", {})
    rev_qoq_growth = _to_percent(rev.get("qoq_growth", "0%"))
    rev_yoy_growth = _to_percent(rev.get("yoy_growth", "0%"))

    # Slightly tighter bands for revenue
    rev_qoq_score = norm_linear(rev_qoq_growth, bad=-20.0, good=40.0)
    rev_yoy_score = norm_linear(rev_yoy_growth, bad=-15.0, good=30.0)
    revenue_growth_score = 0.5 * rev_yoy_score + 0.5 * rev_qoq_score

    # ---------- 2) EBITDA & Margin Strength ----------
    ebitda = results.get("ebitda", {})
    cur_ebitda = _to_float(ebitda.get("current", "0"))
    prev_qoq_ebitda = _to_float(ebitda.get("prev_qoq", "0"))
    prev_yoy_ebitda = _to_float(ebitda.get("prev_yoy", "0"))

    ebitda_qoq_growth = growth_pct(cur_ebitda, prev_qoq_ebitda)
    ebitda_yoy_growth = growth_pct(cur_ebitda, prev_yoy_ebitda)

    ebitda_qoq_score = norm_linear(ebitda_qoq_growth, bad=-30.0, good=25.0)
    ebitda_yoy_score = norm_linear(ebitda_yoy_growth, bad=-25.0, good=20.0)
    ebitda_growth_score = 0.5 * ebitda_yoy_score + 0.5 * ebitda_qoq_score

    ebitda_margin = results.get("ebitda_margin", {})
    cur_margin = _to_percent(ebitda_margin.get("current", "0%"))
    prev_qoq_margin = _to_percent(ebitda_margin.get("prev_qoq", "0%"))
    prev_yoy_margin = _to_percent(ebitda_margin.get("prev_yoy", "0%"))

    # Margin level: 0–25% mapped to 0–100
    margin_level_score = norm_linear(cur_margin, bad=0.0, good=25.0)

    # Margin trend: penalize large drops (multiplied to punish strongly)
    drop_qoq = max(0.0, prev_qoq_margin - cur_margin)
    drop_yoy = max(0.0, prev_yoy_margin - cur_margin)

    # Every 5pp drop ≈ -15 points
    margin_trend_qoq = max(0.0, 100.0 - (drop_qoq / 5.0) * 15.0)
    margin_trend_yoy = max(0.0, 100.0 - (drop_yoy / 5.0) * 15.0)
    margin_trend_score = 0.6 * margin_trend_yoy + 0.4 * margin_trend_qoq

    # Overall profitability (EBITDA + margins)
    margin_strength_score = 0.6 * margin_level_score + 0.4 * margin_trend_score
    ebitda_and_margin_score = 0.6 * margin_strength_score + 0.4 * ebitda_growth_score

    # ---------- 3) Profit (PAT) Growth ----------
    adj_pat = results.get("adjusted_pat", {})
    cur_pat = _to_float(adj_pat.get("current", "0"))
    prev_qoq_pat = _to_float(adj_pat.get("prev_qoq", "0"))
    prev_yoy_pat = _to_float(adj_pat.get("prev_yoy", "0"))

    pat_qoq_growth = growth_pct(cur_pat, prev_qoq_pat)
    pat_yoy_growth = growth_pct(cur_pat, prev_yoy_pat)

    pat_qoq_score = norm_linear(pat_qoq_growth, bad=-40.0, good=25.0)
    pat_yoy_score = norm_linear(pat_yoy_growth, bad=-30.0, good=20.0)
    profit_growth_score = 0.6 * pat_yoy_score + 0.4 * pat_qoq_score

    # ---------- 4) Valuation ----------
    eps = results.get("eps", {})
    pe_val = _to_float(eps.get("ttm_pe", "0"))
    valuation_score = pe_to_score(pe_val)

    # ---------- QUALITY GUARDRAILS ----------
    # If profits & EBITDA are weak and margins are weak, cap revenue's contribution.
    if profit_growth_score < 30.0 and ebitda_growth_score < 30.0 and margin_strength_score < 40.0:
        revenue_growth_score = min(revenue_growth_score, 40.0)

    # If PAT has collapsed heavily QoQ & YoY, cap total score later
    severe_pat_collapse = (pat_qoq_growth <= -50.0 and pat_yoy_growth <= -40.0)

    # If margin dropped > 15pp and current margin < 10%, apply strong penalty later
    margin_drop_big = (drop_qoq > 15.0 or drop_yoy > 15.0) and cur_margin < 10.0

    # ---------- 5) Final Weighted Score ----------
    # Weights: Revenue 15%, EBITDA+Margins 35%, PAT 35%, Valuation 15%
    final_score = (
        0.15 * revenue_growth_score
        + 0.35 * ebitda_and_margin_score
        + 0.35 * profit_growth_score
        + 0.15 * valuation_score
    )

    if severe_pat_collapse:
        final_score = min(final_score, 35.0)

    if margin_drop_big:
        final_score *= 0.7  # 30% haircut

    # Clip to [0, 100]
    final_score = max(0.0, min(100.0, final_score))

    result_quality = classify_result(final_score)

    return round(final_score, 2)