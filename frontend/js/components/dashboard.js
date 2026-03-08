/**
 * View 3 — Results dashboard with stats cards + campaign table.
 */
import { api } from "../api.js";
import { el, formatCurrency, formatPercent } from "../utils.js";
import { CampaignDetail } from "./campaign-detail.js";

export class Dashboard {
  constructor({ simId, onRunMore, onNewSim }) {
    this.simId = simId;
    this.onRunMore = onRunMore;
    this.onNewSim = onNewSim;
    this.container = null;
    this.campaignDetailEl = null;
    this.activeCampaignDetail = null;
  }

  render(parent, dashboardData) {
    this.container = el("div", { className: "view" });

    const title = el("h2", {
      className: "mt-16",
      textContent: "Results Dashboard",
      style:
        "font-family: var(--font-sans); font-size: 1.3rem; font-weight: 600; margin-bottom: 20px;",
    });

    const stats = this._renderStats(dashboardData);
    const table = this._renderCampaignTable(
      dashboardData.campaigns,
      dashboardData,
    );
    this.campaignDetailEl = el("div");

    const actions = el("div", { className: "dashboard-actions" }, [
      el("button", {
        className: "btn btn-green",
        textContent: "Run More Rounds",
        onClick: () => this.onRunMore(),
      }),
      el("button", {
        className: "btn btn-ghost",
        textContent: "Export to Google Sheets",
        onClick: (e) => this._exportToSheets(e.target),
      }),
      el("button", {
        className: "btn btn-ghost",
        textContent: "New Simulation",
        onClick: () => this.onNewSim(),
      }),
    ]);

    this.container.append(title, stats, table, this.campaignDetailEl, actions);
    parent.appendChild(this.container);
  }

  _renderStats(data) {
    const cards = [
      { value: data.total_auctions, label: "Auctions" },
      { value: formatCurrency(data.avg_winning_bid), label: "Avg Winning Bid" },
      { value: formatPercent(data.like_ratio), label: "Like Ratio" },
      { value: formatCurrency(data.total_budget_spent), label: "Budget Spent" },
    ];

    return el(
      "div",
      { className: "stats-row" },
      cards.map((c) =>
        el("div", { className: "stat-card" }, [
          el("div", { className: "stat-value", textContent: String(c.value) }),
          el("div", { className: "stat-label", textContent: c.label }),
        ]),
      ),
    );
  }

  _renderCampaignTable(campaigns, dashboard) {
    const table = el("table", { className: "campaign-table" });
    table.innerHTML = `
      <thead>
        <tr>
          <th>Campaign</th>
          <th>Goal</th>
          <th>Budget</th>
          <th>Remaining</th>
          <th>Insights</th>
        </tr>
      </thead>
    `;
    const tbody = el("tbody");

    for (const camp of campaigns) {
      const goalClass = camp.goal === "reach" ? "goal-reach" : "goal-quality";
      const tr = el("tr");
      tr.innerHTML = `
        <td>${camp.campaign_name}</td>
        <td><span class="goal-badge ${goalClass}">${camp.goal}</span></td>
        <td>${formatCurrency(camp.total_budget)}</td>
        <td>${formatCurrency(camp.remaining_budget)}</td>
        <td><button class="btn btn-ghost btn-sm insight-btn">Analyze</button></td>
      `;
      const btn = tr.querySelector(".insight-btn");
      btn.addEventListener("click", (e) => {
        e.stopPropagation();
        this._showCampaignDetail(camp);
      });
      tbody.appendChild(tr);
    }

    table.appendChild(tbody);
    return table;
  }

  async _exportToSheets(btn) {
    const original = btn.textContent;
    btn.textContent = "Exporting...";
    btn.disabled = true;
    try {
      const result = await api.exportToSheets(this.simId);
      btn.textContent = "Exported!";
      window.open(result.spreadsheet_url, "_blank");
    } catch (err) {
      btn.textContent = "Export Failed";
      console.error("Export error:", err);
      alert(`Export failed: ${err.message}`);
    } finally {
      setTimeout(() => {
        btn.textContent = original;
        btn.disabled = false;
      }, 2000);
    }
  }

  _showCampaignDetail(campaign) {
    if (this.activeCampaignDetail) {
      this.activeCampaignDetail.destroy();
    }
    this.activeCampaignDetail = new CampaignDetail({ simId: this.simId });
    this.activeCampaignDetail.render(this.campaignDetailEl, campaign);
  }

  destroy() {
    if (this.activeCampaignDetail) this.activeCampaignDetail.destroy();
    if (this.container) this.container.remove();
  }
}
