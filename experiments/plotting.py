"""
Plotting Module

Generates publication-quality plots comparing all configurations and scenarios.

Plots generated:
    1. State trajectories (θ over time) — all configs overlaid per scenario
    2. Control signals comparison
    3. Risk score timeline with mode annotations (Full PROBE)
    4. Resource usage over time
    5. Box plots for statistical comparison
    6. Lyapunov function evolution
"""

import json
import os
import sys
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.gridspec import GridSpec

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Style configuration
plt.rcParams.update({
    "figure.facecolor": "#0d1117",
    "axes.facecolor": "#161b22",
    "axes.edgecolor": "#30363d",
    "axes.labelcolor": "#c9d1d9",
    "text.color": "#c9d1d9",
    "xtick.color": "#8b949e",
    "ytick.color": "#8b949e",
    "grid.color": "#21262d",
    "grid.alpha": 0.8,
    "figure.dpi": 150,
    "font.family": "sans-serif",
    "font.size": 10,
    "axes.titlesize": 12,
    "axes.labelsize": 10,
})

# Color palette
COLORS = {
    "A_Weak_LQR": "#ff6b6b",
    "A_Strong_LQR": "#ffb86c",
    "B_PID_NN_unconstrained": "#ffd93d",
    "C_PID_NN_Lyapunov": "#6bcb77",
    "D_Full_PROBE": "#4d96ff",
}

MODE_COLORS = {
    "NORMAL": "#6bcb7744",
    "FALLBACK": "#ffd93d44",
    "EMERGENCY": "#ff6b6b44",
}


def load_results(path: str = "results/experiment_results.json") -> dict:
    """Load experiment results."""
    with open(path, "r") as f:
        return json.load(f)


def plot_theta_comparison(results: dict, output_dir: str = "results/plots"):
    """
    Plot θ trajectories for all configs, one subplot per scenario.
    Uses first seed for each config.
    """
    configs = list(results.keys())
    scenarios = list(results[configs[0]].keys())

    n_scenarios = len(scenarios)
    cols = 3
    rows = (n_scenarios + cols - 1) // cols

    fig, axes = plt.subplots(rows, cols, figsize=(18, 5 * rows))
    fig.suptitle("Pole Angle (θ) Over Time — All Configurations", fontsize=16, fontweight="bold")
    axes = axes.flatten()

    for idx, scenario in enumerate(scenarios):
        ax = axes[idx]
        ax.set_title(scenario.replace("_", " ").title(), fontsize=11)

        for config in configs:
            runs = results[config][scenario]
            if not runs or runs[0].get("status") != "success":
                continue
            telemetry = runs[0].get("telemetry", [])
            if not telemetry:
                continue

            times = [t["time"] for t in telemetry]
            thetas = [np.degrees(t["theta"]) for t in telemetry]
            ax.plot(times, thetas, color=COLORS[config], linewidth=1.2,
                    alpha=0.9, label=config.replace("_", " "))

        # Operating region bounds
        ax.axhline(y=30, color="#ff6b6b", linestyle="--", alpha=0.3, linewidth=0.8)
        ax.axhline(y=-30, color="#ff6b6b", linestyle="--", alpha=0.3, linewidth=0.8)

        ax.set_xlabel("Time (s)")
        ax.set_ylabel("θ (degrees)")
        ax.grid(True, alpha=0.3)
        ax.set_ylim(-50, 50)

    axes[0].legend(loc="upper right", fontsize=7, framealpha=0.7)
    plt.tight_layout()
    os.makedirs(output_dir, exist_ok=True)
    plt.savefig(os.path.join(output_dir, "theta_comparison.png"), bbox_inches="tight")
    plt.close()


