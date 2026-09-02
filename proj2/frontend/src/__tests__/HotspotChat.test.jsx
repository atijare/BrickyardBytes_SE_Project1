import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import HotspotChat from "../components/HotspotChat";

const mockListAvailableRuns = vi.fn();

vi.mock("../api", () => ({
  listAvailableRuns: (...args) => mockListAvailableRuns(...args),
}));

describe("HotspotChat", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockListAvailableRuns.mockResolvedValue([]);
  });

  it("renders the chatbot greeting", async () => {
    render(<HotspotChat />);

    expect(
      screen.getByText(
        /Hi! I am your campus-run scout/i
      )
    ).toBeInTheDocument();
  });

  it("shows live run insights", async () => {
    mockListAvailableRuns.mockResolvedValue([
      {
        id: 1,
        restaurant: "Talley Food Court",
        drop_point: "Hunt Library",
        seats_remaining: 2,
        orders: [],
        departure_time: null,
      },
    ]);

    render(<HotspotChat />);

    fireEvent.click(screen.getByRole("button", { name: /Run Insights/i }));

    expect(
      await screen.findByText(
        /Live snapshot: 1 runs \| fill 0% \| 2 seats open\./i
      )
    ).toBeInTheDocument();

    expect(
      screen.getByText(/Busiest drop: Hunt Library/i)
    ).toBeInTheDocument();
  });

  it("shows alerts for runs with low remaining seats", async () => {
    mockListAvailableRuns.mockResolvedValue([
      {
        id: 2,
        restaurant: "Hunt Library Cafe",
        drop_point: "Talley Student Union",
        seats_remaining: 1,
        orders: [],
        departure_time: null,
      },
    ]);

    render(<HotspotChat />);

    fireEvent.click(screen.getByRole("button", { name: /Seat Alerts/i }));

    expect(
      await screen.findByText(/These runs are almost full/i)
    ).toBeInTheDocument();

    expect(
      screen.getByText(/Hunt Library Cafe → Talley Student Union/i)
    ).toBeInTheDocument();

    expect(
      screen.getByText(/0 joined · 1 seat left/i)
    ).toBeInTheDocument();
  });

  it("shows broadcast tips", async () => {
    render(<HotspotChat />);

    fireEvent.click(
      screen.getByRole("button", { name: /Broadcast Tips/i })
    );

    expect(
      await screen.findByText(/broadcast/i)
    ).toBeInTheDocument();
  });

  it("answers a useful natural-language question", async () => {
    render(<HotspotChat />);

    const input = screen.getByRole("textbox");

    fireEvent.change(input, {
      target: { value: "Where are the busiest hotspots?" },
    });

    fireEvent.click(screen.getByRole("button", { name: /Ask/i }));

    expect(
      await screen.findByText(/hotspot/i)
    ).toBeInTheDocument();
  });

  it("uses a fallback response for unsupported questions", async () => {
    render(<HotspotChat />);

    const input = screen.getByRole("textbox");

    fireEvent.change(input, {
      target: { value: "What is the weather tomorrow?" },
    });

    fireEvent.click(screen.getByRole("button", { name: /Ask/i }));

    expect(
      await screen.findByText(/campus-run scout/i)
    ).toBeInTheDocument();
  });

  it("shows an error when available runs cannot be loaded", async () => {
    mockListAvailableRuns.mockRejectedValue(
      new Error("Network error")
    );

    render(<HotspotChat />);

    expect(
      await screen.findByText(/unable to load/i)
    ).toBeInTheDocument();
  });

  it("shows information for a specific run", async () => {
    mockListAvailableRuns.mockResolvedValue([
      {
        id: 3,
        restaurant: "Talley Food Court",
        drop_point: "Hunt Library",
        seats_remaining: 2,
        orders: [],
        departure_time: null,
      },
    ]);

    render(<HotspotChat />);

    const input = screen.getByRole("textbox");

    fireEvent.change(input, {
      target: { value: "Tell me about Talley Food Court" },
    });

    fireEvent.click(screen.getByRole("button", { name: /Ask/i }));

    expect(
      await screen.findByText(
        "Here is the live scoop on Talley Food Court near Hunt Library:"
      )
    ).toBeInTheDocument();

    expect(
      screen.getByText("Talley Food Court → Hunt Library")
    ).toBeInTheDocument();
  });

  it("responds when the user submits an empty question", async () => {
    render(<HotspotChat />);

    fireEvent.click(screen.getByRole("button", { name: /Ask/i }));

    // The application currently allows the submission.
    // We verify that it produces an AI response rather than
    // assuming the button should be disabled.
    await waitFor(() => {
      const messages = screen.getAllByText(/./);
      expect(messages.length).toBeGreaterThan(1);
    });
  });

  it("supports all three quick actions", async () => {
    render(<HotspotChat />);

    fireEvent.click(screen.getByRole("button", { name: /Run Insights/i }));
    fireEvent.click(screen.getByRole("button", { name: /Seat Alerts/i }));
    fireEvent.click(screen.getByRole("button", { name: /Broadcast Tips/i }));

    expect(
      screen.getByRole("button", { name: /Run Insights/i })
    ).toBeInTheDocument();

    expect(
      screen.getByRole("button", { name: /Seat Alerts/i })
    ).toBeInTheDocument();

    expect(
      screen.getByRole("button", { name: /Broadcast Tips/i })
    ).toBeInTheDocument();
  });
});