import jsESlint from '@eslint/js'
import tsESlint from 'typescript-eslint'
import pluginVue from 'eslint-plugin-vue'
import eslintConfigPrettier from 'eslint-config-prettier'

export default [
  {
    ignores: ['.output/', '.serverless/', '.nuxt/'],
  },
  jsESlint.configs.recommended,
  ...tsESlint.configs.recommended,
  ...pluginVue.configs['flat/recommended'],
  {
    rules: {
      'vue/require-default-prop': 'off',
      'vue/multi-word-component-names': 'off',
    },
  },
  eslintConfigPrettier, // eslint-config-prettier last
]
