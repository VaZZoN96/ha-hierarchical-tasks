"""Browser checks: real card + real domain model, with a simulated HA connection.

This is NOT an end-to-end test against Home Assistant. Requires Playwright and
Chromium. Run from the project root: python tests/browser_smoke.py
"""
from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path
import shutil
import tempfile
import traceback

from playwright.async_api import async_playwright, expect

from load_modules import ROOT, model as m

JS = (ROOT / "custom_components/hierarchical_tasks/frontend/hierarchical-tasks-card.js").read_text()
OUT = ROOT / "test-results"
OUT.mkdir(exist_ok=True)

HARNESS = r"""
customElements.define('ha-card', class extends HTMLElement {
 constructor() { super(); this.attachShadow({mode:'open'}).innerHTML = '<style>:host{display:block;border:1px solid var(--divider-color,#ddd);border-radius:16px;background:var(--card-background-color,#fff);box-shadow:0 2px 8px #0001}</style><slot></slot>'; }
});
const events = new Map(), subscribers = new Set();
window.mockConnection = {
 connected: true,
 addEventListener(type, fn) { if(!events.has(type)) events.set(type, new Set()); events.get(type).add(fn); },
 removeEventListener(type, fn) { events.get(type)?.delete(fn); },
 fire(type) { for(const fn of events.get(type) || []) fn(); },
 async subscribeMessage(fn, msg) {
   subscribers.add(fn);
   const reply = await htBridge({type:'hierarchical_tasks/get'});
   if(!reply.ok) { subscribers.delete(fn); throw reply.error; }
   fn(reply.result);
   return async () => subscribers.delete(fn);
 },
 async sendMessagePromise(msg) {
   if(!this.connected) throw {code:'connection_lost'};
   const reply = await htBridge(msg);
   if(!reply.ok) throw reply.error;
   if(msg.type.endsWith('/mutate')) for(const fn of subscribers) fn(reply.snapshot);
   return reply.result;
 },
 async broadcast() {
   const reply = await htBridge({type:'hierarchical_tasks/get'});
   if(this.connected) for(const fn of subscribers) fn(reply.result);
 },
 count() { return subscribers.size; }
};
window.mockHass = {connection:mockConnection, user:{id:'alice',is_admin:true}};
window.mountCard = (config = {}) => {
 const card = document.createElement('hierarchical-tasks-card');
 card.setConfig({type:'custom:hierarchical-tasks-card', title:'Moje zadania', ...config});
 card.hass = mockHass;
 document.querySelector('main').append(card);
 return card;
};
"""


async def fixture(browser, *, mobile=False, config=None, write=True):
    async def save(data):
        pass
    manager = m.TaskManager(m.initial_data(), save, lambda: None)
    context = await browser.new_context(viewport={"width": 390 if mobile else 1000, "height": 900}, has_touch=mobile, is_mobile=mobile, accept_downloads=True)
    page = await context.new_page()
    page.set_default_timeout(3500)
    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))

    def payload():
        snapshot = manager.snapshot()
        list_permissions = {
            list_id: {
                "read": True,
                "write": write,
                "manage": write,
                "role": "admin" if write else "read",
            }
            for list_id in snapshot["lists"]
        }
        return {
            "api_version": 2,
            "available": True,
            "data": snapshot,
            "permissions": {
                "admin": write,
                "write": write,
                "create_list": write,
                "import": write,
                "undo": write and manager.can_undo("alice"),
                "lists": list_permissions,
            },
        }

    async def bridge(source, message):
        try:
            if message["type"] == "hierarchical_tasks/users":
                return {"ok": True, "result": [
                    {"id": "alice", "name": "Alice", "is_active": True, "is_admin": True},
                    {"id": "bob", "name": "Bob", "is_active": True, "is_admin": False},
                    {"id": "disabled", "name": "Disabled", "is_active": False, "is_admin": False},
                ]}
            if message["type"].endswith("/get"):
                return {"ok": True, "result": payload()}
            result = await manager.execute(message["operation"], message["data"], "alice", message["expected_revision"])
            return {"ok": True, "result": result, "snapshot": payload()}
        except m.TaskError as err:
            return {"ok": False, "error": {"code": err.code, "message": str(err)}}

    await page.expose_binding("htBridge", bridge)
    await page.set_content('<!doctype html><html lang="pl"><head><meta name="viewport" content="width=device-width, initial-scale=1"><style>body{margin:0;padding:16px;background:#f4f6f8;font-family:Arial,sans-serif;color:#212121;--primary-color:#0288d1;--primary-text-color:#212121;--secondary-text-color:#64748b;--divider-color:#dde3e9;--card-background-color:#fff;--secondary-background-color:#f2f5f8;--text-primary-color:#fff}main{max-width:560px;margin:auto}</style></head><body><main></main></body></html>')
    await page.add_script_tag(content=HARNESS)
    await page.add_script_tag(content=JS)
    await page.evaluate("config => { window.card = mountCard(config); }", config or {})
    card = page.locator("hierarchical-tasks-card").first
    await expect(card.locator(".toolbar")).to_be_visible()
    return context, page, card, manager, errors


