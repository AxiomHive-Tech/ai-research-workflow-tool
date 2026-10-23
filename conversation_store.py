"""Chronological conversation organizer with explicit provenance and non-destructive edits.

Similarity suggestions are navigation aids only; they never establish truth or links automatically.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from difflib import SequenceMatcher
import json
from pathlib import Path
import re
from typing import Any

TAGS = {"a", "b", "c", "d", "e", "f"}
HEADINGS = ("Goals and Requirements", "Required Information", "Product and Goal", "References")


def normalize_terms(text: str, mapping: dict[str, str] | None = None) -> tuple[str, list[dict[str, str]]]:
    mapping = mapping or {"axiom hive": "Axiom Hive"}
    normalized = text
    applied = []
    for source, target in mapping.items():
        updated = re.sub(re.escape(source), target, normalized, flags=re.IGNORECASE)
        if updated != normalized:
            applied.append({"from": source, "to": target})
            normalized = updated
    return normalized, applied


@dataclass
class Item:
    item_id: str
    turn_index: int
    speaker: str
    text: str
    normalized_text: str
    tag: str
    topic_id: str
    source: str
    location: str
    timestamp: str | None = None
    normalized_terms: list[dict[str, str]] = field(default_factory=list)
    continuation_of: list[str] = field(default_factory=list)
    references: list[str] = field(default_factory=list)
    duplicates_of: list[str] = field(default_factory=list)
    duplicate_cluster_id: str | None = None
    supports: list[str] = field(default_factory=list)
    contradicts: list[str] = field(default_factory=list)
    status: str = "unverified"
    sensitive: bool = False


@dataclass
class Topic:
    topic_id: str
    created_at_turn: int
    title: str
    items: list[str] = field(default_factory=list)
    related_topics: list[dict[str, str]] = field(default_factory=list)
    outstanding_questions: list[str] = field(default_factory=list)


class ConversationStore:
    """In-memory store; persistence is explicit via save/load JSON."""
    def __init__(self) -> None:
        self.items: dict[str, Item] = {}
        self.topics: dict[str, Topic] = {}
        self.restructure_log: list[dict[str, Any]] = []
        self._duplicate_cluster = 0

    def add_item(self, *, item_id: str, turn_index: int, speaker: str, text: str, tag: str,
                 topic_id: str, source: str, location: str, timestamp: str | None = None,
                 title: str | None = None, references: list[str] | None = None,
                 continuation_of: list[str] | None = None, supports: list[str] | None = None,
                 contradicts: list[str] | None = None, sensitive: bool = False,
                 status: str = "unverified") -> Item:
        if item_id in self.items:
            raise ValueError(f"Duplicate item_id: {item_id}")
        if tag not in TAGS:
            raise ValueError("tag must be one of a, b, c, d, e, f")
        if turn_index < 0 or any(i.turn_index > turn_index for i in self.items.values()):
            raise ValueError("turn_index must be nonnegative and not earlier than stored items")
        if any(link not in self.items for link in (references or []) + (continuation_of or []) + (supports or []) + (contradicts or [])):
            raise ValueError("relationship links must target existing items")
        raw_text = text
        normalized_text, normalized = normalize_terms(raw_text)
        if topic_id not in self.topics:
            if tag not in {"a", "b"}:
                raise ValueError("new topics require tag a or b")
            self.topics[topic_id] = Topic(topic_id, turn_index, title or normalized_text[:80])
            self._log(turn_index, "CreateTopic", {}, {"topic_id": topic_id}, "New subject introduced")
        item = Item(item_id, turn_index, speaker, raw_text, normalized_text, tag, topic_id, source, location, timestamp,
                    normalized, list(continuation_of or []), list(references or []), [], None,
                    list(supports or []), list(contradicts or []), status, sensitive)
        self.items[item_id] = item
        self.topics[topic_id].items.append(item_id)
        self.topics[topic_id].items.sort(key=lambda key: self.items[key].turn_index)
        if tag == "f" and any(marker in text.lower() for marker in ("open question", "unresolved", "outstanding")):
            self.topics[topic_id].outstanding_questions.append(text)
        self._log(turn_index, "AddItem", {}, {"item_id": item_id, "topic_id": topic_id, "tag": tag}, "Captured verbatim information unit")
        return item

    def suggest_duplicates(self, item_id: str, threshold: float = 0.82) -> list[tuple[str, float]]:
        """Return candidate duplicates for human review; no links are changed."""
        item = self.items[item_id]
        candidates = []
        for other_id, other in self.items.items():
            if other_id == item_id:
                continue
            score = SequenceMatcher(None, item.normalized_text.casefold(), other.normalized_text.casefold()).ratio()
            if score >= threshold:
                candidates.append((other_id, score))
        return sorted(candidates, key=lambda pair: (-pair[1], self.items[pair[0]].turn_index))

    def link_duplicate(self, item_id: str, duplicate_id: str, turn_index: int) -> str:
        if item_id not in self.items or duplicate_id not in self.items:
            raise ValueError("duplicate links must target existing items")
        self._duplicate_cluster += 1
        cluster = self.items[item_id].duplicate_cluster_id or self.items[duplicate_id].duplicate_cluster_id or f"dup-{self._duplicate_cluster}"
        self.items[item_id].duplicate_cluster_id = cluster
        self.items[duplicate_id].duplicate_cluster_id = cluster
        if duplicate_id not in self.items[item_id].duplicates_of:
            self.items[item_id].duplicates_of.append(duplicate_id)
        if item_id not in self.items[duplicate_id].duplicates_of:
            self.items[duplicate_id].duplicates_of.append(item_id)
        self._log(turn_index, "Consolidate", {"item_id": item_id}, {"duplicates_of": duplicate_id, "cluster_id": cluster}, "Non-destructive duplicate link; original items retained")
        return cluster

    def link_topics(self, source_topic: str, target_topic: str, relation: str, turn_index: int) -> None:
        allowed = {"RelatedTo", "DependsOn", "Supports"}
        if source_topic not in self.topics or target_topic not in self.topics or relation not in allowed:
            raise ValueError("topics must exist and relation must be RelatedTo, DependsOn, or Supports")
        relation_record = {"topic_id": target_topic, "relation": relation}
        if relation_record not in self.topics[source_topic].related_topics:
            self.topics[source_topic].related_topics.append(relation_record)
            self._log(turn_index, "AddRelation", {}, {"source_topic": source_topic, **relation_record}, "Explicit topic relationship")

    def split_topic(self, topic_id: str, new_topic_id: str, item_ids: list[str], turn_index: int,
                    title: str, rationale: str) -> None:
        if topic_id not in self.topics or new_topic_id in self.topics or not item_ids:
            raise ValueError("source topic must exist, new topic must be unique, and item_ids must be nonempty")
        if any(item_id not in self.topics[topic_id].items for item_id in item_ids):
            raise ValueError("all split items must belong to the source topic")
        self.topics[new_topic_id] = Topic(new_topic_id, turn_index, title)
        for item_id in item_ids:
            self.topics[topic_id].items.remove(item_id)
            self.topics[new_topic_id].items.append(item_id)
            self.items[item_id].topic_id = new_topic_id
        self._log(turn_index, "SplitTopic", {"topic_id": topic_id, "item_ids": list(item_ids)},
                  {"topic_id": new_topic_id, "item_ids": list(item_ids)}, rationale)

    def move_item(self, item_id: str, target_topic_id: str, turn_index: int, rationale: str) -> None:
        if item_id not in self.items or target_topic_id not in self.topics:
            raise ValueError("item and target topic must exist")
        item = self.items[item_id]
        old = item.topic_id
        if old == target_topic_id:
            return
        before = {"item_id": item_id, "topic_id": old}
        self.topics[old].items.remove(item_id)
        item.topic_id = target_topic_id
        self.topics[target_topic_id].items.append(item_id)
        self.topics[target_topic_id].items.sort(key=lambda key: self.items[key].turn_index)
        self._log(turn_index, "ReassignItem", before, {"item_id": item_id, "topic_id": target_topic_id}, rationale)

    def merge_topics(self, first: str, second: str, turn_index: int, *, user_approved: bool = False) -> str:
        if first not in self.topics or second not in self.topics:
            raise ValueError("topics must exist")
        if first == second:
            return first
        has_conflict = any(i.contradicts for i in (self.items[item_id] for item_id in self.topics[first].items + self.topics[second].items))
        if not user_approved and has_conflict:
            raise ValueError("merging topics with contradictions requires explicit user approval")
        target, source = sorted((first, second), key=lambda topic_id: self.topics[topic_id].created_at_turn)
        before = {"topics": [target, source]}
        for item_id in list(self.topics[source].items):
            self.items[item_id].topic_id = target
            self.topics[target].items.append(item_id)
        self.topics[target].items.sort(key=lambda key: self.items[key].turn_index)
        del self.topics[source]
        self._log(turn_index, "MergeTopics", before, {"topic_id": target}, "User approved" if user_approved else "No contradictions identified")
        return target

    def render(self) -> str:
        lines = []
        for heading in HEADINGS:
            lines.extend([f"## {heading}", ""])
            if heading == "References":
                selected = [i for i in self.items.values() if i.source == "document"]
            else:
                selected = list(self.items.values())
            for topic in sorted(self.topics.values(), key=lambda t: t.created_at_turn):
                in_topic = [self.items[item_id] for item_id in topic.items if self.items[item_id] in selected]
                if not in_topic:
                    continue
                lines.append(f"### {topic.title} ({topic.topic_id})")
                for item in sorted(in_topic, key=lambda value: value.turn_index):
                    links = []
                    if item.continuation_of: links.append("continues " + ", ".join(item.continuation_of))
                    if item.references: links.append("references " + ", ".join(item.references))
                    if item.duplicates_of: links.append("duplicates " + ", ".join(item.duplicates_of))
                    if item.supports: links.append("supports " + ", ".join(item.supports))
                    if item.contradicts: links.append("contradicts " + ", ".join(item.contradicts))
                    suffix = f" — links: {'; '.join(links)}" if links else ""
                    lines.append(f"- [{item.tag}] #{item.turn_index} {item.item_id}: {item.normalized_text}{suffix} (provenance: {item.source}, {item.location}; {item.status})")
            if heading == "Goals and Requirements":
                lines.extend(["", "> This view organizes source items; it does not independently establish their truth."])
            lines.append("")
        return "\n".join(lines)

    def save(self, path: Path) -> None:
        payload = {"topics": [asdict(t) for t in self.topics.values()], "items": [asdict(i) for i in self.items.values()], "restructure_log": self.restructure_log}
        path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    @classmethod
    def load(cls, path: Path) -> "ConversationStore":
        """Load a saved store after validating IDs, topic membership, and chronology."""
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ValueError(f"Cannot load conversation store: {exc}") from exc
        if not isinstance(payload, dict) or set(payload) != {"topics", "items", "restructure_log"}:
            raise ValueError("conversation store must contain topics, items, and restructure_log")
        store = cls()
        try:
            for raw in payload["topics"]:
                topic = Topic(**raw)
                if topic.topic_id in store.topics:
                    raise ValueError(f"duplicate topic_id: {topic.topic_id}")
                store.topics[topic.topic_id] = topic
            for raw in payload["items"]:
                item = Item(**raw)
                if item.item_id in store.items or item.tag not in TAGS:
                    raise ValueError(f"duplicate item_id or invalid tag: {item.item_id}")
                store.items[item.item_id] = item
            for topic in store.topics.values():
                for item_id in topic.items:
                    if item_id not in store.items or store.items[item_id].topic_id != topic.topic_id:
                        raise ValueError(f"invalid item membership in topic {topic.topic_id}")
                ordered = sorted(topic.items, key=lambda key: store.items[key].turn_index)
                if ordered != topic.items:
                    raise ValueError(f"items are not chronological in topic {topic.topic_id}")
            if set(item.topic_id for item in store.items.values()) - set(store.topics):
                raise ValueError("an item references an unknown topic")
            if not isinstance(payload["restructure_log"], list) or any(not isinstance(event, dict) for event in payload["restructure_log"]):
                raise ValueError("restructure_log must be an array of objects")
            store.restructure_log = payload["restructure_log"]
            store._duplicate_cluster = max((int(item.duplicate_cluster_id.split("-")[-1]) for item in store.items.values() if item.duplicate_cluster_id and item.duplicate_cluster_id.startswith("dup-") and item.duplicate_cluster_id.split("-")[-1].isdigit()), default=0)
        except (TypeError, KeyError) as exc:
            raise ValueError(f"Invalid conversation store record: {exc}") from exc
        return store

    def _log(self, turn_index: int, operation: str, before: dict[str, Any], after: dict[str, Any], rationale: str) -> None:
        self.restructure_log.append({"event_id": f"event-{len(self.restructure_log)+1}", "turn_index": turn_index,
                                     "operation_type": operation, "before": before, "after": after, "rationale": rationale})
