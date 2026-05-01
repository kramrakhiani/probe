from probe.probe_system import PROBESystem, SystemConfig
from probe.environment import DisturbanceConfig

system = PROBESystem(
    config=SystemConfig.full_probe(),
    disturbance=DisturbanceConfig(wind_enabled=True, wind_std=6.0, force_limit_override=3.0),
    seed=42,
    debug=False
)
system.run(duration=0.1, seed=42)

