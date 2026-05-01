======================================================================
SSAAS EXPERIMENT ANALYSIS
======================================================================

# Summary: RMS Tracking Error (rad)

| Scenario | A_Weak_LQR | A_Strong_LQR | D_Full_SSAAS |
|---|---|---|---|
| 1_baseline | 0.0021±0.0013 | 0.0016±0.0010 | 0.0026±0.0013 |
| 2_wind | 0.0157±0.0009 | 0.0061±0.0004 | 0.0157±0.0011 |
| 3_drift | 0.0021±0.0013 | 0.0016±0.0010 | 0.0026±0.0013 |
| 4_sensor | 0.0021±0.0013 | 0.0016±0.0010 | 0.0026±0.0013 |
| 5_combined | 0.0160±0.0012 | 0.0062±0.0004 | 0.0163±0.0011 |
| 6_resource | 0.0106±0.0006 | 0.0043±0.0004 | 0.0107±0.0008 |
| 7_extreme_wind | 0.2060±0.1537 | 0.1725±0.1478 | 0.2145±0.1698 |
| 8_model_mismatch | 0.0026±0.0018 | 0.0017±0.0011 | 0.0028±0.0016 |
| 9_sensor_noise | 0.0073±0.0005 | 0.0074±0.0004 | 0.0075±0.0008 |
| A_adv_extreme_saturation | 0.4327±0.1138 | 0.3796±0.1315 | 0.4075±0.1019 |
| B_adv_delayed_control | 0.0022±0.0014 | 0.0017±0.0011 | 0.0028±0.0014 |
| C_adv_severe_mismatch | 0.1638±0.1792 | 0.0037±0.0009 | 0.0254±0.0084 |
| D_adv_sensor_corruption | 0.0201±0.0018 | 0.0219±0.0010 | 0.0202±0.0018 |
| E_adv_worst_case | 0.1440±0.1027 | 0.3030±0.0590 | 0.1533±0.1079 |

# Summary: Max Deviation (deg)

| Scenario | A_Weak_LQR | A_Strong_LQR | D_Full_SSAAS |
|---|---|---|---|
| 1_baseline | 1.1±0.8 | 1.1±0.8 | 1.4±0.8 |
| 2_wind | 2.8±0.3 | 1.4±0.5 | 2.8±0.3 |
| 3_drift | 1.1±0.8 | 1.1±0.8 | 1.4±0.8 |
| 4_sensor | 1.1±0.8 | 1.1±0.8 | 1.4±0.8 |
| 5_combined | 2.8±0.3 | 1.5±0.5 | 3.0±0.4 |
| 6_resource | 2.0±0.3 | 1.3±0.6 | 2.0±0.3 |
| 7_extreme_wind | 67.9±36.6 | 60.2±41.2 | 68.9±37.2 |
| 8_model_mismatch | 1.1±0.8 | 1.1±0.8 | 1.4±0.8 |
| 9_sensor_noise | 1.5±0.5 | 1.6±0.4 | 1.8±0.7 |
| A_adv_extreme_saturation | 92.3±1.3 | 92.3±1.2 | 92.5±1.8 |
| B_adv_delayed_control | 1.2±0.8 | 1.2±0.8 | 1.5±0.8 |
| C_adv_severe_mismatch | 33.5±39.5 | 1.8±0.5 | 4.9±1.0 |
| D_adv_sensor_corruption | 3.4±0.5 | 3.9±0.4 | 3.4±0.5 |
| E_adv_worst_case | 44.2±39.1 | 91.5±1.3 | 44.3±39.1 |

# Summary: Stability Violations (|θ| > π/6)

