/**
 * Main app controller — view switching and data flow.
 */
import { $, el } from "./utils.js";
import { api, connectSSE } from "./api.js";
import { ScenarioInput } from "./components/scenario-input.js";
import { AgentStream } from "./components/agent-stream.js";
import { Dashboard } from "./components/dashboard.js";

class App {
  constructor() {
    this.root = $("#app-root");
    this.newSimBtn = $("#btn-new-sim");
    this.currentView = null;
    this.simId = null;
    this.scenario = null;
    this.sseConnection = null;

    this.newSimBtn.addEventListener("click", () => this.showLaunchView());
    this.showLaunchView();
  }

  clearView() {
    if (this.sseConnection) {
      this.sseConnection.close();
      this.sseConnection = null;
    }
    if (this.currentView) {
      this.currentView.destroy();
      this.currentView = null;
    }
    this.root.innerHTML = "";
  }

  // --- View 1: Launch ---
  showLaunchView() {
    this.clearView();
    this.newSimBtn.style.display = "none";

    const view = new ScenarioInput({
      onLaunch: (config) => this.launchSimulation(config),
    });
    view.render(this.root);
    this.currentView = view;
  }

  async launchSimulation({
    scenario,
    numConsumers,
    numWebsites,
    numCampaigns,
    numRounds,
  }) {
    try {
      const sim = await api.createSimulation(
        scenario,
        numConsumers,
        numWebsites,
        numCampaigns,
        numRounds,
      );
      this.simId = sim.id;
      this.scenario = scenario;
      this.numRounds = sim.num_rounds;
      this.showStreamView();
      this.startSeeding();
    } catch (err) {
      alert(`Failed to create simulation: ${err.message}`);
    }
  }

  // --- View 2: Agent Stream ---
  showStreamView() {
    this.clearView();
    this.newSimBtn.style.display = "block";

    const view = new AgentStream({
      onRunAuctions: (rounds) => this.startAuctions(rounds),
      onViewResults: () => this.showDashboard(),
    });
    view.render(this.root, this.scenario);
    this.currentView = view;
  }

  startSeeding() {
    const view = this.currentView;
    view.setStatus("Seeding simulation...", "active");

    this.sseConnection = connectSSE(
      `/simulations/${this.simId}/stream/seed`,
      (event) => {
        view.handleEvent(event);
        if (event.type === "done") {
          if (this.sseConnection) this.sseConnection.close();
          this.sseConnection = null;
          view.showSeedComplete(this.numRounds);
        }
        if (event.type === "error") {
          if (this.sseConnection) this.sseConnection.close();
          this.sseConnection = null;
        }
      },
      (err) => {
        view.setStatus("Connection lost", "error");
      },
    );
  }

  startAuctions(rounds) {
    const view = this.currentView;
    view.setStatus(`Running ${rounds} auction rounds...`, "active");

    this.sseConnection = connectSSE(
      `/simulations/${this.simId}/stream/run?rounds=${rounds}`,
      (event) => {
        view.handleEvent(event);
        if (event.type === "done") {
          if (this.sseConnection) this.sseConnection.close();
          this.sseConnection = null;
          view.showRunComplete();
        }
        if (event.type === "error") {
          if (this.sseConnection) this.sseConnection.close();
          this.sseConnection = null;
        }
      },
      (err) => {
        view.setStatus("Connection lost", "error");
      },
    );
  }

  // --- View 3: Dashboard ---
  async showDashboard() {
    try {
      const data = await api.getDashboard(this.simId);
      this.clearView();
      this.newSimBtn.style.display = "block";

      const view = new Dashboard({
        simId: this.simId,
        onRunMore: () => {
          this.showStreamView();
          this.startAuctions(3);
        },
        onNewSim: () => this.showLaunchView(),
      });
      view.render(this.root, data);
      this.currentView = view;
    } catch (err) {
      alert(`Failed to load dashboard: ${err.message}`);
    }
  }
}

// Boot
new App();
