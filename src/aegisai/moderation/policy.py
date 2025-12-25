"""
Policy helpers: how strict Aegis should be in different modes. 
We can add modes in future(child, teen, adult, streamer, custom etc).
"""

from .text_rules import TextModerationResult


def should_block_text(result: TextModerationResult, mode: str = "default") -> bool:
    return result.count > 0