def row(card, node_id):
    return card.locator(f'.row[data-node-id="{node_id}"]')


async def idle(card):
    await expect(card.locator(".footer")).not_to_contain_text("Zapisywanie")


async def external(page, manager, operation, **data):
    await manager.execute(operation, data, "bob")
    await page.evaluate("mockConnection.broadcast()")


async def case_checkbox(browser):
    ctx, page, card, manager, errors = await fixture(browser)
    try:
        await row(card, "kapusta").locator('input[type="checkbox"]').check()
        await idle(card)
        assert await row(card, "warzywniak").locator("input").evaluate("e => e.indeterminate")
        await row(card, "marchew").locator("input").check()
        await idle(card)
        await expect(row(card, "warzywniak").locator("input")).to_be_checked()
        await row(card, "warzywniak").locator("input").click()
        await expect(card.locator("dialog")).to_be_visible()
        await card.locator("dialog").get_by_role("button", name="Potwierd\u017a", exact=True).click()
        await idle(card)
        assert m.aggregate(manager.snapshot()["lists"]["zakupy"]["nodes"])["done"] == 0
        assert not errors, errors
    finally:
        await ctx.close()


async def case_hidden_and_empty(browser):
    ctx, page, card, manager, errors = await fixture(browser)
    try:
        await row(card, "kapusta").locator("input").check(); await idle(card)
        await card.get_by_label("Ukryj wykonane").check()
        await expect(row(card, "kapusta")).to_have_count(0)
        await row(card, "warzywniak").locator("input").click(); await idle(card)
        await expect(row(card, "warzywniak").locator("input")).to_be_checked()
        await row(card, "warzywniak").locator("input").click()
        await card.locator("dialog").get_by_role("button", name="Potwierd\u017a", exact=True).click(); await idle(card)
        await expect(row(card, "kapusta")).to_be_visible()
        await external(page, manager, "add_item", list_id="zakupy", name="Empty", kind="category", node_id="empty")
        await expect(row(card, "empty").locator("input")).to_be_disabled()
        assert not errors, errors
    finally:
        await ctx.close()


async def case_add_and_draft_conflict(browser):
    ctx, page, card, manager, errors = await fixture(browser, mobile=True)
    try:
        await card.locator(".actions").get_by_role("button", name="+ Kategoria", exact=True).click()
        dialog = card.locator("dialog")
        await dialog.get_by_label("Nazwa", exact=True).fill("Nabia\u0142")
        await dialog.get_by_label("ID (opcjonalne, dla automatyzacji)", exact=True).fill("nabial")
        await dialog.get_by_role("button", name="Zapisz", exact=True).click(); await idle(card)
        await expect(row(card, "nabial")).to_be_visible()
        await card.locator(".actions").get_by_role("button", name="+ Zadanie", exact=True).click()
        await dialog.get_by_label("Nazwa", exact=True).fill("Mleko")
        await dialog.get_by_label("Kategoria nadrz\u0119dna", exact=True).select_option("nabial")
        await dialog.get_by_label("ID (opcjonalne, dla automatyzacji)", exact=True).fill("mleko")
        # A remote change while editing must preserve the draft and reject the
        # first stale submit, without replaying it silently.
        await external(page, manager, "add_item", list_id="zakupy", name="Remote", node_id="remote")
        await expect(dialog.get_by_label("Nazwa", exact=True)).to_have_value("Mleko")
        await dialog.get_by_role("button", name="Zapisz", exact=True).click(); await idle(card)
        await expect(dialog.locator(".dialog-error")).to_contain_text("Dane zmieni\u0142y")
        assert "mleko" not in manager.snapshot()["lists"]["zakupy"]["nodes"]
        await dialog.get_by_role("button", name="Zapisz", exact=True).click(); await idle(card)
        assert manager.snapshot()["lists"]["zakupy"]["nodes"]["mleko"]["parent_id"] == "nabial"
        assert "remote" in manager.snapshot()["lists"]["zakupy"]["nodes"]
        assert not errors, errors
    finally:
        await ctx.close()


async def case_delete_undo(browser):
    ctx, page, card, manager, errors = await fixture(browser)
    try:
        await row(card, "warzywniak").get_by_role("button", name="Opcje: WARZYWNIAK", exact=True).click()
        await card.locator("dialog").get_by_role("button", name="Usu\u0144", exact=True).click()
        await card.locator("dialog").get_by_role("button", name="Potwierd\u017a", exact=True).click(); await idle(card)
        await expect(row(card, "kapusta")).to_have_count(0)
        await card.get_by_role("button", name="Cofnij", exact=True).click(); await idle(card)
        await expect(row(card, "kapusta")).to_be_visible()
        assert not errors, errors
    finally:
        await ctx.close()


