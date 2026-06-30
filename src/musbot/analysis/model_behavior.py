"""Informes legibles sobre comportamiento y tendencias de modelos."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path

from musbot.agents.rl_agent import RLAgent


def write_behavior_report(
    *,
    run_dir: str | Path,
    run_id: str,
    trainer_version: str,
    checkpoint_used: str,
    opponent: str,
    metrics: Mapping[str, float],
    behavior_summary: Mapping[str, object],
    agent: RLAgent | None = None,
) -> list[Path]:
    """Escribe uno o varios informes de comportamiento para un run."""

    root = Path(run_dir)
    report_name = f"comportamiento_{opponent}.md"
    report_path = root / report_name
    generic_path = root / "comportamiento.md"
    contenido = _render_behavior_report(
        run_id=run_id,
        trainer_version=trainer_version,
        checkpoint_used=checkpoint_used,
        opponent=opponent,
        metrics=metrics,
        behavior_summary=behavior_summary,
        agent=agent,
    )
    report_path.write_text(contenido, encoding="utf-8")
    generic_path.write_text(contenido, encoding="utf-8")
    return [report_path, generic_path]


def _render_behavior_report(
    *,
    run_id: str,
    trainer_version: str,
    checkpoint_used: str,
    opponent: str,
    metrics: Mapping[str, float],
    behavior_summary: Mapping[str, object],
    agent: RLAgent | None,
) -> str:
    action_counts = _mapping_of_ints(behavior_summary.get("action_counts"))
    phase_top_actions = behavior_summary.get("phase_top_actions")
    envite_amounts = _mapping_of_ints(behavior_summary.get("envite_amounts"))
    insights = _insights_from_behavior(behavior_summary, metrics)
    policy_preferences = _policy_preferences(agent)

    lineas = [
        f"# {run_id} - Comportamiento",
        "",
        "## Contexto",
        "",
        f"- trainer: {trainer_version}",
        f"- checkpoint: {checkpoint_used}",
        f"- evaluado contra: {opponent}",
        f"- episodios evaluados: {int(behavior_summary.get('episodes', 0) or 0)}",
        "",
        "## Resultado",
        "",
        f"- win_rate: {float(metrics.get('win_rate', 0.0)):.3f}",
        f"- avg_reward: {float(metrics.get('avg_reward', 0.0)):.3f}",
        f"- avg_score_diff: {float(metrics.get('avg_score_diff', 0.0)):.3f}",
        "",
        "## Tendencias",
        "",
    ]

    if insights:
        for insight in insights:
            lineas.append(f"- {insight}")
    else:
        lineas.append("- Aun no hay suficientes decisiones para inferir tendencias.")

    lineas.extend(
        [
            "",
            "## Frecuencia de Acciones",
            "",
        ]
    )
    if not action_counts:
        lineas.append("- sin datos de acciones")
    else:
        total = max(int(behavior_summary.get("total_decisions", 0) or 0), 1)
        for action, count in sorted(action_counts.items(), key=lambda item: (-item[1], item[0])):
            lineas.append(f"- {action}: {count} ({count / total:.1%})")

    lineas.extend(["", "## Envites", ""])
    lineas.append(f"- envite_rate: {float(behavior_summary.get('envite_rate', 0.0)):.3f}")
    lineas.append(
        f"- ordago_bad_context_rate: "
        f"{float(behavior_summary.get('ordago_bad_context_rate', 0.0)):.3f}"
    )
    lineas.append(
        f"- avg_envite_amount: {float(behavior_summary.get('avg_envite_amount', 0.0)):.3f}"
    )
    lineas.append(
        f"- aggressive_envite_bad_context_rate: "
        f"{float(behavior_summary.get('aggressive_envite_bad_context_rate', 0.0)):.3f}"
    )
    lineas.append(
        f"- avg_aggressive_envite_amount: "
        f"{float(behavior_summary.get('avg_aggressive_envite_amount', 0.0)):.3f}"
    )
    if envite_amounts:
        for cantidad, count in sorted(envite_amounts.items()):
            lineas.append(f"- envidar {cantidad}: {count}")
    else:
        lineas.append("- no hay envites registrados en la muestra")

    lineas.extend(["", "## Acciones por Fase", ""])
    if isinstance(phase_top_actions, Mapping) and phase_top_actions:
        for phase, entries in sorted(phase_top_actions.items()):
            lineas.append(f"- {phase}:")
            if isinstance(entries, Sequence):
                for entry in entries:
                    if isinstance(entry, Mapping):
                        lineas.append(f"  - {entry.get('action')}: {entry.get('count')}")
    else:
        lineas.append("- sin resumen por fases")

    lineas.extend(["", "## Patrones Aprendidos", ""])
    if not policy_preferences:
        lineas.append("- no hay preferencias de politica disponibles")
    else:
        for preference in policy_preferences:
            lineas.append(
                (
                    "- visitas={visits}, mejor_accion={action}, valor={value:.3f}, estado={state}"
                ).format(**preference)
            )

    return "\n".join(lineas) + "\n"


def _mapping_of_ints(value: object) -> dict[str, int]:
    if not isinstance(value, Mapping):
        return {}
    return {str(key): int(count) for key, count in value.items()}


def _insights_from_behavior(
    behavior_summary: Mapping[str, object],
    metrics: Mapping[str, float],
) -> list[str]:
    insights: list[str] = []
    mus_cut_rate = float(behavior_summary.get("mus_cut_rate", 0.0) or 0.0)
    quiero_rate = float(behavior_summary.get("quiero_rate", 0.0) or 0.0)
    no_quiero_rate = float(behavior_summary.get("no_quiero_rate", 0.0) or 0.0)
    ordago_rate = float(behavior_summary.get("ordago_rate", 0.0) or 0.0)
    ordago_bad_context_rate = float(behavior_summary.get("ordago_bad_context_rate", 0.0) or 0.0)
    envite_rate = float(behavior_summary.get("envite_rate", 0.0) or 0.0)
    aggressive_envite_bad_context_rate = float(
        behavior_summary.get("aggressive_envite_bad_context_rate", 0.0) or 0.0
    )
    win_rate = float(metrics.get("win_rate", 0.0) or 0.0)
    score_diff = float(metrics.get("avg_score_diff", 0.0) or 0.0)

    if mus_cut_rate >= 0.7:
        insights.append("Corta mus con mucha frecuencia.")
    elif mus_cut_rate <= 0.3:
        insights.append("Suele pedir mus con bastante frecuencia.")

    if envite_rate >= 0.18:
        insights.append("Tiende a abrir o subir envites con bastante actividad.")
    elif envite_rate <= 0.05:
        insights.append("Apuesta poco y juega de forma conservadora.")

    if quiero_rate >= 0.65:
        insights.append("Acepta muchos envites cuando le responden.")
    elif no_quiero_rate >= 0.60:
        insights.append("Rechaza bastantes envites; posible sesgo conservador.")

    if ordago_rate >= 0.04:
        insights.append("Usa ordagos con relativa frecuencia.")
    if ordago_rate >= 0.04 and ordago_bad_context_rate >= 0.45:
        insights.append("Muchos ordagos llegan en contextos flojos; posible sobreuso.")
    elif ordago_rate > 0.0 and ordago_bad_context_rate <= 0.15:
        insights.append("Los ordagos parecen reservados a cierres o contextos fuertes.")

    if envite_rate >= 0.18 and aggressive_envite_bad_context_rate >= 0.40:
        insights.append("Muchos envites altos aparecen en contextos flojos; posible sobreapuesta.")
    elif envite_rate > 0.0 and aggressive_envite_bad_context_rate <= 0.15:
        insights.append("Los envites altos parecen mas reservados a contextos fuertes.")

    if win_rate >= 0.55 and score_diff > 0:
        insights.append("El estilo actual parece competitivo frente a este baseline.")
    elif win_rate < 0.5 and score_diff < 0:
        insights.append("El estilo actual esta perdiendo valor frente a este baseline.")

    return insights


def _policy_preferences(agent: RLAgent | None, *, limit: int = 8) -> list[dict[str, object]]:
    if agent is None or not agent.visit_counts:
        return []

    preferencias: list[dict[str, object]] = []
    for state, visits_by_action in agent.visit_counts.items():
        if not visits_by_action:
            continue
        total_visits = sum(visits_by_action.values())
        best_action = max(
            visits_by_action,
            key=lambda action: (
                visits_by_action[action],
                agent.policy.get(state, {}).get(action, float("-inf")),
                action,
            ),
        )
        preferencias.append(
            {
                "state": state,
                "action": best_action,
                "visits": total_visits,
                "value": float(agent.policy.get(state, {}).get(best_action, 0.0)),
            }
        )

    preferencias.sort(
        key=lambda entry: (
            int(entry["visits"]),
            float(entry["value"]),
            str(entry["action"]),
        ),
        reverse=True,
    )
    return preferencias[:limit]
