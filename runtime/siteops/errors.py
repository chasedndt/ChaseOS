"""Typed errors for the ChaseOS SiteOps production scaffold."""

from __future__ import annotations


class SiteOpsError(ValueError):
    """Base SiteOps error."""


class SiteOpsValidationError(SiteOpsError):
    """Raised when a SiteOps object fails validation."""


class SiteOpsPolicyError(SiteOpsError):
    """Raised when a SiteOps policy check fails closed."""


class SiteOpsNotFoundError(SiteOpsError):
    """Raised when a SiteOps object cannot be found in scoped storage."""


class SiteOpsSecretError(SiteOpsValidationError):
    """Raised when raw secret-like material appears in SiteOps config."""


class SiteOpsSecurityError(SiteOpsValidationError):
    """Raised when a scoped object would cross tenant/user/session boundaries."""
