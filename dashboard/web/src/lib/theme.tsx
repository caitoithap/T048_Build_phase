// Chế độ sáng/tối. Mặc định theo hệ điều hành; chọn tay thì nhớ trong trình duyệt này.
import { createContext, useContext, useEffect, useState, type ReactNode } from "react";

const KEY = "m22-theme";
const ThemeContext = createContext({ dark: false, setDark: (_: boolean) => {} });

function initial(): boolean {
  try {
    const saved = localStorage.getItem(KEY);
    if (saved) return saved === "dark";
  } catch {
    // trình duyệt chặn bộ nhớ: theo hệ điều hành
  }
  return window.matchMedia("(prefers-color-scheme: dark)").matches;
}

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [dark, setState] = useState(initial);

  useEffect(() => {
    document.documentElement.classList.toggle("dark", dark);
  }, [dark]);

  const setDark = (value: boolean) => {
    try {
      localStorage.setItem(KEY, value ? "dark" : "light");
    } catch {
      // không nhớ được thì thôi, chế độ vẫn đổi
    }
    setState(value);
  };

  return <ThemeContext.Provider value={{ dark, setDark }}>{children}</ThemeContext.Provider>;
}

export const useTheme = () => useContext(ThemeContext);
