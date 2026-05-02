import { useMutation, useQuery } from '@tanstack/react-query'
import { explainPost, fetchModels } from '../api/explainApi'

export function useModels() {
  return useQuery({
    queryKey: ['models'],
    queryFn: fetchModels,
    staleTime: Infinity,
  })
}

export function useExplain() {
  return useMutation({
    mutationFn: ({ url, model }: { url: string; model: string }) =>
      explainPost(url, model),
  })
}
