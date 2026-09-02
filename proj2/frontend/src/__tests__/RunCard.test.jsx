import { render, screen } from "@testing-library/react";
import React from "react";
import RunCard from "../components/RunCard";

describe("RunCard ETA rendering", () => {
  it("does not display an invalid non-numeric ETA", () => {
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

    const etaText = screen.getByText(/ETA:/i).parentElement.textContent;

    // Invalid ETA should not be displayed as if it were a valid ETA.
    expect(etaText).not.toMatch(/asd123/);
  });

  it("does not render literal 'undefined' or 'null' when ETA is missing", () => {
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

    const etaText = screen.getByText(/ETA:/i).parentElement.textContent;

    expect(etaText).not.toMatch(/undefined|null/);
  });
});
