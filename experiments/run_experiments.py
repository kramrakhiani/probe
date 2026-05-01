"""
Experiment Runner

Runs the full ablation study:
    4 configurations × 6 scenarios × 10 seeds = 240 experiments

Configurations:
    A: PID only
    B: PID + NN (unconstrained)
    C: PID + NN + Lyapunov
    D: Full PROBE

Scenarios:
    1: Baseline (no disturbance)
    2: Wind noise
    3: Parameter drift
    4: Sensor failure
    5: Combined (2+3+4)
    6: Resource depletion
"""

import json
import os
import sys
import time
import numpy as np

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from probe.environment import DisturbanceConfig, EnvironmentParams
from probe.probe_system import PROBESystem, SystemConfig


def get_configs() -> dict:
    # Define ablation configurations
    configs = {
        "A_Weak_LQR": SystemConfig.weak_lqr_only(),
        "A_Strong_LQR": SystemConfig.strong_lqr_only(),
        "D_Full_PROBE": SystemConfig.full_probe(enable_power_decay=True),
    }
    return configs


def get_scenarios() -> dict:
    """Return all disturbance scenarios."""
    return {
        "1_baseline": DisturbanceConfig(),
        "2_wind": DisturbanceConfig(wind_enabled=True, wind_std=1.5, wind_start_time=2.0),
        "3_drift": DisturbanceConfig(
            drift_enabled=True, drift_mass_factor=1.5,
            drift_start_time=3.0, drift_end_time=8.0,
        ),
        "4_sensor": DisturbanceConfig(
            sensor_failure_enabled=True,
            sensor_failure_time=5.0, sensor_failure_duration=0.5,
        ),
        "5_combined": DisturbanceConfig(
            wind_enabled=True, wind_std=1.5, wind_start_time=3.0,
            drift_enabled=True, drift_mass_factor=1.5,
            drift_start_time=3.0, drift_end_time=8.0,
            sensor_failure_enabled=True,
            sensor_failure_time=5.0, sensor_failure_duration=0.5,
        ),
        "6_resource": DisturbanceConfig(
            wind_enabled=True, wind_std=1.0, wind_start_time=2.0,
        ),
        "7_extreme_wind": DisturbanceConfig(wind_enabled=True, wind_start_time=0.0, wind_std=6.0),
        "8_model_mismatch": DisturbanceConfig(gravity_mismatch_factor=1.5),
        "9_sensor_noise": DisturbanceConfig(measurement_noise_std=0.02),
        "A_adv_extreme_saturation": DisturbanceConfig(
            wind_enabled=True, wind_start_time=0.0, wind_std=6.0,
            force_limit_override=3.0,
        ),
        "B_adv_delayed_control": DisturbanceConfig(actuator_delay_steps=2),
        "C_adv_severe_mismatch": DisturbanceConfig(
            gravity_mismatch_factor=2.0,
            constant_bias_force=2.0,
        ),
        "D_adv_sensor_corruption": DisturbanceConfig(
            measurement_noise_std=0.05,
            sensor_spike_prob=0.05,
            sensor_spike_magnitude=0.5,
        ),
        "E_adv_worst_case": DisturbanceConfig(
            actuator_delay_steps=2,
            force_limit_override=4.0,
            measurement_noise_std=0.05,
            wind_enabled=True, wind_std=4.0,
        ),
    }


