interface ChatProps {
  params: { chatid: string }
}

export default async function ChatDetailPage({ params }: ChatProps) {
  const { chatid } = await params
  return <h1>Chat ID: {chatid}</h1>
}