"""Exact executor method at Hermes b13e2fd6948a59eeb59fe618914147d97a2ee90a.

Imports/class shell are test scaffolding. The complete method is native source.
"""
import asyncio
from contextvars import copy_context


class GatewayRunner:
    async def _run_in_executor_with_context(self, func, *args):
        """Run blocking work in the thread pool while preserving session contextvars."""
        loop = asyncio.get_running_loop()
        ctx = copy_context()
        return await loop.run_in_executor(None, ctx.run, func, *args)

    def scheduling_seam(self, run_sync):
        # Surrounding method is scaffolding; these statements are the exact
        # pinned main-loop scheduling site, not the complete conversation loop.
            _warning_fired = False
            _executor_task = asyncio.ensure_future(
                self._run_in_executor_with_context(run_sync)
            )

            _inactivity_timeout = False
            return _executor_task
