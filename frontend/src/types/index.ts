export interface BulletPoint {
  text: string
}

export interface PostMeta {
  author_handle: string
  text: string
  image_url: string | null
}

export interface ExplainResponse {
  post: PostMeta
  bullets: BulletPoint[]
  sources: string[]
}