async def case_mobile_move(browser):
    ctx, page, card, manager, errors = await fixture(browser, mobile=True)
    try:
        await external(page, manager, "create_list", list_id="dom", name="Dom")
        await row(card, "kapusta").get_by_role("button", name="Opcje: Kapusta", exact=True).click()
        await card.locator("dialog").get_by_role("button", name="Przenie\u015b do kategorii / listy\u2026", exact=True).click()
        await card.locator("dialog").get_by_label("Lista docelowa", exact=True).select_option("dom")
        await card.locator("dialog").get_by_role("button", name="Zapisz", exact=True).click(); await idle(card)
        assert "kapusta" not in manager.snapshot()["lists"]["zakupy"]["nodes"]
        await card.get_by_label("Wybierz list\u0119", exact=True).select_option("dom")
        await expect(row(card, "kapusta")).to_be_visible()
        assert not errors, errors
    finally:
        await ctx.close()


async def case_drag_drop(browser):
    ctx, page, card, manager, errors = await fixture(browser)
    try:
        await row(card, "kapusta").drag_to(row(card, "piekarnia"))
        await idle(card)
        assert manager.snapshot()["lists"]["zakupy"]["nodes"]["kapusta"]["parent_id"] == "piekarnia"
        assert not errors, errors
    finally:
        await ctx.close()


async def case_two_cards_and_cleanup(browser):
    ctx, page, card, manager, errors = await fixture(browser)
    try:
        await page.evaluate("window.second = mountCard()")
        second = page.locator("hierarchical-tasks-card").nth(1)
        await expect(row(second, "kapusta")).to_be_visible()
        assert await page.evaluate("mockConnection.count()") == 2
        await row(card, "kapusta").locator("input").check(); await idle(card)
        await expect(row(second, "kapusta").locator("input")).to_be_checked()
        await page.evaluate("second.remove()")
        assert await page.evaluate("mockConnection.count()") == 1
        await page.evaluate("card.remove(); document.querySelector('main').append(card)")
        await expect(row(card, "kapusta")).to_be_visible()
        assert await page.evaluate("mockConnection.count()") == 1
        assert not errors, errors
    finally:
        await ctx.close()


async def case_disconnect_reconnect(browser):
    ctx, page, card, manager, errors = await fixture(browser)
    try:
        await page.evaluate("mockConnection.connected = false; mockConnection.fire('disconnected')")
        await expect(card.locator(".empty")).to_contain_text("Brak po\u0142\u0105czenia")
        await manager.execute("set_completed", {"list_id": "zakupy", "node_id": "kapusta", "completed": True}, "bob")
        await page.evaluate("mockConnection.connected = true; mockConnection.fire('ready')")
        await expect(row(card, "kapusta").locator("input")).to_be_checked()
        assert await page.evaluate("mockConnection.count()") == 1
        assert not errors, errors
    finally:
        await ctx.close()


async def case_html_is_text(browser):
    ctx, page, card, manager, errors = await fixture(browser)
    try:
        name = '<img src=x onerror="window.xss=1">'
        await external(page, manager, "add_item", list_id="zakupy", node_id="xss", name=name)
        await expect(row(card, "xss").locator(".name")).to_have_text(name)
        assert await row(card, "xss").locator("img").count() == 0
        assert await page.evaluate("window.xss === undefined")
        assert not errors, errors
    finally:
        await ctx.close()


async def case_readonly(browser):
    ctx, page, card, manager, errors = await fixture(browser, write=False)
    try:
        await expect(row(card, "kapusta").locator("input")).to_be_disabled()
        await expect(card.locator(".actions")).to_have_count(0)
        await expect(card.get_by_role("button", name="Import", exact=True)).to_have_count(0)
        await expect(card.locator(".footer")).to_contain_text("tylko odczyt")
        assert not errors, errors
    finally:
        await ctx.close()


async def case_missing_fixed_list(browser):
    ctx, page, card, manager, errors = await fixture(browser, config={"list_id": "missing"})
    try:
        await expect(card.locator(".empty")).to_contain_text("Nie ma tej listy albo nie masz do niej dostępu")
        await expect(card.locator(".row")).to_have_count(0)
        assert not errors, errors
    finally:
        await ctx.close()


