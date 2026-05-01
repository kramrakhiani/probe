"""Resource Manager"""

import numpy as np 
import time as time_module 
from dataclasses import dataclass 

@dataclass 
class ResourceState :
    """Current resource state returned by the resource manager."""
    power_level :float 
    nn_enabled :bool # whether NN forward pass should run
    learning_enabled :bool # whether NN backward pass should run
    update_this_step :bool # whether to do learning THIS step
    mask_ratio :float 
    compute_budget_used :float # fraction of compute budget used this step
    tier :str 

class ResourceManager :
    """Simulates power and compute constraints."""

    def __init__ (
    self ,
    initial_power :float =1.0 ,
    base_decay_per_second :float =0.005 ,
    nn_eval_cost :float =0.002 ,
    nn_learn_cost :float =0.003 ,
    dt :float =0.02 ,
    enable_power_decay :bool =True ,
    ):
        """Args:"""
        self .initial_power =initial_power 
        self .base_decay_per_step =base_decay_per_second *dt 
        self .nn_eval_cost =nn_eval_cost 
        self .nn_learn_cost =nn_learn_cost 
        self .dt =dt 
        self .enable_power_decay =enable_power_decay 

        self .power =initial_power 
        self ._step =0 
        self ._learning_counter =0 

        # Compute budget tracking
        self .compute_costs ={
        "pid":0.05 ,
        "nn_forward":0.25 ,
        "nn_backward":0.35 ,
        "monitor":0.05 ,
        "fault_handler":0.02 ,
        "resource_mgr":0.03 ,
        }

        self .latency_log =[]
        self ._step_start_time =None 

        self ._mask_refresh_interval =50 
        self ._last_mask_refresh =0 

    def step_start (self ):
        """Mark the start of a step for latency measurement."""
        self ._step_start_time =time_module .perf_counter ()

    def step (self ,nn_was_evaluated :bool =False ,nn_was_trained :bool =False )->ResourceState :
        """Advance resource state by one step."""
        self ._step +=1 

        # Power decay
        if self .enable_power_decay :
            self .power -=self .base_decay_per_step 
            if nn_was_evaluated :
                self .power -=self .nn_eval_cost 
            if nn_was_trained :
                self .power -=self .nn_learn_cost 
            self .power =max (0.0 ,self .power )

        tier ,nn_enabled ,mask_ratio ,update_freq =self ._get_tier ()

        self ._learning_counter +=1 
        update_this_step =False 
        if nn_enabled and update_freq >0 :
            update_this_step =(self ._learning_counter %update_freq )==0 

            # Compute budget used this step
        budget =self .compute_costs ["pid"]+self .compute_costs ["monitor"]
        budget +=self .compute_costs ["fault_handler"]+self .compute_costs ["resource_mgr"]
        if nn_enabled :
            budget +=self .compute_costs ["nn_forward"]*(1.0 -mask_ratio )
            if update_this_step :
                budget +=self .compute_costs ["nn_backward"]*(1.0 -mask_ratio )

        if self ._step_start_time is not None :
            elapsed =(time_module .perf_counter ()-self ._step_start_time )*1000 
            self .latency_log .append ({
            "step":self ._step ,
            "total_ms":elapsed ,
            "power":self .power ,
            "tier":tier ,
            "nn_eval":nn_was_evaluated ,
            "nn_train":nn_was_trained ,
            "compute_budget":budget ,
            })

        return ResourceState (
        power_level =self .power ,
        nn_enabled =nn_enabled ,
        learning_enabled =nn_enabled and update_this_step ,
        update_this_step =update_this_step ,
        mask_ratio =mask_ratio ,
        compute_budget_used =budget ,
        tier =tier ,
        )

    def _get_tier (self )->tuple :
        """Determine resource tier based on power level."""
        if self .power >0.60 :
            return ("full",True ,0.0 ,1 )
        elif self .power >0.30 :
            return ("reduced",True ,0.0 ,3 )
        elif self .power >0.15 :
            return ("minimal",True ,0.5 ,5 )
        else :
            return ("disabled",False ,1.0 ,0 )

    def should_refresh_mask (self )->bool :
        """Check if neuron mask should be re-sampled."""
        if self ._step -self ._last_mask_refresh >=self ._mask_refresh_interval :
            self ._last_mask_refresh =self ._step 
            return True 
        return False 

    def get_telemetry (self )->dict :
        """Return resource usage telemetry."""
        if not self .latency_log :
            return {
            "power_remaining":self .power ,
            "mean_latency_ms":0.0 ,
            "total_steps":self ._step ,
            }

        latencies =[l ["total_ms"]for l in self .latency_log ]
        return {
        "power_remaining":self .power ,
        "mean_latency_ms":float (np .mean (latencies )),
        "max_latency_ms":float (np .max (latencies )),
        "total_steps":self ._step ,
        "tier_history":[l ["tier"]for l in self .latency_log [-10 :]],
        }

    def reset (self ):
        """Reset resource state."""
        self .power =self .initial_power 
        self ._step =0 
        self ._learning_counter =0 
        self .latency_log =[]
        self ._step_start_time =None 
        self ._last_mask_refresh =0 
