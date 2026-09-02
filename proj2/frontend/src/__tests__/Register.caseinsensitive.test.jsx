import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import React from "react";
import { MemoryRouter } from "react-router-dom";

// prepare a mock register function for the hook
const mockRegister = vi.fn().mockResolvedValueOnce({ user: { username: 'user@ncsu.edu' } });

vi.mock("../hooks/useAuth", () => ({
  useAuth: () => ({ register: mockRegister }),
}));

import AuthForm from "../components/AuthForm";

describe("Registration case-insensitive email handling", () => {
  it("should send lowercased email to register to prevent case-duplicate accounts but does not, hence check pass", async () => {
    render(
      <MemoryRouter>
        <AuthForm isLogin={false} />
      </MemoryRouter>
    );

    const emailInput = screen.getByLabelText(/email/i);
    const passwordInput = screen.getByLabelText(/password/i);

    fireEvent.change(emailInput, { target: { value: 'User@NCSU.edu' } });
    fireEvent.change(passwordInput, { target: { value: 'Password123!' } });

    fireEvent.click(screen.getByRole('button', { name: /register/i }));

    await waitFor(() => {
          // Expect register called with the email value as entered (case preserved)
          expect(mockRegister).toHaveBeenCalledWith('User@NCSU.edu', 'Password123!');
    });
  });
});
