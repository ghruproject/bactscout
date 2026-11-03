/* BactScout report controls. All recorded strings are inserted as text nodes. */
(() => {
  "use strict";
  const data = JSON.parse(document.getElementById("report-data").textContent);
  const samples = data.samples;
  const $ = (id) => document.getElementById(id);
  const knownStatuses = new Set(["PASSED", "WARNING", "FAILED"]);
  let statusFilter = data.needs_review ? "REVIEW" : "ALL";
  const mixedReadTypes = new Set(samples.map((sample) => sample.read_type)).size > 1;
  const hasShortReads = samples.some((sample) => sample.read_type === "Short reads");
  const valueColumns = ["read_type", "species", "quality", "sylph_coverage", "calculated_coverage", "mlst"]
    .filter((key) => (key !== "read_type" || mixedReadTypes) && (key !== "mlst" || hasShortReads));
  document.querySelector('[data-column="read_type"]').hidden = !mixedReadTypes;
  document.querySelector('[data-column="mlst"]').hidden = !hasShortReads;
  let sortKey = "id";
  let direction = 1;
  let page = 0;
  let selectedButton = null;
  const dialog = $("sample-detail-dialog");
  const textElement = (tag, text, className) => {
    const node = document.createElement(tag);
    if (text !== undefined && text !== null) node.textContent = String(text);
    if (className) node.className = className;
    return node;
  };
  function badge(status) {
    const tones = { PASSED: "pass", WARNING: "warn", FAILED: "fail" };
    return textElement("span", status, `status-badge status-badge-${tones[status] || "not-evaluated"}`);
  }
  function section(title) {
    const node = textElement("section");
    node.append(textElement("h3", title));
    return node;
  }
  function fieldList(fields) {
    const list = textElement("dl");
    fields.forEach(([name, value]) => {
      const item = textElement("div");
      item.append(textElement("dt", name), textElement("dd", value));
      list.append(item);
    });
    return list;
  }
  function openSample(sample, button) {
    selectedButton = button;
    $("sample-detail-title").textContent = sample.id;
    const content = $("sample-detail-content");
    content.replaceChildren();
    const overview = section("QC overview");
    overview.append(badge(sample.status), fieldList([
      ["Read type", sample.read_type], ["Platform", sample.platform],
      ["Recorded species", sample.species], ["MLST ST", sample.mlst],
      ["Source CSV", sample.source]
    ]));
    if (sample.fastp) {
      const link = textElement("a", "Open fastp HTML report");
      link.href = sample.fastp;
      overview.append(link);
    }
    content.append(overview);
    const review = section("Recorded review reasons");
    const reasons = textElement("ul");
    (sample.review.length ? sample.review : ["No warning or failure reasons were recorded."])
      .forEach((reason) => reasons.append(textElement("li", reason)));
    review.append(reasons);
    content.append(review);
    const metrics = section("Measurements and individual flags");
    metrics.classList.add("raw-fields");
    const table = textElement("table", undefined, "metric-table");
    const head = textElement("thead");
    const header = textElement("tr");
    ["Measurement", "Value", "Recorded flag"].forEach((title) => {
      const cell = textElement("th", title); cell.scope = "col"; header.append(cell);
    });
    head.append(header);
    const body = textElement("tbody");
    sample.metrics.forEach((metric) => {
      const row = textElement("tr");
      const label = textElement("th", metric.label); label.scope = "row";
      const value = textElement("td", metric.value);
      if (metric.message && metric.message !== "Unavailable") {
        value.append(textElement("small", metric.message, "metric-message"));
      }
      const flag = textElement("td");
      flag.append(metric.status ? badge(metric.status) : textElement("span", "Not a QC check"));
      row.append(label, value, flag); body.append(row);
    });
    table.append(head, body); metrics.append(table); content.append(metrics);
    if (sample.resources.length) {
      const resource = section("Recorded resource measurements");
      resource.append(fieldList(sample.resources.map((field) => [field.label, field.value])));
      content.append(resource);
    }
    const raw = section("Full recorded data"); raw.classList.add("raw-fields");
    const disclosure = textElement("details");
    disclosure.append(textElement("summary", "Show every CSV field"), fieldList(Object.entries(sample.raw)));
    raw.append(disclosure); content.append(raw);
    dialog.showModal();
  }
  dialog.addEventListener("close", () => {
    if (selectedButton && selectedButton.isConnected) selectedButton.focus();
  });
  function comparable(value) {
    const numeric = Number.parseFloat(String(value).replaceAll(",", ""));
    return Number.isFinite(numeric) ? numeric : String(value).toLowerCase();
  }
  function compare(a, b) {
    const left = comparable(a[sortKey]), right = comparable(b[sortKey]);
    if (left === right) return a.id.localeCompare(b.id);
    if (typeof left === "number" && typeof right === "number") return direction * (left - right);
    if (typeof left === "number") return -1;
    if (typeof right === "number") return 1;
    return direction * left.localeCompare(right);
  }
  function render() {
    const search = $("sample-search").value.trim().toLowerCase();
    const species = $("species-filter").value;
    const type = $("type-filter").value;
    const rows = samples.filter((sample) => {
      const status = knownStatuses.has(sample.status) ? sample.status : "Unavailable";
      if (statusFilter === "REVIEW" && status === "PASSED") return false;
      if (!["ALL", "REVIEW"].includes(statusFilter) && status !== statusFilter) return false;
      return (!species || sample.species === species) && (!type || sample.read_type === type)
        && (!search || JSON.stringify(sample.raw).toLowerCase().includes(search)
          || sample.read_type.toLowerCase().includes(search));
    }).sort(compare);
    const size = Number($("page-size").value);
    const totalPages = Math.max(1, Math.ceil(rows.length / size));
    page = Math.max(0, Math.min(page, totalPages - 1));
    const tbody = $("sample-rows"); tbody.replaceChildren();
    rows.slice(page * size, (page + 1) * size).forEach((sample) => {
      const row = textElement("tr");
      const sampleCell = textElement("td");
      const button = textElement("button", sample.id, "sample-open"); button.type = "button";
      button.setAttribute("aria-label", `Open details for ${sample.id}`);
      button.title = sample.id;
      button.addEventListener("click", () => openSample(sample, button));
      sampleCell.append(button); row.append(sampleCell);
      const status = textElement("td"); status.append(badge(sample.status)); row.append(status);
      const checks = textElement("td", undefined, "review-checks");
      const checkText = sample.review_checks.map((check) => check.label).join(", ");
      const checkSummary = textElement("span", checkText || (sample.status === "PASSED" ? "—" : "See details"));
      checkSummary.title = sample.review_checks.map((check) =>
        `${check.label}: ${check.status}${check.message === "Unavailable" ? "" : ` — ${check.message}`}`
      ).join("\n") || (sample.review.join("\n") || "No individual warning or failure flags recorded.");
      if (sample.review_checks.length) {
        checkSummary.classList.add(sample.review_checks.some((check) => check.status === "FAILED") ? "check-failed" : "check-warning");
      }
      checks.append(checkSummary); row.append(checks);
      valueColumns.forEach((key) => {
        const cell = textElement("td", sample[key]); cell.title = sample[key]; row.append(cell);
      });
      tbody.append(row);
    });
    if (!rows.length) {
      const row = textElement("tr"), cell = textElement("td", "No samples match these filters.");
      cell.colSpan = 3 + valueColumns.length; row.append(cell); tbody.append(row);
    }
    $("filter-summary").textContent = `Showing ${rows.length ? page * size + 1 : 0}–${Math.min((page + 1) * size, rows.length)} of ${rows.length} matching samples (${samples.length} total).`;
    $("page-summary").textContent = `Page ${page + 1} of ${totalPages}`;
    $("previous-page").disabled = page === 0;
    $("next-page").disabled = page + 1 >= totalPages;
    document.querySelectorAll("[data-filter]").forEach((button) => {
      const active = button.dataset.filter === statusFilter;
      button.classList.toggle("is-active", active);
      button.setAttribute("aria-pressed", String(active));
    });
  }
  [...new Set(samples.map((sample) => sample.species))].sort().forEach((species) => {
    const option = textElement("option", species); option.value = species; $("species-filter").append(option);
  });
  document.querySelectorAll("[data-filter]").forEach((button) => {
    button.addEventListener("click", () => { statusFilter = button.dataset.filter; page = 0; render(); });
  });
  ["sample-search", "species-filter", "type-filter", "page-size"].forEach((id) => {
    $(id).addEventListener(id === "sample-search" ? "input" : "change", () => { page = 0; render(); });
  });
  document.querySelectorAll("[data-sort]").forEach((button) => {
    button.addEventListener("click", () => {
      direction = sortKey === button.dataset.sort ? -direction : 1;
      sortKey = button.dataset.sort;
      document.querySelectorAll("#sample-table th").forEach((cell) => cell.removeAttribute("aria-sort"));
      button.parentElement.setAttribute("aria-sort", direction === 1 ? "ascending" : "descending");
      render();
    });
  });
  $("previous-page").addEventListener("click", () => { page -= 1; render(); });
  $("next-page").addEventListener("click", () => { page += 1; render(); });
  $("sidebar-toggle").addEventListener("click", () => {
    const collapsed = $("report-layout").classList.toggle("sidebar-collapsed");
    $("sidebar-toggle").setAttribute("aria-expanded", String(!collapsed));
    $("sidebar-toggle").setAttribute("aria-label", collapsed ? "Expand report navigation" : "Collapse report navigation");
    $("sidebar-toggle").firstElementChild.textContent = collapsed ? "→" : "←";
  });
  $("download-data").addEventListener("click", () => {
    const url = URL.createObjectURL(new Blob([JSON.stringify(data, null, 2)], { type: "application/json" }));
    const link = textElement("a"); link.href = url; link.download = "bactscout-report-data.json";
    document.body.append(link); link.click(); link.remove(); setTimeout(() => URL.revokeObjectURL(url), 1000);
  });
  render();
})();
