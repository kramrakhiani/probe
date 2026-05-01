"""PROBE System — Main Orchestrator"""

import numpy as np 
from dataclasses import dataclass ,field 
from typing import Optional 

from .environment import InvertedPendulum ,DisturbanceConfig ,EnvironmentParams 
from .pid_controller import PIDController 
from .learning_module import ResidualLearner 
from .stability_layer import LyapunovProjection 
from .self_monitor import SelfMonitor 
from .fault_handler import FaultHandler ,Mode 
from .resource_manager import ResourceManager 

@dataclass 
class SystemConfig :
    """Configuration for which modules are active (ablation support)."""
    use_nn :bool =True 
    use_stability_constraint :bool =True 
    use_monitor :bool =True 
    use_fault_handler :bool =True 
    use_resource_manager :bool =True 
    enable_power_decay :bool =False # Only for resource depletion scenario
    r_lqr :float =1.0 # Base controller effort penalty

    @classmethod 
    def weak_lqr_only (cls ):
        """Config A1: Weak PID only (lazy baseline)."""
        return cls (
        use_nn =False ,use_stability_constraint =False ,
        use_monitor =False ,use_fault_handler =False ,
        use_resource_manager =False ,
        r_lqr =1.0 ,
        )

    @classmethod 
    def strong_lqr_only (cls ):
        """Config A2: Strong PID only (aggressive baseline)."""
        return cls (
        use_nn =False ,use_stability_constraint =False ,
        use_monitor =False ,use_fault_handler =False ,
        use_resource_manager =False ,
        r_lqr =0.01 ,
        )

    @classmethod 
    def pid_only (cls ):
    # Legacy mapping, redirecting to weak LQR
        return cls .weak_lqr_only ()

    @classmethod 
    def pid_nn_unconstrained (cls ):
        """Config B: PID + NN, no stability constraint."""
        return cls (
        use_nn =True ,use_stability_constraint =False ,
        use_monitor =False ,use_fault_handler =False ,
        use_resource_manager =False ,
        r_lqr =1.0 ,
        )

    @classmethod 
    def pid_nn_lyapunov (cls ):
        """Config C: PID + NN + Lyapunov constraint."""
        return cls (
        use_nn =True ,use_stability_constraint =True ,
        use_monitor =False ,use_fault_handler =False ,
        use_resource_manager =False ,
        r_lqr =1.0 ,
        )

    @classmethod 
    def full_probe (cls ,enable_power_decay :bool =False ):
        """Config D: Full PROBE."""
        return cls (
        use_nn =True ,use_stability_constraint =True ,
        use_monitor =True ,use_fault_handler =True ,
        use_resource_manager =True ,
        enable_power_decay =enable_power_decay ,
        r_lqr =1.0 ,
        )

@dataclass 
class StepLog :
    """Telemetry for a single simulation step."""
    step :int =0 
    time :float =0.0 

    state :np .ndarray =field (default_factory =lambda :np .zeros (4 ))
    true_state :np .ndarray =field (default_factory =lambda :np .zeros (4 ))
    observation :np .ndarray =field (default_factory =lambda :np .zeros (4 ))

    u_pid :float =0.0 
    u_nn_candidate :float =0.0 
    u_nn_safe :float =0.0 
    u_total :float =0.0 

    V :float =0.0 
    V_dot :float =0.0 
    was_projected :bool =False 
    conflict :bool =False 
    phi_raw :float =0.0 
    phi_clamped :float =0.0 
    psi :float =0.0 
    projection_degenerate :bool =False 
    lyap_min :float =0.0 
    lyap_max :float =0.0 
    phys_min :float =0.0 
    phys_max :float =0.0 
    u_applied :float =0.0 

    risk_score :float =0.0 
    risk_pred :float =0.0 
    risk_shift :float =0.0 
    risk_lyap :float =0.0 
    prediction_error :float =0.0 

    mode :str ="NORMAL"

    power_level :float =1.0 
    tier :str ="full"
    nn_active :bool =True 
    learning_active :bool =True 
    mask_ratio :float =0.0 
    compute_budget :float =0.0 
    step_latency_ms :float =0.0 

    loss :float =0.0 
    weight_norm :float =0.0 

    in_operating_region :bool =True 
    effective_mass :float =0.1 
    reward :float =0.0 

