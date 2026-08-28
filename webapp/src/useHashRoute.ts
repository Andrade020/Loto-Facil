import { useEffect, useState } from "react";

/**
 * Roteamento minimo por hash (sem dependencia externa): funciona em
 * qualquer hospedagem estatica, sem precisar de rewrite de servidor.
 */
export type Route = "home" | "como-funciona";

function parseHash(): Route {
  return window.location.hash.replace(/^#\/?/, "") === "como-funciona"
    ? "como-funciona"
    : "home";
}

export function useHashRoute() {
  const [route, setRoute] = useState<Route>(parseHash);

  useEffect(() => {
    const onHashChange = () => setRoute(parseHash());
    window.addEventListener("hashchange", onHashChange);
    return () => window.removeEventListener("hashchange", onHashChange);
  }, []);

  const navigate = (r: Route) => {
    window.location.hash = r === "home" ? "/" : `/${r}`;
    window.scrollTo({ top: 0 });
  };

  return { route, navigate };
}