def plot_control_signals(results: dict, output_dir: str = "results/plots"):
    """
    Plot control signals for selected scenarios.
    """
    configs = list(results.keys())
    scenarios = ["2_wind", "5_combined"]

    fig, axes = plt.subplots(len(scenarios), 1, figsize=(14, 8))
    fig.suptitle("Control Signals Comparison", fontsize=16, fontweight="bold")

    for idx, scenario in enumerate(scenarios):
        ax = axes[idx]
        ax.set_title(scenario.replace("_", " ").title(), fontsize=11)

        for config in configs:
            runs = results[config][scenario]
            if not runs or runs[0].get("status") != "success":
                continue
            telemetry = runs[0].get("telemetry", [])
            if not telemetry:
                continue

            times = [t["time"] for t in telemetry]
            controls = [t["u_total"] for t in telemetry]
            ax.plot(times, controls, color=COLORS[config], linewidth=0.8,
                    alpha=0.8, label=config.replace("_", " "))

        ax.set_xlabel("Time (s)")
        ax.set_ylabel("Control Force (N)")
        ax.grid(True, alpha=0.3)
        ax.legend(loc="upper right", fontsize=7, framealpha=0.7)

    plt.tight_layout()
    os.makedirs(output_dir, exist_ok=True)
    plt.savefig(os.path.join(output_dir, "control_signals.png"), bbox_inches="tight")
    plt.close()


def plot_probe_dashboard(results: dict, scenario: str = "5_combined",
                         output_dir: str = "results/plots"):
    """
    Detailed dashboard for Full PROBE under a specific scenario.
    Shows: θ, control, risk score, mode, V, power.
    """
    config = "D_Full_PROBE"
    runs = results.get(config, {}).get(scenario, [])
    if not runs or runs[0].get("status") != "success":
        print(f"No successful run for {config} / {scenario}")
        return

    telemetry = runs[0].get("telemetry", [])
    if not telemetry:
        return

    times = [t["time"] for t in telemetry]
    thetas = [np.degrees(t["theta"]) for t in telemetry]
    controls = [t["u_total"] for t in telemetry]
    u_pids = [t["u_pid"] for t in telemetry]
    u_nns = [t["u_nn_safe"] for t in telemetry]
    risks = [t["risk_score"] for t in telemetry]
    modes = [t["mode"] for t in telemetry]
    Vs = [t["V"] for t in telemetry]
    V_dots = [t["V_dot"] for t in telemetry]
    powers = [t["power_level"] for t in telemetry]
    pred_errors = [t["prediction_error"] for t in telemetry]

    fig = plt.figure(figsize=(16, 14))
    gs = GridSpec(5, 1, figure=fig, hspace=0.4)
    fig.suptitle(f"PROBE Dashboard — {scenario.replace('_', ' ').title()}",
                 fontsize=16, fontweight="bold")

    # 1. Theta
    ax1 = fig.add_subplot(gs[0])
    ax1.plot(times, thetas, color="#4d96ff", linewidth=1.2)
    ax1.axhline(y=30, color="#ff6b6b", linestyle="--", alpha=0.4, label="Operating bound")
    ax1.axhline(y=-30, color="#ff6b6b", linestyle="--", alpha=0.4)
    _shade_modes(ax1, times, modes)
    ax1.set_ylabel("θ (deg)")
    ax1.set_title("Pole Angle")
    ax1.legend(loc="upper right", fontsize=7)
    ax1.grid(True, alpha=0.3)

    # 2. Control
    ax2 = fig.add_subplot(gs[1])
    ax2.plot(times, u_pids, color="#ff6b6b", linewidth=0.8, alpha=0.7, label="PID")
    ax2.plot(times, u_nns, color="#6bcb77", linewidth=0.8, alpha=0.7, label="NN (safe)")
    ax2.plot(times, controls, color="#4d96ff", linewidth=1.0, alpha=0.9, label="Total")
    _shade_modes(ax2, times, modes)
    ax2.set_ylabel("Force (N)")
    ax2.set_title("Control Signals")
    ax2.legend(loc="upper right", fontsize=7)
    ax2.grid(True, alpha=0.3)

    # 3. Risk & Mode
    ax3 = fig.add_subplot(gs[2])
    ax3.plot(times, risks, color="#ffd93d", linewidth=1.0)
    ax3.axhline(y=0.7, color="#ff6b6b", linestyle="--", alpha=0.5, label="Rising threshold")
    ax3.axhline(y=0.3, color="#6bcb77", linestyle="--", alpha=0.5, label="Falling threshold")
    _shade_modes(ax3, times, modes)
    ax3.set_ylabel("Risk Score")
    ax3.set_title("Risk Score & Operating Mode")
    ax3.set_ylim(-0.05, 1.05)
    ax3.legend(loc="upper right", fontsize=7)
    ax3.grid(True, alpha=0.3)

    # 4. Lyapunov
    ax4 = fig.add_subplot(gs[3])
    ax4.plot(times, Vs, color="#4d96ff", linewidth=1.0, label="V(x)")
    ax4_twin = ax4.twinx()
    ax4_twin.plot(times, V_dots, color="#ff6b6b", linewidth=0.8, alpha=0.7, label="V̇(x)")
    ax4_twin.axhline(y=0, color="#ffd93d", linestyle="--", alpha=0.3)
    ax4.set_ylabel("V(x)", color="#4d96ff")
    ax4_twin.set_ylabel("V̇(x)", color="#ff6b6b")
    ax4.set_title("Lyapunov Function")
    ax4.grid(True, alpha=0.3)

    # 5. Resources
    ax5 = fig.add_subplot(gs[4])
    ax5.plot(times, powers, color="#6bcb77", linewidth=1.2)
    ax5.axhline(y=0.6, color="#4d96ff", linestyle=":", alpha=0.3, label="Full tier")
    ax5.axhline(y=0.3, color="#ffd93d", linestyle=":", alpha=0.3, label="Reduced tier")
    ax5.axhline(y=0.15, color="#ff6b6b", linestyle=":", alpha=0.3, label="Minimal tier")
    ax5.set_ylabel("Power Level")
    ax5.set_xlabel("Time (s)")
    ax5.set_title("Power & Resources")
    ax5.set_ylim(-0.05, 1.05)
    ax5.legend(loc="upper right", fontsize=7)
    ax5.grid(True, alpha=0.3)

    os.makedirs(output_dir, exist_ok=True)
    plt.savefig(os.path.join(output_dir, f"probe_dashboard_{scenario}.png"),
                bbox_inches="tight")
    plt.close()


