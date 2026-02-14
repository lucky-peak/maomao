from maomao.sources.base import KnowledgeSource, SourceChange, SourceItem, SourceRegistry
from maomao.sources.local_doc import LocalDocSource
from maomao.sources.siyuan import SiyuanSource

__all__ = [
    "KnowledgeSource",
    "SourceRegistry",
    "SourceItem",
    "SourceChange",
    "SiyuanSource",
    "LocalDocSource",
]

SourceRegistry.register(SiyuanSource)
SourceRegistry.register(LocalDocSource)
