"""PID Controller"""

import numpy as np 
from scipy .linalg import solve_continuous_are 

class PIDController :
    """State-feedback controller for inverted pendulum stabilization."""

    def __init__ (
    self ,
    A :np .ndarray =None ,
    B :np .ndarray =None ,
    Q_lqr :np .ndarray =None ,
    R_lqr :np .ndarray =None ,
    integral_gain :float =-2.0 ,
    integral_limit :float =5.0 ,
    dt :float =0.02 ,
    ):
        """Args:"""
        # Default linearized system for standard pendulum params
        if A is None :
            M ,m ,l ,g =1.0 ,0.1 ,0.5 ,9.81 
            total_mass =M +m 
            denom =l *(4.0 /3.0 -m /total_mass )
            A =np .array ([
            [0 ,1 ,0 ,0 ],
            [0 ,0 ,-m *g /total_mass ,0 ],
            [0 ,0 ,0 ,1 ],
            [0 ,0 ,g /denom ,0 ],
            ])
            B =np .array ([[0 ],[1.0 /total_mass ],[0 ],[-1.0 /(total_mass *denom )]])

        if Q_lqr is None :
            Q_lqr =np .diag ([0.5 ,0.5 ,5.0 ,0.5 ])# Weaker angle penalty
        if R_lqr is None :
            R_lqr =np .array ([[1.0 ]])# High penalty on control effort

        self .A =A 
        self .B =B .flatten ()if B .ndim >1 else B 
        self .dt =dt 
        self .integral_gain =integral_gain 
        self .integral_limit =integral_limit 

        # Solve LQR for optimal gains
        # ARE: A^T P + P A - P B R^-1 B^T P + Q = 0
        B_col =self .B .reshape (-1 ,1 )
        P_are =solve_continuous_are (A ,B_col ,Q_lqr ,R_lqr )
        self .K_lqr =(np .linalg .inv (R_lqr )@B_col .T @P_are ).flatten ()# shape (4,)

        A_cl =A -B_col @self .K_lqr .reshape (1 ,-1 )
        eigvals =np .linalg .eigvals (A_cl )
        assert np .all (np .real (eigvals )<0 ),(
        f"LQR closed-loop is not stable! Eigenvalues: {eigvals }"
        )
        self ._cl_eigenvalues =eigvals 

        self ._integral =0.0 

    def reset (self ):
        """Reset integral accumulator."""
        self ._integral =0.0 

    def compute (self ,state :np .ndarray )->float :
        """Compute state-feedback control force."""
        theta =state [2 ]

        # Integral with anti-windup
        self ._integral +=theta *self .dt 
        self ._integral =np .clip (
        self ._integral ,-self .integral_limit ,self .integral_limit 
        )

        u_lqr =-self .K_lqr @state 

        u_integral =self .integral_gain *self ._integral 

        return float (u_lqr +u_integral )

    def get_gain_vector (self )->np .ndarray :
        """Return the gain vector K such that u ≈ -K @ x."""
        return self .K_lqr .copy ()

    def get_damping_control (self ,state :np .ndarray )->float :
        """Emergency damping-only control."""
        x ,x_dot ,theta ,theta_dot =state 
        # Heavy damping on velocities + proportional on angle
        return -3.0 *x_dot +50.0 *theta -30.0 *theta_dot 
