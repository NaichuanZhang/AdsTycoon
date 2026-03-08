/**
 * Campaign detail panel with streamed AI insights.
 */
import { el, formatCurrency, renderMarkdown } from "../utils.js";
import { api, connectSSE } from "../api.js";

export class CampaignDetail {
  constructor({ simId }) {
    this.simId = simId;
    this.container = null;
    this.sseConnection = null;
  }

  render(parent, campaign) {
    if (this.container) this.container.remove();

    this.container = el("div", { className: "insight-panel" });
    this.container.innerHTML = `
      <h3>${campaign.campaign_name} — Insights</h3>
      <div class="summary text-dim">Analyzing with AI agent...</div>
      <ul class="suggestions"></ul>
    `;

    parent.appendChild(this.container);
    this._fetchInsights(campaign.id);
  }

  async _fetchInsights(campaignId) {
    const summaryEl = this.container.querySelector(".summary");
    const suggestionsEl = this.container.querySelector(".suggestions");

    let textBuffer = "";

    this.sseConnection = connectSSE(
      `/simulations/${this.simId}/stream/insights/${campaignId}`,
      (event) => {
        if (event.type === "text") {
          textBuffer += event.content;
          summaryEl.innerHTML = renderMarkdown(textBuffer);
          summaryEl.classList.add("log-markdown");
        } else if (event.type === "tool_call") {
          summaryEl.textContent = `Calling ${event.tool}...`;
        } else if (event.type === "done") {
          this._parseInsights(textBuffer, summaryEl, suggestionsEl);
          if (this.sseConnection) this.sseConnection.close();
        } else if (event.type === "error") {
          summaryEl.textContent = `Error: ${event.message}`;
          summaryEl.className = "summary text-red";
          if (this.sseConnection) this.sseConnection.close();
        }
      },
      (err) => {
        // Stream ended — try to parse whatever we have
        if (textBuffer) {
          this._parseInsights(textBuffer, summaryEl, suggestionsEl);
        }
      },
    );
  }

  _parseInsights(text, summaryEl, suggestionsEl) {
    try {
      const start = text.indexOf("{");
      const end = text.lastIndexOf("}") + 1;
      if (start >= 0 && end > start) {
        const json = JSON.parse(text.slice(start, end));
        summaryEl.textContent = json.summary || text;
        suggestionsEl.innerHTML = "";
        for (const s of json.suggestions || []) {
          suggestionsEl.appendChild(el("li", { textContent: s }));
        }
        return;
      }
    } catch {
      // Not JSON, display raw text
    }
    summaryEl.innerHTML = renderMarkdown(text || "Analysis complete.");
    summaryEl.classList.add("log-markdown");
  }

  destroy() {
    if (this.sseConnection) this.sseConnection.close();
    if (this.container) this.container.remove();
  }
}
