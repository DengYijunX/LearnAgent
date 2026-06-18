"""ReadUrl 工具 —— 读取网页内容。"""

import ipaddress
import logging
import os
import re
import socket
from urllib.parse import urljoin, urlparse

from app.tools.base import Tool

logger = logging.getLogger(__name__)

# 禁止访问的地址段（防 SSRF）
_BLOCKED_CIDRS = [
    # IPv4
    ipaddress.ip_network("127.0.0.0/8"),       # loopback
    ipaddress.ip_network("10.0.0.0/8"),        # private A
    ipaddress.ip_network("172.16.0.0/12"),     # private B
    ipaddress.ip_network("192.168.0.0/16"),    # private C
    ipaddress.ip_network("169.254.0.0/16"),    # link-local / cloud metadata
    ipaddress.ip_network("0.0.0.0/8"),         # "this" network
    ipaddress.ip_network("100.64.0.0/10"),     # CGNAT
    ipaddress.ip_network("198.18.0.0/15"),     # benchmark
    ipaddress.ip_network("224.0.0.0/4"),       # multicast
    ipaddress.ip_network("240.0.0.0/4"),       # reserved
    # IPv6
    ipaddress.ip_network("::1/128"),           # loopback
    ipaddress.ip_network("fe80::/10"),         # link-local
    ipaddress.ip_network("fc00::/7"),          # unique local
    ipaddress.ip_network("ff00::/8"),          # multicast
]


def _is_safe_url(url: str) -> tuple[bool, str]:
    """验证 URL 不会访问内网/本地地址。返回 (安全?, 用户友好消息)，
    内部详情通过 logger 记录。"""
    try:
        parsed = urlparse(url)
        hostname = parsed.hostname
        if not hostname:
            return False, "无效的主机名"

        # 先检查是否为 IP 字面量
        try:
            addr = ipaddress.ip_address(hostname)
            for cidr in _BLOCKED_CIDRS:
                if addr in cidr:
                    logger.warning("SSRF blocked: %s → %s", url, hostname)
                    return False, "不允许访问内网地址"
            return True, ""
        except ValueError:
            pass  # 不是 IP，继续 DNS 检查

        # DNS 解析后再次检查
        resolved = socket.getaddrinfo(hostname, None)
        for _, _, _, _, sockaddr in resolved:
            ip = sockaddr[0]
            addr = ipaddress.ip_address(ip)
            for cidr in _BLOCKED_CIDRS:
                if addr in cidr:
                    logger.warning("SSRF blocked: %s → %s → %s", url, hostname, ip)
                    return False, "不允许访问内网地址"
        return True, ""

    except socket.gaierror:
        logger.info("DNS 解析失败: %s → %s", url, hostname)
        return False, "无法解析该域名"
    except Exception as exc:
        logger.error("URL 安全检查异常: %s → %s: %s", url, hostname, exc)
        return False, "URL 格式无效"


class MockReadUrl(Tool):
    name = "read_url"
    description = "读取网页正文，提取主要内容。输入 url 地址。"
    input_schema = {
        "type": "object",
        "properties": {
            "url": {
                "type": "string",
                "description": "要读取的网页 URL",
            }
        },
        "required": ["url"],
    }

    async def call(self, tool_input: dict, context: dict | None = None) -> dict:
        url = tool_input.get("url", "")
        return {
            "content": f"[Mock 网页内容] 来自 {url} 的正文摘要：\n"
                       f"这是关于该技术主题的核心介绍内容（mock）。\n"
                       f"主要包含概念解释、使用示例和注意事项。",
            "metadata": {
                "title": f"文档 - {url}",
                "source": url,
            },
        }


