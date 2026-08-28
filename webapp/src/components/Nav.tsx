import Logo from "./Logo";
import type { Route } from "../useHashRoute";
import type { Theme } from "../useTheme";

interface Props {
  route: Route;
  navigate: (r: Route) => void;
  theme: Theme;
  toggleTheme: () => void;
}

export default function Nav({ route, navigate, theme, toggleTheme }: Props) {
  return (
    <div className="nav-wrap">
      <div className="navbar">
        <Logo onClick={() => navigate("home")} />
        <div className="nav-links">
          <button
            type="button"
            className={`nav-link ${route === "como-funciona" ? "active" : ""}`}
            onClick={() => navigate("como-funciona")}
          >
            Como funciona
          </button>
          <button
            type="button"
            className="theme-toggle"
            onClick={toggleTheme}
            title={theme === "light" ? "Mudar para tema escuro" : "Mudar para tema claro"}
            aria-label="Alternar tema"
          >
            {theme === "light" ? (
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" />
              </svg>
            ) : (
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                <circle cx="12" cy="12" r="4" />
                <path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M6.34 17.66l-1.41 1.41M19.07 4.93l-1.41 1.41" />
              </svg>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
