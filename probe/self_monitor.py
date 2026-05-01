"""Self-Monitoring Module"""

import numpy as np 
from typing import Optional 

class SelfMonitor :
    """Self-monitoring module with calibrated thresholds and hysteresis."""

    def __init__ (
    self ,
    state_dim :int =4 ,
    pred_ema_beta :float =0.95 ,
    stats_gamma :float =0.99 ,
    pred_threshold_mult :float =100.0 ,
    z_threshold :float =20.0 ,
    v_dot_critical :float =5.0 ,# V_dot threshold for instability risk
    ):
        """Args:"""
        self .state_dim =state_dim 
        self .pred_ema_beta =pred_ema_beta 
        self .stats_gamma =stats_gamma 
        self .pred_threshold_mult =pred_threshold_mult 
        self .z_threshold =z_threshold 
        self .v_dot_critical =v_dot_critical 

        # Running prediction error (EMA)
        self .sigma_pred =0.0 

        self .running_mean =np .zeros (state_dim )
        self .running_var =np .ones (state_dim )

        self .sigma_pred_threshold =1.0 
        self .calibrated =False 

        self .detection_log =[]
        self ._step =0 

        self ._risk_above_threshold =False 

    def calibrate (self ,prediction_errors :np .ndarray ,states :np .ndarray ):
        """Calibrate thresholds from baseline run data."""
        # Prediction error threshold
        baseline_sigma =np .mean (prediction_errors )
        self .sigma_pred_threshold =max (baseline_sigma *self .pred_threshold_mult ,0.01 )

        self .running_mean =np .mean (states ,axis =0 )
        self .running_var =np .var (states ,axis =0 )+1e-8 

        self .sigma_pred =baseline_sigma 

        self .calibrated =True 

    def update (
    self ,
    state :np .ndarray ,
    prediction_error :float ,
    V :float =0.0 ,
    V_dot :float =0.0 ,
    )->dict :
        """Update monitoring state and compute risk score."""
        self ._step +=1 

        # --- Prediction error tracking ---
        self .sigma_pred =(
        self .pred_ema_beta *self .sigma_pred 
        +(1 -self .pred_ema_beta )*prediction_error 
        )
        risk_pred =float (np .clip (
        self .sigma_pred /self .sigma_pred_threshold ,0.0 ,1.0 
        ))

        # Update running statistics
        self .running_mean =(
        self .stats_gamma *self .running_mean 
        +(1 -self .stats_gamma )*state 
        )
        diff =state -self .running_mean 
        self .running_var =(
        self .stats_gamma *self .running_var 
        +(1 -self .stats_gamma )*diff **2 
        )

        # Z-score per dimension, take max
        z_scores =np .abs (state -self .running_mean )/(
        np .sqrt (self .running_var )+1e-8 
        )
        z_max =float (np .max (z_scores ))
        risk_shift =float (np .clip (z_max /self .z_threshold ,0.0 ,1.0 ))
        shift_detected =z_max >self .z_threshold 

        # --- Lyapunov stability monitoring ---
        # V_dot > 0 means energy is increasing (destabilizing)
        # 3. Lyapunov risk: is the system gaining energy?
        r_lyap =0.0 
        if V_dot >0 :
            if V >1e-6 :
            # Scaled down sensitivity to V_dot since wind naturally increases energy
                r_lyap =V_dot /(1.0 *V +0.1 )
            else :
                r_lyap =V_dot /0.1 
        risk_lyap =float (np .clip (r_lyap ,0.0 ,1.0 ))

        # --- Composite risk score ---
        risk_score =float (max (risk_pred ,risk_shift ,risk_lyap ))

        # Anomaly: any component exceeds 0.7
        anomaly_detected =risk_score >0.7 

        if anomaly_detected or shift_detected :
            self .detection_log .append ({
            "step":self ._step ,
            "risk_score":risk_score ,
            "risk_pred":risk_pred ,
            "risk_shift":risk_shift ,
            "risk_lyap":risk_lyap ,
            "shift_detected":shift_detected ,
            "anomaly_detected":anomaly_detected ,
            "z_max":z_max ,
            "sigma_pred":self .sigma_pred ,
            })

        return {
        "risk_score":risk_score ,
        "risk_pred":risk_pred ,
        "risk_shift":risk_shift ,
        "risk_lyap":risk_lyap ,
        "shift_detected":shift_detected ,
        "anomaly_detected":anomaly_detected ,
        "z_max":z_max ,
        "sigma_pred":self .sigma_pred ,
        }

    def get_detection_log (self )->list :
        """Return the full detection event log."""
        return self .detection_log 

    def reset (self ):
        """Reset monitoring state (but keep calibration)."""
        self .sigma_pred =0.0 
        self .running_mean =np .zeros (self .state_dim )
        self .running_var =np .ones (self .state_dim )
        self .detection_log =[]
        self ._step =0 
        self ._risk_above_threshold =False 
