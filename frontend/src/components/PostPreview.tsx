import type { PostMeta } from '../types'

interface Props {
  post: PostMeta
}

export function PostPreview({ post }: Props) {
  const initial = post.author_handle[0]?.toUpperCase() ?? '?'

  return (
    <div className="rounded-2xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 p-5 shadow-sm">
      <div className="flex items-start gap-3 mb-3">
        <div className="w-10 h-10 rounded-full bg-sky-500 flex items-center justify-center text-white font-semibold flex-shrink-0">
          {initial}
        </div>
        <div className="min-w-0">
          <p className="text-sm text-gray-500 dark:text-gray-400">@{post.author_handle}</p>
        </div>
      </div>

      <p className="text-gray-800 dark:text-gray-200 text-sm leading-relaxed whitespace-pre-wrap mb-3">
        {post.text}
      </p>

      {post.image_url && (
        <div className="rounded-xl overflow-hidden border border-gray-100 dark:border-gray-800">
          <img
            src={post.image_url}
            alt="Post image"
            className="w-full object-cover max-h-64"
          />
        </div>
      )}
    </div>
  )
}
