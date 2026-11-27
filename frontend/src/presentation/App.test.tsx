import { render, screen } from "@testing-library/react";
import { App } from "./App";

test("shows the permanent demo banner", () => {
  render(<App />);
  expect(screen.getByRole("note")).toHaveTextContent(
    "Synthetic data. Demo only. Not for clinical use.",
  );
});
