import js from "@eslint/js";
import globals from "globals";

export default [
  {
    ignores: [
      "node_modules/**",
      "artifacts/**",
      "site/public/search/**",
      "articles/**",
      "config/**",
      "examples/**",
      ".agents/**",
      "utils/**",
      "skills/**"
    ]
  },
  js.configs.recommended,
  {
    files: ["**/*.{js,mjs,cjs}"],
    languageOptions: {
      globals: {
        ...globals.node
      }
    }
  }
];