class PROBESystem :
    """Self-Stabilizing Adaptive Autonomous System."""

    def __init__ (
    self ,
    config :Optional [SystemConfig ]=None ,
    env_params :Optional [EnvironmentParams ]=None ,
    disturbance :Optional [DisturbanceConfig ]=None ,
    seed :int =42 ,
    debug :bool =False ,
    ):
        self .config =config or SystemConfig .full_probe ()
        self .env_params =env_params or EnvironmentParams ()
        self .disturbance =disturbance or DisturbanceConfig ()
        self .seed =seed 
        self .debug =debug 

        self .env =None 
        self .pid =None 
        self .learner =None 
        self .lyapunov =None 
        self .monitor =None 
        self .fault_handler =None 
        self .resource_mgr =None 

        self .telemetry =[]

    def _init_modules (self ,seed :int ):
        """Initialize all modules."""

        self .env =InvertedPendulum (
        params =self .env_params ,
        disturbance =self .disturbance ,
        seed =seed ,
        )

        # Linearized system for LQR and Lyapunov
        A ,B =self .env .get_linearized_system ()

        # 5. PID Controller
        self .pid_controller =PIDController (
        dt =self .env_params .dt ,
        R_lqr =np .array ([[self .config .r_lqr ]])
        )
        K_pid =self .pid_controller .get_gain_vector ()

        if self .config .use_nn :
            self .learner =ResidualLearner (seed =seed +1 )
            self .learner .checkpoint ()# initial checkpoint

        self .lyapunov_layer =None 
        if self .config .use_stability_constraint :
            self .lyapunov_layer =LyapunovProjection (A ,B ,K_pid ,alpha =0.01 )
        elif self .config .use_monitor :
        # Still need Lyapunov for monitoring even without constraint
            self .lyapunov_layer =LyapunovProjection (A ,B ,K_pid ,alpha =0.01 )

        if self .config .use_monitor :
            self .monitor =SelfMonitor ()

        if self .config .use_fault_handler :
            self .fault_handler =FaultHandler ()

        if self .config .use_resource_manager :
            self .resource_mgr =ResourceManager (
            dt =self .env_params .dt ,
            enable_power_decay =self .config .enable_power_decay ,
            )

    def _calibrate_monitor (self ,n_steps :int =200 ):
        """Run a calibration phase to set monitor thresholds."""
        if self .monitor is None :
            return 

            # Temporarily disable disturbances
        orig_disturbance =self .env .disturbance 
        self .env .disturbance =DisturbanceConfig ()

        pred_errors =[]
        states =[]

        obs =self .env .reset ()
        for _ in range (n_steps ):
            u_pid =self .pid_controller .compute (obs )

            # Nominal prediction
            nominal_next =self .env .get_nominal_next_state (obs ,u_pid )

            result =self .env .step (u_pid )
            actual_next =result ["true_state"]

            # Prediction error
            pred_error =float (np .linalg .norm (actual_next -nominal_next ))
            pred_errors .append (pred_error )
            states .append (obs .copy ())

            obs =result ["observation"]

        self .monitor .calibrate (
        np .array (pred_errors ),
        np .array (states ),
        )

        self .env .disturbance =orig_disturbance 
        self .env .reset ()
        self .pid_controller .reset ()

    def run (
    self ,
    duration :float =10.0 ,
    seed :Optional [int ]=None ,
    initial_state :Optional [np .ndarray ]=None ,
    )->list :
        """Run the full system for the specified duration."""
        if seed is None :
            seed =self .seed 

        self ._init_modules (seed )
        obs =self .env .reset (initial_state )
        self .pid_controller .reset ()

        if self .config .use_monitor :
            self ._calibrate_monitor ()
            obs =self .env .reset (initial_state )
            self .pid_controller .reset ()

        n_steps =int (duration /self .env_params .dt )
        self .telemetry =[]

        # Previous state for learning
        prev_obs =obs .copy ()
        prev_u_total =0.0 
        prev_predicted_residual =np .zeros (4 )

        for step_idx in range (n_steps ):
            log =StepLog (step =step_idx ,time =step_idx *self .env_params .dt )

            if self .resource_mgr :
                self .resource_mgr .step_start ()

            log .observation =obs .copy ()

            # --- Compute prediction error (for learning and monitoring) ---
            prediction_error =0.0 
            actual_residual =np .zeros (4 )
            if step_idx >0 and self .config .use_nn :
                nominal_next =self .env .get_nominal_next_state (prev_obs ,prev_u_total )
                actual_residual =obs -nominal_next 
                prediction_error =float (np .linalg .norm (
                actual_residual -prev_predicted_residual 
                ))
            log .prediction_error =prediction_error 

            risk_score =0.0 
            V ,V_dot =0.0 ,0.0 
            if self .lyapunov_layer is not None :
                V =self .lyapunov_layer .compute_lyapunov (obs )
                V_dot =self .lyapunov_layer .compute_lyapunov_derivative (obs ,0.0 )

            if self .monitor is not None :
                monitor_result =self .monitor .update (
                obs ,prediction_error ,V ,V_dot 
                )
                risk_score =monitor_result ["risk_score"]
                log .risk_score =risk_score 
                log .risk_pred =monitor_result ["risk_pred"]
                log .risk_shift =monitor_result ["risk_shift"]
                log .risk_lyap =monitor_result ["risk_lyap"]

            log .V =V 
            log .V_dot =V_dot 

            mode =Mode .NORMAL 
            if self .fault_handler is not None :
                mode =self .fault_handler .update (
                risk_score ,obs [2 ],obs [3 ],V ,V_dot 
                )
            log .mode =mode .name 

            # --- Resource Manager: determine available compute ---
            nn_enabled =self .config .use_nn 
            learning_enabled =self .config .use_nn 
            mask_ratio =0.0 
            power_level =1.0 
            tier ="full"

            if self .resource_mgr is not None :
                res_state =self .resource_mgr .step (
                nn_was_evaluated =nn_enabled ,
                nn_was_trained =learning_enabled ,
                )
                nn_enabled =nn_enabled and res_state .nn_enabled 
                learning_enabled =learning_enabled and res_state .learning_enabled 
                mask_ratio =res_state .mask_ratio 
                power_level =res_state .power_level 
                tier =res_state .tier 
                log .power_level =power_level 
                log .tier =tier 
                log .compute_budget =res_state .compute_budget_used 

            if mode ==Mode .FALLBACK :
                nn_enabled =False 
                learning_enabled =False 
            elif mode ==Mode .EMERGENCY :
                nn_enabled =False 
                learning_enabled =False 

            log .nn_active =nn_enabled 
            log .learning_active =learning_enabled 
            log .mask_ratio =mask_ratio 

            # --- PID Controller ---

            # In FALLBACK/EMERGENCY, the NN is disabled, so PID acts alone.
            u_pid =self .pid_controller .compute (obs )
            log .u_pid =u_pid 

            u_nn_candidate =0.0 
            u_nn_safe =0.0 
            predicted_residual =np .zeros (4 )

            if nn_enabled and self .learner is not None :
            # Apply neuron mask if needed
                if mask_ratio >0 and self .resource_mgr and self .resource_mgr .should_refresh_mask ():
                    self .learner .set_mask (mask_ratio )
                elif mask_ratio <=0 :
                    self .learner .set_mask (0.0 )

                    # Forward pass
                predicted_residual =self .learner .forward (obs )
                u_nn_candidate =self .learner .get_compensating_control (predicted_residual )
                log .u_nn_candidate =u_nn_candidate 

                # --- Lyapunov Projection ---
                if self .config .use_stability_constraint and self .lyapunov_layer is not None :
                # Pass physical constraints to projection layer
                    active_limit =getattr (self .env ,"active_force_limit",self .env_params .force_limit )
                    proj_info =self .lyapunov_layer .project (
                    u_nn_candidate ,
                    obs ,
                    u_pid =u_pid ,
                    env_limit =active_limit ,
                    nn_clamp =1.5 
                    )
                    u_nn_safe =proj_info ["u_nn_safe"]
                    log .V =proj_info ["V"]
                    log .V_dot =proj_info ["V_dot"]
                    log .was_projected =proj_info ["was_projected"]
                    log .conflict =proj_info .get ("conflict",False )
                    log .phi_raw =proj_info .get ("phi_raw",0.0 )
                    log .phi_clamped =proj_info .get ("phi_clamped",0.0 )
                    log .psi =proj_info .get ("psi",0.0 )
                    log .lyap_min =proj_info .get ("lyap_min",0.0 )
                    log .lyap_max =proj_info .get ("lyap_max",0.0 )
                    log .phys_min =proj_info .get ("phys_min",0.0 )
                    log .phys_max =proj_info .get ("phys_max",0.0 )
                    log .projection_degenerate =proj_info .get ("projection_degenerate",False )

                    if not log .conflict :
                    # Projection Correctness Check
                        assert log .phys_min -1e-6 <=u_nn_safe <=log .phys_max +1e-6 ,f"u_nn_safe {u_nn_safe } outside physical bounds [{log .phys_min }, {log .phys_max }]"
                        if not log .projection_degenerate :
                            assert log .lyap_min -1e-6 <=u_nn_safe <=log .lyap_max +1e-6 ,f"u_nn_safe {u_nn_safe } outside lyap bounds [{log .lyap_min }, {log .lyap_max }]"

                            # Lyapunov Violation Logging
                        alpha =self .lyapunov_layer .alpha 
                        if log .V >0.0 and log .V_dot >-alpha *log .V +1e-6 :
                            if self .debug :
                                print (f"  [WARN] Step {step_idx }: Lyapunov violation! V={log .V :.4f}, V_dot={log .V_dot :.4f}, Margin={log .V_dot +alpha *log .V :.4f}")
                else :
                    u_nn_safe =u_nn_candidate 

                log .u_nn_safe =u_nn_safe 

            u_total =u_pid +u_nn_safe 
            log .u_total =u_total 

            active_limit =getattr (self .env ,"active_force_limit",self .env_params .force_limit )

            # 1. HARD INVARIANT CHECK: Actuator bounds
            # We can only guarantee the control system strictly respects bounds if the projection 
            # found a feasible solution (no conflict) AND was active. Otherwise, u_pid passes through to be clipped by env.
            if self .config .use_stability_constraint and nn_enabled and not log .conflict :
                assert abs (u_total )<=active_limit +1e-6 ,f"HARD INVARIANT FAILED: |u_total| > F_max! u_total={u_total }, F_max={active_limit }"

            if self .debug and step_idx %10 ==0 :
                print (f"Step {step_idx }: u_pid={u_pid :.2f}, u_nn_cand={u_nn_candidate :.2f}, u_nn_safe={u_nn_safe :.2f}, u_tot={u_total :.2f}")
                if nn_enabled and self .config .use_stability_constraint :
                    print (f"  phi_raw={log .phi_raw :.4e}, phi_clamped={log .phi_clamped :.4e}, psi={log .psi :.4e}, degen={log .projection_degenerate }, conflict={log .conflict }")
                    print (f"  bounds: phys=[{log .phys_min :.2f}, {log .phys_max :.2f}], lyap=[{log .lyap_min :.2f}, {log .lyap_max :.2f}]")

                    # --- Apply to environment ---
            result =self .env .step (u_total )
            log .true_state =result ["true_state"]
            log .state =result ["true_state"]
            log .in_operating_region =result ["in_operating_region"]
            log .effective_mass =result ["effective_mass"]
            log .reward =result ["reward"]
            log .u_applied =result .get ("u_applied",u_total )

            next_obs =result ["observation"]

            # --- Learning update ---
            loss =0.0 
            if learning_enabled and self .learner is not None and step_idx >0 :
            # Train on the residual from the PREVIOUS step
                loss =self .learner .update (
                prev_obs ,
                actual_residual ,
                prev_predicted_residual ,
                )
                log .loss =loss 

            if self .learner is not None :
                log .weight_norm =self .learner .get_weight_norm ()

                # --- Checkpoint on stable operation ---
            if (
            self .learner is not None 
            and mode ==Mode .NORMAL 
            and step_idx >0 
            and step_idx %100 ==0 
            and risk_score <0.3 
            ):
                self .learner .checkpoint ()

            if (
            self .fault_handler is not None 
            and self .learner is not None 
            and len (self .fault_handler .audit_log )>0 
            ):
                last_event =self .fault_handler .audit_log [-1 ]
                if (
                last_event ["step"]==step_idx +1 
                and "EMERGENCY"in last_event ["transition"]
                and "→FALLBACK"in last_event ["transition"]
                ):
                    self .learner .restore ()
                elif (
                last_event ["step"]==step_idx +1 
                and last_event ["transition"]=="FALLBACK→NORMAL"
                ):
                    self .learner .reduce_learning_rate (factor =0.5 ,duration =100 )

            self .telemetry .append (log )

            # --- Prepare for next step ---
            prev_obs =obs .copy ()
            prev_u_total =u_total 
            prev_predicted_residual =predicted_residual .copy ()
            obs =next_obs 

            if result ["done"]:
                break 

        if not self .debug :
            metrics =self .get_metrics ()
            print (f"Run Summary (Seed {self .seed }): "
            f"Lyap Violations: {metrics .get ('lyapunov_violation_rate',0.0 ):.2%}, "
            f"Max V_dot Margin: {metrics .get ('max_vdot_margin',0.0 ):.4f}, "
            f"Conflicts: {metrics .get ('conflict_count',0 )}, "
            f"Env Clips: {metrics .get ('env_clip_count',0 )}, "
            f"Degen Rate: {metrics .get ('phi_degeneracy_rate',0.0 ):.2%}")

        return self .telemetry 

    def get_metrics (self )->dict :
        """Compute evaluation metrics from telemetry."""
        if not self .telemetry :
            return {}

        thetas =np .array ([log .true_state [2 ]for log in self .telemetry ])
        controls =np .array ([log .u_total for log in self .telemetry ])
        risks =np .array ([log .risk_score for log in self .telemetry ])

        rms_error =float (np .sqrt (np .mean (thetas **2 )))
        max_deviation =float (np .max (np .abs (thetas )))
        stability_violations =int (np .sum (np .abs (thetas )>np .pi /6 ))
        control_effort =float (np .mean (controls **2 ))
        mean_risk =float (np .mean (risks ))
        max_risk =float (np .max (risks ))
        latencies =[log .step_latency_ms for log in self .telemetry ]

        # Lyapunov violations (V_dot > -alpha * V + 1e-6)
        alpha =0.01 
        lyapunov_margins =np .array ([log .V_dot +alpha *log .V for log in self .telemetry if log .V >0.0 ])
        if len (lyapunov_margins )>0 :
            lyapunov_violation_rate =np .mean (lyapunov_margins >1e-6 )
            max_vdot_margin =float (np .max (lyapunov_margins ))
        else :
            lyapunov_violation_rate =0.0 
            max_vdot_margin =0.0 

            # Clipping checks (only when NN/projection is active and no conflict)
        env_clip_count =0 
        for log in self .telemetry :
            if log .nn_active and not log .conflict and abs (log .u_applied -log .u_total )>1e-8 :
                env_clip_count +=1 

                # NN Contribution ratio (ignore steps where u_total < 0.05)
        nn_safes =np .array ([log .u_nn_safe for log in self .telemetry ])
        valid_idxs =np .abs (controls )>=0.05 
        if np .any (valid_idxs ):
            nn_ratios =np .abs (nn_safes [valid_idxs ])/np .maximum (np .abs (controls [valid_idxs ]),1e-6 )
            nn_contrib_mean =float (np .mean (nn_ratios ))
            nn_contrib_p95 =float (np .percentile (nn_ratios ,95 ))
            nn_contrib_max =float (np .max (nn_ratios ))
        else :
            nn_contrib_mean =nn_contrib_p95 =nn_contrib_max =0.0 

        conflicts =np .array ([log .conflict for log in self .telemetry ],dtype =bool )
        conflict_count =int (np .sum (conflicts ))
        conflict_rate =conflict_count /len (conflicts )if len (conflicts )>0 else 0.0 

        max_conflict_dur =0 
        current_dur =0 
        for c in conflicts :
            if c :
                current_dur +=1 
                max_conflict_dur =max (max_conflict_dur ,current_dur )
            else :
                current_dur =0 

                # Strict Recovery time: time until |θ| < 0.05 and |θ̇| < 0.05 for 50 consecutive steps
        recovery_time =self .telemetry [-1 ].time if self .telemetry else 0.0 
        consecutive =0 
        for log in self .telemetry :
            if abs (log .true_state [2 ])<0.05 and abs (log .true_state [3 ])<0.05 :
                consecutive +=1 
                if consecutive >=50 :
                    recovery_time =log .time -50 *self .env_params .dt 
                    break 
            else :
                consecutive =0 

        mode_transitions =sum (
        1 for i in range (1 ,len (self .telemetry ))
        if self .telemetry [i ].mode !=self .telemetry [i -1 ].mode 
        )

        modes =[log .mode for log in self .telemetry ]
        normal_frac =modes .count ("NORMAL")/len (modes )
        fallback_frac =modes .count ("FALLBACK")/len (modes )
        emergency_frac =modes .count ("EMERGENCY")/len (modes )
        projection_active_rate =np .mean ([log .was_projected for log in self .telemetry ])

        active_limit =getattr (self .env ,"active_force_limit",self .env_params .force_limit )
        saturation_count =np .sum (np .abs (controls )>=active_limit -1e-2 )
        saturation_rate =float (saturation_count /len (controls ))if len (controls )>0 else 0.0 

        divergence_events =int (np .sum (np .abs (thetas )>np .pi /2 ))

        # Phi Degeneracy (projection matrix singular)
        phis =np .array ([log .phi_raw for log in self .telemetry ])
        phi_degeneracy_rate =float (np .mean (np .abs (phis )<1e-4 ))if len (phis )>0 else 0.0 

        metrics ={
        "rms_tracking_error":float (rms_error ),
        "max_deviation_deg":float (np .degrees (max_deviation )),
        "stability_violations":int (stability_violations ),
        "recovery_time":float (recovery_time ),
        "control_effort":float (control_effort ),
        "saturation_rate":float (saturation_rate ),
        "lyapunov_violation_rate":float (lyapunov_violation_rate ),
        "max_vdot_margin":float (max_vdot_margin ),
        "env_clip_count":int (env_clip_count ),
        "conflict_count":int (conflict_count ),
        "conflict_rate":float (conflict_rate ),
        "max_conflict_duration":int (max_conflict_dur ),
        "nn_contribution_mean":float (nn_contrib_mean ),
        "nn_contribution_p95":float (nn_contrib_p95 ),
        "nn_contribution_max":float (nn_contrib_max ),
        "max_risk":float (max_risk ),
        "mean_risk":float (np .mean (risks )),
        "mode_transitions":mode_transitions ,
        "normal_fraction":float (normal_frac ),
        "fallback_fraction":float (fallback_frac ),
        "emergency_fraction":float (emergency_frac ),
        "projection_active_rate":float (projection_active_rate ),
        "final_power":float (self .telemetry [-1 ].power_level ),
        "mean_step_latency_ms":float (np .mean (latencies )),
        "phi_degeneracy_rate":float (phi_degeneracy_rate ),
        "divergence_events":int (divergence_events ),
        }

        if self .fault_handler :
            fh_stats =self .fault_handler .get_stats ()
            metrics ["fault_count"]=fh_stats ["fault_count"]
            metrics ["emergency_count"]=fh_stats ["emergency_count"]
            metrics ["transitions"]=fh_stats ["total_transitions"]

        if self .learner :
            metrics ["final_weight_norm"]=self .learner .get_weight_norm ()
            metrics ["param_count"]=self .learner .get_param_count ()

        return metrics 

    def get_fault_log (self )->list :
        """Return fault handler audit log."""
        if self .fault_handler :
            return self .fault_handler .get_audit_log ()
        return []

    def get_detection_log (self )->list :
        """Return self-monitor detection log."""
        if self .monitor :
            return self .monitor .get_detection_log ()
        return []
