import { useMutation } from '@tanstack/react-query'
import { explainPost } from '../api/explainApi'

export function useExplain() {
  return useMutation({
    mutationFn: (url: string) => explainPost(url),
  })
}
