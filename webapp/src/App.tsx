import Nav from "./components/Nav";
import Hero from "./components/Hero";
import ToolPage from "./components/ToolPage";
import ComoFunciona from "./components/ComoFunciona";
import Footer from "./components/Footer";
import { useHashRoute } from "./useHashRoute";
import { useTheme } from "./useTheme";

export default function App() {
  const { theme, toggle } = useTheme();
  const { route, navigate } = useHashRoute();

  return (
    <>
      <Nav route={route} navigate={navigate} theme={theme} toggleTheme={toggle} />
      <div className="app">
        {route === "como-funciona" ? (
          <ComoFunciona navigate={navigate} />
        ) : (
          <>
            <Hero navigate={navigate} />
            <ToolPage />
          </>
        )}
        <Footer />
      </div>
    </>
  );
}
