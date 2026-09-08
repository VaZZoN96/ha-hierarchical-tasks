"""Pure, dependency-free domain model for Hierarchical Tasks.

All changes operate on a private copy. The async manager serializes commands,
checks revisions and publishes only after a successful durable save.
"""
from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from copy import deepcopy
import re
import logging
from typing import Any
from uuid import uuid4

SCHEMA_VERSION = 1
MAX_LISTS = 30
MAX_NODES = 2000
MAX_DEPTH = 16
MAX_NAME = 200
ID_RE = re.compile(r"[a-z0-9][a-z0-9_-]{0,63}\Z")
_LOGGER = logging.getLogger(__name__)


class TaskError(Exception):
    """A safe, expected error, suitable for returning to a client."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


def fail(message: str, code: str = "invalid_input") -> None:
    raise TaskError(code, message)


def valid_id(value: Any) -> str:
    if not isinstance(value, str) or not ID_RE.fullmatch(value):
        fail("ID: use 1-64 lowercase letters, digits, underscores or hyphens.")
    return value


def valid_name(value: Any) -> str:
    if not isinstance(value, str) or not 1 <= len(value.strip()) <= MAX_NAME:
        fail(f"Name must contain 1-{MAX_NAME} characters.")
    if any(ord(char) < 32 or 0xD800 <= ord(char) <= 0xDFFF for char in value):
        fail("Names must not contain control characters or invalid Unicode.")
    return value.strip()


def integer(value: Any, minimum: int = 0) -> int:
    if type(value) is not int or value < minimum:
        fail(f"Expected an integer >= {minimum}.")
    return value


def empty_data() -> dict[str, Any]:
    return {"schema": SCHEMA_VERSION, "revision": 0, "lists": {}}


def children(nodes: dict, parent_id: str | None) -> list[dict]:
    return sorted(
        (node for node in nodes.values() if node["parent_id"] == parent_id),
        key=lambda node: (node["position"], node["id"]),
    )


def subtree(nodes: dict, node_id: str) -> set[str]:
    """Return a node and all its descendants; no recursive Python calls."""
    if node_id not in nodes:
        fail("Item not found.", "not_found")
    by_parent: dict[str | None, list[str]] = {}
    for node in nodes.values():
        by_parent.setdefault(node["parent_id"], []).append(node["id"])
    result: set[str] = set()
    pending = [node_id]
    while pending:
        current = pending.pop()
        if current in result:
            fail("A cycle was found in the tree.")
        result.add(current)
        pending.extend(by_parent.get(current, []))
    return result


def normalize(nodes: dict) -> None:
    parents = {node["parent_id"] for node in nodes.values()}
    for parent_id in parents:
        for position, node in enumerate(children(nodes, parent_id)):
            node["position"] = position


def aggregate(nodes: dict, node_id: str | None = None) -> dict[str, Any]:
    ids = set(nodes) if node_id is None else subtree(nodes, node_id)
    tasks = [nodes[key] for key in ids if nodes[key]["kind"] == "task"]
    total = len(tasks)
    done = sum(node["completed"] for node in tasks)
    return {
        "total": total,
        "done": done,
        "checked": total > 0 and done == total,
        "indeterminate": 0 < done < total,
    }


def validate_document(raw: Any) -> dict[str, Any]:
    """Strict validation of imports and disk data; never silently discard data."""
    if not isinstance(raw, dict) or set(raw) != {"schema", "revision", "lists"}:
        fail("Invalid document. Required fields: schema, revision, lists.")
    if type(raw["schema"]) is not int or raw["schema"] != SCHEMA_VERSION:
        fail("Unsupported data schema. Do not overwrite the original file.")
    integer(raw["revision"])
    lists = raw["lists"]
    if not isinstance(lists, dict) or len(lists) > MAX_LISTS:
        fail(f"Expected at most {MAX_LISTS} lists.")
    total_nodes = 0
    for list_id, task_list in lists.items():
        valid_id(list_id)
        if not isinstance(task_list, dict) or set(task_list) != {"id", "name", "nodes"}:
            fail("Invalid list fields.")
        if task_list["id"] != list_id:
            fail("List ID does not match its key.")
        if valid_name(task_list["name"]) != task_list["name"]:
            fail("Stored names must not have surrounding whitespace.")
        nodes = task_list["nodes"]
        if not isinstance(nodes, dict):
            fail("nodes must be an object.")
        total_nodes += len(nodes)
        if total_nodes > MAX_NODES:
            fail(f"Limit: {MAX_NODES} items across all lists.")
        for node_id, node in nodes.items():
            valid_id(node_id)
            if not isinstance(node, dict) or set(node) != {
                "id", "name", "kind", "parent_id", "completed", "position"
            }:
                fail("Invalid item fields.")
            if node["id"] != node_id:
                fail("Item ID does not match its key.")
            if valid_name(node["name"]) != node["name"]:
                fail("Stored names must not have surrounding whitespace.")
            if node["kind"] not in ("category", "task"):
                fail("Item kind must be category or task.")
            if type(node["completed"]) is not bool:
                fail("completed must be a boolean.")
            if node["kind"] == "category" and node["completed"]:
                fail("Categories do not store their own completed state.")
            integer(node["position"])
            if node["parent_id"] is not None:
                valid_id(node["parent_id"])
                parent = nodes.get(node["parent_id"])
                if not isinstance(parent, dict) or parent.get("kind") != "category":
                    fail("The parent must be an existing category in the same list.")
        for node_id in nodes:
            seen: set[str] = set()
            current = node_id
            while current is not None:
                if current in seen:
                    fail("A category cannot contain itself or an ancestor.")
                seen.add(current)
                if len(seen) > MAX_DEPTH:
                    fail(f"Maximum tree depth: {MAX_DEPTH}.")
                current = nodes[current]["parent_id"]
    return deepcopy(raw)


# Each operation rejects unknown fields, including misspelled automation keys.
FIELDS: dict[str, tuple[set[str], set[str]]] = {
    "create_list": ({"name"}, {"list_id"}),
    "rename_list": ({"list_id", "name"}, set()),
    "delete_list": ({"list_id"}, set()),
    "add_item": ({"list_id", "name"}, {"kind", "parent_id", "node_id"}),
    "rename_item": ({"list_id", "node_id", "name"}, set()),
    "delete_item": ({"list_id", "node_id"}, set()),
    "move_item": ({"list_id", "node_id", "parent_id"}, {"position", "target_list_id"}),
    "set_completed": ({"list_id", "completed"}, {"node_id"}),
    "clear_completed": ({"list_id"}, {"node_id"}),
    "import_data": ({"document"}, set()),
    "undo": (set(), set()),
}


def check_fields(operation: str, data: Any) -> None:
    if operation not in FIELDS:
        fail("Unknown operation.")
    if not isinstance(data, dict):
        fail("Operation data must be an object.")
    required, optional = FIELDS[operation]
    if required - data.keys():
        fail("Missing fields: " + ", ".join(sorted(required - data.keys())))
    if data.keys() - required - optional:
        fail("Unknown fields: " + ", ".join(sorted(data.keys() - required - optional)))


def apply_operation(doc: dict, operation: str, data: dict) -> dict[str, Any]:
    """Mutate a private copy and return affected IDs/counts."""
    check_fields(operation, data)
    lists = doc["lists"]
    if operation == "import_data":
        imported = validate_document(data["document"])
        doc["lists"] = imported["lists"]
        return {"imported_lists": len(doc["lists"])}
    if operation == "create_list":
        list_id = valid_id(data.get("list_id", uuid4().hex))
        if list_id in lists:
            fail("List ID already exists.", "already_exists")
        lists[list_id] = {"id": list_id, "name": valid_name(data["name"]), "nodes": {}}
        return {"list_id": list_id}
    list_id = valid_id(data["list_id"])
    if list_id not in lists:
        fail("List not found.", "not_found")
    task_list = lists[list_id]
    nodes = task_list["nodes"]
    result: dict[str, Any] = {"list_id": list_id}
    if operation == "rename_list":
        task_list["name"] = valid_name(data["name"])
    elif operation == "delete_list":
        del lists[list_id]
    elif operation == "add_item":
        node_id = valid_id(data.get("node_id", uuid4().hex))
        if node_id in nodes:
            fail("Item ID already exists.", "already_exists")
        kind = data.get("kind", "task")
        if kind not in ("task", "category"):
            fail("Item kind must be category or task.")
        parent_id = data.get("parent_id")
        _validate_parent(nodes, parent_id)
        nodes[node_id] = {
            "id": node_id,
            "name": valid_name(data["name"]),
            "kind": kind,
            "parent_id": parent_id,
            "completed": False,
            "position": len(children(nodes, parent_id)),
        }
        result["node_id"] = node_id
    elif operation in ("set_completed", "clear_completed"):
        node_id = data.get("node_id")
        ids = set(nodes) if node_id is None else subtree(nodes, valid_id(node_id))
        targets = [nodes[key] for key in ids if nodes[key]["kind"] == "task"]
        changed = 0
        if operation == "set_completed":
            completed = data["completed"]
            if type(completed) is not bool:
                fail("completed must be true or false.")
            for node in targets:
                if node["completed"] != completed:
                    node["completed"] = completed
                    changed += 1
        else:
            for node in targets:
                if node["completed"]:
                    del nodes[node["id"]]
                    changed += 1
            normalize(nodes)
        result["affected"] = changed
    else:
        node_id = valid_id(data["node_id"])
        if node_id not in nodes:
            fail("Item not found.", "not_found")
        result["node_id"] = node_id
        if operation == "rename_item":
            nodes[node_id]["name"] = valid_name(data["name"])
        elif operation == "delete_item":
            ids = subtree(nodes, node_id)
            for key in ids:
                del nodes[key]
            normalize(nodes)
            result["affected"] = len(ids)
        elif operation == "move_item":
            target_id = valid_id(data.get("target_list_id", list_id))
            if target_id not in lists:
                fail("Target list not found.", "not_found")
            target_nodes = lists[target_id]["nodes"]
            parent_id = data["parent_id"]
            _validate_parent(target_nodes, parent_id)
            ids = subtree(nodes, node_id)
            if target_id == list_id and parent_id in ids:
                fail("Cannot move a category into itself or a descendant.", "cycle")
            if target_id != list_id and ids & target_nodes.keys():
                fail("An item with this ID exists in the destination.", "already_exists")
            moved = {key: nodes[key] for key in ids}
            for key in ids:
                del nodes[key]
            normalize(nodes)
            siblings = children(target_nodes, parent_id)
            position = integer(data.get("position", len(siblings)))
            position = min(position, len(siblings))
            moved[node_id]["parent_id"] = parent_id
            siblings.insert(position, moved[node_id])
            target_nodes.update(moved)
            for index, node in enumerate(siblings):
                node["position"] = index
            result["target_list_id"] = target_id
    return result


def _validate_parent(nodes: dict, parent_id: Any) -> None:
    if parent_id is None:
        return
    valid_id(parent_id)
    if parent_id not in nodes or nodes[parent_id]["kind"] != "category":
        fail("The parent must be an existing category.")


def initial_data(seed_example: bool = True) -> dict:
    doc = empty_data()
    apply_operation(doc, "create_list", {"list_id": "zakupy", "name": "Zakupy"})
    if seed_example:
        for category_id, name in (("warzywniak", "WARZYWNIAK"), ("piekarnia", "PIEKARNIA")):
            apply_operation(doc, "add_item", {
                "list_id": "zakupy", "node_id": category_id, "name": name, "kind": "category"
            })
        for node_id, name, parent in (
            ("kapusta", "Kapusta", "warzywniak"),
            ("marchew", "Marchew", "warzywniak"),
            ("chleb", "Chleb", "piekarnia"),
        ):
            apply_operation(doc, "add_item", {
                "list_id": "zakupy", "node_id": node_id, "name": name, "parent_id": parent
            })
    return validate_document(doc)


class TaskManager:
    """Single writer with optimistic concurrency and one-step, actor-bound undo."""

    def __init__(
        self,
        data: dict,
        save: Callable[[dict], Awaitable[None]],
        notify: Callable[[], None],
    ) -> None:
        self._data = validate_document(data)
        self._save = save
        self._notify = notify
        self._lock = asyncio.Lock()
        self._undo: tuple[str, dict] | None = None
        self.active = True

    def snapshot(self) -> dict:
        return deepcopy(self._data)

    def can_undo(self, actor: str) -> bool:
        return self._undo is not None and self._undo[0] == actor

    async def execute(
        self,
        operation: str,
        data: dict,
        actor: str,
        expected_revision: int | None = None,
    ) -> dict:
        """Commands are deliberately not auto-retried after network failures."""
        check_fields(operation, data)
        if expected_revision is not None:
            integer(expected_revision)
        if operation in ("undo", "import_data") and expected_revision is None:
            fail("This operation requires expected_revision.")
        async with self._lock:
            if not self.active:
                fail("Integration is unloaded.", "not_ready")
            if expected_revision is not None and expected_revision != self._data["revision"]:
                fail("The data changed on another client. Refresh and try again.", "conflict")
            previous = self._data
            candidate = deepcopy(previous)
            if operation == "undo":
                if not self.can_undo(actor):
                    fail("Only your own most recent change can be undone.", "cannot_undo")
                assert self._undo is not None
                candidate["lists"] = deepcopy(self._undo[1]["lists"])
                result: dict[str, Any] = {"undone": True}
            else:
                result = apply_operation(candidate, operation, data)
            # Validate tree depth, references, quotas and data types before disk I/O.
            candidate = validate_document(candidate)
            changed = candidate["lists"] != previous["lists"]
            if changed:
                candidate["revision"] = previous["revision"] + 1
                # Cancellation must not release the lock while disk I/O is still in
                # flight. Finish the commit, then propagate cancellation to caller.
                commit = asyncio.create_task(self._commit(candidate, previous, operation, actor))
                try:
                    await asyncio.shield(commit)
                except asyncio.CancelledError:
                    await commit
                    raise
            result.update(revision=self._data["revision"], changed=changed)
            return result

    async def _commit(self, candidate: dict, previous: dict, operation: str, actor: str) -> None:
        await self._save(candidate)
        self._data = candidate
        self._undo = None if operation == "undo" else (actor, previous)
        try:
            self._notify()
        except Exception:
            # A notification failure must not misreport a committed write as
            # failed and encourage a client to duplicate the operation.
            _LOGGER.exception("Data saved, but notifying clients failed")

    async def close(self) -> None:
        async with self._lock:
            self.active = False
