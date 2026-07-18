from __future__ import annotations

import asyncio
import re
import shutil


PUBLIC_URL_RE = re.compile(r"https://[a-z0-9-]+\.trycloudflare\.com")


class TunnelError(RuntimeError):
    pass


class CloudflareQuickTunnel:
    def __init__(self, port: int) -> None:
        self.port = port
        self.process: asyncio.subprocess.Process | None = None
        self.public_url: str | None = None

    async def start(self, timeout: float = 30) -> str:
        executable = shutil.which("cloudflared")
        if not executable:
            raise TunnelError("cloudflared is required for the one-command local demo")
        self.process = await asyncio.create_subprocess_exec(
            executable,
            "tunnel",
            "--url",
            f"http://127.0.0.1:{self.port}",
            "--no-autoupdate",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
        )

        async def _read_url() -> str:
            assert self.process and self.process.stdout
            while line := await self.process.stdout.readline():
                text = line.decode("utf-8", errors="replace")
                match = PUBLIC_URL_RE.search(text)
                if match:
                    return match.group(0)
            raise TunnelError("cloudflared exited before publishing a URL")

        try:
            self.public_url = await asyncio.wait_for(_read_url(), timeout=timeout)
            return self.public_url
        except Exception:
            await self.stop()
            raise

    async def stop(self) -> None:
        if not self.process or self.process.returncode is not None:
            return
        self.process.terminate()
        try:
            await asyncio.wait_for(self.process.wait(), timeout=5)
        except asyncio.TimeoutError:
            self.process.kill()
            await self.process.wait()
