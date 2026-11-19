"""Core trust vocabulary for Secure Core Mobile.

This package is experimental. Importing it conveys no security assurance.
"""

from .compat import StrEnum


class TrustState(StrEnum):
    TRUSTED = "TRUSTED"
    UNTRUSTED = "UNTRUSTED"
    SIMULATED = "SIMULATED"
    HARDWARE_BACKED = "HARDWARE_BACKED"
    TEST_EVIDENCED = "TEST_EVIDENCED"


class ClaimMaturity(StrEnum):
    CLAIMED = "CLAIMED"
    IMPLEMENTED = "IMPLEMENTED"
    TESTED = "TESTED"
    ADVERSARIALLY_TESTED = "ADVERSARIALLY_TESTED"
    EXTERNALLY_VALIDATED = "EXTERNALLY_VALIDATED"
