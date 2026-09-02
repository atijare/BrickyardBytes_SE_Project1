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

// Mock Menu so we can directly provide different quantity/tip inputs.
vi.mock("../components/Menu", () => ({
  __esModule: true,
  default: ({ onConfirm, onClose }) => (
    <div data-testid="menu-mock">
      {/* Valid large quantity */}
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

      {/* Non-numeric tip */}
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

      {/* Numeric strings */}
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

      {/* Large exponential value */}
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

      {/* Empty quantity */}
      <button
        onClick={() =>
          onConfirm(
            [{ id: 5, name: "E", price: 5, qty: "" }],
            0
          )
        }
      >
        Confirm Empty Qty
      </button>

      {/* Non-numeric quantity */}
      <button
        onClick={() =>
          onConfirm(
            [{ id: 6, name: "F", price: 5, qty: "abc" }],
            0
          )
        }
      >
        Confirm Invalid Qty
      </button>

      {/* Negative quantity */}
      <button
        onClick={() =>
          onConfirm(
            [{ id: 7, name: "G", price: 5, qty: "-5" }],
            0
          )
        }
      >
        Confirm Negative Qty
      </button>

      {/* Zero quantity */}
      <button
        onClick={() =>
          onConfirm(
            [{ id: 8, name: "H", price: 5, qty: "0" }],
            0
          )
        }
      >
        Confirm Zero Qty
      </button>

      {/* Null quantity */}
      <button
        onClick={() =>
          onConfirm(
            [{ id: 9, name: "I", price: 5, qty: null }],
            0
          )
        }
      >
        Confirm Null Qty
      </button>

      {/* Undefined quantity */}
      <button
        onClick={() =>
          onConfirm(
            [{ id: 10, name: "J", price: 5, qty: undefined }],
            0
          )
        }
      >
        Confirm Undefined Qty
      </button>

      {/* Quantity that converts to Infinity */}
      <button
        onClick={() =>
          onConfirm(
            [{ id: 11, name: "K", price: 5, qty: "1e999" }],
            0
          )
        }
      >
        Confirm Infinite Qty
      </button>

      {/* Negative tip */}
      <button
        onClick={() =>
          onConfirm(
            [{ id: 12, name: "L", price: 5, qty: 2 }],
            "-100"
          )
        }
      >
        Confirm Negative Tip
      </button>

      {/* Infinite tip */}
      <button
        onClick={() =>
          onConfirm(
            [{ id: 13, name: "M", price: 5, qty: 2 }],
            "Infinity"
          )
        }
      >
        Confirm Infinite Tip
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

    joinRun.mockResolvedValue({
      pin: "0000",
    });
  });

  const openJoinMenu = async () => {
    renderHome();

    const joinButton = await screen.findByRole("button", {
      name: /full|join/i,
    });

    fireEvent.click(joinButton);

    await screen.findByTestId("menu-mock");
  };

  it("submits a valid large quantity with the correct calculated amount", async () => {
    await openJoinMenu();

    fireEvent.click(screen.getByText("Confirm Large Qty"));

    await waitFor(() => {
      expect(joinRun).toHaveBeenCalledTimes(1);
    });

    const [runId, payload] = joinRun.mock.calls[0];

    expect(runId).toBe(1);
    expect(payload.amount).toBe(1000000000);
  });

  it("accepts numeric string quantities and numeric string tips", async () => {
    await openJoinMenu();

    fireEvent.click(screen.getByText("Confirm String Qty and Tip"));

    await waitFor(() => {
      expect(joinRun).toHaveBeenCalledTimes(1);
    });

    const payload = joinRun.mock.calls[0][1];

    expect(payload.amount).toBe(7.5);
    expect(payload.tip).toBe(12.5);
  });

  it("handles a non-numeric tip without submitting an invalid value", async () => {
    await openJoinMenu();

    fireEvent.click(screen.getByText("Confirm Bad Tip"));

    await waitFor(() => {
      expect(joinRun).toHaveBeenCalledTimes(1);
    });

    const payload = joinRun.mock.calls[0][1];

    expect(Number.isFinite(payload.tip)).toBe(true);
    expect(payload.tip).toBe(0);
  });

  it("rejects an empty quantity", async () => {
    await openJoinMenu();

    fireEvent.click(screen.getByText("Confirm Empty Qty"));

    await waitFor(() => {
      expect(joinRun).not.toHaveBeenCalled();
    });
  });

  it("rejects a non-numeric quantity", async () => {
    await openJoinMenu();

    fireEvent.click(screen.getByText("Confirm Invalid Qty"));

    await waitFor(() => {
      expect(joinRun).not.toHaveBeenCalled();
    });
  });

  it("rejects a negative quantity", async () => {
    await openJoinMenu();

    fireEvent.click(screen.getByText("Confirm Negative Qty"));

    await waitFor(() => {
      expect(joinRun).not.toHaveBeenCalled();
    });
  });

  it("rejects a zero quantity", async () => {
    await openJoinMenu();

    fireEvent.click(screen.getByText("Confirm Zero Qty"));

    await waitFor(() => {
      expect(joinRun).not.toHaveBeenCalled();
    });
  });

  it("rejects a null quantity", async () => {
    await openJoinMenu();

    fireEvent.click(screen.getByText("Confirm Null Qty"));

    await waitFor(() => {
      expect(joinRun).not.toHaveBeenCalled();
    });
  });

  it("rejects an undefined quantity", async () => {
    await openJoinMenu();

    fireEvent.click(screen.getByText("Confirm Undefined Qty"));

    await waitFor(() => {
      expect(joinRun).not.toHaveBeenCalled();
    });
  });

  it("rejects a quantity that evaluates to Infinity", async () => {
    await openJoinMenu();

    fireEvent.click(screen.getByText("Confirm Infinite Qty"));

    await waitFor(() => {
      expect(joinRun).not.toHaveBeenCalled();
    });
  });

  it("rejects a negative tip", async () => {
    await openJoinMenu();

    fireEvent.click(screen.getByText("Confirm Negative Tip"));

    await waitFor(() => {
      expect(joinRun).not.toHaveBeenCalled();
    });
  });

  it("rejects an infinite tip", async () => {
    await openJoinMenu();

    fireEvent.click(screen.getByText("Confirm Infinite Tip"));

    await waitFor(() => {
      expect(joinRun).not.toHaveBeenCalled();
    });
  });

  it("does not submit an infinite amount even when quantity is extremely large", async () => {
    await openJoinMenu();

    fireEvent.click(screen.getByText("Confirm Infinite Qty"));

    await waitFor(() => {
      expect(joinRun).not.toHaveBeenCalled();
    });
  });
});
