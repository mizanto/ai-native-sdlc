import { atom, read, update } from 'claude-code'
import type { EngineInterface, Register } from 'claude-code'

import type { Active, Item } from '../types'

const PANE = 'sdlc'
// Stages per lane, as LANES in sdlc_artifact.py.
const LANES: Record<string, string[]> = {
  full: ['intent', 'spec', 'plan', 'build', 'verify', 'review'],
  standard: ['plan', 'build', 'verify', 'review'],
  bugfix: ['bug', 'build', 'verify', 'review'],
}

// Change the tag when Item's fields change.
const items = atom({ plugin: 'ai-native-sdlc', key: 'items' } as const, [], { shape: 'items-1' })
const active = atom({ plugin: 'ai-native-sdlc', key: 'active' } as const, null)
const error = atom({ plugin: 'ai-native-sdlc', key: 'error' } as const, null)

// Parses the markdown table `sdlc_artifact.py status` prints.
export function parseStatus(stdout: string): Item[] {
  return stdout
    .split('\n')
    .filter(line => line.startsWith('| ') && !line.startsWith('| ID ') && !line.startsWith('|---'))
    .map(line => {
      const [id, lane, arts, next] = line.slice(1, -1).split(' | ').map(cell => cell.trim())
      const artifacts = arts === '—' ? [] : arts.split(' ').map(pair => {
        const [name, state] = pair.split(':')
        return { name, state: state || '?' }
      })
      return { id, lane, artifacts, next }
    })
}

async function refresh($: EngineInterface) {
  const script = `${$.plugin.root}/scripts/sdlc_artifact.py`
  try {
    const { exitCode, stdout, stderr } = await $.process.run(['python3', script, 'status'])
    if (exitCode !== 0) {
      await update($, error, () => stderr.trim() || `status exited ${exitCode}`)
      return
    }
    await update($, items, () => parseStatus(stdout))
    await update($, error, () => null)
  } catch (err) {
    await update($, error, () => String(err))
  }
}

export type Progress = { done: number; current: string | null; isWaiting: boolean; isBlocked: boolean }

// Reads where an item stands from its Next step: the stage it names is the current one.
export function progress(item: Item): Progress {
  const chain = LANES[item.lane] ?? []
  if (item.next.startsWith('done')) return { done: chain.length, current: null, isWaiting: false, isBlocked: false }
  const accept = /^\/sdlc-accept \S+ ([a-z]+)/.exec(item.next)
  const stage = accept?.[1] ?? /^\/sdlc-([a-z]+)/.exec(item.next)?.[1] ?? null
  const index = stage ? chain.indexOf(stage) : -1
  return {
    done: Math.max(0, index),
    current: index >= 0 ? stage : null,
    isWaiting: Boolean(accept),
    isBlocked: /\((fix|revise)/.test(item.next),
  }
}

function fit(text: string, width: number): string {
  return text.length >= width ? text.slice(0, width - 1) + ' ' : text.padEnd(width)
}

export const register: Register = on => {
  on('session.start', async ($, e, next) => {
    await $.command.register({ name: 'sdlc-pane', description: 'Show the AI-Native SDLC pane' })
    void $.ui.open({ id: PANE, title: 'SDLC' })
    void refresh($)

    return next(e)
  })

  on('command.run', { command: 'sdlc-pane' }, async $ => {
    await $.ui.open({ id: PANE, title: 'SDLC' })
    await refresh($)

    return { text: 'SDLC pane opened.' }
  })

  on('skill.prompt', async ($, e, next) => {
    const stage = /sdlc-([a-z]+)$/.exec(e.skill)?.[1]
    if (stage && stage !== 'status') {
      const args = /^\/?\S*sdlc-[a-z]+\s+(\S+)/.exec(e.text)?.[1] ?? ''
      const now: Active = { stage, args }
      await update($, active, () => now)
      $.ui.status(`SDLC: ${stage}${args ? ` · ${args}` : ''}`)
    }

    return next(e)
  })

  on('turn.complete', async ($, e, next) => {
    if (await read($, active)) {
      await update($, active, () => null)
      $.ui.status(undefined)
    }
    await refresh($)

    return next(e)
  })

  on('ui.render', { component: 'Pane', requestId: PANE }, async ($, e) => {
    const { Box, Text, Button } = $.ui.resolve(e)
    const list = await read($, items)
    const now = await read($, active)
    const problem = await read($, error)

    return (
      <Box flexDirection="column">
        {now && (
          <Text color="cyan" bold>
            ▶ Running: /sdlc-{now.stage} {now.args}
          </Text>
        )}
        {problem && <Text color="red">{problem}</Text>}
        {!problem && list.length === 0 && (
          <Text dimColor>No work items in docs/sdlc. Start with /sdlc-intent, /sdlc-plan or /sdlc-maintain.</Text>
        )}
        {list.map(item => {
          const chain = LANES[item.lane] ?? []
          const p = progress(item)
          const width = Math.max(4, Math.min(10, Math.floor((e.props.bodyColumns - 2) / Math.max(1, chain.length))))
          const isRunning = (name: string) => now?.stage === name && item.id.startsWith(now.args)
          const color = (i: number, name: string) =>
            i < p.done ? 'green' : name !== p.current ? undefined :
            isRunning(name) ? 'cyan' : p.isBlocked ? 'red' : p.isWaiting ? 'yellow' : 'cyan'
          const state = p.current === null ? 'complete' :
            chain.some(isRunning) ? `running ${p.current}` :
            p.isBlocked ? `${p.current} needs rework` :
            p.isWaiting ? `${p.current} awaiting your approval` : `ready for ${p.current}`
          return (
            <Box flexDirection="column" marginTop={1}>
              <Text>
                <Text bold>{item.id}</Text> <Text dimColor>{item.lane} · {p.done}/{chain.length} · {state}</Text>
              </Text>
              <Text>
                {chain.map((name, i) => (
                  <Text color={color(i, name)} dimColor={i > p.done || (i === p.done && p.current === null)}>
                    {fit(i < p.done || name === p.current ? '█'.repeat(width - 1) : '░'.repeat(width - 1), width)}
                  </Text>
                ))}
              </Text>
              <Text>
                {chain.map((name, i) => (
                  <Text color={color(i, name)} bold={name === p.current} dimColor={i > p.done}>
                    {fit(name, width)}
                  </Text>
                ))}
              </Text>
              {p.current !== null && <Text dimColor>Next: {item.next}</Text>}
            </Box>
          )
        })}
        <Box marginTop={1}>
          <Button key="refresh" label="Refresh" onPress={() => refresh($)} />
        </Box>
      </Box>
    )
  })
}