def plot_boxplots(results: dict, output_dir: str = "results/plots"):
    """
    Box plots of RMS tracking error across seeds for each config/scenario.
    """
    configs = list(results.keys())
    scenarios = list(results[configs[0]].keys())

    n_scenarios = len(scenarios)
    cols = 3
    rows = (n_scenarios + cols - 1) // cols

    fig, axes = plt.subplots(rows, cols, figsize=(18, 5 * rows))
    fig.suptitle("RMS Tracking Error Distribution (10 seeds)", fontsize=16, fontweight="bold")
    axes = axes.flatten()

    for idx, scenario in enumerate(scenarios):
        ax = axes[idx]
        ax.set_title(scenario.replace("_", " ").title(), fontsize=11)

        data = []
        labels = []
        colors_list = []

        for config in configs:
            runs = results[config][scenario]
            successful = [r for r in runs if r.get("status") == "success"]
            if successful:
                vals = [r["metrics"]["rms_tracking_error"] for r in successful]
                data.append(vals)
                labels.append(config.split("_")[0])
                colors_list.append(COLORS[config])

        if data:
            bp = ax.boxplot(data, tick_labels=labels, patch_artist=True, widths=0.6)
            for patch, color in zip(bp["boxes"], colors_list):
                patch.set_facecolor(color + "44")
                patch.set_edgecolor(color)
            for element in ["whiskers", "caps", "medians"]:
                for item in bp[element]:
                    item.set_color("#8b949e")

        ax.set_ylabel("RMS Error (rad)")
        ax.grid(True, alpha=0.3, axis="y")

    # Hide unused subplots
    for i in range(len(scenarios), len(axes)):
        fig.delaxes(axes[i])

    plt.tight_layout()
    os.makedirs(output_dir, exist_ok=True)
    plt.savefig(os.path.join(output_dir, "boxplots.png"), bbox_inches="tight")
    plt.close()


