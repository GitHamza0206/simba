import { defineConfig } from "tsup";
import { copyFileSync, mkdirSync } from "fs";

export default defineConfig({
  entry: ["src/index.ts"],
  format: ["esm"],
  dts: true,
  splitting: false,
  sourcemap: true,
  clean: true,
  external: ["react", "react-dom"],
  esbuildOptions(options) {
    options.jsx = "automatic";
  },
  onSuccess: async () => {
    // Copy CSS file to dist
    mkdirSync("dist", { recursive: true });
    copyFileSync("src/styles/simba-chat.css", "dist/simba-chat.css");
    console.log("Copied simba-chat.css to dist/");
  },
});