| Scenario | A_Weak_LQR | A_Strong_LQR | D_Full_SSAAS |
|---|---|---|---|
| 1_baseline | 0.0±0.0 | 0.0±0.0 | 0.0±0.0 |
| 2_wind | 0.0±0.0 | 0.0±0.0 | 0.0±0.0 |
| 3_drift | 0.0±0.0 | 0.0±0.0 | 0.0±0.0 |
| 4_sensor | 0.0±0.0 | 0.0±0.0 | 0.0±0.0 |
| 5_combined | 0.0±0.0 | 0.0±0.0 | 0.0±0.0 |
| 6_resource | 0.0±0.0 | 0.0±0.0 | 0.0±0.0 |
| 7_extreme_wind | 15.5±10.4 | 15.7±13.3 | 15.8±10.6 |
| 8_model_mismatch | 0.0±0.0 | 0.0±0.0 | 0.0±0.0 |
| 9_sensor_noise | 0.0±0.0 | 0.0±0.0 | 0.0±0.0 |
| A_adv_extreme_saturation | 20.5±2.9 | 18.8±3.1 | 20.0±2.3 |
| B_adv_delayed_control | 0.0±0.0 | 0.0±0.0 | 0.0±0.0 |
| C_adv_severe_mismatch | 4.0±6.1 | 0.0±0.0 | 0.0±0.0 |
| D_adv_sensor_corruption | 0.0±0.0 | 0.0±0.0 | 0.0±0.0 |
| E_adv_worst_case | 9.6±12.0 | 20.8±4.2 | 10.3±12.8 |

# Summary: Control Effort (N²)

| Scenario | A_Weak_LQR | A_Strong_LQR | D_Full_SSAAS |
|---|---|---|---|
| 1_baseline | 0.00±0.00 | 0.01±0.01 | 0.06±0.01 |
| 2_wind | 0.39±0.04 | 0.66±0.04 | 0.45±0.04 |
| 3_drift | 0.00±0.00 | 0.01±0.01 | 0.06±0.01 |
| 4_sensor | 0.00±0.00 | 0.01±0.01 | 0.06±0.01 |
| 5_combined | 0.38±0.03 | 0.64±0.04 | 0.44±0.04 |
| 6_resource | 0.18±0.02 | 0.30±0.02 | 0.23±0.02 |
| 7_extreme_wind | 148.06±247.98 | 941.72±1319.20 | 168.30±296.45 |
| 8_model_mismatch | 0.00±0.00 | 0.01±0.01 | 0.06±0.02 |
| 9_sensor_noise | 0.44±0.02 | 3.61±0.13 | 0.52±0.02 |
| A_adv_extreme_saturation | 499.33±283.13 | 2998.32±2459.25 | 441.59±273.41 |
| B_adv_delayed_control | 0.00±0.00 | 0.02±0.02 | 0.07±0.01 |
| C_adv_severe_mismatch | 235.99±352.31 | 4.03±0.02 | 4.51±0.34 |
| D_adv_sensor_corruption | 6.68±0.84 | 50.67±6.80 | 6.86±0.82 |
| E_adv_worst_case | 73.45±106.27 | 1829.47±943.55 | 80.49±104.93 |

# Summary: Recovery Time (s)

| Scenario | A_Weak_LQR | A_Strong_LQR | D_Full_SSAAS |
|---|---|---|---|
| 1_baseline | 0.22±0.25 | 0.19±0.16 | 0.88±0.37 |
| 2_wind | 0.22±0.25 | 0.19±0.16 | 15.30±14.69 |
| 3_drift | 0.22±0.25 | 0.19±0.16 | 0.88±0.37 |
| 4_sensor | 0.22±0.25 | 0.19±0.16 | 0.88±0.37 |
| 5_combined | 0.22±0.25 | 0.19±0.16 | 0.88±0.37 |
| 6_resource | 0.22±0.25 | 0.19±0.16 | 9.53±13.39 |
| 7_extreme_wind | 20.28±11.53 | 21.46±10.83 | 20.12±11.58 |
| 8_model_mismatch | 0.29±0.32 | 0.25±0.26 | 0.87±0.43 |
| 9_sensor_noise | 5.72±3.85 | 29.98±0.00 | 6.46±4.43 |
| A_adv_extreme_saturation | 3.22±1.78 | 4.24±2.27 | 3.42±1.48 |
| B_adv_delayed_control | 0.26±0.24 | 0.22±0.13 | 1.05±0.20 |
| C_adv_severe_mismatch | 17.47±10.30 | 0.85±0.23 | 14.26±5.00 |
| D_adv_sensor_corruption | 29.98±0.00 | 29.98±0.00 | 29.98±0.00 |
| E_adv_worst_case | 22.50±9.81 | 6.34±3.28 | 21.65±10.46 |

# Summary: Saturation Rate (%)

