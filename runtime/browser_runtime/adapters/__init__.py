"""Provider wrappers for the ChaseOS Browser Runtime Adapter spike."""

from runtime.browser_runtime.adapters.browser_use_cli import BrowserUseCLIAdapter
from runtime.browser_runtime.adapters.cdp_design import CDPAdapterDesignRequest, evaluate_cdp_adapter_design

__all__ = ["BrowserUseCLIAdapter", "CDPAdapterDesignRequest", "evaluate_cdp_adapter_design"]
