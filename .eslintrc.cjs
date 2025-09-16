module.exports = {
  root: true,
  env: { es2021: true, browser: true, node: true },
  extends: [
    'eslint:recommended',
  ],
  parserOptions: { ecmaVersion: 2021, sourceType: 'module' },
  ignorePatterns: [
    'node_modules/',
    'dist/',
    '**/*.min.js',
  ],
  rules: {
    'no-unused-vars': ['warn', { argsIgnorePattern: '^_' }],
    'no-undef': 'error',
    'no-console': 'off'
  },
  overrides: [
    {
      files: ['**/*.ts', '**/*.tsx'],
      parser: '@typescript-eslint/parser',
      plugins: ['@typescript-eslint'],
      extends: [
        'plugin:@typescript-eslint/recommended'
      ]
    }
  ]
};

