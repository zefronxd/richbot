# ==============================================================================
# download.py - YouTube Downloader Engine
# ==============================================================================
# This file orchestrates the downloading of audio and video from YouTube.
# Features:
# - Limits concurrency using semaphores
# - Prevents duplicate concurrent downloads using locks
# - Executes yt-dlp to download streams and files
# - Resolves Spotify fallbacks lazily
# ==============================================================================

import re
import glob
import os
import subprocess
import time
import asyncio
from pathlib import Path
from typing import Optional
import aiohttp
import yt_dlp
from ZefronMusic import config, logger

class Downloader:
    def __init__(self, cookies_manager, storage_manager, searcher):
        self._cookies = cookies_manager
        self._storage = storage_manager
        self._searcher = searcher
        self._download_locks: dict = {}
        self._download_semaphore = asyncio.Semaphore(5)
        self._max_video_height = getattr(config, "VIDEO_MAX_HEIGHT", 1080)
        
    def _get_download_lock(self, video_id: str) -> asyncio.Lock:
        if video_id not in self._download_locks:
            self._download_locks[video_id] = asyncio.Lock()
        return self._download_locks[video_id]

    async def _normalize_external_audio(
        self, source: Path, target: Path
    ) -> Optional[str]:
        """Convert API audio responses to a real MP3 container.

        Some media APIs return WebM/Opus bytes for an audio request while
        naming the response `.mp3`. Local FFmpeg may still probe that file,
        but Heroku's FFprobe can return empty JSON for the mislabeled input.
        """
        temporary_target = target.with_name(f".{target.stem}.normalized.mp3")

        def _convert() -> bool:
            try:
                result = subprocess.run(
                    [
                        "ffmpeg",
                        "-hide_banner",
                        "-loglevel",
                        "error",
                        "-y",
                        "-i",
                        str(source),
                        "-vn",
                        "-c:a",
                        "libmp3lame",
                        "-b:a",
                        "128k",
                        "-ar",
                        "48000",
                        "-ac",
                        "2",
                        str(temporary_target),
                    ],
                    capture_output=True,
                    text=True,
                    timeout=180,
                )
                if result.returncode != 0:
                    logger.warning(
                        f"⚠️ Could not normalize external audio for "
                        f"{source.stem}: {result.stderr[-500:]}"
                    )
                    return False
                return self._storage.is_valid_file(str(temporary_target))
            except FileNotFoundError:
                logger.warning(
                    "⚠️ FFmpeg is unavailable; using the original external audio file."
                )
                return False
            except (OSError, subprocess.TimeoutExpired) as ex:
                logger.warning(
                    f"⚠️ External audio normalization failed for {source.stem}: {ex}"
                )
                return False

        try:
            converted = await asyncio.to_thread(_convert)
            if not converted:
                return None
            os.replace(temporary_target, target)
            return str(target)
        finally:
            try:
                if temporary_target.exists():
                    temporary_target.unlink()
            except OSError:
                pass

    async def _download_with_external_api(
        self, video_id: str, video: bool = False
    ) -> Optional[str]:
        """Download media through the configured external API when available."""
        api_key = getattr(config, "API_KEY", "").strip()
        api_urls = getattr(config, "API_URLS", None) or [
            getattr(config, "API_URL", "").strip()
        ]
        api_urls = [url.rstrip("/") for url in api_urls if url]
        if not api_urls or not api_key:
            return None

        extension = "mp4" if video else "mp3"
        target = Path("downloads") / f"{video_id}.{extension}"
        temporary = Path("downloads") / f".{video_id}.{extension}.part"

        timeout = aiohttp.ClientTimeout(total=600 if video else 300)
        params = {
            "url": video_id,
            "type": "video" if video else "audio",
            "api_key": api_key,
        }
        try:
            async with aiohttp.ClientSession(timeout=timeout) as session:
                for api_url in api_urls:
                    endpoint = api_url
                    if not endpoint.endswith("/download"):
                        endpoint = f"{endpoint}/download"
                    try:
                        async with session.get(endpoint, params=params) as response:
                            if response.status != 200:
                                logger.warning(
                                    f"⚠️ External downloader returned HTTP {response.status} "
                                    f"for {video_id} at {api_url}; trying the next endpoint."
                                )
                                continue

                            with temporary.open("wb") as media_file:
                                async for chunk in response.content.iter_chunked(131072):
                                    media_file.write(chunk)

                        if not temporary.exists() or not self._storage.is_valid_file(
                            str(temporary)
                        ):
                            logger.warning(
                                f"⚠️ External downloader returned invalid media for "
                                f"{video_id} at {api_url}; trying the next endpoint."
                            )
                            continue

                        if not video:
                            normalized = await self._normalize_external_audio(
                                temporary, target
                            )
                            if normalized:
                                try:
                                    temporary.unlink()
                                except OSError:
                                    pass
                                logger.info(
                                    f"✅ Normalized external audio for {video_id} to MP3."
                                )
                                return normalized
                            logger.warning(
                                f"⚠️ External API audio for {video_id} could not be "
                                "normalized; falling back to yt-dlp with cookies."
                            )
                            try:
                                temporary.unlink()
                            except OSError:
                                pass
                            continue

                        os.replace(temporary, target)
                        logger.info(
                            f"✅ Downloaded {video_id} through the external media API."
                        )
                        return str(target)
                    except asyncio.TimeoutError:
                        logger.warning(
                            f"⚠️ External downloader timed out for {video_id} at "
                            f"{api_url}; trying the next endpoint."
                        )
                    except Exception as ex:
                        logger.warning(
                            f"⚠️ External downloader failed for {video_id} at "
                            f"{api_url}: {ex}; trying the next endpoint."
                        )

            logger.warning(
                f"⚠️ All external downloader endpoints failed for {video_id}; "
                "falling back to yt-dlp."
            )
            return None
        finally:
            try:
                if temporary.exists():
                    temporary.unlink()
            except OSError:
                pass

    async def download(self, video_id: str, is_live: bool = False, video: bool = False) -> Optional[str]:
        # Lazily resolve query or Spotify link to a YouTube video ID if needed
        if not re.fullmatch(r"[A-Za-z0-9_-]{11}", video_id):
            try:
                from ZefronMusic import spotify
                if spotify.valid(video_id):
                    resolved = await spotify.search(video_id, 0)
                else:
                    resolved = await self._searcher.search(video_id, 0)
                if resolved and resolved.id:
                    video_id = resolved.id
                    is_live = getattr(resolved, "is_live", is_live)
                else:
                    logger.warning(f"Could not resolve '{video_id}' for download")
                    return None
            except Exception as e:
                logger.warning(f"Failed to lazily resolve '{video_id}': {e}")
                return None

        url = "https://www.youtube.com/watch?v=" + video_id

        # Extract live stream URL
        if is_live:
            cookie = self._cookies.get_cookies()
            ydl_opts = {
                "quiet": True,
                "no_warnings": True,
                "cookiefile": cookie,
                "format": "bestaudio/best",
                "noplaylist": True,
                "socket_timeout": 20,
                "extractor_retries": 5,
                "sleep_interval_requests": 1,
            }

            def _extract_url():
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    try:
                        info = ydl.extract_info(url, download=False)
                        if not info:
                            return None

                        direct = info.get("url")
                        if direct:
                            return direct

                        # Find URL in formats
                        for fmt in info.get("formats", []):
                            if fmt.get("acodec") != "none" and fmt.get("url"):
                                return fmt["url"]

                        return info.get("manifest_url")
                    except yt_dlp.utils.ExtractorError as ex:
                        error_msg = str(ex)
                        if "not available" in error_msg.lower():
                            logger.error(
                                "Video format not available or region-blocked.")
                        else:
                            logger.error(
                                "Live stream URL extraction failed: %s", ex)
                        return None
                    except Exception as ex:
                        logger.error(
                            "Unexpected error during live stream extraction: %s", ex)
                        return None

            try:
                stream_url = await asyncio.wait_for(asyncio.to_thread(_extract_url), timeout=35)
            except asyncio.TimeoutError:
                logger.error("Live stream URL extraction timed out for %s", video_id)
                return None

            return stream_url

        # Let yt-dlp choose the best format
        filename_pattern = f"downloads/{video_id}"

        def _check_cache() -> Optional[str]:
            """Check downloads/ for a valid existing file. Deletes invalid stubs on the way."""
            existing_files = [
                f for f in glob.glob(f"{filename_pattern}.*")
                if not f.endswith((".part", ".ytdl", ".temp"))
            ]
            if video:
                video_candidates = [
                    f for f in existing_files
                    if Path(f).suffix.lower() in {".mp4", ".mkv", ".mov"}
                ]
                for f in video_candidates:
                    if self._storage.is_valid_file(f):
                        return f
                    self._storage.delete_stub(f)
            else:
                audio_candidates = [
                    f for f in existing_files
                    if Path(f).suffix.lower() in {".m4a", ".webm", ".opus", ".mp3", ".ogg", ".wav", ".flac"}
                ]
                for f in audio_candidates:
                    if self._storage.is_valid_file(f):
                        return f
                    self._storage.delete_stub(f)
                # Fallback to mp4 for audio
                container_fallbacks = [
                    f for f in existing_files
                    if Path(f).suffix.lower() in {".mp4", ".mkv", ".mov"}
                ]
                for f in container_fallbacks:
                    if self._storage.is_valid_file(f):
                        return f
                    self._storage.delete_stub(f)
            return None

        # Fast path: check cache without acquiring any lock
        cached = _check_cache()
        if cached:
            return cached

        # Create downloads dir
        downloads_dir = Path("downloads")
        if not downloads_dir.exists():
            try:
                downloads_dir.mkdir(parents=True, exist_ok=True)
                logger.info("📁 Created downloads directory")
            except Exception as e:
                logger.error(f"❌ Cannot create downloads directory: {e}")
                return None

        # Acquire per-video-ID lock to prevent duplicate concurrent downloads of the same video.
        async with self._get_download_lock(video_id):
            cached = _check_cache()
            if cached:
                return cached

            # **PERFORMANCE FIX**: Use semaphore to limit concurrent downloads
            async with self._download_semaphore:
                # Always try the external API before yt-dlp. Cookies are only
                # used by the fallback path below if the API is unavailable or
                # cannot return usable media.
                if not is_live:
                    logger.info(
                        f"⬇️ Trying external media API first for {video_id} "
                        "before cookies-enabled yt-dlp fallback."
                    )
                    external_file = await self._download_with_external_api(
                        video_id, video=video
                    )
                    if external_file:
                        return external_file

                logger.info(
                    f"⬇️ Falling back to yt-dlp with cookies for {video_id}."
                )
                cookie = self._cookies.get_cookies()
                base_opts = {
                    "outtmpl": "downloads/%(id)s.%(ext)s",
                    "quiet": True,
                    "noplaylist": True,
                    "geo_bypass": True,
                    "no_warnings": True,
                    "overwrites": False,
                    "nocheckcertificate": True,
                    "continuedl": True,
                    "noprogress": True,
                    "concurrent_fragment_downloads": 4,
                    "http_chunk_size": 524288,  # 512KB chunks
                    "socket_timeout": 30,
                    "retries": 2,
                    "fragment_retries": 2,
                    "extractor_retries": 5,
                    "sleep_interval_requests": 1,
                }

                if video:
                    height_filter = ""
                    if self._max_video_height and self._max_video_height > 0:
                        height_filter = f"[height<={self._max_video_height}]"
                    format_chain = (
                        f"bestvideo[ext=mp4]{height_filter}+bestaudio[ext=m4a]/"
                        f"bestvideo{height_filter}+bestaudio/"
                        "bestvideo+bestaudio/best"
                    )
                    ydl_opts = {
                        **base_opts,
                        "format": format_chain,
                        "merge_output_format": "mp4",
                        "postprocessors": [
                            {
                                "key": "FFmpegVideoConvertor",
                                "preferedformat": "mp4",
                            }
                        ],
                    }
                else:
                    ydl_opts = {
                        **base_opts,
                        "format": "bestaudio/best",
                        "postprocessors": [],
                    }

                ydl_opts_cookie = {
                    **ydl_opts,
                    "cookiefile": cookie,
                }

                def _download(ydl_runtime_opts, is_retry: bool = False):
                    ydl_instance = None
                    retry_with_alternate_client = False
                    try:
                        ydl_instance = yt_dlp.YoutubeDL(ydl_runtime_opts)
                        info = ydl_instance.extract_info(url, download=True)
                        if not info:
                            logger.error(f"❌ Failed to extract info for {video_id}")
                            return None

                        time.sleep(0.5)
                        located = self._storage.locate_download_file(video_id, video=video)
                        if located:
                            return located
                        logger.error(f"❌ Download completed but file not found for: {video_id}")
                        return None
                    except yt_dlp.utils.ExtractorError as ex:
                        error_msg = str(ex)
                        error_lower = error_msg.lower()
                        if (
                            not is_retry
                            and "the page needs to be reloaded" in error_lower
                        ):
                            retry_with_alternate_client = True
                        elif "not available" in error_lower:
                            logger.error(
                                "❌ Video not available: May be region-blocked or private.")
                        elif "age" in error_lower:
                            logger.error(
                                "❌ Age-restricted video: Cookies required.")
                        else:
                            logger.error("❌ YouTube extraction failed: %s", ex)
                        if not retry_with_alternate_client:
                            return None
                    except yt_dlp.utils.DownloadError as ex:
                        error_msg = str(ex)
                        error_lower = error_msg.lower()
                        recovered = self._storage.locate_download_file(video_id, video=video)
                        if (
                            not is_retry
                            and "the page needs to be reloaded" in error_lower
                        ):
                            retry_with_alternate_client = True
                        elif "unable to rename file" in error_lower and recovered:
                            logger.warning(
                                f"⚠️ Renaming failed for {video_id}, using recovered file {Path(recovered).name}"
                            )
                            return recovered
                        if "416" in error_msg or "Requested range not satisfiable" in error_msg:
                            logger.warning(f"⚠️ Range error for {video_id}, skipping")
                        else:
                            logger.warning(f"⚠️ Download error for {video_id}: {ex}")
                            if recovered:
                                logger.warning(
                                    f"⚠️ Using recovered file for {video_id} despite download error"
                                )
                                return recovered
                        if not retry_with_alternate_client:
                            return None
                    except Exception as ex:
                        logger.warning(f"⚠️ Unexpected download error for {video_id}: {ex}")
                        return None
                    finally:
                        if ydl_instance:
                            try:
                                ydl_instance.close()
                            except Exception:
                                pass

                    if retry_with_alternate_client:
                        logger.warning(
                            f"⚠️ YouTube requested a page reload for {video_id}; "
                            "retrying with the web_safari client."
                        )
                        alternate_opts = {
                            **ydl_runtime_opts,
                            "extractor_args": {
                                "youtube": {
                                    "player_client": ["web_safari"],
                                }
                            },
                        }
                        return _download(alternate_opts, is_retry=True)

                return await asyncio.to_thread(_download, ydl_opts_cookie)
