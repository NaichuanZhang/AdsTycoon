/**
 * Campaign editor cards — editable campaign data between seed and auction.
 */
import { el } from "../utils.js";
import { api } from "../api.js";

export class CampaignEditor {
  constructor({ simId }) {
    this.simId = simId;
    this.container = null;
  }

  async render(parent) {
    this.container = el("div", { className: "campaign-editor" });

    const header = el("h3", {
      className: "campaign-editor-header",
      textContent: "Review & Edit Campaigns",
    });
    this.container.appendChild(header);

    const grid = el("div", { className: "campaign-grid" });
    this.container.appendChild(grid);
    parent.appendChild(this.container);

    try {
      const campaigns = await api.getCampaigns(this.simId);
      for (const c of campaigns) {
        grid.appendChild(this._buildCard(c));
      }
    } catch (err) {
      grid.appendChild(
        el("div", { className: "campaign-card-error", textContent: `Failed to load campaigns: ${err.message}` }),
      );
    }
  }

  _buildCard(campaign) {
    const card = el("div", { className: "campaign-card" });

    const nameInput = this._field(card, "Name", "input", campaign.campaign_name);
    const descArea = this._field(card, "Description", "textarea", campaign.product_description);
    const creativeArea = this._field(card, "Creative", "textarea", campaign.creative);
    const goalSelect = this._goalSelect(card, campaign.goal);
    const budgetInput = this._field(card, "Budget ($)", "number", campaign.total_budget);

    const feedback = el("div", { className: "card-feedback" });
    const saveBtn = el("button", {
      className: "btn btn-primary btn-sm",
      textContent: "Save",
      onClick: () =>
        this._save(campaign.id, { nameInput, descArea, creativeArea, goalSelect, budgetInput }, feedback),
    });

    const footer = el("div", { className: "card-footer" }, [saveBtn, feedback]);
    card.appendChild(footer);
    return card;
  }

  _field(card, label, type, value) {
    const group = el("div", { className: "card-field" });
    group.appendChild(el("label", { textContent: label }));

    let input;
    if (type === "textarea") {
      input = el("textarea", { className: "card-input", rows: "2" });
      input.value = value ?? "";
    } else if (type === "number") {
      input = el("input", { type: "number", className: "card-input", min: "0.01", step: "0.01" });
      input.value = value ?? "";
    } else {
      input = el("input", { type: "text", className: "card-input" });
      input.value = value ?? "";
    }

    group.appendChild(input);
    card.appendChild(group);
    return input;
  }

  _goalSelect(card, current) {
    const group = el("div", { className: "card-field" });
    group.appendChild(el("label", { textContent: "Goal" }));

    const select = el("select", { className: "card-input" });
    for (const opt of ["reach", "quality"]) {
      const option = el("option", { value: opt, textContent: opt });
      if (opt === current) option.selected = true;
      select.appendChild(option);
    }

    group.appendChild(select);
    card.appendChild(group);
    return select;
  }

  async _save(campaignId, fields, feedbackEl) {
    const budget = parseFloat(fields.budgetInput.value);
    if (!fields.nameInput.value.trim()) {
      this._showFeedback(feedbackEl, "Name cannot be empty", true);
      return;
    }
    if (isNaN(budget) || budget <= 0) {
      this._showFeedback(feedbackEl, "Budget must be positive", true);
      return;
    }

    const data = {
      campaign_name: fields.nameInput.value.trim(),
      product_description: fields.descArea.value.trim(),
      creative: fields.creativeArea.value.trim(),
      goal: fields.goalSelect.value,
      total_budget: budget,
    };

    try {
      await api.updateCampaign(this.simId, campaignId, data);
      this._showFeedback(feedbackEl, "Saved", false);
    } catch (err) {
      this._showFeedback(feedbackEl, err.message, true);
    }
  }

  _showFeedback(el, message, isError) {
    el.textContent = message;
    el.className = isError ? "card-feedback error" : "card-feedback success";
    setTimeout(() => {
      el.textContent = "";
      el.className = "card-feedback";
    }, 3000);
  }

  destroy() {
    if (this.container) this.container.remove();
  }
}
