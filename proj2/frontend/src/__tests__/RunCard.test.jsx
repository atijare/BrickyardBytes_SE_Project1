import { render, screen } from "@testing-library/react";
import React from "react";
import RunCard from "../components/RunCard";

describe("RunCard ETA rendering", () => {
  it("renders numeric ETA without crashing and shows value", () => {
    const run = {
      id: "r1",
      restaurant: "Place",
      drop_point: "Spot",
      eta: "asd123",
    };

    render(
      <RunCard
        run={run}
        joinedRuns={[]}
      />
    );

    const strong = screen.getByText(/ETA:/i);
    expect(strong).toBeInTheDocument();

    // Parent paragraph should include the numeric ETA
    expect(strong.parentElement.textContent).toMatch(/ETA:\s*asd123/);
  });

  it("does not render literal 'undefined' or 'null' when ETA missing", () => {
    const run = {
      id: "r2",
      restaurant: "Place",
      drop_point: "Spot",
    };

    render(
      <RunCard
        run={run}
        joinedRuns={[]}
      />
    );

    const strong = screen.getByText(/ETA:/i);
    expect(strong).toBeInTheDocument();

    expect(strong.parentElement.textContent).not.toMatch(/undefined|null/);
  });
});