# Projection-Restricted Online Behavior Engine (PROBE)

A simulation-based autonomous control system demonstrating **adaptive intelligence that remains stable, self-aware, and resource-conscious under uncertainty**.

## Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│                        PROBE System                                  │
│                                                                      │
│  ┌─────────────┐    ┌──────────────┐    ┌───────────────────┐       │
│  │ Environment  │───▶│ Self-Monitor │───▶│  Fault Handler    │       │
│  │ (Inverted    │    │ (Uncertainty │    │  (NORMAL/FALLBACK │       │
│  │  Pendulum)   │    │  + Z-score)  │    │   /EMERGENCY)     │       │
│  └──────┬───────┘    └──────────────┘    └─────────┬─────────┘       │
│         │                                          │                 │
│         ▼                                          ▼                 │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────────┐       │
│  │ PID Controller│──▶│     (+)      │◀──│ Lyapunov         │       │
│  │ (Baseline)   │    │  u_pid+u_nn  │    │ Projection       │       │
│  └──────────────┘    └──────┬───────┘    │ (Stability       │       │
│                             │            │  Guarantee)       │       │
│  ┌──────────────┐           │            └────────┬─────────┘       │
│  │ Learning     │           │                     │                  │
│  │ Module       │───────────────────────────────▶│                  │
│  │ (Residual NN)│           │                                       │
│  └──────────────┘           ▼                                       │
│                    ┌──────────────┐                                  │
│                    │ Resource Mgr │                                  │
│                    │ (Power/      │                                  │
│                    │  Compute)    │                                  │
│                    └──────────────┘                                  │
└──────────────────────────────────────────────────────────────────────┘
```

## Key Features

- **Formal Stability Guarantees**: Lyapunov-based closed-form projection ensures NN output cannot violate stability
- **Runtime Invariants**: Real-time bounded assertions and debug traces mathematically prevent silent projection failures
- **Residual Dynamics Learning**: Online neural network learns unmodeled disturbances with actuator-aware bounds
- **Calibrated Self-Monitoring**: EMA prediction errors + distribution shift detection with hysteresis
- **Auditable Fault Handling**: State machine with transition table, dwell times, and full audit logs
- **Resource-Aware**: Simulated power/compute with neuron masking and frequency throttling

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run all stress-testing experiments (14 scenarios)
python experiments/run_experiments.py

# Generate analysis
python experiments/analysis.py

# Generate plots
python experiments/plotting.py
```

## Ablation Configurations

| Config | Description | R (Cost) | NN | Lyapunov | Monitor | Fault Handler |
|--------|-----|-----|----------|---------|---------------|-------------|
| A: Weak LQR | Energy-efficient but fragile baseline | 1.0 | ✗ | ✗ | ✗ | ✗ |
| B: Strong LQR | High-effort robust baseline | 0.01 | ✗ | ✗ | ✗ | ✗ |
| D: Full PROBE | Adaptive, efficient, self-monitoring | 1.0 | ✓ | ✓ | ✓ | ✓ |

## Disturbance Scenarios

1. **Baseline**: No disturbance
2. **Wind**: Gaussian force perturbation (σ=1.5 N)
3. **Parameter Drift**: Pole mass increases 50% over 5s
4. **Sensor Failure**: Angle sensor frozen for 0.5s
5. **Combined**: All disturbances simultaneously
6. **Resource Depletion**: Power decays to 0% over 20s
7. **Extreme Wind**: Massive Gaussian force perturbation (σ=6.0 N)
8. **Model Mismatch**: Mass parameters incorrect by 50% from initialization
9. **Sensor Noise**: Additive Gaussian noise on state sensors (σ=0.01)
10. **Adv_Extreme_Saturation**: Actuator limits reduced to 3.0N under 6.0N wind
11. **Adv_Delayed_Control**: 40ms control latency injection
12. **Adv_Severe_Mismatch**: Gravity doubled + constant +2.0N physical bias
13. **Adv_Sensor_Corruption**: Massive sensor spikes (+5.0 deviation)
14. **Adv_Worst_Case**: Combined delay, heavy noise, high wind, and saturation limits
## Mathematical Foundation

See [implementation_plan.md](implementation_plan.md) and [walkthrough.md](walkthrough.md) for detailed mathematical justification of:
- Lyapunov stability constraint derivation
- Closed-form admissible control bound with empty intersection handling
- Actuator-aware saturation limits during projection
- Bounded SGD update rule
- Calibrated uncertainty estimation
- Phi degeneracy mechanics (singular projection matrices)

## Limitations

1. **Local guarantees**: Stability based on linearization (valid within |θ| < 30°)
2. **Quadratic Lyapunov**: Conservative; nonlinear Lyapunov could extend operating region
3. **Single-step learning**: NN learns one-step residuals only
4. **Simplified resources**: Linear power decay model