def plot_lyapunov_comparison(results: dict, output_dir: str = "results/plots"):
    """
    Compare Lyapunov function V(x) between constrained and unconstrained NN.
    """
    scenarios = ["2_wind", "3_drift"]
    configs_to_compare = ["B_PID_NN_unconstrained", "C_PID_NN_Lyapunov", "D_Full_PROBE"]

    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    fig.suptitle("Lyapunov Function V(x) — Constrained vs Unconstrained",
                 fontsize=14, fontweight="bold")

    for idx, scenario in enumerate(scenarios):
        ax = axes[idx]
        ax.set_title(scenario.replace("_", " ").title())

        for config in configs_to_compare:
            runs = results.get(config, {}).get(scenario, [])
            if not runs or runs[0].get("status") != "success":
                continue
            telemetry = runs[0].get("telemetry", [])
            if not telemetry:
                continue

            times = [t["time"] for t in telemetry]
            Vs = [t["V"] for t in telemetry]
            ax.plot(times, Vs, color=COLORS[config], linewidth=1.0,
                    label=config.replace("_", " "), alpha=0.9)

        ax.set_xlabel("Time (s)")
        ax.set_ylabel("V(x)")
        ax.grid(True, alpha=0.3)
        ax.legend(fontsize=7)

    plt.tight_layout()
    os.makedirs(output_dir, exist_ok=True)
    plt.savefig(os.path.join(output_dir, "lyapunov_comparison.png"), bbox_inches="tight")
    plt.close()


def plot_recovery_times(results: dict, output_dir: str = "results/plots"):
    """
    Bar chart comparing recovery times across configs for selected scenarios.
    """
    configs = list(results.keys())
    scenarios = ["2_wind", "5_combined"]
    
    fig, ax = plt.subplots(figsize=(10, 6))
    fig.suptitle("Recovery Time Comparison", fontsize=14, fontweight="bold")
    
    x = np.arange(len(scenarios))
    width = 0.2
    
    for i, config in enumerate(configs):
        means = []
        stds = []
        for scenario in scenarios:
            runs = results.get(config, {}).get(scenario, [])
            successful = [r for r in runs if r.get("status") == "success"]
            if successful:
                vals = [r["metrics"].get("recovery_time", 0.0) for r in successful]
                means.append(np.mean(vals))
                stds.append(np.std(vals))
            else:
                means.append(0)
                stds.append(0)
                
        offset = (i - len(configs)/2 + 0.5) * width
        ax.bar(x + offset, means, width, yerr=stds, label=config.replace("_", " "), 
               color=COLORS[config], alpha=0.9, capsize=5)
               
    ax.set_ylabel("Recovery Time (s)")
    ax.set_xticks(x)
    ax.set_xticklabels([s.replace("_", " ").title() for s in scenarios])
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.3, axis="y")
    
    plt.tight_layout()
    os.makedirs(output_dir, exist_ok=True)
    plt.savefig(os.path.join(output_dir, "recovery_times.png"), bbox_inches="tight")
    plt.close()


from scipy.spatial import ConvexHull

