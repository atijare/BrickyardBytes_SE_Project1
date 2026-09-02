import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import React from "react";
import { MemoryRouter } from "react-router-dom";
import { describe, it, expect, beforeEach, vi } from "vitest";

const mockRegister = vi.fn();

vi.mock("../hooks/useAuth", () => ({
  useAuth: () => ({ register: mockRegister }),
}));

import AuthForm from "../components/AuthForm";

describe("Registration email case handling", () => {
  beforeEach(() => {
    vi.clearAllMocks();

    mockRegister.mockResolvedValue({
      user: { username: "user@ncsu.edu" },
    });
  });

  it("normalizes email to lowercase before registration", async () => {
    render(
      <MemoryRouter>
        <AuthForm isLogin={false} />
      </MemoryRouter>
    );

    const emailInput = screen.getByLabelText(/email/i);
    const passwordInput = screen.getByLabelText(/password/i);

    fireEvent.change(emailInput, {
      target: { value: "User@NCSU.edu" },
    });

    fireEvent.change(passwordInput, {
      target: { value: "Password123!" },
    });

    fireEvent.click(
      screen.getByRole("button", { name: /register/i })
    );

    await waitFor(() => {
      expect(mockRegister).toHaveBeenCalledTimes(1);
    });

    expect(mockRegister).toHaveBeenCalledWith(
      "user@ncsu.edu",
      "Password123!"
    );
  });

  it("treats differently-cased versions of the same email consistently", async () => {
    render(
      <MemoryRouter>
        <AuthForm isLogin={false} />
      </MemoryRouter>
    );

    const emailInput = screen.getByLabelText(/email/i);
    const passwordInput = screen.getByLabelText(/password/i);

    fireEvent.change(emailInput, {
      target: { value: "USER@ncsu.EDU" },
    });

    fireEvent.change(passwordInput, {
      target: { value: "Password123!" },
    });

    fireEvent.click(
      screen.getByRole("button", { name: /register/i })
    );

    await waitFor(() => {
      expect(mockRegister).toHaveBeenCalledTimes(1);
    });

    const [email] = mockRegister.mock.calls[0];

    expect(email).toBe("user@ncsu.edu");
    expect(email).not.toBe("USER@ncsu.EDU");
  });
});
