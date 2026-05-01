"""Inverted Pendulum Environment"""

import numpy as np 
from dataclasses import dataclass ,field 
from typing import Optional 

@dataclass 
class DisturbanceConfig :
    """Configuration for environment disturbances."""

    wind_enabled :bool =False 
    wind_std :float =4.0 
    wind_start_time :float =2.0 

    # Parameter drift
    drift_enabled :bool =False 
    drift_mass_factor :float =1.5 
    drift_start_time :float =2.0 
    drift_end_time :float =5.0 

    sensor_failure_enabled :bool =False 
    sensor_failure_time :float =5.0 
    sensor_failure_duration :float =1.0 

    gravity_mismatch_factor :float =1.0 # Multiplier for gravity

    # Sensor Noise and Corruption
    measurement_noise_std :float =0.0 
    sensor_spike_prob :float =0.0 # Probability of a massive sensor spike per step
    sensor_spike_magnitude :float =0.0 # Magnitude of the sensor spike

    actuator_delay_steps :int =0 # Number of timesteps to delay control force
    force_limit_override :Optional [float ]=None 
    constant_bias_force :float =0.0 # Constant disturbance force applied to the cart

@dataclass 
class EnvironmentParams :
    """Physical parameters of the inverted pendulum."""
    cart_mass :float =1.0 
    pole_mass :float =0.1 
    pole_half_length :float =0.5 
    gravity :float =9.81 
    dt :float =0.02 # s, time step
    force_limit :float =5.0 

