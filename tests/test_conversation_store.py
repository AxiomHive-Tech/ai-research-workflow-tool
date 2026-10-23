import unittest
from pathlib import Path
import tempfile
from conversation_store import ConversationStore


class ConversationStoreTests(unittest.TestCase):
    def setUp(self):
        self.store = ConversationStore()
        self.store.add_item(item_id="i1", turn_index=1, speaker="user", text="axiom hive scope", tag="a", topic_id="t1", source="user", location="turn 1")

    def test_normalization_and_provenance_preserved(self):
        item = self.store.items["i1"]
        self.assertEqual(item.text, "axiom hive scope")
        self.assertEqual(item.normalized_text, "Axiom Hive scope")
        self.assertEqual(item.source, "user")
        self.assertEqual(item.location, "turn 1")
        self.assertTrue(item.normalized_terms)

    def test_same_turn_can_have_multiple_atomic_items(self):
        item = self.store.add_item(item_id="i2", turn_index=1, speaker="user", text="clarification", tag="c", topic_id="t1", source="user", location="turn 1")
        self.assertEqual(item.turn_index, 1)

    def test_conflicts_remain_explicit_and_output_is_chronological(self):
        self.store.add_item(item_id="i2", turn_index=2, speaker="user", text="This contradicts the prior position", tag="c", topic_id="t1", source="user", location="turn 2", contradicts=["i1"])
        rendered = self.store.render()
        self.assertIn("contradicts i1", rendered)
        self.assertLess(rendered.index("#1 i1"), rendered.index("#2 i2"))

    def test_unknown_link_rejected(self):
        with self.assertRaisesRegex(ValueError, "existing items"):
            self.store.add_item(item_id="i2", turn_index=2, speaker="user", text="x", tag="c", topic_id="t1", source="user", location="turn 2", references=["absent"])

    def test_duplicate_suggestions_do_not_change_records(self):
        self.store.add_item(item_id="i2", turn_index=2, speaker="user", text="Axiom Hive scope", tag="c", topic_id="t1", source="user", location="turn 2")
        self.assertEqual(self.store.suggest_duplicates("i2", 0.8), [("i1", 1.0)])
        self.assertEqual(self.store.items["i2"].duplicates_of, [])

    def test_merge_with_contradiction_requires_approval(self):
        self.store.add_item(item_id="i2", turn_index=2, speaker="user", text="new topic", tag="b", topic_id="t2", source="user", location="turn 2", contradicts=["i1"])
        with self.assertRaisesRegex(ValueError, "approval"):
            self.store.merge_topics("t1", "t2", 3)
        self.assertEqual(set(self.store.topics), {"t1", "t2"})

    def test_split_and_topic_relation_are_logged(self):
        self.store.add_item(item_id="i2", turn_index=2, speaker="user", text="related subject", tag="b", topic_id="t2", source="user", location="turn 2")
        self.store.link_topics("t1", "t2", "RelatedTo", 2)
        self.store.split_topic("t1", "t3", ["i1"], 3, "split subject", "Separate distinct material")
        self.assertEqual(self.store.items["i1"].topic_id, "t3")
        self.assertEqual(self.store.topics["t1"].items, [])
        self.assertEqual([e["operation_type"] for e in self.store.restructure_log][-2:], ["AddRelation", "SplitTopic"])

    def test_duplicate_link_assigns_cluster_without_deleting_items(self):
        self.store.add_item(item_id="i2", turn_index=2, speaker="user", text="Axiom Hive scope", tag="c", topic_id="t1", source="user", location="turn 2")
        cluster = self.store.link_duplicate("i2", "i1", 2)
        self.assertEqual(self.store.items["i1"].duplicate_cluster_id, cluster)
        self.assertEqual(self.store.items["i2"].duplicate_cluster_id, cluster)
        self.assertEqual(len(self.store.items), 2)

    def test_json_save_and_load_round_trip(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "store.json"
            self.store.save(path)
            loaded = ConversationStore.load(path)
        self.assertEqual(loaded.items["i1"].text, self.store.items["i1"].text)
        self.assertEqual(loaded.items["i1"].topic_id, "t1")
        self.assertEqual(loaded.restructure_log, self.store.restructure_log)


if __name__ == "__main__":
    unittest.main()