def run_single_experiment(
    config: SystemConfig,
    disturbance: DisturbanceConfig,
    seed: int,
    duration: float = 10.0,
) -> dict:
    """
    Run a single experiment and return metrics + telemetry summary.

    Returns:
        dict with metrics and compact telemetry
    """
    system = PROBESystem(
        config=config,
        disturbance=disturbance,
        seed=seed,
    )

    telemetry = system.run(duration=duration, seed=seed)
    metrics = system.get_metrics()

    # Compact telemetry (subsample for storage)
    step_interval = max(1, len(telemetry) // 500)
    compact_telemetry = []
    for i, log in enumerate(telemetry):
        if i % step_interval == 0 or i == len(telemetry) - 1:
            compact_telemetry.append({
                "step": log.step,
                "time": log.time,
                "theta": float(log.true_state[2]),
                "theta_dot": float(log.true_state[3]),
                "x": float(log.true_state[0]),
                "u_total": log.u_total,
                "u_pid": log.u_pid,
                "u_nn_safe": log.u_nn_safe,
                "risk_score": log.risk_score,
                "mode": log.mode,
                "V": log.V,
                "V_dot": log.V_dot,
                "power_level": log.power_level,
                "tier": log.tier,
                "was_projected": log.was_projected,
                "loss": log.loss,
                "prediction_error": log.prediction_error,
            })

    return {
        "metrics": metrics,
        "telemetry": compact_telemetry,
        "fault_log": system.get_fault_log(),
    }


def run_all_experiments(
    n_seeds: int = 10,
    duration: float = 30.0,
    output_dir: str = "results",
) -> dict:
    """
    Run the full experiment matrix.

    Args:
        n_seeds: number of random seeds per (config, scenario)
        duration: simulation duration per run (seconds)
        output_dir: directory to save results

    Returns:
        dict of all results
    """
    configs = get_configs()
    scenarios = get_scenarios()
    seeds = list(range(42, 42 + n_seeds))

    total = len(configs) * len(scenarios) * n_seeds
    results = {}
    completed = 0

    print(f"Running {total} experiments ({len(configs)} configs × {len(scenarios)} scenarios × {n_seeds} seeds)")
    print("=" * 70)

    for config_name, config in configs.items():
        results[config_name] = {}

        for scenario_name, disturbance in scenarios.items():
            results[config_name][scenario_name] = []

            # Special handling for resource depletion scenario
            if scenario_name == "6_resource":
                if config_name == "D_Full_PROBE":
                    config_to_use = SystemConfig.full_probe(enable_power_decay=True)
                else:
                    config_to_use = config  # other configs don't use resource mgr
            else:
                config_to_use = config

            for seed in seeds:
                t0 = time.time()
                try:
                    result = run_single_experiment(
                        config_to_use, disturbance, seed, duration
                    )
                    result["seed"] = seed
                    result["status"] = "success"
                except Exception as e:
                    result = {
                        "seed": seed,
                        "status": "failed",
                        "error": str(e),
                        "metrics": {"terminated_early": True},
                        "telemetry": [],
                        "fault_log": [],
                    }

                elapsed = time.time() - t0
                completed += 1
                results[config_name][scenario_name].append(result)

                status = "✓" if result["status"] == "success" else "✗"
                print(
                    f"  [{completed:3d}/{total}] {status} {config_name:30s} | "
                    f"{scenario_name:15s} | seed={seed:3d} | {elapsed:.2f}s"
                )

    # Save results
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "experiment_results.json")

    # Convert to serializable format
    serializable = _make_serializable(results)
    with open(output_path, "w") as f:
        json.dump(serializable, f, indent=2)

    # Dump Configs
    config_dump = {
        name: {
            "r_lqr": conf.r_lqr,
            "use_nn": conf.use_nn,
            "use_stability_constraint": conf.use_stability_constraint,
            "alpha": 0.01,
            "lambda_eff": 1e-4,
            "nn_clamp": 1.5,
            "force_limit": 5.0,
        }
        for name, conf in configs.items()
    }
    with open(os.path.join(output_dir, "configs.json"), "w") as f:
        json.dump(config_dump, f, indent=2)

    print(f"\nResults saved to {output_path}")
    return results


def _make_serializable(obj):
    """Convert numpy types to Python types for JSON serialization."""
    if isinstance(obj, dict):
        return {k: _make_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_make_serializable(v) for v in obj]
    elif isinstance(obj, (np.integer,)):
        return int(obj)
    elif isinstance(obj, (np.floating,)):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, (np.bool_,)):
        return bool(obj)
    return obj


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run PROBE experiments")
    parser.add_argument("--seeds", type=int, default=10, help="Number of seeds per experiment")
    parser.add_argument("--duration", type=float, default=30.0, help="Simulation duration (s)")
    parser.add_argument("--output", type=str, default="results", help="Output directory")
    args = parser.parse_args()

    results = run_all_experiments(
        n_seeds=args.seeds,
        duration=args.duration,
        output_dir=args.output,
    )

    print("\n" + "=" * 70)
    print("QUICK SUMMARY")
    print("=" * 70)

    for config_name in results:
        print(f"\n{config_name}:")
        for scenario_name in results[config_name]:
            runs = results[config_name][scenario_name]
            successful = [r for r in runs if r["status"] == "success"]
            if successful:
                rms_errors = [r["metrics"]["rms_tracking_error"] for r in successful]
                max_devs = [r["metrics"]["max_deviation_deg"] for r in successful]
                print(
                    f"  {scenario_name:15s}: "
                    f"RMS={np.mean(rms_errors):.4f}±{np.std(rms_errors):.4f}  "
                    f"MaxDev={np.mean(max_devs):.4f}±{np.std(max_devs):.4f}  "
                    f"({len(successful)}/{len(runs)} succeeded)"
                )
            else:
                print(f"  {scenario_name:15s}: ALL FAILED")
