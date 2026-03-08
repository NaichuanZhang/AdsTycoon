/**
 * View 2 — Live agent event log (tool calls, text, auction events).
 */
import { el, formatJson, formatCurrency, renderMarkdown } from "../utils.js";

export class AgentStream {
  constructor({ onRunAuctions, onViewResults }) {
    this.onRunAuctions = onRunAuctions;
    this.onViewResults = onViewResults;
    this.container = null;
    this.logEl = null;
    this.statusDot = null;
    this.statusText = null;
    this.actionsEl = null;
    this.textBuffer = "";
  }

  render(parent, scenario) {
    this.container = el("div", { className: "view" });

    const header = el("div", { className: "stream-header" }, [
      el("h2", { textContent: "Agent Activity" }),
      el("div", { className: "scenario-text", textContent: scenario }),
    ]);

    this.statusDot = el("div", { className: "status-dot" });
    this.statusText = el("span", { textContent: "Connecting..." });
    const statusBar = el("div", { className: "stream-status" }, [
      this.statusDot,
      this.statusText,
    ]);

    this.logEl = el("div", { className: "stream-log" });

    this.actionsEl = el("div", { className: "stream-actions hidden" });

    this.container.append(header, statusBar, this.logEl, this.actionsEl);
    parent.appendChild(this.container);
  }

  handleEvent(event) {
    switch (event.type) {
      case "status":
        this.setStatus(event.message, "active");
        break;
      case "text":
        this._appendText(event.content);
        break;
      case "tool_call":
        this._flushText();
        this._appendToolCall(event.tool, event.input);
        break;
      case "auction_start":
        this._flushText();
        this._appendAuctionStart(event);
        break;
      case "campaign_turn":
        this._flushText();
        this._appendCampaignTurn(event);
        break;
      case "auction_winner":
        this._flushText();
        this._appendWinner(event);
        break;
      case "auction_end":
        this._flushText();
        this._appendAuctionEnd(event);
        break;
      case "done":
        this._flushText();
        this.setStatus(event.message, "done");
        break;
      case "error":
        this._flushText();
        this._appendError(event.message);
        this.setStatus("Error", "error");
        break;
    }
    this._autoScroll();
  }

  setStatus(message, state = "active") {
    this.statusText.textContent = message;
    this.statusDot.className =
      "status-dot" +
      (state === "done" ? " done" : state === "error" ? " error" : "");
  }

  showSeedComplete(defaultRounds = 3) {
    this.actionsEl.classList.remove("hidden");
    this.actionsEl.innerHTML = "";

    const label = el("span", {
      className: "rounds-label",
      textContent: "Rounds:",
    });
    const input = el("input", {
      type: "number",
      className: "rounds-input",
      value: String(defaultRounds),
      min: "1",
      max: "50",
    });
    const runBtn = el("button", {
      className: "btn btn-green",
      textContent: "Run Auctions",
      onClick: () => {
        const rounds = parseInt(input.value) || 3;
        this.actionsEl.classList.add("hidden");
        this.onRunAuctions(rounds);
      },
    });

    this.actionsEl.append(label, input, runBtn);
  }

  showRunComplete() {
    this.actionsEl.classList.remove("hidden");
    this.actionsEl.innerHTML = "";

    const label = el("span", {
      className: "rounds-label",
      textContent: "More rounds:",
    });
    const input = el("input", {
      type: "number",
      className: "rounds-input",
      value: "3",
      min: "1",
      max: "50",
    });
    const moreBtn = el("button", {
      className: "btn btn-green",
      textContent: "Run More",
      onClick: () => {
        const rounds = parseInt(input.value) || 3;
        this.actionsEl.classList.add("hidden");
        this.onRunAuctions(rounds);
      },
    });
    const resultsBtn = el("button", {
      className: "btn btn-primary",
      textContent: "View Results",
      onClick: () => this.onViewResults(),
    });

    this.actionsEl.append(label, input, moreBtn, resultsBtn);
  }

  _appendText(content) {
    this.textBuffer += content;
  }

  _flushText() {
    if (!this.textBuffer.trim()) {
      this.textBuffer = "";
      return;
    }
    const entry = el("div", {
      className: "log-entry log-text log-markdown",
      innerHTML: renderMarkdown(this.textBuffer.trim()),
    });
    this.logEl.appendChild(entry);
    this.textBuffer = "";
  }

  _appendToolCall(toolName, input) {
    const entry = el("div", { className: "log-entry log-tool-call" });
    entry.innerHTML = `<span class="tool-name">${toolName}</span>`;
    const inputEl = el("div", { className: "tool-input" });
    inputEl.textContent = formatJson(input);
    entry.appendChild(inputEl);
    entry.addEventListener("click", () => entry.classList.toggle("expanded"));
    this.logEl.appendChild(entry);
  }

  _appendAuctionStart(event) {
    const entry = el("div", { className: "log-entry log-auction-start" });
    entry.innerHTML = `
      <div class="round-label">Round ${event.round} / ${event.total_rounds}</div>
      <div class="context">${event.consumer} browsing ${event.website}</div>
    `;
    this.logEl.appendChild(entry);
  }

  _appendCampaignTurn(event) {
    const entry = el("div", {
      className: "log-entry log-campaign-turn",
      textContent: `${event.campaign} (${event.goal}) — budget: ${formatCurrency(event.remaining_budget)}`,
    });
    this.logEl.appendChild(entry);
  }

  _appendWinner(event) {
    const entry = el("div", { className: "log-entry log-winner" });
    entry.innerHTML = `<span class="winner-label">Winner: ${event.campaign} — ${formatCurrency(event.bid)}</span>`;
    this.logEl.appendChild(entry);
  }

  _appendAuctionEnd(event) {
    const entry = el("div", { className: "log-entry log-auction-end" });
    const feedbackClass =
      event.feedback === "like"
        ? "feedback-like"
        : event.feedback === "dislike"
          ? "feedback-dislike"
          : "";
    entry.innerHTML = `
      <span>${event.winner || "No bids"}</span>
      <span>${event.winning_bid ? formatCurrency(event.winning_bid) : "-"}</span>
      <span class="${feedbackClass}">${event.feedback || "-"}</span>
    `;
    this.logEl.appendChild(entry);
  }

  _appendError(message) {
    const entry = el("div", {
      className: "log-entry log-error",
      textContent: message,
    });
    this.logEl.appendChild(entry);
  }

  _autoScroll() {
    if (this.logEl) {
      this.logEl.scrollTop = this.logEl.scrollHeight;
    }
  }

  destroy() {
    if (this.container) this.container.remove();
  }
}