| Scenario | A_Weak_LQR | A_Strong_LQR | D_Full_SSAAS |
|---|---|---|---|
| 1_baseline | 0.0±0.0% | 0.0±0.0% | 0.0±0.0% |
| 2_wind | 0.0±0.0% | 0.0±0.0% | 0.0±0.0% |
| 3_drift | 0.0±0.0% | 0.0±0.0% | 0.0±0.0% |
| 4_sensor | 0.0±0.0% | 0.0±0.0% | 0.0±0.0% |
| 5_combined | 0.0±0.0% | 0.0±0.0% | 0.0±0.0% |
| 6_resource | 0.0±0.0% | 0.0±0.0% | 0.0±0.0% |
| 7_extreme_wind | 18.4±18.0% | 30.8±18.2% | 19.9±21.8% |
| 8_model_mismatch | 0.0±0.0% | 0.0±0.0% | 0.0±0.0% |
| 9_sensor_noise | 0.0±0.0% | 0.8±0.2% | 0.0±0.0% |
| A_adv_extreme_saturation | 56.6±15.9% | 67.4±9.5% | 57.5±12.8% |
| B_adv_delayed_control | 0.0±0.0% | 0.0±0.0% | 0.0±0.0% |
| C_adv_severe_mismatch | 20.8±31.2% | 0.0±0.0% | 0.4±0.4% |
| D_adv_sensor_corruption | 3.7±0.4% | 32.5±1.5% | 3.8±0.4% |
| E_adv_worst_case | 24.0±7.3% | 64.6±4.8% | 24.5±6.9% |

# Summary: NN Contribution (P95)

| Scenario | A_Weak_LQR | A_Strong_LQR | D_Full_SSAAS |
|---|---|---|---|
| 1_baseline | 0.00 | 0.00 | 1.82 |
| 2_wind | 0.00 | 0.00 | 0.00 |
| 3_drift | 0.00 | 0.00 | 1.82 |
| 4_sensor | 0.00 | 0.00 | 1.82 |
| 5_combined | 0.00 | 0.00 | 0.00 |
| 6_resource | 0.00 | 0.00 | 0.00 |
| 7_extreme_wind | 0.00 | 0.00 | 0.20 |
| 8_model_mismatch | 0.00 | 0.00 | 1.89 |
| 9_sensor_noise | 0.00 | 0.00 | 0.00 |
| A_adv_extreme_saturation | 0.00 | 0.00 | 0.75 |
| B_adv_delayed_control | 0.00 | 0.00 | 2.06 |
| C_adv_severe_mismatch | 0.00 | 0.00 | 0.00 |
| D_adv_sensor_corruption | 0.00 | 0.00 | 0.00 |
| E_adv_worst_case | 0.00 | 0.00 | 0.18 |

# Summary: Lyapunov Violation Rate

| Scenario | A_Weak_LQR | A_Strong_LQR | D_Full_SSAAS |
|---|---|---|---|
| 1_baseline | 0.00000% | 0.00000% | 0.00000% |
| 2_wind | 0.00000% | 0.00000% | 0.00000% |
| 3_drift | 0.00000% | 0.00000% | 0.00000% |
| 4_sensor | 0.00000% | 0.00000% | 0.00000% |
| 5_combined | 0.00000% | 0.00000% | 0.00000% |
| 6_resource | 0.00000% | 0.00000% | 0.00000% |
| 7_extreme_wind | 0.00000% | 0.00000% | 0.00000% |
| 8_model_mismatch | 0.00000% | 0.00000% | 0.00000% |
| 9_sensor_noise | 0.00000% | 0.00000% | 0.00000% |
| A_adv_extreme_saturation | 0.00000% | 0.00000% | 0.00000% |
| B_adv_delayed_control | 0.00000% | 0.00000% | 0.00000% |
| C_adv_severe_mismatch | 0.00000% | 0.00000% | 0.00000% |
| D_adv_sensor_corruption | 0.00000% | 0.00000% | 0.00000% |
| E_adv_worst_case | 0.00000% | 0.00000% | 0.00000% |

# Pareto Efficiency (Normalized Composite Cost J)
J = (RMS / RMS_weak) + 0.5 * (Effort / Effort_strong) [Lower is better]

