"""Learning Module — Residual Dynamics Neural Network"""

import numpy as np 
from typing import Optional 

class ResidualLearner :
    """Feedforward neural network for residual dynamics learning."""

    def __init__ (
    self ,
    input_dim :int =4 ,
    hidden1 :int =32 ,
    hidden2 :int =16 ,
    output_dim :int =4 ,
    lr :float =1.0 ,
    delta_max :float =5.0 ,# Allow large weight updates per step
    weight_decay :float =1e-5 ,
    max_weight_norm :float =10.0 ,
    seed :int =42 ,
    ):
        self .input_dim =input_dim 
        self .hidden1 =hidden1 
        self .hidden2 =hidden2 
        self .output_dim =output_dim 
        self .lr =lr 
        self .delta_max =delta_max 
        self .weight_decay =weight_decay 
        self .max_weight_norm =max_weight_norm 
        self .rng =np .random .default_rng (seed )

        self .W1 =self .rng .normal (0 ,np .sqrt (2.0 /input_dim ),(input_dim ,hidden1 ))
        self .b1 =np .zeros (hidden1 )
        self .W2 =self .rng .normal (0 ,np .sqrt (2.0 /hidden1 ),(hidden1 ,hidden2 ))
        self .b2 =np .zeros (hidden2 )
        self .W3 =self .rng .normal (0 ,0.001 ,(hidden2 ,output_dim ))# Near-zero init: NN starts with ~0 output
        self .b3 =np .zeros (output_dim )

        # Compensation gains and efficiency penalty
        self .K_comp =np .array ([0.0 ,0.0 ,-200.0 ,-50.0 ])
        self .lambda_eff =1e-4 

        # Hard clamp on compensating control output
        self .u_nn_clamp =1.5 

        self .mask1 =np .ones (hidden1 )
        self .mask2 =np .ones (hidden2 )

        # Checkpoint storage
        self ._checkpoint =None 

        # Learning rate multiplier (can be reduced after recovery)
        self .lr_multiplier =1.0 
        self ._lr_restore_countdown =0 

        # Cached activations for backprop
        self ._cache ={}

    def _relu (self ,x :np .ndarray )->np .ndarray :
        return np .maximum (0 ,x )

    def _relu_grad (self ,x :np .ndarray )->np .ndarray :
        return (x >0 ).astype (float )

    def forward (self ,state :np .ndarray )->np .ndarray :
        """Forward pass: predict residual dynamics Δx."""

        z1 =state @self .W1 +self .b1 
        a1 =self ._relu (z1 )*self .mask1 

        z2 =a1 @self .W2 +self .b2 
        a2 =self ._relu (z2 )*self .mask2 

        # Output layer (linear)
        out =a2 @self .W3 +self .b3 

        # Cache for backprop
        self ._cache ={
        "state":state ,"z1":z1 ,"a1":a1 ,
        "z2":z2 ,"a2":a2 ,"out":out ,
        }

        return out 

    def update (
    self ,
    state :np .ndarray ,
    actual_residual :np .ndarray ,
    predicted_residual :np .ndarray ,
    )->float :
        """Online SGD update step."""
        if not self ._cache :
            return 0.0 

        error =predicted_residual -actual_residual # shape (4,)
        loss =0.5 *np .sum (error **2 )

        # Backprop
        # dL/d_out = error + gradient of efficiency penalty
        u_nn_unclamped =float (self .K_comp @predicted_residual )
        penalty_grad =self .lambda_eff *2.0 *u_nn_unclamped *self .K_comp 
        d_out =error +penalty_grad 
        d_out =np .clip (d_out ,-5.0 ,5.0 )# Gradient clipping for stability

        dW3 =np .outer (self ._cache ["a2"],d_out )
        db3 =d_out 
        d_a2 =d_out @self .W3 .T 

        d_z2 =d_a2 *self ._relu_grad (self ._cache ["z2"])*self .mask2 
        dW2 =np .outer (self ._cache ["a1"],d_z2 )
        db2 =d_z2 
        d_a1 =d_z2 @self .W2 .T 

        d_z1 =d_a1 *self ._relu_grad (self ._cache ["z1"])*self .mask1 
        dW1 =np .outer (self ._cache ["state"],d_z1 )
        db1 =d_z1 

        grads =[dW1 ,db1 ,dW2 ,db2 ,dW3 ,db3 ]
        params =[self .W1 ,self .b1 ,self .W2 ,self .b2 ,self .W3 ,self .b3 ]

        # Compute total gradient norm
        total_grad_norm =np .sqrt (sum (np .sum (g **2 )for g in grads ))

        # Bounded update: scale gradient if ||Δw|| would exceed δ_max
        effective_lr =self .lr *self .lr_multiplier 
        if total_grad_norm *effective_lr >self .delta_max :
            scale =self .delta_max /(total_grad_norm *effective_lr )
            grads =[g *scale for g in grads ]

            # Apply updates with weight decay
        for i ,(p ,g )in enumerate (zip (params ,grads )):
            p -=effective_lr *g 
            if i %2 ==0 :
                p *=(1.0 -self .weight_decay )

                # Reassign (numpy arrays are mutable, but ensure reference)
        self .W1 ,self .b1 =params [0 ],params [1 ]
        self .W2 ,self .b2 =params [2 ],params [3 ]
        self .W3 ,self .b3 =params [4 ],params [5 ]

        total_norm =np .sqrt (
        np .sum (self .W1 **2 )+np .sum (self .W2 **2 )+np .sum (self .W3 **2 )
        )
        if total_norm >self .max_weight_norm :
            scale =self .max_weight_norm /total_norm 
            self .W1 *=scale 
            self .W2 *=scale 
            self .W3 *=scale 

        if self ._lr_restore_countdown >0 :
            self ._lr_restore_countdown -=1 
            if self ._lr_restore_countdown ==0 :
                self .lr_multiplier =1.0 

        return loss 

    def get_compensating_control (
    self ,predicted_residual :np .ndarray ,K_comp :Optional [np .ndarray ]=None 
    )->float :
        """Derive a compensating control signal from the predicted residual."""
        if K_comp is None :
            K_comp =self .K_comp 

        u_nn =float (K_comp @predicted_residual )
        # Hard clamp to prevent NN from overwhelming PID
        return float (np .clip (u_nn ,-self .u_nn_clamp ,self .u_nn_clamp ))

    def set_mask (self ,mask_ratio :float ):
        """Apply neuron masking for resource-aware computation."""
        if mask_ratio <=0 :
            self .mask1 =np .ones (self .hidden1 )
            self .mask2 =np .ones (self .hidden2 )
        else :
            n_mask1 =int (self .hidden1 *mask_ratio )
            n_mask2 =int (self .hidden2 *mask_ratio )
            self .mask1 =np .ones (self .hidden1 )
            self .mask2 =np .ones (self .hidden2 )
            idx1 =self .rng .choice (self .hidden1 ,n_mask1 ,replace =False )
            idx2 =self .rng .choice (self .hidden2 ,n_mask2 ,replace =False )
            self .mask1 [idx1 ]=0.0 
            self .mask2 [idx2 ]=0.0 

    def checkpoint (self ):
        """Save current weights as a known-good checkpoint."""
        self ._checkpoint ={
        "W1":self .W1 .copy (),"b1":self .b1 .copy (),
        "W2":self .W2 .copy (),"b2":self .b2 .copy (),
        "W3":self .W3 .copy (),"b3":self .b3 .copy (),
        }

    def restore (self ):
        """Restore weights from last checkpoint."""
        if self ._checkpoint is not None :
            self .W1 =self ._checkpoint ["W1"].copy ()
            self .b1 =self ._checkpoint ["b1"].copy ()
            self .W2 =self ._checkpoint ["W2"].copy ()
            self .b2 =self ._checkpoint ["b2"].copy ()
            self .W3 =self ._checkpoint ["W3"].copy ()
            self .b3 =self ._checkpoint ["b3"].copy ()

    def reduce_learning_rate (self ,factor :float =0.5 ,duration :int =100 ):
        """Temporarily reduce learning rate (used after fault recovery)."""
        self .lr_multiplier =factor 
        self ._lr_restore_countdown =duration 

    def get_weight_norm (self )->float :
        """Return total L2 norm of all weight matrices."""
        return float (np .sqrt (
        np .sum (self .W1 **2 )+np .sum (self .W2 **2 )+np .sum (self .W3 **2 )
        ))

    def get_param_count (self )->int :
        """Return total number of parameters."""
        return (
        self .W1 .size +self .b1 .size +
        self .W2 .size +self .b2 .size +
        self .W3 .size +self .b3 .size 
        )