def plot_pareto_efficiency(results: dict, output_dir: str = "results/plots"):
    """
    Scatter plot showing Control Effort vs RMS Tracking Error.
    Demonstrates Pareto efficiency with convex hulls.
    """
    configs = list(results.keys())
    scenarios = ["2_wind", "5_combined", "7_extreme_wind"]
    
    fig, axes = plt.subplots(1, len(scenarios), figsize=(15, 5))
    fig.suptitle("Pareto Efficiency: Control Effort vs Tracking Error", fontsize=14, fontweight="bold")
    
    for idx, scenario in enumerate(scenarios):
        ax = axes[idx]
        ax.set_title(scenario.replace("_", " ").title())
        
        all_points = []
        for config in configs:
            runs = results.get(config, {}).get(scenario, [])
            successful = [r for r in runs if r.get("status") == "success"]
            
            if not successful:
                continue
                
            efforts = [r["metrics"]["control_effort"] for r in successful]
            errors = [r["metrics"]["rms_tracking_error"] for r in successful]
            points = np.column_stack((efforts, errors))
            all_points.extend(points)
            
            color = COLORS.get(config, "#ffffff")
            ax.scatter(efforts, errors, color=color, alpha=0.7, s=50, label=config.replace("_", " "))
            
            # Per-config convex hull
            if len(points) >= 3:
                try:
                    hull = ConvexHull(points)
                    for simplex in hull.simplices:
                        ax.plot(points[simplex, 0], points[simplex, 1], color=color, alpha=0.5, linestyle="--")
                    ax.fill(points[hull.vertices, 0], points[hull.vertices, 1], color=color, alpha=0.1)
                except Exception:
                    pass
            
            # Mean star
            ax.scatter([np.mean(efforts)], [np.mean(errors)], color=color, marker="*", s=200, edgecolors="white", linewidth=1.0)
            
        # Global convex hull (Pareto frontier approximation)
        if len(all_points) >= 3:
            try:
                all_pts = np.array(all_points)
                hull = ConvexHull(all_pts)
                ax.plot(all_pts[hull.vertices, 0], all_pts[hull.vertices, 1], 'w-', linewidth=2, alpha=0.8, label="Global Frontier")
            except Exception:
                pass

        ax.set_xlabel("Control Effort (N²)")
        ax.set_ylabel("RMS Tracking Error (rad)")
        ax.grid(True, alpha=0.3)
        if idx == 0:
            ax.legend(fontsize=8)
            
    plt.tight_layout()
    os.makedirs(output_dir, exist_ok=True)
    plt.savefig(os.path.join(output_dir, "pareto_efficiency.png"), bbox_inches="tight")
    plt.close()


def _shade_modes(ax, times, modes):
    """Shade background by operating mode."""
    if not times or not modes:
        return

    # Find mode transitions
    current_mode = modes[0]
    start_time = times[0]

    for i in range(1, len(times)):
        if modes[i] != current_mode or i == len(times) - 1:
            end_time = times[i]
            color = MODE_COLORS.get(current_mode, "#ffffff00")
            ax.axvspan(start_time, end_time, facecolor=color, alpha=1.0)
            current_mode = modes[i]
            start_time = end_time


def generate_all_plots(results_path: str = "results/experiment_results.json",
                       output_dir: str = "results/plots"):
    """Generate all plots."""
    results = load_results(results_path)

    print("Generating plots...")

    print("  1/5 Theta comparison...")
    plot_theta_comparison(results, output_dir)

    print("  2/5 Control signals...")
    plot_control_signals(results, output_dir)

    print("  3/5 PROBE dashboards...")
    for scenario in ["5_combined", "2_wind", "4_sensor"]:
        plot_probe_dashboard(results, scenario, output_dir)

    print("  4/5 Box plots...")
    plot_boxplots(results, output_dir)

    print("  5/6 Lyapunov comparison...")
    plot_lyapunov_comparison(results, output_dir)

    print("  6/7 Recovery times...")
    plot_recovery_times(results, output_dir)

    print("  7/7 Pareto efficiency...")
    plot_pareto_efficiency(results, output_dir)

    print(f"\nAll plots saved to {output_dir}/")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Generate PROBE experiment plots")
    parser.add_argument("--results", type=str, default="results/experiment_results.json")
    parser.add_argument("--output", type=str, default="results/plots")
    args = parser.parse_args()

    generate_all_plots(args.results, args.output)