class InvertedPendulum :
    """Nonlinear inverted pendulum on a cart."""

    def __init__ (
    self ,
    params :Optional [EnvironmentParams ]=None ,
    disturbance :Optional [DisturbanceConfig ]=None ,
    seed :int =42 ,
    ):
        self .params =params or EnvironmentParams ()
        self .disturbance =disturbance or DisturbanceConfig ()
        self .rng =np .random .default_rng (seed )

        self .active_force_limit =self .params .force_limit 
        if getattr (self .disturbance ,"force_limit_override",None )is not None :
            self .active_force_limit =self .disturbance .force_limit_override 

        self ._u_buffer =[]

        self .state =np .zeros (4 )
        self .time =0.0 
        self .step_count =0 

        self ._frozen_theta =None 
        self ._sensor_failed =False 

        # Current effective pole mass (may drift)
        self ._effective_pole_mass =self .params .pole_mass 

        # Operating region bounds
        self .operating_bounds =np .array ([2.0 ,2.0 ,np .pi /6 ,2.0 ])

    def reset (self ,initial_state :Optional [np .ndarray ]=None )->np .ndarray :
        """Reset environment. Default: small random perturbation from upright."""
        if initial_state is not None :
            self .state =initial_state .copy ()
        else :
            self .state =self .rng .uniform (-0.05 ,0.05 ,size =4 )
        self .time =0.0 
        self .step_count =0 
        self ._effective_pole_mass =self .params .pole_mass 
        self ._frozen_theta =None 
        self ._sensor_failed =False 

        self .active_force_limit =self .params .force_limit 
        if getattr (self .disturbance ,"force_limit_override",None )is not None :
            self .active_force_limit =self .disturbance .force_limit_override 
        self ._u_buffer =[]

        return self .get_observation ()

    def _dynamics (self ,state :np .ndarray ,force :float ,pole_mass :float )->np .ndarray :
        """Compute state derivatives for the nonlinear pendulum."""
        p =self .params 
        M =p .cart_mass 
        m =pole_mass 
        l =p .pole_half_length 
        g =p .gravity *self .disturbance .gravity_mismatch_factor 

        x ,x_dot ,theta ,theta_dot =state 
        sin_t =np .sin (theta )
        cos_t =np .cos (theta )

        total_mass =M +m 
        temp =(force +m *l *theta_dot **2 *sin_t )/total_mass 
        theta_ddot =(g *sin_t -cos_t *temp )/(
        l *(4.0 /3.0 -m *cos_t **2 /total_mass )
        )
        x_ddot =temp -m *l *theta_ddot *cos_t /total_mass 

        return np .array ([x_dot ,x_ddot ,theta_dot ,theta_ddot ])

    def _rk4_step (self ,state :np .ndarray ,force :float ,pole_mass :float )->np .ndarray :
        """4th-order Runge-Kutta integration step."""
        dt =self .params .dt 
        k1 =self ._dynamics (state ,force ,pole_mass )
        k2 =self ._dynamics (state +0.5 *dt *k1 ,force ,pole_mass )
        k3 =self ._dynamics (state +0.5 *dt *k2 ,force ,pole_mass )
        k4 =self ._dynamics (state +dt *k3 ,force ,pole_mass )
        return state +(dt /6.0 )*(k1 +2 *k2 +2 *k3 +k4 )

    def _apply_disturbances (self ,force :float )->float :
        """Apply active disturbances and return modified force."""
        d =self .disturbance 
        t =self .time 

        force +=getattr (d ,"constant_bias_force",0.0 )

        if d .wind_enabled and t >=d .wind_start_time :
            force +=self .rng .normal (0 ,d .wind_std )

            # Parameter drift
        if d .drift_enabled :
            if d .drift_start_time <=t <=d .drift_end_time :
                progress =(t -d .drift_start_time )/(d .drift_end_time -d .drift_start_time )
                self ._effective_pole_mass =self .params .pole_mass *(
                1.0 +(d .drift_mass_factor -1.0 )*progress 
                )
            elif t >d .drift_end_time :
                self ._effective_pole_mass =self .params .pole_mass *d .drift_mass_factor 

        if d .sensor_failure_enabled :
            fail_start =d .sensor_failure_time 
            fail_end =fail_start +d .sensor_failure_duration 
            if fail_start <=t <fail_end :
                if not self ._sensor_failed :
                    self ._frozen_theta =self .state [2 ]
                    self ._sensor_failed =True 
            else :
                self ._sensor_failed =False 
                self ._frozen_theta =None 

        return force 

    def get_observation (self )->np .ndarray :
        """Get the observed state (may differ from true state under sensor failure)."""
        obs =self .state .copy ()

        if self .disturbance .measurement_noise_std >0 :
            obs +=self .rng .normal (0 ,self .disturbance .measurement_noise_std ,size =4 )

        if self ._sensor_failed and self ._frozen_theta is not None :
            obs [2 ]=self ._frozen_theta 

        if getattr (self .disturbance ,"sensor_spike_prob",0.0 )>0.0 :
            if self .rng .random ()<self .disturbance .sensor_spike_prob :
                spike =(self .rng .random (4 )*2 -1 )*self .disturbance .sensor_spike_magnitude 
                obs +=spike 

        return obs 

    def get_true_state (self )->np .ndarray :
        """Get the true state (unaffected by sensor failure)."""
        return self .state .copy ()

    def is_in_operating_region (self )->bool :
        """Check if state is within the linearized stability guarantee region."""
        return np .all (np .abs (self .state )<self .operating_bounds )

    def is_terminal (self )->bool :
        """Check if pendulum has fallen beyond recovery (|theta| > pi/2)."""
        return abs (self .state [2 ])>np .pi /2 

    def step (self ,force :float )->dict :
        """Advance simulation by one timestep."""

        self ._u_buffer .append (force )
        delay_steps =getattr (self .disturbance ,"actuator_delay_steps",0 )
        if len (self ._u_buffer )>delay_steps :
            u_delayed =self ._u_buffer .pop (0 )
        else :
            u_delayed =0.0 # No force applied yet

            # Clamp force
        u_applied =np .clip (u_delayed ,-self .active_force_limit ,self .active_force_limit )

        # Apply disturbances
        effective_force =self ._apply_disturbances (u_applied )

        self .state =self ._rk4_step (self .state ,effective_force ,self ._effective_pole_mass )
        self .time +=self .params .dt 
        self .step_count +=1 

        # Reward: negative of angle squared (encourage upright)
        theta =self .state [2 ]
        reward =-(theta **2 +0.01 *self .state [0 ]**2 +0.001 *force **2 )

        done =self .is_terminal ()
        in_region =self .is_in_operating_region ()

        return {
        "observation":self .get_observation (),
        "true_state":self .get_true_state (),
        "reward":reward ,
        "done":done ,
        "in_operating_region":in_region ,
        "time":self .time ,
        "effective_mass":self ._effective_pole_mass ,
        "u_applied":u_applied ,
        }

    def get_linearized_system (self )->tuple :
        """Return (A, B) matrices of the linearized system around upright equilibrium."""
        p =self .params 
        M =p .cart_mass 
        m =p .pole_mass 
        l =p .pole_half_length 
        g =p .gravity 

        total_mass =M +m 
        denom =l *(4.0 /3.0 -m /total_mass )

        A =np .array ([
        [0 ,1 ,0 ,0 ],
        [0 ,0 ,-m *g /total_mass ,0 ],
        [0 ,0 ,0 ,1 ],
        [0 ,0 ,g /denom ,0 ],
        ])

        B =np .array ([
        [0 ],
        [1.0 /total_mass ],
        [0 ],
        [-1.0 /(total_mass *denom )],
        ])

        return A ,B 

    def get_nominal_next_state (self ,state :np .ndarray ,force :float )->np .ndarray :
        """Compute predicted next state using nominal model (no disturbances)."""
        return self ._rk4_step (state ,force ,self .params .pole_mass )