| Scenario | A_Weak_LQR | A_Strong_LQR | D_Full_SSAAS |
|---|---|---|---|
| 1_baseline | 1.159 | 1.293 | 5.460 |
| 2_wind | 1.297 | 0.889 | 1.337 |
| 3_drift | 1.159 | 1.293 | 5.460 |
| 4_sensor | 1.159 | 1.293 | 5.460 |
| 5_combined | 1.302 | 0.890 | 1.366 |
| 6_resource | 1.295 | 0.905 | 1.390 |
| 7_extreme_wind | 1.079 | 1.337 | 1.131 |
| 8_model_mismatch | 1.281 | 1.141 | 4.673 |
| 9_sensor_noise | 1.061 | 1.506 | 1.097 |
| A_adv_extreme_saturation | 1.083 | 1.377 | 1.015 |
| B_adv_delayed_control | 1.074 | 1.301 | 2.856 |
| C_adv_severe_mismatch | 30.303 | 0.522 | 0.715 |
| D_adv_sensor_corruption | 1.066 | 1.587 | 1.073 |
| E_adv_worst_case | 1.020 | 2.604 | 1.086 |

# Fault Detection & Failure Mode Analysis (Full SSAAS)

| Scenario | Fault Count (mean) | Mode Transitions | Fallback % | Emergency % | Projection Active % | Conflict Count (mean) |
|---|---|---|---|---|---|---|
| 1_baseline | 1.0±0.0 | 4.2±0.6 | 5.0%±0.5% | 7.3%±2.0% | 1.8%±0.4% | 0.0±0.0 |
| 2_wind | 1.0±0.0 | 25.0±0.0 | 16.2%±0.1% | 80.0%±0.0% | 1.8%±0.4% | 0.0±0.0 |
| 3_drift | 1.0±0.0 | 4.2±0.6 | 5.0%±0.5% | 7.3%±2.0% | 1.8%±0.4% | 0.0±0.0 |
| 4_sensor | 1.0±0.0 | 4.2±0.6 | 5.0%±0.5% | 7.3%±2.0% | 1.8%±0.4% | 0.0±0.0 |
| 5_combined | 1.0±0.0 | 25.0±0.0 | 16.2%±0.1% | 80.0%±0.0% | 1.8%±0.4% | 0.0±0.0 |
| 6_resource | 1.0±0.0 | 25.0±0.0 | 16.2%±0.1% | 80.0%±0.0% | 1.8%±0.4% | 0.0±0.0 |
| 7_extreme_wind | 1.0±0.0 | 16.0±9.5 | 13.9%±3.8% | 71.5%±19.9% | 10.7%±22.0% | 5.4±12.4 |
| 8_model_mismatch | 1.0±0.0 | 4.0±0.0 | 4.8%±0.2% | 6.7%±0.0% | 1.8%±0.4% | 0.0±0.0 |
| 9_sensor_noise | 1.0±0.0 | 25.0±0.0 | 16.5%±0.0% | 80.0%±0.0% | 1.7%±0.3% | 0.0±0.0 |
| A_adv_extreme_saturation | 0.9±0.3 | 2.3±1.3 | 11.5%±4.2% | 53.2%±14.5% | 26.5%±17.3% | 15.0±9.8 |
| B_adv_delayed_control | 1.0±0.0 | 4.0±0.0 | 4.7%±0.1% | 6.7%±0.0% | 1.6%±0.2% | 0.0±0.0 |
| C_adv_severe_mismatch | 1.0±0.0 | 25.0±0.0 | 16.5%±0.0% | 80.0%±0.0% | 2.1%±0.4% | 0.0±0.0 |
| D_adv_sensor_corruption | 1.0±0.0 | 22.0±1.2 | 14.7%±0.8% | 81.9%±0.8% | 1.6%±0.2% | 1.3±1.1 |
| E_adv_worst_case | 1.0±0.0 | 17.2±8.9 | 15.1%±1.7% | 77.2%±5.4% | 4.2%±4.0% | 1.7±1.4 |

# Resource Depletion (Scenario 6)

| Config | Final Power | RMS Error | Max Deviation (deg) | Stability Violations |
|---|---|---|---|---|
| A_Weak_LQR | 1.00 | 0.0106±0.0006 | 2.0±0.3 | 0.0 |
| A_Strong_LQR | 1.00 | 0.0043±0.0004 | 1.3±0.6 | 0.0 |
| D_Full_SSAAS | 0.00 | 0.0107±0.0008 | 2.0±0.3 | 0.0 |