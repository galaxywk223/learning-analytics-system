module.exports = {
  root: true,
  env: {
    browser: true,
    node: true,
    es2022: true,
  },
  parser: "vue-eslint-parser",
  parserOptions: {
    parser: "@typescript-eslint/parser",
    ecmaVersion: 2022,
    sourceType: "module",
    extraFileExtensions: [".vue"],
  },
  extends: ["plugin:vue/vue3-recommended", "@vue/eslint-config-prettier"],
  rules: {},
};
