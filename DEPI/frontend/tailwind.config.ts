import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./services/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        background: "#F5F5F7",
        foreground: "#111111",
        card: "#FFFFFF",
        border: "#EAEAF0",
        muted: "#7B7B88",
        accent: {
          100: "#F4EEFF",
          200: "#E8DBFF",
          300: "#D9C5FF",
          400: "#C5A6FF",
          500: "#AE84FF",
        },
      },
      borderRadius: {
        xl: "1.25rem",
        "2xl": "1.5rem",
        "3xl": "1.75rem",
      },
      boxShadow: {
        soft: "0 10px 30px rgba(25, 20, 45, 0.06)",
        card: "0 8px 24px rgba(25, 20, 45, 0.05)",
        float: "0 14px 40px rgba(25, 20, 45, 0.08)",
      },
      backgroundImage: {
        "accent-gradient": "linear-gradient(135deg, #E9DFFF 0%, #B892FF 100%)",
      },
      fontWeight: {
        medium: "500",
        semibold: "600",
      },
    },
  },
};

export default config;
