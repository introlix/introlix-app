interface ChatProps {
  params: { chatId: string }
}

export default function ChatDetailPage({ params }: ChatProps) {
  return <h1>Chat ID: {params.chatId}</h1>
}