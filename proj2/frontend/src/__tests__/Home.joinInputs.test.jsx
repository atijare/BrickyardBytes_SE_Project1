import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { describe, it, expect, beforeEach, vi } from "vitest";

import Home from "../pages/Home";
import { useAuth } from "../hooks/useAuth";
import {
  listAvailableRuns,
  listJoinedRuns,
  joinRun,
} from "../services/runsService";
import { ToastProvider } from "../context/ToastContext";

vi.mock("../hooks/useAuth");
vi.mock("../services/runsService");

// Mock Menu to expose test buttons that call onConfirm with crafted payloads
vi.mock("../components/Menu", () => ({
  __esModule: true,
  default: ({ onConfirm, onClose }) => (
    <div data-testid="menu-mock">
      <button
        onClick={() =>
          onConfirm(
            [{ id: 1, name: "A", price: 1, qty: 1000000000 }],
            0
          )
        }
      >
        Confirm Large Qty
      </button>

      <button
        onClick={() =>
          onConfirm(
            [{ id: 2, name: "B", price: 5.0, qty: 2 }],
            "not-a-number"
          )
        }
      >
        Confirm Bad Tip
      </button>

      <button
        onClick={() =>
          onConfirm(
            [{ id: 3, name: "C", price: 2.5, qty: "3" }],
            "12.5"
          )
        }
      >
        Confirm String Qty and Tip
      </button>

      <button
        onClick={() =>
          onConfirm(
            [{ id: 4, name: "D", price: 0.01, qty: "1e12" }],
            0
          )
        }
      >
        Confirm Exponential Qty
      </button>

      <button onClick={onClose}>Close</button>
    </div>
  ),
}));

describe("Home joinRun input handling edge cases", () => {
  const renderHome = () =>
    render(
      <ToastProvider>
        <Home />
      </ToastProvider>
    );

  beforeEach(() => {
    vi.clearAllMocks();

    useAuth.mockReturnValue({
      user: { username: "tester" },
    });

    listAvailableRuns.mockResolvedValue([
      {
        id: 1,
        restaurant: "Cafe",
        runner_username: "alice",
        available_seats: 10,
      },
    ]);

    listJoinedRuns.mockResolvedValue([]);
  });

  it("sends very large numeric amounts when qty is huge", async () => {
    joinRun.mockResolvedValue({ pin: "0000" });

    renderHome();

    const joinButton = await screen.findByRole("button", {
      name: /full|join/i,
    });

    fireEvent.click(joinButton);

    const confirm = await screen.findByText("Confirm Large Qty");
    fireEvent.click(confirm);

    await waitFor(() => expect(joinRun).toHaveBeenCalled());

    const [runId, payload] = joinRun.mock.calls[0];

    expect(runId).toBe(1);
    expect(payload.amount).toBeCloseTo(1000000000);
  });

  it("coerces non-numeric tip to 0", async () => {
    joinRun.mockResolvedValue({ pin: "0001" });

    renderHome();

    const joinButton = await screen.findByRole("button", {
      name: /full|join/i,
    });

    fireEvent.click(joinButton);

    const btn = await screen.findByText("Confirm Bad Tip");
    fireEvent.click(btn);

    await waitFor(() => expect(joinRun).toHaveBeenCalled());

    const payload = joinRun.mock.calls[0][1];

    expect(payload.tip).toBe(0);
  });

  it("accepts numeric string quantities and string numeric tips", async () => {
    joinRun.mockResolvedValue({ pin: "0002" });

    renderHome();

    const joinButton = await screen.findByRole("button", {
      name: /full|join/i,
    });

    fireEvent.click(joinButton);

    const btn = await screen.findByText("Confirm String Qty and Tip");
    fireEvent.click(btn);

    await waitFor(() => expect(joinRun).toHaveBeenCalled());

    const payload = joinRun.mock.calls[0][1];

    expect(payload.amount).toBeCloseTo(7.5);
    expect(payload.tip).toBeCloseTo(12.5);
  });

  it("handles exponential string quantities (1e12)", async () => {
    joinRun.mockResolvedValue({ pin: "0003" });

    renderHome();

    const joinButton = await screen.findByRole("button", {
      name: /full|join/i,
    });

    fireEvent.click(joinButton);

    const btn = await screen.findByText("Confirm Exponential Qty");
    fireEvent.click(btn);

    await waitFor(() => expect(joinRun).toHaveBeenCalled());

    const payload = joinRun.mock.calls[0][1];

    expect(payload.amount).toBeCloseTo(1e10);
  });
});
