# PROBE Documentation Guide

This directory contains the formal documentation for the **PROBE** (Projection-Restricted Online Behavior Engine) framework.

## Files

- `probe_whitepaper.tex`: The main LaTeX source file for the technical whitepaper. It includes the mathematical derivations, architecture diagrams (via TikZ), and a summary of experimental results.

## How to Compile

To generate the PDF version of the whitepaper, use `pdflatex`. It is recommended to run it twice to ensure all references and labels are correctly resolved.

```bash
pdflatex probe_whitepaper.tex
pdflatex probe_whitepaper.tex
```

## Prerequisites

You will need a LaTeX distribution installed on your system (e.g., TeX Live, MiKTeX, or MacTeX). The following packages are required:

- `amsmath`, `amssymb`, `amsthm`
- `graphicx`
- `hyperref`
- `geometry`
- `booktabs`
- `xcolor`
- `listings`
- `tikz` (with `shapes`, `arrows`, `positioning` libraries)

## Summary of Content

The whitepaper covers:
1. **System Architecture**: A high-level view of the signal flow between the Plant, Monitor, Fault Handler, and Controllers.
2. **Lyapunov Projection Layer**: The formal mathematical derivation of the stability-preserving control bounds.
3. **Adversarial Robustness**: A summary of how PROBE handles extreme saturation, control delays, and sensor corruption.
4. **Pareto Efficiency**: Comparison against Weak and Strong LQR baselines.
