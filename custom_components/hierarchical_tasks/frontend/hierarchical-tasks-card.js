/* Hierarchical Tasks 0.2.0 | MIT | No CDN, npm package or external requests. */
(() => {
  "use strict";
  const VERSION = "0.2.0";
  const TYPE = "hierarchical-tasks-card";
  const API = "hierarchical_tasks";
  const CSS = `
    :host { display:block; --ht-gap:12px; color:var(--primary-text-color,#212121); }
    * { box-sizing:border-box; }
    ha-card { display:block; overflow:hidden; padding:18px; }
    header { display:flex; justify-content:space-between; gap:12px; align-items:center; margin-bottom:14px; }
    h2 { margin:0; font-size:22px; line-height:1.3; font-weight:600; }
    .muted { color:var(--secondary-text-color,#666); font-size:12px; line-height:1.5; }
    .top, .toolbar, .actions, .dialog-actions { display:flex; flex-wrap:wrap; align-items:center; gap:8px; }
    .top { margin-bottom:10px; }
    .top select { flex:1; min-width:100px; }
    button, input, select { font:inherit; color:inherit; }
    button { min-height:42px; padding:8px 12px; border:1px solid var(--divider-color,#ddd);
      border-radius:10px; cursor:pointer; background:var(--card-background-color,#fff); }
    button:hover:not(:disabled) { background:var(--secondary-background-color,#f2f2f2); }
    button:focus-visible, input:focus-visible, select:focus-visible { outline:2px solid var(--primary-color,#03a9f4); outline-offset:2px; }
    button:disabled, input:disabled, select:disabled { cursor:default; opacity:.45; }
    button.primary { background:var(--primary-color,#03a9f4); color:var(--text-primary-color,#fff); border-color:transparent; }
    button.danger { color:var(--error-color,#db4437); }
    .icon { width:42px; padding:0; flex:0 0 42px; border:0; font-size:21px; }
    input:not([type=checkbox]), select { min-height:44px; padding:9px 10px; border:1px solid var(--divider-color,#ddd);
      border-radius:9px; background:var(--card-background-color,#fff); min-width:0; max-width:100%; }
    input[type=checkbox] { width:22px; height:22px; accent-color:var(--primary-color,#03a9f4); cursor:pointer; margin:0; }
    .toolbar { padding-bottom:12px; margin-bottom:6px; border-bottom:1px solid var(--divider-color,#ddd); }
    .toolbar button { font-size:12px; min-height:38px; }
    .filter { display:flex; gap:8px; align-items:center; min-height:42px; font-size:13px; }
    .notice { font-size:13px; line-height:1.45; margin:8px 0; padding:9px 11px; border-radius:8px;
      background:var(--secondary-background-color,#f3f3f3); overflow-wrap:anywhere; }
    .notice:empty { display:none; }
    .notice.error { color:var(--error-color,#db4437); }
    .tree { min-height:30px; }
    .row { display:flex; align-items:center; min-height:48px; border-radius:9px; gap:0; }
    .row.category { background:var(--secondary-background-color,#f5f5f5); margin-top:8px; }
    .row.drop-target { outline:2px dashed var(--primary-color,#03a9f4); }
    .row .fold, .row .spacer { flex:0 0 30px; width:30px; }
    .row .fold { padding:0; border:0; background:transparent; font-size:18px; min-height:44px; }
    .check { display:flex; align-items:center; justify-content:center; flex:0 0 40px; min-height:44px; }
    .name { text-align:start; overflow-wrap:anywhere; flex:1; min-width:0; border:0; background:transparent;
      padding:10px 3px; font-size:15px; border-radius:0; }
    .category .name { font-weight:600; font-size:13px; letter-spacing:.3px; }
    .done .name { text-decoration:line-through; color:var(--secondary-text-color,#777); }
    .count { flex:0 0 auto; font-size:12px; padding:0 5px; color:var(--secondary-text-color,#666); }
    .row .menu { flex:0 0 36px; width:36px; font-size:23px; padding:0; border:0; background:transparent; min-height:44px; }
    .category-add { display:flex; flex-wrap:wrap; gap:2px; padding:2px 0 5px 0; }
    .category-add button { font-size:12px; border:0; color:var(--primary-color,#0288d1); min-height:38px; }
    .empty { padding:22px 8px; text-align:center; color:var(--secondary-text-color,#666); line-height:1.6; }
    .actions { margin-top:14px; }
    .footer { display:flex; justify-content:space-between; gap:10px; margin-top:12px; }
    .root-drop { border:1px dashed var(--divider-color,#ddd); padding:10px; margin-top:10px; text-align:center; border-radius:8px; }
    dialog { width:min(440px,94vw); max-height:85vh; overflow:auto; padding:22px; border:1px solid var(--divider-color,#ddd);
      border-radius:16px; background:var(--card-background-color,#fff); color:var(--primary-text-color,#212121);
      box-shadow:0 12px 48px #0005; }
    dialog::backdrop { background:#0006; }
    dialog h3 { font-size:19px; margin:0 0 14px; overflow-wrap:anywhere; }
    dialog p { line-height:1.5; overflow-wrap:anywhere; }
    dialog label.field { display:flex; flex-direction:column; gap:6px; margin:12px 0; font-size:13px; }
    dialog label.field input, dialog label.field select { width:100%; }
    .dialog-actions { justify-content:flex-end; margin-top:18px; }
    .menu-actions { display:grid; gap:8px; }
    .menu-actions button { text-align:start; }
    .share-list { display:grid; gap:8px; margin:12px 0; }
    .share-row { display:grid; grid-template-columns:minmax(0,1fr) 150px; gap:10px; align-items:center; padding:8px 0; border-bottom:1px solid var(--divider-color,#ddd); }
    .share-row strong, .share-row span { overflow-wrap:anywhere; }
    .share-row select { width:100%; }
    @media (max-width:420px) { .share-row { grid-template-columns:1fr; } }
    .dialog-error { color:var(--error-color,#db4437); font-size:13px; line-height:1.5; }
    .dialog-error:empty { display:none; }
    .id-field { width:100%; font-family:monospace; font-size:12px !important; }
    progress { width:100%; height:5px; display:block; margin:0 0 10px; accent-color:var(--primary-color,#03a9f4); }
    @media (max-width:400px) { ha-card { padding:12px; } h2 { font-size:20px; } .row .spacer, .row .fold { width:24px; flex-basis:24px; } }
  `;

  function el(tag, className, text) {
    const node = document.createElement(tag);
    if (className) node.className = className;
    // Never put a task name, ID, server message or imported string into innerHTML.
    if (text !== undefined) node.textContent = String(text);
    return node;
  }
  function button(label, onClick, className = "", disabled = false) {
    const node = el("button", className, label);
    node.type = "button";
    node.disabled = disabled;
    node.addEventListener("click", onClick);
    return node;
  }
  function ordered(nodes, parent = null) {
    return Object.values(nodes).filter(n => n.parent_id === parent)
      .sort((a, b) => a.position - b.position || (a.id < b.id ? -1 : a.id > b.id ? 1 : 0));
  }
  function statsFor(nodes) {
    const byParent = new Map();
    for (const n of Object.values(nodes)) {
      if (!byParent.has(n.parent_id)) byParent.set(n.parent_id, []);
      byParent.get(n.parent_id).push(n);
    }
    const result = new Map();
    const walk = (id) => {
      const n = nodes[id];
      let total = 0, done = 0;
      if (n.kind === "task") { total = 1; done = n.completed ? 1 : 0; }
      else for (const child of byParent.get(id) || []) {
        const sub = walk(child.id); total += sub.total; done += sub.done;
      }
      const info = { total, done, checked: total > 0 && done === total, mixed: done > 0 && done < total };
      result.set(id, info);
      return info;
    };
    for (const n of byParent.get(null) || []) walk(n.id);
    let total = 0, done = 0;
    for (const n of Object.values(nodes)) if (n.kind === "task") { total++; if (n.completed) done++; }
    result.set(null, { total, done, checked: total > 0 && total === done, mixed: done > 0 && done < total });
    return result;
  }
  function errorText(error) {
    const code = error?.code;
    if (code === "conflict") return "Dane zmieni\u0142y si\u0119 na innym urz\u0105dzeniu. Od\u015bwie\u017cono list\u0119. Sprawd\u017a j\u0105 i pon\u00f3w operacj\u0119.";
    if (code === "forbidden") return "Brak uprawnie\u0144 do tej listy lub operacji. Administrator mo\u017ce zmieni\u0107 udost\u0119pnianie w menu listy.";
    if (code === "not_ready") return "Integracja nie jest uruchomiona. Dodaj Hierarchical Tasks w Ustawieniach HA lub sprawd\u017a jej dziennik.";
    if (code === "unknown_command") return "Home Assistant nie rozpoznaje integracji. Zainstaluj pliki, uruchom HA ponownie i dodaj integracj\u0119.";
    if (code === "storage_error") return "Nie zapisano zmian. Sprawd\u017a wolne miejsce na dysku i dziennik Home Assistanta.";
    if (code === "already_exists") return "Podane ID jest ju\u017c zaj\u0119te. Wybierz inne ID lub sprawd\u017a, czy element ju\u017c istnieje.";
    if (code === "cycle") return "Nie mo\u017cna przenie\u015b\u0107 kategorii do niej samej lub jej podkategorii.";
    return error?.message || "Utracono po\u0142\u0105czenie lub wyst\u0105pi\u0142 b\u0142\u0105d. Sprawd\u017a aktualny stan przed ponowieniem.";
  }
  function uuid() { return crypto.randomUUID ? crypto.randomUUID() : `n${Date.now().toString(36)}${Math.random().toString(36).slice(2)}`; }

  class HierarchicalTasksCard extends HTMLElement {
    constructor() {
      super();
      this.attachShadow({ mode: "open" });
      const style = el("style"); style.textContent = CSS;
      this._card = el("ha-card");
      this._main = el("div");
      this._dialog = el("dialog");
      this._dialog.addEventListener("cancel", event => { if (this._busy) event.preventDefault(); });
      this._card.append(this._main);
      this.shadowRoot.append(style, this._card, this._dialog);
      this._config = null;
      this._state = null;
      this._permissions = {};
      this._collapsed = new Set();
      this._generation = 0;
      this._busy = false;
      this._online = false;
      this._notice = "";
      this._error = false;
      this._onReady = () => { this._online = true; this._refresh().catch(() => {}); };
      this._onDisconnect = () => { this._online = false; this._state = null; if (this._dialog.open) this._dialog.close(); this._render(); };
    }

    static getStubConfig() { return { title: "Zadania", hide_completed: false, confirm_bulk: true }; }
    getCardSize() { return 6; }
    getGridOptions() { return { columns: 12, min_columns: 6, rows: "auto" }; }

    setConfig(config) {
      if (!config || typeof config !== "object") throw new Error("Nieprawid\u0142owa konfiguracja karty.");
      if (config.list_id !== undefined && typeof config.list_id !== "string") throw new Error("list_id musi by\u0107 tekstem.");
      for (const key of ["hide_completed", "confirm_bulk"]) {
        if (config[key] !== undefined && typeof config[key] !== "boolean") throw new Error(`${key}: u\u017cyj true lub false.`);
      }
      this._config = { title: "Zadania", hide_completed: false, confirm_bulk: true, ...config };
      this._hideCompleted = this._config.hide_completed;
      this._selected = config.list_id || this._selected;
      this._render(); this._connect();
    }
    set hass(hass) { this._hass = hass; this._connect(); }
    connectedCallback() { this._mounted = true; this._connect(); }
    disconnectedCallback() { this._mounted = false; this._stop(); if (this._dialog.open) this._dialog.close(); }

    _stop() {
      this._generation++;
      clearTimeout(this._retry);
      if (this._connection) {
        this._connection.removeEventListener("ready", this._onReady);
        this._connection.removeEventListener("disconnected", this._onDisconnect);
      }
      if (this._unsubscribe) Promise.resolve(this._unsubscribe()).catch(() => {});
      this._unsubscribe = null; this._connecting = false; this._connection = null;
    }
    _connect() {
      if (!this._mounted || !this._config || !this._hass?.connection) return;
      const connection = this._hass.connection;
      if (connection === this._connection) return;
      this._stop();
      this._state = null;
      this._connection = connection;
      this._online = connection.connected;
      connection.addEventListener("ready", this._onReady);
      connection.addEventListener("disconnected", this._onDisconnect);
      this._subscribe();
    }
    async _subscribe() {
      if (!this._mounted || !this._connection || this._connecting || this._unsubscribe) return;
      this._connecting = true;
      const generation = this._generation, connection = this._connection;
      try {
        const unsubscribe = await connection.subscribeMessage(
          event => { if (generation === this._generation) this._receive(event); },
          { type: `${API}/subscribe` }
        );
        if (generation !== this._generation || !this._mounted) { await unsubscribe(); return; }
        this._unsubscribe = unsubscribe;
      } catch (error) {
        if (generation !== this._generation) return;
        this._notice = errorText(error); this._error = true; this._render();
        this._retry = setTimeout(() => this._subscribe(), 5000);
      } finally {
        if (generation === this._generation) this._connecting = false;
      }
    }
    _receive(event) {
      if (!event.available) {
        if (this._dialog.open) this._dialog.close();
        this._dialog.replaceChildren();
        this._state = null; this._permissions = {};
        this._notice = errorText(event.error); this._error = true;
      } else if (event.api_version !== 2) {
        this._state = null; this._permissions = {};
        this._notice = "Niezgodna wersja API. Zaktualizuj integracj\u0119 i plik karty razem."; this._error = true;
      } else {
        if (this._state && event.data.revision < this._state.revision) return;
        const wasUnavailable = !this._state;
        this._state = event.data;
        this._permissions = event.permissions || {};
        this._online = this._connection?.connected ?? true;
        if (wasUnavailable) { this._notice = ""; this._error = false; }
        const lists = this._state.lists;
        if (!this._config.list_id && !lists[this._selected]) this._selected = Object.keys(lists)[0];
      }
      this._render();
    }
    async _refresh() {
      if (!this._connection?.connected) return;
      const generation = this._generation;
      try {
        const event = await this._connection.sendMessagePromise({ type: `${API}/get` });
        if (generation === this._generation) this._receive(event);
      } catch (error) {
        if (generation === this._generation) {
          if (["forbidden", "not_ready", "unknown_command"].includes(error?.code)) { this._state = null; this._permissions = {}; if (this._dialog.open) this._dialog.close(); this._dialog.replaceChildren(); }
          this._notice = errorText(error); this._error = true; this._render();
        }
        throw error;
      }
    }
    get _listId() { return this._config?.list_id || this._selected; }
    get _list() { return this._state?.lists[this._listId]; }
    get _listPermissions() { return this._permissions?.lists?.[this._listId] || {}; }
    get _editable() { return !!(this._state && this._online && this._listPermissions.write && !this._busy); }
    get _admin() { return !!this._permissions?.admin; }

    _render() {
      if (!this._config) return;
      const main = this._main; main.replaceChildren();
      const header = el("header"), titles = el("div");
      titles.append(el("h2", "", this._config.title));
      titles.append(el("div", "muted", "Listy \u00b7 kategorie \u00b7 zadania"));
      header.append(titles);
      const refresh = button("\u21bb", () => this._refresh().catch(() => {}), "icon", this._busy);
      refresh.title = "Od\u015bwie\u017c"; refresh.setAttribute("aria-label", "Od\u015bwie\u017c listy"); header.append(refresh);
      main.append(header);
      const status = el("div", `notice${this._error ? " error" : ""}`, this._notice);
      status.setAttribute("role", this._error ? "alert" : "status"); main.append(status);
      if (!this._state) {
        main.append(el("div", "empty", this._online ? "\u0141\u0105czenie z integracj\u0105\u2026" : "Brak po\u0142\u0105czenia z Home Assistant. Edycja offline jest wy\u0142\u0105czona."));
        return;
      }
      const top = el("div", "top"), list = this._list;
      if (!this._config.list_id) {
        const select = el("select"); select.setAttribute("aria-label", "Wybierz list\u0119"); select.disabled = this._busy;
        for (const item of Object.values(this._state.lists)) {
          const option = el("option", "", item.name); option.value = item.id; select.append(option);
        }
        select.value = this._selected || "";
        select.addEventListener("change", () => { this._selected = select.value; this._notice = ""; this._render(); });
        top.append(select, button("+ Lista", () => this._newList(), "", !this._online || this._busy || !this._permissions.create_list));
      } else top.append(el("strong", "", list?.name || this._config.list_id));
      if (list) {
        const listMenu = button("\u22ef", () => this._listMenu(), "icon", this._busy);
        listMenu.title = "Opcje listy"; listMenu.setAttribute("aria-label", `Opcje listy: ${list.name}`); top.append(listMenu);
      }
      main.append(top);
      const toolbar = el("div", "toolbar");
      toolbar.append(button("Cofnij", () => this._mutate("undo", {}), "", !this._online || this._busy || !this._permissions.undo));
      toolbar.append(button("Eksport", () => this._export(), "", this._busy));
      if (this._permissions.import) toolbar.append(button("Import", () => this._import(), "", !this._online || this._busy));
      main.append(toolbar);
      if (!list) {
        main.append(el("div", "empty", this._config.list_id ? "Nie ma tej listy albo nie masz do niej dost\u0119pu." : (this._permissions.create_list ? "Utw\u00f3rz swoj\u0105 pierwsz\u0105 list\u0119 przyciskiem + Lista." : "Administrator nie udost\u0119pni\u0142 Ci jeszcze \u017cadnej listy.")));
        return;
      }
      const stats = statsFor(list.nodes), all = stats.get(null);
      const progress = el("progress"); progress.max = Math.max(1, all.total); progress.value = all.done;
      progress.setAttribute("aria-label", `Wykonano ${all.done} z ${all.total}`); main.append(progress);
      const filter = el("label", "filter"), hide = el("input"); hide.type = "checkbox"; hide.checked = this._hideCompleted;
      hide.addEventListener("change", () => { this._hideCompleted = hide.checked; this._render(); });
      filter.append(hide, el("span", "", "Ukryj wykonane")); main.append(filter);
      const tree = el("div", "tree"); tree.setAttribute("role", "group"); tree.setAttribute("aria-label", list.name);
      let rendered = 0;
      const visit = (parent, depth) => {
        for (const node of ordered(list.nodes, parent)) {
          if (node.kind === "task" && node.completed && this._hideCompleted) continue;
          rendered++;
          tree.append(this._row(node, depth, stats.get(node.id), list));
          if (node.kind === "category" && !this._collapsed.has(`${list.id}/${node.id}`)) {
            visit(node.id, depth + 1);
            if (this._editable) {
              const add = el("div", "category-add"); add.style.marginInlineStart = `${Math.min(depth + 1, 5) * 12 + 28}px`;
              add.append(button("+ Zadanie", () => this._add("task", node.id), "", !this._editable));
              add.append(button("+ Podkategoria", () => this._add("category", node.id), "", !this._editable));
              tree.append(add);
            }
          }
        }
      };
      visit(null, 0);
      if (!rendered) tree.append(el("div", "empty", Object.keys(list.nodes).length ? "Brak widocznych zada\u0144. Wy\u0142\u0105cz ukrywanie wykonanych." : "Lista jest pusta. Dodaj kategori\u0119 lub zadanie."));
      if (this._dragging) {
        const drop = el("div", "root-drop", "Upu\u015b\u0107 tutaj, aby przenie\u015b\u0107 na g\u0142\u00f3wny poziom");
        this._dropTarget(drop, null, list); tree.append(drop);
      }
      main.append(tree);
      if (this._editable) {
        const actions = el("div", "actions");
        actions.append(button("+ Zadanie", () => this._add("task", null), "primary", !this._editable));
        actions.append(button("+ Kategoria", () => this._add("category", null), "", !this._editable));
        actions.append(button("Usu\u0144 wykonane", () => this._clear(), "", !this._editable || all.done === 0));
        main.append(actions);
      }
      const footer = el("div", "footer muted");
      footer.append(el("span", "", `${all.done}/${all.total} wykonanych${this._listPermissions.write ? "" : " \u00b7 tylko odczyt"}`));
      footer.append(el("span", "", this._busy ? "Zapisywanie\u2026" : `v${VERSION} \u00b7 rev ${this._state.revision}`));
      main.append(footer);
    }

    _row(node, depth, stats, list) {
      const category = node.kind === "category", key = `${list.id}/${node.id}`;
      const row = el("div", `row${category ? " category" : ""}${!category && node.completed ? " done" : ""}`);
      row.dataset.nodeId = node.id; row.style.marginInlineStart = `${Math.min(depth, 5) * 12}px`;
      if (category) {
        const folded = this._collapsed.has(key);
        const fold = button(folded ? "\u25b8" : "\u25be", () => this._fold(key), "fold");
        fold.setAttribute("aria-expanded", String(!folded)); fold.setAttribute("aria-label", `${folded ? "Rozwi\u0144" : "Zwi\u0144"}: ${node.name}`); row.append(fold);
      } else row.append(el("span", "spacer"));
      const checkLabel = el("label", "check"), check = el("input"); check.type = "checkbox";
      check.checked = stats.checked; check.indeterminate = stats.mixed;
      check.disabled = !this._editable || stats.total === 0;
      check.setAttribute("aria-label", category ? `Oznacz ca\u0142\u0105 kategori\u0119: ${node.name}` : node.name);
      check.setAttribute("aria-checked", stats.mixed ? "mixed" : String(stats.checked));
      check.addEventListener("change", () => this._check(node, stats)); checkLabel.append(check); row.append(checkLabel);
      const name = button(node.name, () => category ? this._fold(key) : this._check(node, stats), "name", !category && !this._editable);
      name.title = category ? "Kliknij nazw\u0119, aby zwin\u0105\u0107/rozwin\u0105\u0107. Checkbox oznacza wszystkie zadania." : node.name;
      row.append(name);
      if (category) row.append(el("span", "count", `${stats.done}/${stats.total}`));
      const menu = button("\u22ee", () => this._itemMenu(node), "menu", this._busy);
      menu.setAttribute("aria-label", `Opcje: ${node.name}`); row.append(menu);
      // Desktop drag-and-drop. Mobile/keyboard users have the same operations
      // in the item menu (Move, Up, Down); no touch drag gesture is required.
      row.draggable = this._editable && matchMedia("(pointer:fine)").matches;
      row.addEventListener("dragstart", event => {
        if (!this._editable || event.target instanceof HTMLInputElement) { event.preventDefault(); return; }
        this._dragging = { list_id: list.id, node_id: node.id, revision: this._state.revision };
        event.dataTransfer.effectAllowed = "move";
        event.dataTransfer.setData("application/x-hierarchical-task", JSON.stringify(this._dragging));
        // Do not replace the dragged DOM node during dragstart.
        const drop = el("div", "root-drop", "Upu\u015b\u0107 tutaj: poziom g\u0142\u00f3wny");
        this._dropTarget(drop, null, list); this._main.querySelector(".tree")?.append(drop);
      });
      row.addEventListener("dragend", () => { this._dragging = null; this._render(); });
      this._dropTarget(row, node, list);
      return row;
    }
    _fold(key) { this._collapsed.has(key) ? this._collapsed.delete(key) : this._collapsed.add(key); this._render(); }
    _dropTarget(element, target, list) {
      element.addEventListener("dragover", event => {
        if (this._editable && this._dragging) { event.preventDefault(); element.classList.add("drop-target"); event.dataTransfer.dropEffect = "move"; }
      });
      element.addEventListener("dragleave", () => element.classList.remove("drop-target"));
      element.addEventListener("drop", event => {
        event.preventDefault(); event.stopPropagation(); element.classList.remove("drop-target");
        const drag = this._dragging; this._dragging = null;
        if (!drag || !this._editable || drag.node_id === target?.id) return;
        const parent = target ? (target.kind === "category" ? target.id : target.parent_id) : null;
        const data = { list_id: drag.list_id, node_id: drag.node_id, target_list_id: list.id, parent_id: parent };
        if (target?.kind === "task") {
          const siblings = ordered(list.nodes, parent).filter(n => !(drag.list_id === list.id && n.id === drag.node_id));
          data.position = siblings.findIndex(n => n.id === target.id);
        }
        this._mutate("move_item", data, drag.revision);
      });
    }

    async _mutate(operation, data, revision = this._state?.revision) {
      if (!this._state || !this._online || this._busy) return false;
      this._busy = true; this._notice = ""; this._error = false; this._render();
      const formButtons = [...this._dialog.querySelectorAll("button")];
      formButtons.forEach(b => { b.dataset.wasDisabled = String(b.disabled); b.disabled = true; });
      try {
        await this._connection.sendMessagePromise({ type: `${API}/mutate`, operation, data, expected_revision: revision });
        await this._refresh();
        this._notice = "Zapisano."; this._error = false;
        return true;
      } catch (error) {
        if (error?.code === "conflict") await this._refresh().catch(() => {});
        this._notice = errorText(error); this._error = true;
        const errorBox = this._dialog.querySelector(".dialog-error"); if (errorBox) errorBox.textContent = this._notice;
        return false;
      } finally {
        this._busy = false;
        formButtons.forEach(b => { b.disabled = b.dataset.wasDisabled === "true"; });
        this._render();
      }
    }

    _open(title) {
      if (this._dialog.open) this._dialog.close();
      this._dialog.replaceChildren(el("h3", "", title));
      const error = el("div", "dialog-error"); error.setAttribute("role", "alert"); this._dialog.append(error);
      this._dialog.showModal();
      return this._dialog;
    }
    _close() { if (!this._busy && this._dialog.open) this._dialog.close(); }
    _field(parent, label, input) { input.setAttribute("aria-label", label); const wrapper = el("label", "field"); wrapper.append(el("span", "", label), input); parent.append(wrapper); return input; }
    _input(value = "", required = true) { const node = el("input"); node.type = "text"; node.value = value; node.required = required; node.maxLength = 200; return node; }
    _confirm(title, message, action, danger = false) {
      const dialog = this._open(title); dialog.append(el("p", "", message));
      const actions = el("div", "dialog-actions");
      actions.append(button("Anuluj", () => this._close()));
      actions.append(button("Potwierd\u017a", async () => { await action(); this._close(); }, danger ? "danger" : "primary"));
      dialog.append(actions);
    }
    _form(title, builder, operation, makeData, after) {
      const dialog = this._open(title), form = el("form");
      const fields = builder(form); let revision = this._state.revision;
      const actions = el("div", "dialog-actions"), submit = el("button", "primary", "Zapisz"); submit.type = "submit";
      actions.append(button("Anuluj", () => this._close()), submit); form.append(actions); dialog.append(form);
      form.addEventListener("submit", async event => {
        event.preventDefault(); if (!form.reportValidity()) return;
        const data = makeData(fields);
        if (await this._mutate(operation, data, revision)) { this._close(); if (after) after(data); }
        // A rejected stale form retains the user's text, but the next explicit
        // submit uses the newly fetched revision. No silent automatic replay.
        revision = this._state?.revision;
      });
      requestAnimationFrame(() => form.querySelector("input,select")?.focus());
    }
    _categorySelect(form, list, current = null, exclude = new Set()) {
      const select = el("select"), root = el("option", "", "\u2014 Poziom g\u0142\u00f3wny \u2014"); root.value = ""; select.append(root);
      const visit = (parent, prefix) => {
        for (const node of ordered(list.nodes, parent)) {
          if (node.kind !== "category" || exclude.has(node.id)) continue;
          const option = el("option", "", `${prefix}${node.name}`); option.value = node.id; select.append(option); visit(node.id, `${prefix}\u00b7 `);
        }
      };
      visit(null, ""); select.value = current || "";
      this._field(form, "Kategoria nadrz\u0119dna", select); return select;
    }
    _newList() {
      this._form("Nowa lista", form => {
        const name = this._field(form, "Nazwa listy", this._input());
        const id = this._field(form, "ID listy (opcjonalne, np. dom)", this._input("", false));
        id.maxLength = 64; id.pattern = "[a-z0-9][a-z0-9_-]{0,63}";
        return { name, id };
      }, "create_list", f => ({ name: f.name.value, list_id: f.id.value.trim() || uuid() }), data => { this._selected = data.list_id; this._render(); });
    }
    _add(kind, parent) {
      const list = this._list; if (!list) return;
      this._form(kind === "category" ? "Nowa kategoria" : "Nowe zadanie", form => {
        const name = this._field(form, "Nazwa", this._input());
        const category = this._categorySelect(form, list, parent);
        const id = this._field(form, "ID (opcjonalne, dla automatyzacji)", this._input("", false));
        id.maxLength = 64; id.pattern = "[a-z0-9][a-z0-9_-]{0,63}";
        return { name, category, id };
      }, "add_item", f => ({ list_id: list.id, name: f.name.value, kind, parent_id: f.category.value || null, node_id: f.id.value.trim() || uuid() }));
    }
    _rename(node = null) {
      const list = this._list;
      this._form("Zmie\u0144 nazw\u0119", form => this._field(form, "Nazwa", this._input(node ? node.name : list.name)),
        node ? "rename_item" : "rename_list", input => ({ list_id: list.id, ...(node ? { node_id: node.id } : {}), name: input.value }));
    }
    _check(node, stats) {
      if (!this._editable || !stats.total) { this._render(); return; }
      const data = { list_id: this._list.id, node_id: node.id, completed: !stats.checked };
      const revision = this._state.revision;
      const affected = data.completed ? stats.total - stats.done : stats.done;
      if (node.kind === "category" && this._config.confirm_bulk && affected > 1) {
        this._render();
        this._confirm(data.completed ? "Wykona\u0107 ca\u0142\u0105 kategori\u0119?" : "Odznaczy\u0107 ca\u0142\u0105 kategori\u0119?",
          `Kategoria: ${node.name}. Zmienionych zada\u0144: ${affected}. Operacja obejmuje r\u00f3wnie\u017c ukryte i zwini\u0119te pozycje.`,
          () => this._mutate("set_completed", data, revision));
      } else this._mutate("set_completed", data, revision);
    }
    _clear() {
      const list = this._list, revision = this._state.revision;
      const count = Object.values(list.nodes).filter(n => n.kind === "task" && n.completed).length;
      this._confirm("Usun\u0105\u0107 wykonane?", `Usuni\u0119tych zada\u0144: ${count}. Kategorie pozostan\u0105 na li\u015bcie.`,
        () => this._mutate("clear_completed", { list_id: list.id }, revision), true);
    }
    _delete(node = null) {
      const list = this._list, revision = this._state.revision;
      this._confirm("Potwierd\u017a usuni\u0119cie", `Usun\u0105\u0107 \u201e${node ? node.name : list.name}\u201d${!node || node.kind === "category" ? " wraz z ca\u0142\u0105 zawarto\u015bci\u0105" : ""}?`,
        () => this._mutate(node ? "delete_item" : "delete_list", { list_id: list.id, ...(node ? { node_id: node.id } : {}) }, revision), true);
    }
    _listMenu() {
      const list = this._list, dialog = this._open(list.name), actions = el("div", "menu-actions");
      if (this._listPermissions.manage) {
        actions.append(button("Udost\u0119pnianie...", () => this._shareList()));
        actions.append(button("Zmie\u0144 nazw\u0119 listy", () => this._rename()));
        actions.append(button("Usu\u0144 list\u0119", () => this._delete(), "danger"));
      }
      const id = this._input(list.id, false); id.readOnly = true; id.className = "id-field";
      this._field(actions, "ID listy do konfiguracji karty / automatyzacji", id);
      actions.append(button("Zamknij", () => this._close())); dialog.append(actions);
    }
    async _shareList() {
      const list = this._list;
      if (!list || !this._listPermissions.manage || !this._connection?.connected) return;
      const revision = this._state.revision;
      const dialog = this._open(`Udostępnianie: ${list.name}`);
      dialog.append(el("p", "muted", "Administratorzy HA zawsze mają pełny dostęp. Dla pozostałych użytkowników wybierz: brak, tylko odczyt albo edycja."));
      const loading = el("p", "muted", "Pobieranie użytkowników Home Assistant…"); dialog.append(loading);
      let users;
      try {
        users = await this._connection.sendMessagePromise({ type: `${API}/users` });
      } catch (error) {
        loading.textContent = errorText(error);
        loading.className = "dialog-error";
        dialog.append(button("Zamknij", () => this._close()));
        return;
      }
      if (!dialog.open) return;
      loading.remove();
      const form = el("form"), rows = el("div", "share-list");
      const access = list.access || {};
      const controls = new Map();
      const visibleUsers = (users || []).filter(user => !user.system_generated);
      for (const user of visibleUsers) {
        const row = el("div", "share-row"), label = el("div");
        const title = user.name || user.id;
        label.append(el("strong", "", title));
        const details = [];
        if (!user.is_active) details.push("konto nieaktywne");
        const isAdmin = !!user.is_admin;
        if (isAdmin) details.push("administrator – zawsze ma dostęp");
        if (details.length) label.append(el("div", "muted", details.join(" · ")));
        const select = el("select");
        for (const [value, text] of [["", "Brak dostępu"], ["read", "Tylko odczyt"], ["write", "Edycja"]]) {
          const option = el("option", "", text); option.value = value; select.append(option);
        }
        select.value = isAdmin ? "" : (access[user.id] || "");
        select.disabled = isAdmin || !user.is_active;
        controls.set(user.id, { select, isAdmin });
        row.append(label, select); rows.append(row);
      }
      if (!visibleUsers.length) rows.append(el("div", "empty", "Nie znaleziono zwykłych użytkowników Home Assistant."));
      form.append(rows);
      const actions = el("div", "dialog-actions"), save = el("button", "primary", "Zapisz udostępnianie"); save.type = "submit";
      actions.append(button("Anuluj", () => this._close()), save); form.append(actions); dialog.append(form);
      form.addEventListener("submit", async event => {
        event.preventDefault();
        const next = {};
        for (const [userId, item] of controls) if (!item.isAdmin && item.select.value) next[userId] = item.select.value;
        if (await this._mutate("set_list_access", { list_id: list.id, access: next }, revision)) this._close();
      });
    }

    _itemMenu(node) {
      const list = this._list, revision = this._state.revision, dialog = this._open(node.name), actions = el("div", "menu-actions");
      if (this._editable) {
        actions.append(button("Zmie\u0144 nazw\u0119", () => this._rename(node)));
        actions.append(button("Przenie\u015b do kategorii / listy\u2026", () => this._move(node)));
        const siblings = ordered(list.nodes, node.parent_id), index = siblings.findIndex(n => n.id === node.id);
        actions.append(button("\u2191 Wy\u017cej", async () => { await this._reorder(node, index - 1, revision); this._close(); }, "", index === 0));
        actions.append(button("\u2193 Ni\u017cej", async () => { await this._reorder(node, index + 1, revision); this._close(); }, "", index === siblings.length - 1));
        if (node.kind === "category") {
          actions.append(button("+ Zadanie w tej kategorii", () => this._add("task", node.id)));
          actions.append(button("+ Podkategoria", () => this._add("category", node.id)));
        }
        actions.append(button("Usu\u0144", () => this._delete(node), "danger"));
      }
      const id = this._input(node.id, false); id.readOnly = true; id.className = "id-field";
      this._field(actions, "ID elementu (node_id / parent_id)", id);
      actions.append(button("Zamknij", () => this._close())); dialog.append(actions);
    }
    _reorder(node, position, revision) {
      return this._mutate("move_item", { list_id: this._list.id, node_id: node.id, parent_id: node.parent_id, position }, revision);
    }
    _move(node) {
      const source = this._list;
      this._form("Przenie\u015b element", form => {
        const target = el("select");
        for (const list of Object.values(this._state.lists).filter(item => this._permissions?.lists?.[item.id]?.write)) { const option = el("option", "", list.name); option.value = list.id; target.append(option); }
        target.value = source.id; this._field(form, "Lista docelowa", target);
        const parentBox = el("div"); form.append(parentBox);
        let parent;
        const update = () => {
          parentBox.replaceChildren();
          const excluded = new Set();
          if (target.value === source.id) {
            const pending = [node.id]; while (pending.length) { const id = pending.pop(); excluded.add(id); pending.push(...ordered(source.nodes, id).map(n => n.id)); }
          }
          parent = this._categorySelect(parentBox, this._state.lists[target.value], target.value === source.id ? node.parent_id : null, excluded);
        };
        target.addEventListener("change", update); update();
        form.append(el("p", "muted", "Element trafi na koniec wybranej kategorii. Kolejno\u015b\u0107 zmienisz opcjami Wy\u017cej / Ni\u017cej."));
        return { target, get parent() { return parent; } };
      }, "move_item", f => ({ list_id: source.id, node_id: node.id, target_list_id: f.target.value, parent_id: f.parent.value || null }));
    }
    _export() {
      const blob = new Blob([JSON.stringify(this._state)], { type: "application/json" });
      const url = URL.createObjectURL(blob), link = el("a");
      link.href = url; link.download = `hierarchical-tasks-${new Date().toISOString().slice(0, 10)}.json`;
      this.shadowRoot.append(link); link.click(); link.remove(); setTimeout(() => URL.revokeObjectURL(url), 60000);
      this._notice = this._admin ? "Eksport zawiera wszystkie listy wraz z ustawieniami udost\u0119pniania." : "Eksport zawiera tylko listy widoczne dla Twojego konta."; this._error = false; this._render();
    }
    _import() {
      const picker = el("input"); picker.type = "file"; picker.accept = ".json,application/json";
      picker.addEventListener("change", async () => {
        const file = picker.files?.[0]; if (!file) return;
        try {
          if (file.size > 2000000) throw new Error("Plik jest za du\u017cy. Limit wynosi 2 MB.");
          const document = JSON.parse(await file.text()), revision = this._state.revision;
          if (!document || ![1, 2].includes(document.schema) || !document.lists) throw new Error("Nieprawid\u0142owy plik eksportu.");
          this._confirm("Zast\u0105pi\u0107 WSZYSTKIE listy?", "Import zast\u0105pi ca\u0142\u0105 zawarto\u015b\u0107 integracji, nie tylko bie\u017c\u0105c\u0105 list\u0119. Najpierw wykonaj eksport obecnych danych.",
            () => this._mutate("import_data", { document }, revision), true);
        } catch (error) { this._notice = errorText(error); this._error = true; this._render(); }
        finally { picker.remove(); }
      });
      picker.hidden = true; this.shadowRoot.append(picker); picker.click();
      // Cancelled file pickers are harmless, but clean them up on the next task.
      setTimeout(() => { if (!picker.files?.length) picker.remove(); }, 120000);
    }
  }

  if (!customElements.get(TYPE)) customElements.define(TYPE, HierarchicalTasksCard);
  window.customCards = window.customCards || [];
  if (!window.customCards.some(card => card.type === TYPE)) window.customCards.push({
    type: TYPE, name: "Hierarchical Tasks", preview: false,
    description: "Lokalne listy z kategoriami, podkategoriami i tr\u00f3jstanowymi checkboxami.",
  });
  console.info(`HIERARCHICAL TASKS ${VERSION}`);
})();
