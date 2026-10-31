export type Item = {
  id: string
  lane: string
  // artifact name -> status ("accepted", "draft", "pass", ...)
  artifacts: { name: string; state: string }[]
  next: string
}

// The /sdlc-* stage running in the current turn.
export type Active = { stage: string; args: string }

declare module 'claude-code' {
  interface PluginState {
    'ai-native-sdlc': {
      items: Shaped<Item[]>
      active: Active | null
      error: string | null
    }
  }
}
