from __future__ import annotations

from pathlib import Path

from schema.item import Item, load_item


class ItemBank:
    def __init__(self, items: list[Item]) -> None:
        self._items = sorted(items, key=lambda item: item.id)
        self._by_id = {item.id: item for item in self._items}

    @classmethod
    def from_directory(cls, directory: str | Path, *, active_only: bool = True) -> "ItemBank":
        items: list[Item] = []
        for path in sorted(Path(directory).glob("*.json")):
            item = load_item(path)
            if active_only and item.status != "active":
                continue
            items.append(item)
        return cls(items)

    @classmethod
    def from_directory_tree(cls, root: str | Path, *, active_only: bool = True) -> "ItemBank":
        root_path = Path(root)
        items: list[Item] = []
        for child in (root_path / "extended", root_path / "core"):
            if not child.exists():
                continue
            items.extend(cls.from_directory(child, active_only=active_only).all())
        return cls(items)

    def all(self) -> list[Item]:
        return list(self._items)

    def get(self, item_id: str) -> Item:
        return self._by_id[item_id]

    def by_concept(self, concept_id: str) -> list[Item]:
        return [item for item in self._items if concept_id in item.concept_ids]

    def by_tier(self, tier: str) -> list[Item]:
        return [item for item in self._items if item.tier == tier]

    def core_repair_items_for(self, node_id: str) -> list[Item]:
        direct_matches: list[Item] = []
        indirect_matches: list[Item] = []
        for item in self._items:
            refs = set(item.concept_ids + item.prerequisite_ids + item.exam_literacy_ids)
            if item.tier != "core_repair" or node_id not in refs:
                continue
            if node_id in item.concept_ids:
                direct_matches.append(item)
            else:
                indirect_matches.append(item)
        return direct_matches + indirect_matches

    def transfer_variations_for(self, item_id: str) -> list[Item]:
        return [item for item in self._items if item.transfer_variation_of == item_id]

    def first_unseen_for_path(self, seen_item_ids: set[str], *, limit: int) -> list[Item]:
        selected: list[Item] = []
        for item in self._items:
            if item.id in seen_item_ids:
                continue
            selected.append(item)
            if len(selected) == limit:
                break
        return selected
