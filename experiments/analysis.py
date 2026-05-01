"""
Statistical Analysis Module

Computes summary statistics, comparison tables, and fault detection metrics
from experiment results.

Outputs markdown-formatted tables for the walkthrough document.
"""

import json
import os
import sys
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def load_results(results_path: str = "results/experiment_results.json") -> dict:
    """Load experiment results from JSON."""
    with open(results_path, "r") as f:
        return json.load(f)


def compute_summary_table(results: dict) -> str:
    """
    Compute mean ± std for key metrics across all configs and scenarios.

    Returns:
        Markdown-formatted table string
    """
    configs = list(results.keys())
    scenarios = list(results[configs[0]].keys())

    lines = []
    lines.append("# Summary: RMS Tracking Error (rad)")
    lines.append("")
    header = "| Scenario | " + " | ".join(configs) + " |"
    sep = "|" + "---|" * (len(configs) + 1)
    lines.append(header)
    lines.append(sep)

    for scenario in scenarios:
        row = f"| {scenario} |"
        for config in configs:
            runs = results[config][scenario]
            successful = [r for r in runs if r.get("status") == "success"]
            if successful:
                vals = [r["metrics"]["rms_tracking_error"] for r in successful]
                mean_val = np.mean(vals)
                std_val = np.std(vals)
                row += f" {mean_val:.4f}±{std_val:.4f} |"
            else:
                row += " FAILED |"
        lines.append(row)

    lines.append("")
    lines.append("# Summary: Max Deviation (deg)")
    lines.append("")
    header = "| Scenario | " + " | ".join(configs) + " |"
    lines.append(header)
    lines.append(sep)

    for scenario in scenarios:
        row = f"| {scenario} |"
        for config in configs:
            runs = results[config][scenario]
            successful = [r for r in runs if r.get("status") == "success"]
            if successful:
                vals = [r["metrics"]["max_deviation_deg"] for r in successful]
                mean_val = np.mean(vals)
                std_val = np.std(vals)
                row += f" {mean_val:.1f}±{std_val:.1f} |"
            else:
                row += " FAILED |"
        lines.append(row)

    lines.append("")
    lines.append("# Summary: Stability Violations (|θ| > π/6)")
    lines.append("")
    header = "| Scenario | " + " | ".join(configs) + " |"
    lines.append(header)
    lines.append(sep)

    for scenario in scenarios:
        row = f"| {scenario} |"
        for config in configs:
            runs = results[config][scenario]
            successful = [r for r in runs if r.get("status") == "success"]
            if successful:
                vals = [r["metrics"]["stability_violations"] for r in successful]
                mean_val = np.mean(vals)
                std_val = np.std(vals)
                row += f" {mean_val:.1f}±{std_val:.1f} |"
            else:
                row += " FAILED |"
        lines.append(row)

    lines.append("")
    lines.append("# Summary: Control Effort (N²)")
    lines.append("")
    header = "| Scenario | " + " | ".join(configs) + " |"
    lines.append(header)
    lines.append(sep)

    for scenario in scenarios:
        row = f"| {scenario} |"
        for config in configs:
            runs = results[config][scenario]
            successful = [r for r in runs if r.get("status") == "success"]
            if successful:
                vals = [r["metrics"]["control_effort"] for r in successful]
                mean_val = np.mean(vals)
                std_val = np.std(vals)
                row += f" {mean_val:.2f}±{std_val:.2f} |"
            else:
                row += " FAILED |"
        lines.append(row)

    lines.append("")
    lines.append("# Summary: Recovery Time (s)")
    lines.append("")
    header = "| Scenario | " + " | ".join(configs) + " |"
    lines.append(header)
    lines.append(sep)

    for scenario in scenarios:
        row = f"| {scenario} |"
        for config in configs:
            runs = results[config][scenario]
            successful = [r for r in runs if r.get("status") == "success"]
            if successful:
                vals = [r["metrics"].get("recovery_time", 0.0) for r in successful]
                mean_val = np.mean(vals)
                std_val = np.std(vals)
                row += f" {mean_val:.2f}±{std_val:.2f} |"
            else:
                row += " FAILED |"
        lines.append(row)

    lines.append("")
    lines.append("# Summary: Saturation Rate (%)")
    lines.append("")
    header = "| Scenario | " + " | ".join(configs) + " |"
    lines.append(header)
    lines.append(sep)

    for scenario in scenarios:
        row = f"| {scenario} |"
        for config in configs:
            runs = results[config][scenario]
            successful = [r for r in runs if r.get("status") == "success"]
            if successful:
                vals = [r["metrics"].get("saturation_rate", 0.0) * 100 for r in successful]
                mean_val = np.mean(vals)
                std_val = np.std(vals)
                row += f" {mean_val:.1f}±{std_val:.1f}% |"
            else:
                row += " FAILED |"
        lines.append(row)

    lines.append("")
    lines.append("# Summary: NN Contribution (P95)")
    lines.append("")
    lines.append(header)
    lines.append(sep)

    for scenario in scenarios:
        row = f"| {scenario} |"
        for config in configs:
            if config in ["A_Weak_LQR", "A_Strong_LQR"]:
                row += " 0.00 |"
                continue
            runs = results[config][scenario]
            successful = [r for r in runs if r.get("status") == "success"]
            if successful:
                vals = [r["metrics"].get("nn_contribution_p95", 0.0) for r in successful]
                mean_val = np.mean(vals)
                row += f" {mean_val:.2f} |"
            else:
                row += " FAILED |"
        lines.append(row)

    lines.append("")
    lines.append("# Summary: Lyapunov Violation Rate")
    lines.append("")
    lines.append(header)
    lines.append(sep)

    for scenario in scenarios:
        row = f"| {scenario} |"
        for config in configs:
            runs = results[config][scenario]
            successful = [r for r in runs if r.get("status") == "success"]
            if successful:
                vals = [r["metrics"].get("lyapunov_violation_rate", 0.0) * 100 for r in successful]
                mean_val = np.mean(vals)
                row += f" {mean_val:.5f}% |"
            else:
                row += " FAILED |"
        lines.append(row)

    return "\n".join(lines)