async def case_keyboard_and_clear(browser):
    ctx, page, card, manager, errors = await fixture(browser)
    try:
        await row(card, "kapusta").locator("input").focus()
        await page.keyboard.press("Space"); await idle(card)
        await expect(row(card, "kapusta").locator("input")).to_be_checked()
        await card.get_by_role("button", name="Usu\u0144 wykonane", exact=True).click()
        await card.locator("dialog").get_by_role("button", name="Potwierd\u017a", exact=True).click(); await idle(card)
        await expect(row(card, "kapusta")).to_have_count(0)
        await expect(row(card, "warzywniak")).to_be_visible()
        await expect(row(card, "marchew")).to_be_visible()
        assert not errors, errors
    finally:
        await ctx.close()


async def case_export_import(browser):
    ctx, page, card, manager, errors = await fixture(browser)
    try:
        async with page.expect_download() as event:
            await card.get_by_role("button", name="Eksport", exact=True).click()
        download = await event.value
        path = await download.path()
        exported = json.loads(Path(path).read_text())
        assert exported == manager.snapshot()
        imported = m.initial_data(False)
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp)/"import.json"; path.write_text(json.dumps(imported))
            async with page.expect_file_chooser() as choice:
                await card.get_by_role("button", name="Import", exact=True).click()
            await (await choice.value).set_files(path)
            await expect(card.locator("dialog")).to_contain_text("WSZYSTKIE")
            await card.locator("dialog").get_by_role("button", name="Potwierd\u017a", exact=True).click(); await idle(card)
            assert manager.snapshot()["lists"]["zakupy"]["nodes"] == {}
        assert not errors, errors
    finally:
        await ctx.close()


async def case_create_list_and_sharing(browser):
    ctx, page, card, manager, errors = await fixture(browser, mobile=True)
    try:
        await card.get_by_role("button", name="+ Lista", exact=True).click()
        dialog = card.locator("dialog")
        await dialog.get_by_label("Nazwa listy", exact=True).fill("Dom")
        await dialog.get_by_label("ID listy (opcjonalne, np. dom)", exact=True).fill("dom")
        await dialog.get_by_role("button", name="Zapisz", exact=True).click(); await idle(card)
        assert manager.snapshot()["lists"]["dom"]["name"] == "Dom"
        await expect(card.get_by_label("Wybierz listę", exact=True)).to_have_value("dom")

        await card.get_by_role("button", name="Opcje listy: Dom", exact=True).click()
        await dialog.get_by_role("button", name="Udostępnianie...", exact=True).click()
        bob = dialog.locator(".share-row").filter(has_text="Bob")
        await bob.locator("select").select_option("write")
        await dialog.get_by_role("button", name="Zapisz udostępnianie", exact=True).click(); await idle(card)
        assert manager.snapshot()["lists"]["dom"]["access"] == {"bob": "write"}
        assert not errors, errors
    finally:
        await ctx.close()


async def case_mobile_layout_preview(browser):
    ctx, page, card, manager, errors = await fixture(browser, mobile=True, config={"title": "Zakupy", "list_id": "zakupy"})
    try:
        await row(card, "kapusta").locator("input").check(); await idle(card)
        await page.evaluate("card._notice = ''; card._render()")
        width = await page.evaluate("({scroll:document.documentElement.scrollWidth,client:document.documentElement.clientWidth})")
        assert width["scroll"] <= width["client"], width
        await card.screenshot(path=str(OUT / "card-mobile.png"))
        await page.screenshot(path=str(OUT / "page-mobile.png"), full_page=True)
        assert not errors, errors
    finally:
        await ctx.close()


async def main():
    cases = [case_checkbox, case_hidden_and_empty, case_add_and_draft_conflict, case_delete_undo, case_mobile_move, case_drag_drop,
             case_two_cards_and_cleanup, case_disconnect_reconnect, case_html_is_text, case_readonly, case_missing_fixed_list,
             case_keyboard_and_clear, case_export_import, case_create_list_and_sharing, case_mobile_layout_preview]
    results = []
    async with async_playwright() as playwright:
        path = os.environ.get("CHROMIUM_EXECUTABLE") or shutil.which("chromium")
        kwargs = {"headless": True, "args": ["--no-sandbox"]}
        if path: kwargs["executable_path"] = path
        browser = await playwright.chromium.launch(**kwargs)
        print("Browser:", browser.version, flush=True)
        for case in cases:
            try:
                await case(browser)
                result = {"name": case.__name__, "passed": True}
                print("PASS", case.__name__, flush=True)
            except Exception as error:
                result = {"name": case.__name__, "passed": False, "error": traceback.format_exc()}
                print("FAIL", case.__name__, repr(error), flush=True)
            results.append(result)
        await browser.close()
    (OUT / "browser-results.json").write_text(json.dumps(results, indent=2))
    print(f"Passed {sum(r['passed'] for r in results)}/{len(results)} browser scenarios.")
    if not all(result["passed"] for result in results):
        raise SystemExit(1)


if __name__ == "__main__":
    asyncio.run(main())
