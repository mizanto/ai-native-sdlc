import { expect, test } from 'claude-code/testing'

const PANE = {
  plugin: 'ai-native-sdlc',
  component: 'Pane',
  requestId: 'sdlc',
  props: {
    title: 'SDLC',
    isFocused: false,
    bodyColumns: 60,
    placement: 'dock',
    scroll: { offset: 0, bodyRows: 20 },
    view: {},
  },
} as const

const STATUS = `| ID | Lane | Artifacts | Next |
|---|---|---|---|
| CLM-7-claim-status | full | intent:accepted spec:draft | /sdlc-accept CLM-7-claim-status spec |
`

test('the pane shows each item, its chain and the next step', async ($, on) => {
  on('command.register', () => ({ value: { command: 'sdlc-pane' } }))
  on('ui.open', () => ({ value: { isPlaced: true } }))
  on('process.run', () => ({ value: { exitCode: 0, stdout: STATUS, stderr: '' } }))
  on('session.start', (_, e) => ({ cwd: e.cwd }))
  on('command.run', () => ({ text: '' }))

  await $.session.start({ cwd: '/', surface: 'desktop', isInteractive: true })
  await $.command.run({ command: 'sdlc-pane', args: '' })

  const ui = await $.ui.mount({ ...PANE, surface: 'desktop' })
  expect((await ui.find({ type: 'Text', text: /^CLM-7-claim-status/ }))).toBeTruthy()
  expect((await ui.find({ type: 'Text', text: /awaiting your approval/ }))).toBeTruthy()
  expect((await ui.find({ type: 'Text', text: /Next: \/sdlc-accept CLM-7-claim-status spec/ }))).toBeTruthy()
  await ui.unmount()
})

test('an empty repo says how to start', async ($, on) => {
  const ui = await $.ui.mount({ ...PANE, surface: 'terminal' })
  expect((await ui.find({ type: 'Text', text: /No work items/ }))).toBeTruthy()
  await ui.unmount()
})