def compute_adaptation_gain(results: dict) -> str:
    """
    Compute adaptation gain of PROBE over PID-only.

    gain = (RMS_pid - RMS_probe) / RMS_pid × 100%

    Returns:
    Compute Pareto efficiency of configs.

    J = (RMS / RMS_weak) + 0.5 * (Effort / Effort_strong) [Lower is better]

    Returns:
        Markdown table
    """
    configs = list(results.keys())
    scenarios = list(results[configs[0]].keys())

    lines = []
    lines.append("# Pareto Efficiency (Normalized Composite Cost J)")
    lines.append("J = (RMS / RMS_weak) + 0.5 * (Effort / Effort_strong) [Lower is better]")
    lines.append("")
    
    if "A_Weak_LQR" not in configs or "A_Strong_LQR" not in configs:
        return "\n".join(lines)
        
    header = "| Scenario | " + " | ".join(configs) + " |"
    sep = "|" + "---|" * (len(configs) + 1)
    lines.append(header)
    lines.append(sep)

    for scenario in scenarios:
        weak_runs = [r for r in results["A_Weak_LQR"][scenario] if r.get("status") == "success"]
        strong_runs = [r for r in results["A_Strong_LQR"][scenario] if r.get("status") == "success"]
        
        if not weak_runs or not strong_runs:
            continue
            
        weak_rms = np.mean([r["metrics"]["rms_tracking_error"] for r in weak_runs])
        strong_effort = np.mean([r["metrics"]["control_effort"] for r in strong_runs])
        
        if weak_rms < 1e-8 or strong_effort < 1e-8:
            continue

        row = f"| {scenario} |"
        for config in configs:
            runs = results[config][scenario]
            successful = [r for r in runs if r.get("status") == "success"]
            if successful:
                rms = np.mean([r["metrics"]["rms_tracking_error"] for r in successful])
                effort = np.mean([r["metrics"]["control_effort"] for r in successful])
                
                # J = normalized error + 0.5 * normalized effort
                j_score = (rms / weak_rms) + 0.5 * (effort / strong_effort)
                row += f" {j_score:.3f} |"
            else:
                row += " N/A |"
        lines.append(row)

    return "\n".join(lines)


