/**
 * View 1 — Scenario text input + config + "Launch" button.
 */
import { el } from "../utils.js";

const EXAMPLE_SCENARIOS = [
  "A luxury watch brand vs a budget fitness tracker competing for affluent professionals aged 30-50 who browse business news and lifestyle sites.",
  "Three coffee brands with different strategies: one wants maximum reach, one targets quality coffee enthusiasts, and one focuses on eco-conscious millennials.",
  "A tech startup launching a new AI coding assistant competing against established IDE tools. Target: software developers browsing tech blogs and forums.",
];

export class ScenarioInput {
  constructor({ onLaunch }) {
    this.onLaunch = onLaunch;
    this.container = null;
  }

  render(parent) {
    this.container = el("div", { className: "view scenario-container" });

    const title = el("h2", { textContent: "Launch a Simulation" });
    const subtitle = el("p", {
      textContent:
        "Describe your ad scenario. AdsTycoon's AI agents will generate consumers, websites, and competing campaigns, then run real-time auctions.",
    });

    const textarea = el("textarea", {
      className: "scenario-textarea",
      placeholder:
        'e.g. "Two sneaker brands — Nike targeting athletes and Allbirds targeting eco-conscious millennials — competing across sports and lifestyle websites..."',
    });
    textarea.rows = 5;

    const exampleBtn = el("button", {
      className: "btn btn-ghost btn-sm",
      textContent: "Try an example",
      onClick: () => {
        const idx = Math.floor(Math.random() * EXAMPLE_SCENARIOS.length);
        textarea.value = EXAMPLE_SCENARIOS[idx];
      },
    });

    const options = el("div", { className: "scenario-options" }, [
      this._makeSelect("Consumers", "consumers", [5, 10, 15, 20, 30, 50], 20),
      this._makeSelect("Websites", "websites", [3, 5, 8, 10, 15, 20], 10),
      this._makeSelect("Campaigns", "campaigns", [2, 3, 4, 5, 6, 8], 4),
      this._makeSelect("Rounds", "rounds", [1, 3, 5, 10, 15, 20, 30, 50], 3),
    ]);

    const launchBtn = el("button", {
      className: "btn btn-primary",
      textContent: "Launch Simulation",
      onClick: () => this._handleLaunch(textarea),
    });

    this.container.append(
      title,
      subtitle,
      textarea,
      el("div", { className: "mt-8" }, [exampleBtn]),
      options,
      launchBtn,
    );
    parent.appendChild(this.container);
  }

  _makeSelect(label, id, values, defaultVal) {
    const group = el("div", { className: "option-group" });
    group.appendChild(el("label", { textContent: label }));
    const select = el("select", {
      className: "option-select",
      id: `opt-${id}`,
    });
    for (const v of values) {
      const opt = el("option", { value: v, textContent: String(v) });
      if (v === defaultVal) opt.selected = true;
      select.appendChild(opt);
    }
    group.appendChild(select);
    return group;
  }

  _handleLaunch(textarea) {
    const scenario = textarea.value.trim();
    if (!scenario) {
      textarea.focus();
      return;
    }
    const numConsumers = parseInt(
      document.getElementById("opt-consumers").value,
    );
    const numWebsites = parseInt(document.getElementById("opt-websites").value);
    const numCampaigns = parseInt(
      document.getElementById("opt-campaigns").value,
    );
    const numRounds = parseInt(document.getElementById("opt-rounds").value);

    this.onLaunch({
      scenario,
      numConsumers,
      numWebsites,
      numCampaigns,
      numRounds,
    });
  }

  destroy() {
    if (this.container) this.container.remove();
  }
}
