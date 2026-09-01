# ==============================================================================
# cookies.py - YouTube Cookies Manager
# ==============================================================================
# This file manages the downloading and loading of YouTube cookies.
# Features:
# - Downloads cookies from an external raw URL
# - Caches and randomizes cookies for requests
# ==============================================================================

import os
import random
import aiohttp
from ZefronMusic import logger

class CookieManager:
    def __init__(self):
        self.cookies = []  # List of available cookie files
        self.checked = False  # Whether cookies directory has been checked
        self.warned = False  # Whether missing cookies warning has been shown

    @staticmethod
    def _is_netscape_content(content: bytes) -> bool:
        """Return whether content looks like a yt-dlp Netscape cookie file."""
        try:
            text = content.decode("utf-8-sig")
        except UnicodeDecodeError:
            return False

        lines = text.splitlines()
        has_header = any(
            line.strip().lower().startswith("# netscape http cookie file")
            for line in lines[:10]
        )
        has_cookie = any(
            not line.startswith("#") and len(line.split("\t")) == 7
            for line in lines
        )
        return has_header and has_cookie

    def _refresh(self) -> None:
        """Discover only valid Netscape cookie files."""
        self.cookies = []
        if os.path.exists("ZefronMusic/cookies"):
            for file in sorted(os.listdir("ZefronMusic/cookies")):
                if not file.endswith(".txt"):
                    continue
                path = os.path.join("ZefronMusic/cookies", file)
                try:
                    with open(path, "rb") as cookie_file:
                        if self._is_netscape_content(cookie_file.read()):
                            self.cookies.append(file)
                except OSError:
                    continue
        self.checked = True

    def has_cookies(self) -> bool:
        """Check for usable local cookies without emitting a warning."""
        if not self.checked:
            self._refresh()
        return bool(self.cookies)

    def get_cookies(self):
        if not self.checked:
            self._refresh()
        if not self.cookies:
            if not self.warned:
                self.warned = True
                logger.warning("Cookies are missing; downloads might fail.")
            return None
        return f"ZefronMusic/cookies/{random.choice(self.cookies)}"

    async def save_cookies(self, urls: list[str]) -> None:
        logger.info("🍪 Saving cookies from urls...")
        saved_count = 0
        os.makedirs("ZefronMusic/cookies", exist_ok=True)
        for url in urls:
            try:
                path = f"ZefronMusic/cookies/cookie{random.randint(10000, 99999)}.txt"
                link = url.replace("me/", "me/raw/")
                async with aiohttp.ClientSession() as session:
                    async with session.get(link) as resp:
                        if resp.status != 200:
                            logger.error(f"❌ Cookie download failed: HTTP {resp.status} from {url}")
                            continue
                        content = await resp.read()
                        if not self._is_netscape_content(content):
                            logger.error(
                                f"❌ Cookie file is not valid Netscape format from {url}"
                            )
                            continue
                        with open(path, "wb") as fw:
                            fw.write(content)
                        if os.path.exists(path) and os.path.getsize(path) > 0:
                            saved_count += 1
                            cookie_filename = os.path.basename(path)
                            logger.info(f"✅ Saved: {cookie_filename} ({len(content)} bytes)")
            except Exception as e:
                logger.error(f"❌ Cookie download error from {url}: {e}")
        
        # Refresh cookie list
        self._refresh()
        
        if saved_count > 0:
            logger.info(f"✅ Cookies saved. ({saved_count} file(s))")
        else:
            logger.error("❌ No cookies saved! Check COOKIE_URL in .env. YouTube downloads will fail!")