class RealReadUrl(Tool):
    name = "read_url"
    description = "读取指定 URL 的网页内容，提取正文文本。输入 url 地址。"
    input_schema = {
        "type": "object",
        "properties": {
            "url": {
                "type": "string",
                "description": "要读取的网页 URL",
            }
        },
        "required": ["url"],
    }

    def __init__(self, timeout: int = 15, max_content_length: int = 8000):
        self._timeout = timeout
        self._max_len = max_content_length

    async def call(self, tool_input: dict, context: dict | None = None) -> dict:
        url = (tool_input.get("url") or "").strip()
        if not url:
            return {"isError": True, "error": "请提供 url 参数。"}

        safe, reason = _is_safe_url(url)
        if not safe:
            return {"isError": True, "error": f"安全限制：{reason}"}

        try:
            import httpx

            proxy = os.environ.get("HTTPS_PROXY") or os.environ.get("HTTP_PROXY") or os.environ.get("ALL_PROXY") or ""
            client_kwargs = {"timeout": self._timeout, "follow_redirects": False}
            if proxy:
                client_kwargs["proxies"] = proxy

            async with httpx.AsyncClient(**client_kwargs) as client:
                # 手动处理重定向，每次跳转都重新验证目标 URL
                current_url = url
                for _ in range(5):  # 最多跟 5 次跳转
                    response = await client.get(current_url, headers={
                        "User-Agent": "Mozilla/5.0 (compatible; LearnAgent/0.2; +https://github.com/DengYijunX/LearnAgent)",
                        "Accept": "text/html,application/xhtml+xml",
                    })
                    if response.status_code == 403:
                        response = await client.get(current_url, headers={
                            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
                            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
                            "Accept-Encoding": "gzip, deflate, br",
                            "Referer": "https://www.google.com/",
                            "Cache-Control": "no-cache",
                            "DNT": "1",
                        })

                    # 检测重定向
                    if response.status_code in (301, 302, 303, 307, 308):
                        loc = response.headers.get("Location")
                        if not loc:
                            break
                        # 处理相对 URL
                        next_url = urljoin(current_url, loc)
                        safe, reason = _is_safe_url(next_url)
                        if not safe:
                            return {"isError": True, "error": f"安全限制：重定向目标 {reason}"}
                        current_url = next_url
                        continue

                    break  # 不是重定向，停止跟跳

                # 提取内容
                if response.status_code == 403:
                    html = response.text
                else:
                    response.raise_for_status()
                    html = response.text

            text = self._extract_text(html)
            title = self._extract_title(html)
            links = self._extract_same_domain_links(html, url)

            if len(text) > self._max_len:
                text = text[:self._max_len] + f"\n...(截断，原文共 {len(text)} 字符)"

            return {
                "content": text,
                "metadata": {
                    "title": title,
                    "source": url,
                    "links": links,
                },
                "isError": False,
            }
        except Exception as e:
            return {"isError": True, "error": f"读取失败：{e}"}

    @staticmethod
    def _extract_title(html: str) -> str:
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html, "html.parser")
            t = soup.title
            return t.get_text(strip=True)[:200] if t else ""
        except Exception:
            match = re.search(r"<title[^>]*>(.*?)</title>", html, re.IGNORECASE | re.DOTALL)
            return match.group(1).strip()[:200] if match else ""

    @staticmethod
    def _extract_text(html: str) -> str:
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html, "html.parser")
            # 移除不需要的标签
            for tag in soup(["script", "style", "noscript", "iframe", "nav", "footer", "header", "aside"]):
                tag.decompose()
            # 优先提取 <main> 或 <article> 内容
            main = soup.find("main") or soup.find("article") or soup.find("body")
            if main:
                text = main.get_text(separator="\n", strip=True)
            else:
                text = soup.get_text(separator="\n", strip=True)
            # 清理空白行
            lines = [l.strip() for l in text.split("\n") if l.strip()]
            return "\n".join(lines)
        except Exception:
            # regex fallback
            html = re.sub(r"<(script|style|noscript|iframe)[^>]*>.*?</\1>", "", html, flags=re.IGNORECASE | re.DOTALL)
            text = re.sub(r"<[^>]+>", " ", html)
            text = re.sub(r"\s+", " ", text)
            text = text.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">").replace("&quot;", '"').replace("&#39;", "'").replace("&nbsp;", " ")
            return text.strip()

    @staticmethod
    def _extract_same_domain_links(html: str, source_url: str, limit: int = 20) -> list[str]:
        source_host = urlparse(source_url).netloc.lower()
        if not source_host:
            return []
        links: list[str] = []
        seen: set[str] = set()
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html, "html.parser")
            hrefs = [a.get("href", "") for a in soup.find_all("a")]
        except Exception:
            hrefs = re.findall(r'href=["\']([^"\']+)["\']', html, flags=re.IGNORECASE)

        for href in hrefs:
            href = href.strip()
            if not href or href.startswith(("#", "mailto:", "javascript:")):
                continue
            absolute = urljoin(source_url, href)
            parsed = urlparse(absolute)
            if parsed.netloc.lower() != source_host:
                continue
            cleaned = parsed._replace(fragment="").geturl()
            if cleaned in seen:
                continue
            seen.add(cleaned)
            links.append(cleaned)
            if len(links) >= limit:
                break
        return links
