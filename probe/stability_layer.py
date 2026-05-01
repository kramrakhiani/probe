"""Lyapunov Stability Constraint Layer"""

import numpy as np 
from scipy .linalg import solve_continuous_lyapunov 

class LyapunovProjection :
    """Lyapunov-based stability constraint enforcement."""

    def __init__ (
    self ,
    A :np .ndarray ,
    B :np .ndarray ,
    K_pid :np .ndarray ,
    alpha :float =0.1 ,
    Q :np .ndarray =None ,
    ):
        """Args:"""
        self .A =A 
        self .B =B .flatten ()if B .ndim >1 else B # shape (4,)
        self .K_pid =K_pid 
        self .alpha =alpha 

        # Closed-loop A matrix: A_cl = A - B @ K_pid.T
        B_col =self .B .reshape (-1 ,1 )
        K_row =self .K_pid .reshape (1 ,-1 )
        self .A_cl =A -B_col @K_row 

        # Solve continuous-time Lyapunov equation:
        # A_cl^T P + P A_cl = -Q
        # => X = solve_continuous_lyapunov(A_cl^T, -Q)
        if Q is None :
            Q =np .eye (4 )
        self .Q =Q 

        # solve_continuous_lyapunov solves: A X + X A^T = Q
        # We need: A_cl^T P + P A_cl = -Q
        # Rewrite: A_cl^T P + P (A_cl^T)^T = -Q
        # => solve_continuous_lyapunov(A_cl^T, -Q) = P
        self .P =solve_continuous_lyapunov (self .A_cl .T ,-self .Q )

        # Verify P is positive definite
        eigvals =np .linalg .eigvalsh (self .P )
        if np .any (eigvals <=0 ):
            raise ValueError (
            f"Lyapunov matrix P is not positive definite. "
            f"Eigenvalues: {eigvals }. "
            f"Check that A_cl is stable (all eigenvalues have negative real parts)."
            )

            # Precompute Q - alpha*P for the stability condition
        self .Q_alpha =self .Q -self .alpha *self .P 

        cl_eigvals =np .linalg .eigvals (self .A_cl )
        self ._cl_eigenvalues =cl_eigvals 
        if np .any (np .real (cl_eigvals )>=0 ):
            raise ValueError (
            f"Closed-loop system is not stable. "
            f"Eigenvalues: {cl_eigvals }. "
            f"Check PID gains."
            )

            # Small epsilon for numerical stability
        self ._eps =1e-10 

    def compute_lyapunov (self ,x :np .ndarray )->float :
        """Compute V(x) = x^T P x."""
        return float (x @self .P @x )

    def compute_lyapunov_derivative (
    self ,x :np .ndarray ,u_nn :float =0.0 
    )->float :
        """Compute V_dot(x, u_nn) = -x^T Q x + 2 (B^T P x) * u_nn."""
        # V_dot under PID only: -x^T Q x
        v_dot_pid =-x @self .Q @x 

        # Additional term from u_nn: 2 * (B^T P x) * u_nn
        phi =float (self .B @self .P @x )
        v_dot =v_dot_pid +2.0 *phi *u_nn 

        return float (v_dot )

    def project (
    self ,
    u_nn_candidate :float ,
    x :np .ndarray ,
    u_pid :float =0.0 ,
    env_limit :float =5.0 ,
    nn_clamp :float =1.5 ,
    )->dict :
        """Project u_nn onto the admissible set satisfying physical and Lyapunov constraints."""
        phi =float (self .B @self .P @x )
        psi =float (x @self .Q_alpha @x )
        V =self .compute_lyapunov (x )

        # 1. Determine Lyap bounds
        lyap_min =-1e6 
        lyap_max =1e6 

        safe_phi =phi 

        if abs (phi )>self ._eps :
        # Numerical stability: clamp denominator to prevent extreme bounds
            safe_phi =phi if abs (phi )>=1e-10 else 1e-10 *(1 if phi >=0 else -1 )
            u_bound =psi /(2.0 *safe_phi )
            # Clip extreme bounds
            u_bound =float (np .clip (u_bound ,-1e6 ,1e6 ))

            if phi >0 :
                lyap_max =u_bound 
            else :
                lyap_min =u_bound 

        projection_degenerate =abs (phi )<self ._eps 

        # 2. Determine Physical & Clamp bounds
        phys_min =-env_limit -u_pid 
        phys_max =env_limit -u_pid 

        u_min =max (lyap_min ,phys_min ,-nn_clamp )
        u_max =min (lyap_max ,phys_max ,nn_clamp )

        conflict =False 
        if u_min >u_max :
        # Empty intersection! Physical constraints contradict stability.
        # Safest physical action is to minimize NN interference.
            u_safe =0.0 
            conflict =True 
            was_projected =True 
        else :
            u_safe =np .clip (u_nn_candidate ,u_min ,u_max )
            was_projected =(u_safe !=u_nn_candidate )

        V_dot =self .compute_lyapunov_derivative (x ,u_safe )

        return {
        "u_nn_safe":float (u_safe ),
        "V":V ,
        "V_dot":V_dot ,
        "was_projected":was_projected ,
        "phi_raw":phi ,
        "phi_clamped":safe_phi ,
        "psi":psi ,
        "conflict":conflict ,
        "u_min_allowed":float (u_min ),
        "u_max_allowed":float (u_max ),
        "lyap_min":float (lyap_min ),
        "lyap_max":float (lyap_max ),
        "phys_min":float (phys_min ),
        "phys_max":float (phys_max ),
        "projection_degenerate":projection_degenerate ,
        }

    def get_info (self )->dict :
        """Return diagnostic information about the stability layer."""
        return {
        "P_eigenvalues":np .linalg .eigvalsh (self .P ).tolist (),
        "A_cl_eigenvalues":[complex (e )for e in self ._cl_eigenvalues ],
        "alpha":self .alpha ,
        "Q_alpha_eigenvalues":np .linalg .eigvalsh (self .Q_alpha ).tolist (),
        }
