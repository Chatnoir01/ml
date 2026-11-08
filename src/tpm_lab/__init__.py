"""TPM mutual-learning research simulator; NEVER production key agreement."""

from .sync import TPM, TPMProtocol, run_study, trial

__all__ = ["TPM", "TPMProtocol", "run_study", "trial"]
