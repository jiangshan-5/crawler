import re

# Site-specific rules for headers, anti-bot markers, and strategies.
# This makes the engine data-driven and easy to extend.

SITE_RULES = {
    "flaticon.com": {
        "headers": {
            "Referer": "https://www.flaticon.com/",
            "Origin": "https://www.flaticon.com",
            "Sec-Fetch-Site": "same-origin",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Dest": "document",
            "sec-ch-ua": '"Not(A:Brand";v="99", "Google Chrome";v="120", "Chromium";v="120"',
            "Upgrade-Insecure-Requests": "1",
        },
        "anti_bot_markers": [
            "access denied",
            "support@freepik.com",
            "error reference",
            "subject=access%20denied"
        ],
        "wait_strategy": [
            (r"/free-icons/", 1.2),
            (r".*", 1.8)
        ],
        "force_headed": True,
        "heuristic_fallback": "flaticon_v1"
    },
    "biquuge.com": {
        "headers": {
            "Referer": "https://www.biquuge.com/",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
            "Upgrade-Insecure-Requests": "1",
        },
        "anti_bot_markers": [
            "访问频繁",
            "安全验证",
            "验证码",
            "403 forbidden",
            "access denied",
            "请稍后再试",
            "请求过于频繁",
            "系统检测到异常"
        ],
        "search_templates": [
            "https://www.biquuge.com/search.php?q={q}",
            "https://www.biquuge.com/search.php?keyword={q}",
        ],
        "performance": {
            "max_workers": 32,
            "retry_count": 2,
            "sample_count": 5,
            "max_subpages": 20
        },
        "force_headed": False
    },
    "5sing.kugou.com": {
        "force_headed": True,
        "anti_bot_markers": ["验证码", "稍后再试"],
        "wait_strategy": [
            ("search", 5),   # search pages need extra JS render time
            (".*", 3)
        ],
        "performance": {
            "recommended_wait": 5
        }
    },
    "kuwo.cn": {
        "force_headed": True
    },
    "guomantuku.com": {
        "force_headed": True
    }
}

def get_site_rule(url):
    """
    Look up the applicable rule for a given URL.
    Returns the first matching rule or a default empty rule.
    """
    if not url:
        return {}
    
    url_lower = str(url).lower()
    for domain, rule in SITE_RULES.items():
        if domain in url_lower:
            return rule
    return {}

def get_recommended_wait(url, rules=None):
    """Calculate recommended wait time based on URL patterns in rules."""
    rules = rules or get_site_rule(url)
    strategy = rules.get("wait_strategy", [])
    if not strategy:
        return 3 # Default wait
    
    for pattern, wait_time in strategy:
        if re.search(pattern, url):
            return wait_time
    return 3