def compute_fault_detection_metrics(results: dict) -> str:
    """
    Compute fault detection precision, recall, and latency
    for the Full PROBE config under fault scenarios.

    Returns:
        Markdown table
    """
    lines = []
    lines.append("# Fault Detection & Failure Mode Analysis (Full PROBE)")
    lines.append("")
    lines.append("| Scenario | Fault Count (mean) | Mode Transitions | Fallback % | Emergency % | Projection Active % | Conflict Count (mean) |")
    lines.append("|---|---|---|---|---|---|---|")

    config = "D_Full_PROBE"
    configs = list(results.keys())
    if not configs:
        return ""
    scenarios = list(results[configs[0]].keys())

    for scenario in scenarios:
        if config not in results or scenario not in results[config]:
            continue
        runs = results[config][scenario]
        successful = [r for r in runs if r.get("status") == "success"]
        if not successful:
            continue

        fault_counts = [r["metrics"].get("fault_count", 0) for r in successful]
        transitions = [r["metrics"].get("transitions", 0) for r in successful]
        fallback_pcts = [r["metrics"].get("fallback_fraction", 0) * 100 for r in successful]
        emergency_pcts = [r["metrics"].get("emergency_fraction", 0) * 100 for r in successful]
        projection_pcts = [r["metrics"].get("projection_active_rate", 0) * 100 for r in successful]
        conflict_counts = [r["metrics"].get("conflict_count", 0) for r in successful]

        lines.append(
            f"| {scenario} | "
            f"{np.mean(fault_counts):.1f}±{np.std(fault_counts):.1f} | "
            f"{np.mean(transitions):.1f}±{np.std(transitions):.1f} | "
            f"{np.mean(fallback_pcts):.1f}%±{np.std(fallback_pcts):.1f}% | "
            f"{np.mean(emergency_pcts):.1f}%±{np.std(emergency_pcts):.1f}% | "
            f"{np.mean(projection_pcts):.1f}%±{np.std(projection_pcts):.1f}% | "
            f"{np.mean(conflict_counts):.1f}±{np.std(conflict_counts):.1f} |"
        )

    return "\n".join(lines)


def compute_resource_metrics(results: dict) -> str:
    """
    Compute resource depletion experiment metrics.

    Returns:
        Markdown table
    """
    lines = []
    lines.append("# Resource Depletion (Scenario 6)")
    lines.append("")
    lines.append("| Config | Final Power | RMS Error | Max Deviation (deg) | Stability Violations |")
    lines.append("|---|---|---|---|---|")

    for config in results:
        if "6_resource" not in results[config]:
            continue
        runs = results[config]["6_resource"]
        successful = [r for r in runs if r.get("status") == "success"]
        if not successful:
            continue

        powers = [r["metrics"].get("final_power", 1.0) for r in successful]
        rms = [r["metrics"]["rms_tracking_error"] for r in successful]
        max_devs = [r["metrics"]["max_deviation_deg"] for r in successful]
        violations = [r["metrics"]["stability_violations"] for r in successful]

        lines.append(
            f"| {config} | "
            f"{np.mean(powers):.2f} | "
            f"{np.mean(rms):.4f}±{np.std(rms):.4f} | "
            f"{np.mean(max_devs):.1f}±{np.std(max_devs):.1f} | "
            f"{np.mean(violations):.1f} |"
        )

    return "\n".join(lines)


def generate_full_analysis(results_path: str = "results/experiment_results.json") -> str:
    """Generate complete analysis report."""
    results = load_results(results_path)

    sections = [
        "=" * 70,
        "PROBE EXPERIMENT ANALYSIS",
        "=" * 70,
        "",
        compute_summary_table(results),
        "",
        compute_adaptation_gain(results),
        "",
        compute_fault_detection_metrics(results),
        "",
        compute_resource_metrics(results),
    ]

    return "\n".join(sections)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Analyze PROBE experiment results")
    parser.add_argument(
        "--results", type=str, default="results/experiment_results.json",
        help="Path to experiment results JSON"
    )
    parser.add_argument(
        "--output", type=str, default="results/analysis.md",
        help="Output path for analysis report"
    )
    args = parser.parse_args()

    report = generate_full_analysis(args.results)
    print(report)

    # Save to file
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    with open(args.output, "w") as f:
        f.write(report)
    print(f"\nAnalysis saved to {args.output}")
