"""Fault Handler — Auditable State Machine"""

import numpy as np 
from enum import Enum ,auto 
from typing import Optional 

class Mode (Enum ):
    NORMAL =auto ()
    FALLBACK =auto ()
    EMERGENCY =auto ()

class FaultHandler :
    """Fault handling state machine with hysteresis and dwell times."""

    def __init__ (
    self ,
    risk_rising :float =0.99 ,
    risk_falling :float =0.3 ,
    risk_emergency :float =0.99 ,
    theta_emergency :float =np .pi /3 ,
    theta_recovery :float =np .pi /8 ,
    theta_dot_recovery :float =1.0 ,
    rising_count :int =50 ,
    falling_count :int =25 ,
    emergency_count :int =20 ,
    emergency_recovery_count :int =50 ,
    min_fallback_dwell :int =50 ,
    min_emergency_dwell :int =100 ,
    ):
        self .risk_rising =risk_rising 
        self .risk_falling =risk_falling 
        self .risk_emergency =risk_emergency 
        self .theta_emergency =theta_emergency 
        self .theta_recovery =theta_recovery 
        self .theta_dot_recovery =theta_dot_recovery 
        self .rising_count =rising_count 
        self .falling_count =falling_count 
        self .emergency_count =emergency_count 
        self .emergency_recovery_count =emergency_recovery_count 
        self .min_fallback_dwell =min_fallback_dwell 
        self .min_emergency_dwell =min_emergency_dwell 

        self .mode =Mode .NORMAL 
        self ._dwell_counter =0 # steps in current mode
        self ._rising_counter =0 
        self ._falling_counter =0 
        self ._emergency_trigger_counter =0 
        self ._emergency_recovery_counter =0 

        self .fault_count =0 
        self .emergency_count_total =0 

        self .audit_log =[]
        self ._step =0 

    def update (
    self ,
    risk_score :float ,
    theta :float ,
    theta_dot :float ,
    V :float =0.0 ,
    V_dot :float =0.0 ,
    )->Mode :
        """Update fault handler state and return current mode."""
        self ._step +=1 
        self ._dwell_counter +=1 
        prev_mode =self .mode 

        if self .mode ==Mode .NORMAL :
            self ._handle_normal (risk_score ,theta )

        elif self .mode ==Mode .FALLBACK :
            self ._handle_fallback (risk_score ,theta ,theta_dot )

        elif self .mode ==Mode .EMERGENCY :
            self ._handle_emergency (theta ,theta_dot )

        if self .mode !=prev_mode :
            event ={
            "step":self ._step ,
            "timestamp":self ._step *0.02 ,
            "transition":f"{prev_mode .name }→{self .mode .name }",
            "risk_score":risk_score ,
            "theta":theta ,
            "theta_dot":theta_dot ,
            "V":V ,
            "V_dot":V_dot ,
            "trigger":self ._last_trigger ,
            }
            self .audit_log .append (event )
            self ._dwell_counter =0 

        return self .mode 

    def _handle_normal (self ,risk_score :float ,theta :float ):
        """Handle transitions from NORMAL mode."""
        self ._last_trigger =""

        if risk_score >self .risk_rising :
            self ._rising_counter +=1 
        else :
            self ._rising_counter =0 

        if self ._rising_counter >=self .rising_count :
            self .mode =Mode .FALLBACK 
            self .fault_count +=1 
            self ._rising_counter =0 
            self ._falling_counter =0 
            self ._last_trigger =f"risk_score>{self .risk_rising } for {self .rising_count } steps"

        if abs (theta )>self .theta_emergency :
            self .mode =Mode .EMERGENCY 
            self .emergency_count_total +=1 
            self ._last_trigger =f"|theta|={abs (theta ):.3f} > {self .theta_emergency :.3f}"

    def _handle_fallback (self ,risk_score :float ,theta :float ,theta_dot :float ):
        """Handle transitions from FALLBACK mode."""
        self ._last_trigger =""

        if abs (theta )>self .theta_emergency :
            self .mode =Mode .EMERGENCY 
            self .emergency_count_total +=1 
            self ._emergency_trigger_counter =0 
            self ._last_trigger =f"|theta|={abs (theta ):.3f} > {self .theta_emergency :.3f}"
            return 

        if risk_score >self .risk_emergency :
            self ._emergency_trigger_counter +=1 
        else :
            self ._emergency_trigger_counter =0 

        if self ._emergency_trigger_counter >=self .emergency_count :
            self .mode =Mode .EMERGENCY 
            self .emergency_count_total +=1 
            self ._emergency_trigger_counter =0 
            self ._last_trigger =f"risk_score>{self .risk_emergency } for {self .emergency_count } steps"
            return 

        if risk_score <self .risk_falling :
            self ._falling_counter +=1 
        else :
            self ._falling_counter =0 

        if (
        self ._falling_counter >=self .falling_count 
        and self ._dwell_counter >=self .min_fallback_dwell 
        ):
            self .mode =Mode .NORMAL 
            self ._falling_counter =0 
            self ._last_trigger =f"risk_score<{self .risk_falling } for {self .falling_count } steps, dwell={self ._dwell_counter }"

    def _handle_emergency (self ,theta :float ,theta_dot :float ):
        """Handle transitions from EMERGENCY mode."""
        self ._last_trigger =""

        if abs (theta )<self .theta_recovery and abs (theta_dot )<self .theta_dot_recovery :
            self ._emergency_recovery_counter +=1 
        else :
            self ._emergency_recovery_counter =0 

        if (
        self ._emergency_recovery_counter >=self .emergency_recovery_count 
        and self ._dwell_counter >=self .min_emergency_dwell 
        ):
            self .mode =Mode .FALLBACK 
            self ._emergency_recovery_counter =0 
            self ._last_trigger =f"|theta|<{self .theta_recovery :.3f}, |theta_dot|<{self .theta_dot_recovery }, dwell={self ._dwell_counter }"

    def get_audit_log (self )->list :
        """Return the full audit log of mode transitions."""
        return self .audit_log 

    def get_stats (self )->dict :
        """Return fault handling statistics."""
        return {
        "current_mode":self .mode .name ,
        "fault_count":self .fault_count ,
        "emergency_count":self .emergency_count_total ,
        "dwell_steps":self ._dwell_counter ,
        "total_transitions":len (self .audit_log ),
        }

    def reset (self ):
        """Reset to NORMAL mode."""
        self .mode =Mode .NORMAL 
        self ._dwell_counter =0 
        self ._rising_counter =0 
        self ._falling_counter =0 
        self ._emergency_trigger_counter =0 
        self ._emergency_recovery_counter =0 
        self .fault_count =0 
        self .emergency_count_total =0 
        self .audit_log =[]
        self ._step =0 
